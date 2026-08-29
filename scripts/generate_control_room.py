#!/usr/bin/env python3
import html, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=ROOT/'site/control-room/index.html'

def load(name, default):
    try:return json.loads((DATA/name).read_text(encoding='utf-8'))
    except Exception:return default

def esc(v):return html.escape(str(v if v is not None else 'UNKNOWN'))

def instagram_embed_url(permalink):
    p=str(permalink or '').rstrip('/')
    return p+'/embed/' if p.startswith('https://www.instagram.com/') else ''

def main():
    snap=load('dashboard_snapshot.json',{})
    telemetry=load('telemetry_state.json',{})
    attr=load('affiliate_attribution_state.json',{})
    work=load('rio_work_status.json',{})
    published=(load('ig_published.json',{}).get('posted') or {})
    posts=(telemetry.get('instagram') or {}).get('posts') or {}
    cards=[]
    for offer, meta in reversed(list(published.items())):
        p=posts.get(offer,{})
        image=p.get('media_url') or p.get('thumbnail_url')
        permalink=p.get('permalink') or meta.get('permalink') or '#'
        embed=instagram_embed_url(permalink)
        if embed:
            visual=f'<iframe class="igembed" src="{esc(embed)}" loading="lazy" allowtransparency="true" frameborder="0" scrolling="no"></iframe>'
        elif image:
            visual=f'<img src="{esc(image)}" loading="lazy" alt="{esc(meta.get("product_name"))}">'
        else:
            visual='<div class="noimg">Instagram preview unavailable</div>'
        cards.append(f'''<article class="post">{visual}<div class="pad"><b>{esc(meta.get('product_name'))}</b><small>{esc(meta.get('posted_at'))}</small><div class="metrics">Impr: {esc(p.get('impressions'))} · Reach: {esc(p.get('reach'))} · Likes: {esc(p.get('like_count'))} · Comments: {esc(p.get('comments_count'))} · Clicks: {esc(p.get('clicks'))}</div><a target="_blank" rel="noopener" href="{esc(permalink)}">Open on Instagram</a></div></article>''')
    post_html=''.join(cards) or '<p>No published posts recorded.</p>'
    current=esc(work.get('current_task') or work.get('last_completed'))
    nxt=esc(work.get('next_task'))
    changed=''.join(f'<li>{esc(x)}</li>' for x in (work.get('changed_files') or [])) or '<li>None</li>'
    tele_status=esc(telemetry.get('status'))
    ig_status=esc((telemetry.get('instagram') or {}).get('status'))
    website_status=esc((telemetry.get('website') or {}).get('status'))
    attribution_status=esc(attr.get('status'))
    html_doc=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RIO Control Room</title><style>
body{{font-family:system-ui;margin:0;background:#0d1117;color:#e6edf3}}main{{max-width:1280px;margin:auto;padding:24px}}a{{color:#58a6ff}}.top{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}}.card,.panel,.post{{background:#161b22;border:1px solid #30363d;border-radius:14px}}.card{{padding:16px}}.card small,.post small{{display:block;color:#8b949e}}.card strong{{font-size:28px}}.panel{{padding:18px;margin:16px 0}}.posts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}.post{{overflow:hidden}}.post img,.noimg{{width:100%;height:420px;object-fit:cover;background:#21262d;display:flex;align-items:center;justify-content:center;color:#8b949e}}.igembed{{width:100%;height:560px;background:white}}.pad{{padding:12px}}.metrics{{font-size:13px;color:#8b949e;margin:8px 0}}.actions a{{display:inline-block;margin:4px 8px 4px 0;padding:10px 12px;border:1px solid #30363d;border-radius:9px;text-decoration:none}}code{{white-space:pre-wrap}}</style></head><body><main>
<div class="top"><div><h1>RIO Control Room</h1><p>Revenue, actual Instagram posts, website, telemetry and live development in one place.</p></div><div class="actions"><a href="../">Open Live Website</a><a href="../dashboard/">CEO Dashboard</a><a href="../products/">Products</a><a href="../guides/">Guides</a><a href="../blog/">Blog</a></div></div>
<div class="grid"><div class="card"><small>Ready offers</small><strong>{esc(snap.get('ready_offers'))}</strong></div><div class="card"><small>Instagram posted</small><strong>{esc(snap.get('instagram_posted'))}</strong></div><div class="card"><small>Revenue</small><strong>₹{esc(snap.get('revenue_inr'))}</strong></div><div class="card"><small>Telemetry</small><strong>{tele_status}</strong></div><div class="card"><small>Affiliate attribution</small><strong>{attribution_status}</strong></div></div>
<section class="panel"><h2>Current Development</h2><p><b>Current / last task:</b> {current}</p><p><b>Next:</b> {nxt}</p><p><b>Validators:</b> {esc(work.get('validators'))} · <b>Blocker:</b> {esc(work.get('blocker'))}</p><h3>Latest changed files</h3><ul>{changed}</ul></section>
<section class="panel"><h2>Commercial Funnel</h2><p>Offers ready: {esc(snap.get('ready_offers'))} → Posts: {esc(snap.get('instagram_posted'))} → Website clicks: {esc((telemetry.get('website') or {}).get('clicks'))} → Affiliate orders: {esc(attr.get('orders'))} → Commission: {esc(attr.get('commission_inr'))} → Settled revenue: ₹{esc(attr.get('settled_revenue_inr'))}</p><p>Instagram telemetry: <b>{ig_status}</b> · Website telemetry: <b>{website_status}</b>. UNKNOWN is never treated as zero.</p></section>
<section class="panel"><h2>Published Instagram Posts</h2><p>These cards embed the actual Instagram posts. Use “Open on Instagram” for the live post.</p><div class="posts">{post_html}</div></section>
<section class="panel"><h2>Website & Content</h2><div class="actions"><a href="../" target="_blank">Homepage</a><a href="../products/" target="_blank">Product pages</a><a href="../guides/" target="_blank">Buying guides</a><a href="../articles/" target="_blank">Articles</a><a href="../compare.html" target="_blank">Compare page</a></div></section>
</main></body></html>'''
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(html_doc,encoding='utf-8')
    print('RIO Control Room generated with Instagram embeds')

if __name__=='__main__':main()
