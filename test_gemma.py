"""Offline validation/UI tests; opt-in real API smoke test with --live."""
import io
import json
import os
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from PIL import Image
from analyzer import AnalysisError, analyze_message, parse_response, prepare_image

MESSAGE = "Send your password now."


def payload():
    return dict(risk_level="High", summary="Requests a password.",
                red_flags=[dict(title="Credential request", quote="your password", source="text",
                                explanation="Passwords should not be shared in a message.")],
                recommended_actions=["Contact the organization through a known channel."],
                image_transcription="", limitations="Sender identity is not verified.")


class BackendTests(unittest.TestCase):
    def test_valid_and_fenced_json(self):
        for raw in (json.dumps(payload()), '```json\n' + json.dumps(payload()) + '\n```'):
            self.assertEqual(parse_response(raw, MESSAGE, False).risk_level, "High")

    def test_rejects_invented_evidence(self):
        with self.assertRaises(AnalysisError):
            parse_response(json.dumps(payload()), "Hello there", False)

    def test_rejects_invalid_output(self):
        for raw in ("not json", "{}", "[]"):
            with self.assertRaises(AnalysisError):
                parse_response(raw, MESSAGE, False)

    def test_risk_requires_evidence(self):
        data = payload()
        data['red_flags'] = []
        with self.assertRaises(AnalysisError):
            parse_response(json.dumps(data), MESSAGE, False)

    def test_uncertain_allowed(self):
        data = payload()
        data.update(risk_level="Uncertain", red_flags=[])
        self.assertEqual(parse_response(json.dumps(data), "Hi", False).risk_level, "Uncertain")

    def test_image_evidence(self):
        data = payload()
        data['red_flags'][0]['source'] = 'image'
        data['image_transcription'] = MESSAGE
        self.assertEqual(len(parse_response(json.dumps(data), '', True).red_flags), 1)
        with self.assertRaises(AnalysisError):
            parse_response(json.dumps(data), '', False)

    def test_image_validation(self):
        out = io.BytesIO()
        Image.new('RGB', (20, 20), 'white').save(out, format='PNG')
        self.assertEqual(prepare_image(out.getvalue())[1], 'image/png')
        with self.assertRaises(AnalysisError):
            prepare_image(b'not an image')

    def test_empty_input(self):
        with self.assertRaises(AnalysisError):
            analyze_message('   ')

    @patch.dict(os.environ, {'GEMINI_API_KEY': ''})
    def test_missing_key(self):
        with self.assertRaisesRegex(AnalysisError, 'GEMINI_API_KEY'):
            analyze_message(MESSAGE)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'unit-test-placeholder'})
    @patch('analyzer.genai.Client')
    def test_sdk_call_and_safe_failure(self, client):
        model = client.return_value.__enter__.return_value.models
        model.generate_content.return_value.text = json.dumps(payload())
        self.assertEqual(analyze_message(MESSAGE).risk_level, 'High')
        self.assertEqual(model.generate_content.call_args.kwargs['model'], 'gemma-4-26b-a4b-it')
        model.generate_content.side_effect = RuntimeError('private provider error')
        with self.assertRaises(AnalysisError) as ctx:
            analyze_message(MESSAGE)
        self.assertNotIn('private', str(ctx.exception))

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'unit-test-placeholder'})
    @patch('analyzer.genai.Client')
    def test_safe_diagnostics(self, client):
        model = client.return_value.__enter__.return_value.models
        for detail, expected in [
            ('CERTIFICATE_VERIFY_FAILED private-secret', 'HTTPS certificate'),
            ('API key not valid private-secret', 'API key is invalid'),
            ('request timed out private-secret', 'timed out'),
        ]:
            model.generate_content.side_effect = RuntimeError(detail)
            with self.assertRaises(AnalysisError) as ctx:
                analyze_message(MESSAGE)
            self.assertIn(expected, str(ctx.exception))
            self.assertNotIn('private-secret', str(ctx.exception))

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'unit-test-placeholder'})
    @patch('analyzer.genai.Client')
    def test_grounding_retry_recovers(self, client):
        model = client.return_value.__enter__.return_value.models
        bad = payload()
        bad['red_flags'][0]['quote'] = 'invented phrase'
        model.generate_content.side_effect = [
            SimpleNamespace(text=json.dumps(bad)),
            SimpleNamespace(text=json.dumps(payload())),
        ]
        self.assertEqual(analyze_message(MESSAGE).risk_level, 'High')
        self.assertEqual(model.generate_content.call_count, 2)
        self.assertIn('previous response failed', model.generate_content.call_args.kwargs['config'].system_instruction)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'unit-test-placeholder'})
    @patch('analyzer.genai.Client')
    def test_grounding_retry_is_bounded(self, client):
        model = client.return_value.__enter__.return_value.models
        bad = payload()
        bad['red_flags'][0]['quote'] = 'invented phrase'
        model.generate_content.return_value.text = json.dumps(bad)
        with self.assertRaisesRegex(AnalysisError, 'after two attempts'):
            analyze_message(MESSAGE)
        self.assertEqual(model.generate_content.call_count, 2)


