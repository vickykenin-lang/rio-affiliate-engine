from pathlib import Path
import csv, json, re, subprocess, sys
root=Path(__file__).resolve().parents[1]
site=root/'site'
errors=[]
required=[site/'index.html',site/'legal/affiliate-disclosure.html',site/'legal/privacy.html',root/'data/offers.json',root/'data/content_queue.csv']
for p in required:
    if not p.exists(): errors.append(f'missing: {p.relative_to(root)}')
for p in site.rglob('*.html'):
    txt=p.read_text(encoding='utf-8')
    if '<title>' not in txt: errors.append(f'missing title: {p.relative_to(root)}')
    for href in re.findall(r'href="([^"]+)"',txt):
        if href.startswith(('http://','https://','#','mailto:')): continue
        target=(p.parent/href.split('#')[0]).resolve()
        if href and not target.exists(): errors.append(f'broken local link: {p.relative_to(root)} -> {href}')
offers=json.loads((root/'data/offers.json').read_text())
for o in offers.get('offers',[]):
    if o.get('affiliate_url') and 'example' in o['affiliate_url']: errors.append(f'placeholder affiliate URL active: {o["id"]}')
with (root/'data/content_queue.csv').open(newline='',encoding='utf-8') as f:
    rows=list(csv.DictReader(f))
    if len(rows)<10: errors.append('content queue has fewer than 10 items')
campaign_validation = subprocess.run(
    [sys.executable, str(root / 'scripts' / 'validate_campaigns.py')],
    cwd=root,
    capture_output=True,
    text=True,
    timeout=30,
)
if campaign_validation.returncode != 0:
    detail = (campaign_validation.stderr or campaign_validation.stdout).strip()
    errors.append(f'campaign validation failed: {detail}')
print(f'RIO validation: {len(list(site.rglob("*.html")))} HTML pages, {len(rows)} queue items')
if errors:
    print('\n'.join('ERROR: '+e for e in errors)); sys.exit(1)
print('PASS: structure, internal links, offer placeholders and queue checks')
