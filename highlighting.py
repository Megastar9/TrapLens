"""Safe, self-contained interactive evidence highlighting (no external assets)."""
import html


def evidence_segments(text, flags, source):
    """Partition source into exact spans, retaining every overlapping finding."""
    spans = []
    for index, flag in enumerate(flags):
        if flag.source != source or not flag.quote:
            continue
        start = text.find(flag.quote)
        while start != -1:
            spans.append((start, start + len(flag.quote), index))
            start = text.find(flag.quote, start + 1)
    boundaries = sorted({0, len(text)} | {p for a, b, _ in spans for p in (a, b)})
    return [(text[a:b], tuple(sorted({i for x, y, i in spans if x <= a and b <= y})))
            for a, b in zip(boundaries, boundaries[1:])]


def highlighting_html(text, flags, source="text"):
    escape = html.escape
    fragments = []
    for phrase, indices in evidence_segments(text, flags, source):
        if not indices:
            fragments.append(escape(phrase))
            continue
        ids = ','.join(map(str, indices))
        label = 'Explain: ' + '; '.join(flags[i].title for i in indices)
        fragments.append(f'<button class="highlight" data-findings="{ids}" aria-pressed="false" '
                         f'aria-controls="details" aria-label="{escape(label, quote=True)}">{escape(phrase)}</button>')
    details = []
    for index, flag in enumerate(flags):
        if flag.source == source:
            details.append(f'<section data-detail="{index}" hidden><h3>{escape(flag.title)}</h3>'
                           f'<blockquote>{escape(flag.quote)}</blockquote><p>{escape(flag.explanation)}</p></section>')
    label = 'Original message' if source == 'text' else 'Screenshot transcription · AI-generated'
    return '''<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;color:#edf3f8;background:#111b26;font:15px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    .workspace{border:1px solid #293748;border-radius:14px;padding:20px}
    .label{color:#a6b5c6;font-size:12px;margin:0 0 12px}.message{white-space:pre-wrap;overflow-wrap:anywhere;max-height:245px;overflow:auto;padding:4px}
    .highlight{display:inline;font:inherit;color:#ffe1a1;background:#493c26;border:0;border-bottom:2px solid #d5aa58;border-radius:3px;padding:1px 2px;cursor:pointer;white-space:pre-wrap;overflow-wrap:anywhere}
    .highlight:hover,.highlight[aria-pressed="true"]{background:#70582e;color:#fff}.highlight:focus-visible{outline:2px solid #93f5c5;outline-offset:3px}
    #details{border-top:1px solid #293748;margin-top:18px;padding-top:12px;max-height:210px;overflow:auto;overflow-wrap:anywhere}
    h3{font-size:16px;margin:0 0 6px}p{margin:0 0 12px}blockquote{white-space:pre-wrap;margin:8px 0;padding-left:12px;border-left:2px solid #93f5c5;color:#c9e9db}
    #reset{background:transparent;border:1px solid #526278;border-radius:5px;color:#edf3f8;padding:5px 9px;cursor:pointer;margin-top:12px}
    </style></head><body><div class="workspace"><p class="label">''' + label + '''</p><div class="message">''' + ''.join(fragments) + '''</div>
    <div id="details" role="region" aria-label="Selected evidence" aria-live="polite" aria-atomic="true"><p id="hint" class="label">Select a highlighted phrase to see why it was flagged. Use Tab and Enter with a keyboard.</p>''' + ''.join(details) + '''</div><button id="reset" hidden>Clear selection</button></div>
    <script>
    const highlights = [...document.querySelectorAll('.highlight')];
    const details = [...document.querySelectorAll('[data-detail]')];
    const hint = document.getElementById('hint');
    const reset = document.getElementById('reset');
    function select(ids) {
      details.forEach(el => el.hidden = !ids.includes(el.dataset.detail));
      highlights.forEach(el => el.setAttribute('aria-pressed', String(el.dataset.findings.split(',').some(id => ids.includes(id)))));
      hint.hidden = ids.length > 0;
      reset.hidden = ids.length === 0;
    }
    highlights.forEach(el => el.addEventListener('click', () => select(el.dataset.findings.split(','))));
    reset.addEventListener('click', () => { select([]); if(highlights.length) highlights[0].focus(); });
    if(!highlights.length) hint.textContent = 'No quoted warning signs were identified in this source. This does not establish authenticity.';
    </script></body></html>'''
