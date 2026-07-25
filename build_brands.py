#!/usr/bin/env python3
"""
build_brands.py — Style Made American

Generates fully static brand profile pages (brands/<slug>.html) from:
  - brands/data/<slug>.json   (brand content — one file per brand, hand-edited)
  - sma_clothes_database.csv  (per-garment rows; scores are pulled per slug)

WHY THIS EXISTS
Google was indexing the redirect stub instead of real content, because
brand pages used to redirect to brand-template.html?brand=<slug> and fill
themselves in with JavaScript after load. This script bakes the same
content directly into each brand's own static HTML file — same look,
same data source, just rendered at build time instead of in the browser.

HOW TO USE
  1. Add or edit a brand's content in brands/data/<slug>.json
     (add/edit its scores in sma_clothes_database.csv, "Profile Slug" column)
  2. Run:  python3 build_brands.py
  3. Commit + push the regenerated brands/<slug>.html file(s).

That's it — one JSON file per brand is still the only thing you maintain
by hand. This script just needs to be re-run whenever that data changes.
"""

import csv
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SMA_REPO_ROOT", ROOT)

DATA_DIR = os.path.join(REPO, "brands", "data")
CSV_PATH = os.path.join(REPO, "sma_clothes_database.csv")
OUT_DIR = os.path.join(REPO, "brands")

CATS = ["Commitment", "Character", "Ethics", "Heritage", "Value"]
SECTION_ORDER = [
    ("commitment", "Commitment"),
    ("character", "Character"),
    ("ethics", "Ethics"),
    ("heritage", "Heritage"),
    ("value", "Value"),
]

