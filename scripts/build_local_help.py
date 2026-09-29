#!/usr/bin/env python3
"""Build the self-contained OpenCobolIDE HTML manual from the RST sources.

This intentionally uses only the Python standard library so rebuilding the
Debian package does not require Sphinx or docutils.  It supports the RST
constructs used by this project's user documentation and embeds screenshots as
data URLs, leaving the resulting manual usable without a network connection.
"""

import base64
import html
import mimetypes
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'doc' / 'source'
OUTPUT = ROOT / 'doc' / 'OpenCobolIDE-modern9.html'
PAGES = (
    ('index', 'Documentation overview'),
    ('getting_started', 'Getting started'),
    ('settings', 'Application preferences'),
    ('advanced', 'Advanced topics'),
    ('tipsandtricks', 'Tips and tricks'),
    ('faq', 'Frequently asked questions'),
    ('hacking', 'Reset the window layout'),
    ('download', 'Download and install'),
    ('contribute', 'Contributing'),
    ('license', 'License'),
    ('whats_new', "What's new"),
)


def slug(value):
    value = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return value or 'section'


def inline(text, links):
    """Convert the small set of inline RST markup used in the manual."""
    placeholders = []

    def save(fragment):
        token = f'\x00{len(placeholders)}\x00'
        placeholders.append(fragment)
        return token

    text = re.sub(
        r'``([^`]+)``',
        lambda match: save('<code>%s</code>' % html.escape(match.group(1))),
        text)
    text = html.escape(text, quote=False)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)

    def external(match):
        label = match.group(1)
        url = links.get(label, links.get(label.strip('`')))
        if not url:
            return html.escape(label)
        return '<a href="%s">%s</a>' % (html.escape(url, quote=True),
                                         html.escape(label.strip('`')))

    text = re.sub(r'`([^`]+)`_', external, text)
    text = re.sub(
        r':doc:`([^`]+)`',
        lambda match: '<a href="#page-%s">%s</a>' %
        (slug(match.group(1)), html.escape(match.group(1).replace('_', ' '))),
        text)
    def reference(match):
        label = match.group(1)
        target = 'contents' if label in ('genindex', 'search') else slug(label)
        return '<a href="#%s">%s</a>' % (
            target, html.escape(label.replace('-', ' ')))

    text = re.sub(r':ref:`([^`]+)`', reference, text)
    for index, fragment in enumerate(placeholders):
        text = text.replace(f'\x00{index}\x00', fragment)
    return text


def image_html(relative_path, alt):
    path = SOURCE / relative_path
    if not path.is_file():
        return ('<p class="missing-image">Screenshot unavailable: '
                f'{html.escape(relative_path)}</p>')
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    return (f'<figure><img src="data:{mime};base64,{encoded}" '
            f'alt="{html.escape(alt, quote=True)}" loading="lazy"></figure>')


def render_page(name, title):
    path = SOURCE / f'{name}.rst'
    lines = path.read_text(encoding='utf-8').splitlines()
    links = {}
    for line in lines:
        match = re.match(r'^\.\. _`?([^`:]+)`?:\s+(\S+)', line)
        if match:
            links[match.group(1)] = match.group(2)

    output = [f'<section class="manual-page" id="page-{slug(name)}">',
              f'<div class="page-label">{html.escape(path.name)}</div>']
    paragraph = []
    list_open = False
    index = 0

    def flush_paragraph():
        if paragraph:
            value = ' '.join(part.strip() for part in paragraph)
            output.append(f'<p>{inline(value, links)}</p>')
            paragraph.clear()

    def close_list():
        nonlocal list_open
        if list_open:
            output.append('</ul>')
            list_open = False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if (index + 1 < len(lines) and stripped and
                re.fullmatch(r'[=\-*+^~]{3,}', lines[index + 1].strip())):
            flush_paragraph()
            close_list()
            underline = lines[index + 1].strip()[0]
            level = {'=': 2, '*': 2, '-': 3, '+': 4, '^': 4, '~': 4}.get(
                underline, 3)
            anchor = slug(f'{name}-{stripped}')
            output.append(f'<h{level} id="{anchor}">{inline(stripped, links)}'
                          f'<a class="permalink" href="#{anchor}">#</a></h{level}>')
            index += 2
            continue

        label_match = re.match(r'^\.\. _`?([^`:]+)`?:\s*$', stripped)
        if label_match:
            flush_paragraph()
            close_list()
            output.append('<span class="anchor" id="%s"></span>' %
                          slug(label_match.group(1)))
            index += 1
            continue

        if stripped.startswith('.. _'):
            index += 1
            continue

        image_match = re.match(r'^\.\. image::\s+(.+)$', stripped)
        if image_match:
            flush_paragraph()
            close_list()
            output.append(image_html(image_match.group(1), title))
            index += 1
            while index < len(lines) and lines[index].lstrip().startswith(':'):
                index += 1
            continue

        admonition = re.match(r'^\.\. (note|warning)::\s*(.*)$', stripped)
        if admonition:
            flush_paragraph()
            close_list()
            kind, value = admonition.groups()
            extra = []
            index += 1
            while index < len(lines) and (not lines[index].strip() or
                                           lines[index].startswith(' ')):
                if lines[index].strip():
                    extra.append(lines[index].strip())
                index += 1
            value = ' '.join([value] + extra).strip()
            output.append(f'<aside class="{kind}"><strong>{kind.title()}:</strong> '
                          f'{inline(value, links)}</aside>')
            continue

        if stripped.startswith('.. glossary::') or stripped.startswith('.. toctree::'):
            flush_paragraph()
            close_list()
            index += 1
            while index < len(lines) and (not lines[index].strip() or
                                           lines[index].startswith(' ')):
                index += 1
            continue

        list_match = re.match(r'^\s*(?:[-*]|\d+[.)])\s+(.+)$', line)
        if list_match:
            flush_paragraph()
            if not list_open:
                output.append('<ul>')
                list_open = True
            output.append(f'<li>{inline(list_match.group(1), links)}</li>')
            index += 1
            continue

        if stripped and stripped.endswith('::'):
            flush_paragraph()
            close_list()
            intro = stripped[:-1]
            if intro:
                output.append(f'<p>{inline(intro, links)}</p>')
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            block = []
            while index < len(lines) and (lines[index].startswith(' ') or
                                           not lines[index].strip()):
                block.append(lines[index][4:] if lines[index].startswith('    ')
                             else lines[index])
                index += 1
            output.append('<pre><code>%s</code></pre>' %
                          html.escape('\n'.join(block).rstrip()))
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            index += 1
            continue

        if stripped.startswith('.. '):
            flush_paragraph()
            close_list()
            index += 1
            continue

        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    close_list()
    output.append('<p class="back"><a href="#contents">Back to contents</a></p>')
    output.append('</section>')
    return '\n'.join(output)


