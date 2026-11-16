#!/usr/bin/env python3
"""Regenerate janardan-profile.txt as an exact content twin of janardan-profile.html.
Preserves document order: h1, headline, contact, then each section (title, paragraphs, groups+bullets, tl-rows, bare uls, h3s).
Renders: bullets as '- ', capabilities as 'Label | content', dates already 'to'.
"""
import re, html, pathlib

SRC = pathlib.Path('/Users/janardan/github/janalogy.com/janardan-profile.html')
OUT = pathlib.Path('/Users/janardan/github/janalogy.com/janardan-profile.txt')
doc = SRC.read_text(encoding='utf-8')

def strip(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()

def norm(s):
    return re.sub(r'\s+', ' ', strip(s))

out = []

# Header block (grab from <body><main> up to first <section>)
head = doc.split('<section>', 1)[0]
h1 = re.search(r'<h1>(.*?)</h1>', head, re.S).group(1)
out.append(norm(h1))
headline = re.search(r'class="headline">(.*?)</p>', head, re.S).group(1)
out.append(norm(headline))
# contact: split on <br>
contact = re.search(r'class="contact">\s*(.*?)\s*</p>', head, re.S).group(1)
parts = [norm(p) for p in re.split(r'<br\s*/?>', contact) if norm(p)]
out += parts
out.append('')

# Sections
for sec in re.findall(r'<section>(.*?)</section>', doc, re.S):
    h2 = re.search(r'<h2>(.*?)</h2>', sec, re.S)
    if not h2:
        continue
    out.append(norm(h2.group(1)).upper())
    out.append('')
    body = sec  # keep relative positions

    # Walk the body in order, emitting paragraphs/h3/groups/bare-ul/tl-row.
    # Tokenize by splitting on the constructs we care about.
    # Simplest reliable approach: use a master regex with alternations, finditer preserves order.
    pattern = re.compile(
        r'<p>(.*?)</p>'
        r'|<h3>(.*?)</h3>'
        r'|<div class="group">(.*?)</div>\s*<ul>(.*?)</ul>'
        r'|<div class="tl-row">(.*?)</div>'
        r'|<ul>(.*?)</ul>',
        re.S)
    for m in pattern.finditer(body):
        p, h3, group, gull, tl, bare = m.groups()
        if p is not None:
            t = norm(p)
            if t: out.append(t)
        elif h3 is not None:
            out.append(norm(h3))
        elif group is not None:
            out.append(norm(group))
            for li in re.findall(r'<li>(.*?)</li>', gull, re.S):
                out.append('- ' + norm(li))
        elif tl is not None:
            # label · content  ->  label | content
            t = norm(tl).replace('·', ' | ', 1)
            out.append(t)
        elif bare is not None:
            for li in re.findall(r'<li>(.*?)</li>', bare, re.S):
                out.append('- ' + norm(li))
    out.append('')

text = re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'
OUT.write_text(text, encoding='utf-8')

# Checks
bad = {n: text.count(c) for n, c in [('em-dash', '\u2014'), ('en-dash', '\u2013'), ('tilde', '~'), ('minus', '\u2212')]}
print(f"Wrote {OUT.name}: {len(text)} chars, {text.count(chr(10))+1} lines")
for k, v in bad.items():
    if v: print(f"  WARNING {k}: {v}")