HEAD_CSS = """
    :root {
      --bg: #ffffff; --bg-cream: #f6f1e7; --rule: #e6dfcf; --rule-soft: #f0ead9;
      --ink: #1a1a18; --ink-soft: #4a4a45; --muted: #8a8a82;
      --olive: #5d6843; --olive-dark: #454d31; --olive-soft: #eef0e3;
      --font-display: 'Cormorant Garamond', 'Georgia', serif;
      --font-wordmark: 'Playfair Display', 'Georgia', serif;
      --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      --container-max: 1280px; --reading-max: 720px;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 16px; line-height: 1.6; -webkit-font-smoothing: antialiased; }
    a { color: var(--olive); text-decoration: none; border-bottom: 1px solid transparent; transition: border-color 120ms ease; }
    a:hover { border-bottom-color: var(--olive); }
    .container { max-width: var(--container-max); margin: 0 auto; padding: 0 32px; }
    .reading { max-width: var(--reading-max); margin: 0 auto; }
    .site-header { border-bottom: 1px solid var(--rule); background: var(--bg); }
    .site-header .container { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding-top: 18px; padding-bottom: 18px; }
    .wordmark-link { color: var(--ink); border-bottom: none; flex: 0 0 auto; }
    .wordmark-link:hover { border-bottom: none; }
    .wordmark { font-family: var(--font-wordmark); font-weight: 700; font-size: clamp(18px, 2.2vw, 24px); letter-spacing: 0.18em; text-transform: uppercase; line-height: 1; margin: 0; color: var(--ink); white-space: nowrap; }
    .site-nav { display: flex; align-items: center; gap: 28px; flex: 1 1 auto; justify-content: flex-end; flex-wrap: wrap; }
    .site-nav a { font-family: var(--font-body); font-size: 13px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-soft); border-bottom: 1px solid transparent; padding-bottom: 2px; }
    .site-nav a.active { color: var(--ink); border-bottom-color: var(--olive); }
    .site-nav a:hover { color: var(--olive); border-bottom-color: var(--olive); }
    .site-nav .nav-cta { color: var(--olive-dark); border: 1px solid var(--olive); padding: 7px 14px; border-radius: 2px; }
    .site-nav .nav-cta:hover { background: var(--olive); color: #ffffff; border-bottom: 1px solid var(--olive); }
    .profile-hero { border-bottom: 1px solid var(--rule); padding: 48px 0 40px; text-align: center; }
    .profile-hero .eyebrow { font-family: var(--font-body); font-size: 12px; font-weight: 600; letter-spacing: 0.32em; text-transform: uppercase; color: var(--olive); margin-bottom: 14px; }
    .profile-hero h1 { font-family: var(--font-wordmark); font-weight: 700; font-size: clamp(38px, 5.5vw, 60px); letter-spacing: 0.01em; line-height: 1.05; color: var(--ink); margin: 0 0 14px; }
    .profile-hero .lead { font-family: var(--font-display); font-style: italic; font-weight: 400; font-size: clamp(18px, 2vw, 22px); line-height: 1.5; color: var(--ink-soft); max-width: 680px; margin: 0 auto 30px; }
    .quick-facts { display: flex; flex-wrap: wrap; justify-content: center; gap: 24px 36px; max-width: 920px; margin: 0 auto; padding-top: 20px; border-top: 1px solid var(--rule-soft); }
    .quick-fact { text-align: center; }
    .quick-fact .label { font-family: var(--font-body); font-size: 11px; font-weight: 600; letter-spacing: 0.22em; text-transform: uppercase; color: var(--olive); margin-bottom: 6px; }
    .quick-fact .value { font-family: var(--font-display); font-size: 17px; font-weight: 500; color: var(--ink); }
    .profile-body { padding: 48px 0 32px; }
    .profile-section { margin-bottom: 36px; }
    .profile-section:last-of-type { margin-bottom: 0; }
    .profile-section h2 { font-family: var(--font-wordmark); font-weight: 700; font-size: clamp(24px, 3vw, 32px); letter-spacing: 0; line-height: 1.15; color: var(--ink); margin: 0 0 14px; }
    .profile-section p { font-family: var(--font-display); font-size: 19px; line-height: 1.6; color: var(--ink-soft); margin: 0 0 14px; }
    .profile-section p:last-child { margin-bottom: 0; }
    .profile-section strong { color: var(--ink); font-weight: 600; }
    .profile-section--verdict { background: var(--bg-cream); padding: 28px 32px; border-left: 3px solid var(--olive); border-radius: 2px; }
    .profile-section--verdict h2 { color: var(--olive-dark); }
    .score-panel { padding: 36px 0; border-bottom: 1px solid var(--rule); background: var(--bg); }
    .score-panel .panel-inner { max-width: 640px; margin: 0 auto; }
    .score-panel .panel-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid var(--rule); }
    .score-panel .panel-eyebrow { font-family: var(--font-body); font-size: 12px; font-weight: 600; letter-spacing: 0.32em; text-transform: uppercase; color: var(--olive); }
    .score-panel .panel-link { font-family: var(--font-body); font-size: 11px; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase; color: var(--olive); border-bottom: none; }
    .score-row { display: grid; grid-template-columns: 130px 1fr 60px; align-items: center; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--rule-soft); }
    .score-row:last-child { border-bottom: none; }
    .score-row .row-label { font-family: var(--font-wordmark); font-weight: 700; font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink); }
    .score-row .row-dots { color: var(--olive); font-size: 18px; line-height: 1; letter-spacing: 4px; }
    .score-row .row-dots .empty { color: var(--rule); }
    .score-row .row-num { font-family: var(--font-wordmark); font-weight: 700; font-size: 22px; color: var(--ink); text-align: right; line-height: 1; }
    .score-row.unscored .row-dots { color: var(--rule); }
    .score-row.unscored .row-num { color: var(--muted); font-weight: 400; font-size: 14px; font-family: var(--font-display); font-style: italic; }
    .score-note { font-family: var(--font-body); font-size: 12px; color: var(--muted); line-height: 1.5; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--rule-soft); }
    .closing-actions { padding: 32px 0 56px; border-top: 1px solid var(--rule-soft); display: flex; flex-wrap: wrap; gap: 16px; justify-content: center; }
    .action-btn { font-family: var(--font-body); font-size: 12px; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase; padding: 12px 22px; border: 1px solid var(--olive); color: var(--olive-dark); border-bottom: 1px solid var(--olive); border-radius: 2px; transition: background 120ms ease, color 120ms ease; }
    .action-btn:hover { background: var(--olive); color: #ffffff; border-bottom: 1px solid var(--olive); }
    .action-btn.primary { background: var(--olive); color: #ffffff; }
    .action-btn.primary:hover { background: var(--olive-dark); border-color: var(--olive-dark); border-bottom: 1px solid var(--olive-dark); }
    .site-footer { border-top: 1px solid var(--rule); padding: 28px 0 36px; text-align: center; color: var(--muted); font-size: 13px; font-family: var(--font-body); }
    .site-footer .footer-mark { font-family: var(--font-wordmark); font-weight: 700; font-size: 13px; letter-spacing: 0.22em; text-transform: uppercase; color: var(--ink-soft); }
    .site-footer .footer-links { margin-top: 10px; font-size: 12px; font-weight: 500; letter-spacing: 0.22em; text-transform: uppercase; }
    .site-footer .footer-links a { color: var(--ink-soft); border-bottom: 1px solid transparent; padding-bottom: 2px; }
    .site-footer .footer-links a:hover { color: var(--olive); border-bottom-color: var(--olive); }
    @media (max-width: 900px) { .container { padding: 0 22px; } .site-nav { gap: 20px; } .site-nav a { font-size: 12px; } }
    @media (max-width: 720px) { .container { padding: 0 16px; } .site-header .container { flex-wrap: wrap; gap: 12px; } .site-nav { width: 100%; gap: 16px; justify-content: flex-start; } .profile-hero { padding: 36px 0 28px; } .profile-section--verdict { padding: 22px; } .profile-section p { font-size: 17px; } .score-panel { padding: 24px 0; } .score-row { grid-template-columns: 100px 1fr 48px; gap: 12px; padding: 10px 0; } .score-row .row-label { font-size: 11px; } .score-row .row-dots { font-size: 16px; } .score-row .row-num { font-size: 18px; } }
"""