class HighlightTests(unittest.TestCase):
    def test_overlapping_repeated_quotes_and_source_filter(self):
        from highlighting import evidence_segments
        from analyzer import RedFlag
        flags = [RedFlag(title='One', quote='aba', source='text', explanation='Reason'),
                 RedFlag(title='Two', quote='ba', source='text', explanation='Reason'),
                 RedFlag(title='Image', quote='aba', source='image', explanation='Reason')]
        parts = evidence_segments('ababa <tag>\n', flags, 'text')
        self.assertEqual(''.join(p for p, _ in parts), 'ababa <tag>\n')
        self.assertTrue(any(ids == (0, 1) for _, ids in parts))
        self.assertFalse(any(2 in ids for _, ids in parts))

    def test_untrusted_content_is_escaped(self):
        from highlighting import highlighting_html
        from analyzer import RedFlag
        quote = '<script>alert(1)</script>'
        flag = RedFlag(title=quote, quote=quote, source='text', explanation=quote)
        output = highlighting_html(quote, [flag])
        self.assertNotIn(quote, output)
        self.assertIn('&lt;script&gt;', output)
        self.assertIn('aria-pressed="false"', output)

    def test_unmatched_quotes_do_not_create_highlights(self):
        from highlighting import evidence_segments
        self.assertEqual(evidence_segments('Hello', [], 'text'), [('Hello', ())])


class FrontendTests(unittest.TestCase):
    def test_start_example_clear_and_empty_submission(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file('app.py').run()
        self.assertEqual(len(app.exception), 0)
        next(b for b in app.button if 'Delivery alert' in b.label).click().run()
        self.assertIn('Delivery failed', app.text_area[0].value)
        next(b for b in app.button if b.label == 'Clear').click().run()
        self.assertEqual(app.text_area[0].value, '')
        next(b for b in app.button if 'Analyze Message' in b.label).click().run()
        self.assertIn('Paste a message', app.error[0].value)

    @patch('analyzer.analyze_message')
    def test_result_dashboard_and_stale_input(self, analyze):
        from streamlit.testing.v1 import AppTest
        analyze.return_value = parse_response(json.dumps(payload()), MESSAGE, False)
        app = AppTest.from_file('app.py').run()
        app.text_area[0].set_value(MESSAGE).run()
        next(b for b in app.button if 'Analyze Message' in b.label).click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any(s.value == 'Evidence Mode' for s in app.subheader))
        app.text_area[0].set_value('Different message').run()
        self.assertTrue(any('input changed' in s.value for s in app.info))


if __name__ == '__main__':
    if '--live' in sys.argv:
        if not os.environ.get('GEMINI_API_KEY', '').strip():
            print('SKIPPED: set GEMINI_API_KEY before running the live test.')
            sys.exit(0)
        try:
            result = analyze_message(MESSAGE)
            print(result.model_dump_json(indent=2))
            print('PASS: real Gemma API call and validated response.')
        except AnalysisError as exc:
            print(f'FAIL: {exc}')
            sys.exit(1)
    else:
        unittest.main()