def build():
    navigation = '\n'.join(
        f'<li><a href="#page-{slug(name)}">{html.escape(title)}</a></li>'
        for name, title in PAGES)
    pages = '\n'.join(render_page(name, title) for name, title in PAGES)
    document = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenCobolIDE 4.7.6 modern9.2 manual</title>
<style>
:root {{ color-scheme: light dark; --accent:#2878b5; --paper:#fff; --ink:#20242a;
  --muted:#66717d; --panel:#f2f5f7; --border:#d7dde2; }}
@media (prefers-color-scheme:dark) {{ :root {{ --paper:#171a1d; --ink:#e8ebed;
  --muted:#aab2b9; --panel:#22272b; --border:#3a4248; --accent:#70b7eb; }} }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; color:var(--ink); background:var(--paper); font:16px/1.62
  system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ width:min(1040px,calc(100% - 32px)); margin:auto; padding:34px 0 80px; }}
h1 {{ font-size:2.35rem; line-height:1.1; margin-bottom:.35rem; }}
h2 {{ border-bottom:2px solid var(--border); padding-bottom:.28rem; margin-top:2.2rem; }}
h3 {{ margin-top:1.8rem; }} h4 {{ margin-top:1.4rem; }}
a {{ color:var(--accent); }} code {{ font:0.92em ui-monospace,SFMono-Regular,monospace; }}
pre {{ overflow:auto; padding:1rem; background:var(--panel); border:1px solid var(--border);
  border-radius:8px; }}
nav {{ columns:2; padding:1rem 1.5rem; background:var(--panel); border:1px solid
  var(--border); border-radius:10px; }} nav li {{ break-inside:avoid; margin:.35rem 0; }}
.subtitle,.page-label,.back {{ color:var(--muted); }} .page-label {{ float:right; font-size:.85rem; }}
.manual-page {{ padding-top:1rem; }} .permalink {{ text-decoration:none; margin-left:.45rem;
  font-size:.7em; opacity:.45; }}
aside {{ margin:1rem 0; padding:.8rem 1rem; border-left:4px solid var(--accent);
  background:var(--panel); }} aside.warning {{ border-left-color:#d88718; }}
figure {{ margin:1.4rem auto; text-align:center; }} img {{ max-width:100%; height:auto;
  border:1px solid var(--border); border-radius:6px; }}
.missing-image {{ color:#a85b00; font-style:italic; }}
footer {{ margin-top:3rem; padding-top:1rem; border-top:1px solid var(--border);
  color:var(--muted); }}
@media print {{ nav,.back,.permalink {{ display:none; }} main {{ width:100%; }}
  .manual-page {{ break-before:page; }} }}
@media (max-width:640px) {{ nav {{ columns:1; }} h1 {{ font-size:1.8rem; }} }}
</style>
</head>
<body><main>
<header><h1>OpenCobolIDE 4.7.6 modern9.2 manual</h1>
<p class="subtitle">Offline documentation for the Debian-family Linux compatibility build.</p>
<p>This unofficial compatibility polish preserves the original OpenCobolIDE authorship and
maintainer attribution. The modernization was completed with assistance from OpenAI Codex.</p>
</header>
<h2 id="contents">Contents</h2><nav><ul>{navigation}</ul></nav>
{pages}
<footer>Generated from the RST files in <code>doc/source</code>. This page is self-contained
and can be opened without an internet connection.</footer>
</main></body></html>'''
    OUTPUT.write_text(document, encoding='utf-8')
    print(f'Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)')


if __name__ == '__main__':
    build()