def load_csv_rows():
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def scores_for_slug(rows, slug):
    brand_rows = [r for r in rows if (r.get("Profile Slug") or "").strip() == slug]
    scores = {}
    for cat in CATS:
        val = None
        for r in brand_rows:
            v = (r.get(cat) or "").strip()
            if v:
                val = v
                break
        scores[cat] = val
    return scores


def render_dots(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "─ ─ ─ ─ ─"
    if n < 0 or n > 5:
        return "─ ─ ─ ─ ─"
    return "●" * n + '<span class="empty">' + "○" * (5 - n) + "</span>"


def render_score_panel(scores):
    rows_html = []
    for cat in CATS:
        v = scores.get(cat)
        if v:
            cls = "score-row"
            dots = render_dots(v)
            num = v
        else:
            cls = "score-row unscored"
            dots = "─ ─ ─ ─ ─"
            num = "Unscored"
        rows_html.append(
            f'<div class="{cls}"><span class="row-label">{cat}</span>'
            f'<span class="row-dots">{dots}</span><span class="row-num">{num}</span></div>'
        )
    return "\n".join(rows_html)


def build_jsonld(brand):
    qf = brand.get("quick_facts") or {}
    data = {
        "@context": "https://schema.org",
        "@type": "Brand",
        "name": brand.get("brand_name"),
        "description": brand.get("meta_description") or None,
        "url": brand.get("brand_url") or None,
        "foundingDate": qf.get("founded") or None,
        "location": {"@type": "Place", "name": qf.get("based_in")} if qf.get("based_in") else None,
        "slogan": qf.get("makes") or None,
    }
    data = {k: v for k, v in data.items() if v}
    return json.dumps(data)


def render_page(brand, scores):
    slug = brand["slug"]
    name = brand.get("brand_name", slug)
    meta_desc = brand.get("meta_description", "")
    qf = brand.get("quick_facts") or {}
    sections = brand.get("sections") or {}
    brand_url = brand.get("brand_url")

    facts_html = "".join(
        f'<div class="quick-fact"><div class="label">{label}</div><div class="value">{qf[key]}</div></div>'
        for key, label in [
            ("founded", "Founded"),
            ("based_in", "Based in"),
            ("makes", "Makes"),
            ("price_tier", "Price tier"),
        ]
        if qf.get(key)
    )

    verdict_html = ""
    if sections.get("verdict"):
        verdict_html = (
            '<section class="profile-section profile-section--verdict">'
            "<h2>Worth it?</h2>"
            f"{sections['verdict']}"
            "</section>"
        )

    body_sections_html = []
    for key, heading in SECTION_ORDER:
        if key == "verdict":
            continue
        content = sections.get(key)
        if not content:
            continue
        body_sections_html.append(
            f'<section class="profile-section"><h2>{heading}</h2>{content}</section>'
        )
    body_sections_html = "\n".join(body_sections_html)

    visit_btn = (
        f'<a href="{brand_url}" class="action-btn" target="_blank" rel="noopener">Visit {name} ↗</a>'
        if brand_url
        else ""
    )

    jsonld = build_jsonld(brand)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Style Made American</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="https://stylemadeamerican.com/brands/{slug}.html">
  <script type="application/ld+json">{jsonld}</script>

  <!-- Google tag (gtag.js) — DO NOT EDIT. Same on every page. -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KSBCHKD8H4"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-KSBCHKD8H4');
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;0,900;1,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

  <style>{HEAD_CSS}</style>
</head>
<body>

  <div id="site-header"></div>
  <script src="/nav.js"></script>

  <article id="brand-article">
    <section class="profile-hero">
      <div class="container">
        <div class="eyebrow">Brand Profile</div>
        <h1 id="brand-name">{name}</h1>
        <div id="brand-verdict" class="reading" style="margin-top: 24px; text-align: left;">{verdict_html}</div>
        <div class="quick-facts" id="quick-facts">{facts_html}</div>
      </div>
    </section>

    <section class="score-panel">
      <div class="container"><div class="panel-inner">
        <div class="panel-header">
          <span class="panel-eyebrow">How it scores</span>
          <a href="/brands/index.html#how-we-score" class="panel-link">How we score →</a>
        </div>
        <div id="score-panel-body">
{render_score_panel(scores)}
        </div>
        <p class="score-note">For brands that manufacture both domestically and overseas, our grading focuses only on the domestically manufactured goods. If made in USA is what you are looking for, brands that don't say "all" in the database require you to check the description.</p>
      </div></div>
    </section>

    <section class="profile-body">
      <div class="container">
        <div class="reading" id="brand-sections">
{body_sections_html}
          <div class="closing-actions">
            <a href="/" class="action-btn primary">View in database →</a>
            {visit_btn}
          </div>
        </div>
      </div>
    </section>
  </article>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-mark">Style Made American</div>
      <div class="footer-links"><a href="/contact.html">Contact</a>
        &ensp;&middot;&ensp;
        <a href="/privacy.html">Privacy Policy</a></div>
      <div style="margin-top: 6px;">&copy; <span id="year"></span> &middot; Independent. Unsponsored. Updated by hand.</div>
    </div>
  </footer>

  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
  </script>
</body>
</html>
"""


def main():
    rows = load_csv_rows()
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))
    if not files:
        print("No JSON files found in", DATA_DIR)
        return

    warnings = []
    for fname in files:
        path = os.path.join(DATA_DIR, fname)
        with open(path, encoding="utf-8") as f:
            brand = json.load(f)

        slug = brand.get("slug") or fname[:-5]
        brand["slug"] = slug
        scores = scores_for_slug(rows, slug)
        html = render_page(brand, scores)

        title_len = len(brand.get("brand_name", "")) + len(" — Style Made American")
        if title_len > 60:
            warnings.append(f"{slug}: title is {title_len} chars (recommend <60)")
        desc_len = len(brand.get("meta_description", ""))
        if not (120 <= desc_len <= 155):
            warnings.append(f"{slug}: meta description is {desc_len} chars (recommend 120-155)")

        out_path = os.path.join(OUT_DIR, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote brands/{slug}.html")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(" -", w)


if __name__ == "__main__":
    main()
