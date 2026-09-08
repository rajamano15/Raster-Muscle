#!/usr/bin/env python3
"""Generate news-events.html plus one detail page per article.

Edit news-data.json, then run:  python3 tools-gen-news.py

Shell blocks (sprite, header, footer) are sliced out of index.html verbatim so
the pages cannot drift from the rest of the site.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
articles = json.loads((ROOT / "news-data.json").read_text())

index_lines = (ROOT / "index.html").read_text().splitlines(keepends=True)
def slice_lines(a, b):            # 1-indexed inclusive, as sed -n 'a,bp'
    return "".join(index_lines[a - 1:b])

SPRITE = slice_lines(19, 85)      # comment through last base symbol
HEADER = slice_lines(89, 149)     # header + mobile menu
FOOTER = slice_lines(294, 344)    # footer + cursor glow + script + close

ICON = '<svg class="icon" aria-hidden="true"><use href="#i-%s"/></svg>'

def head(title, desc):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23041109'/%3E%3Ccircle cx='32' cy='32' r='15' fill='%2300A87B'/%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bai+Jamjuree:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
"""

def nav_active(html, href, label):
    """Move the desktop .active / mobile aria-current onto this page's item."""
    html = html.replace('<li><a href="index.html" class="active" aria-current="page">Home</a></li>',
                        '<li><a href="index.html">Home</a></li>')
    html = html.replace('<li><a href="index.html" aria-current="page">Home</a></li>',
                        '<li><a href="index.html">Home</a></li>')
    # topbar secondary nav carries News & Events
    html = html.replace(f'<li><a href="{href}">{label}</a></li>',
                        f'<li><a href="{href}" class="active" aria-current="page">{label}</a></li>', 1)
    return html

def shell(title, desc, main, active_href="news-events.html", active_label="News &amp; Events"):
    return (head(title, desc) + "\n" + SPRITE + "    </defs>\n  </svg>\n\n"
            + nav_active(HEADER, active_href, active_label) + main + "\n" + FOOTER)

# ── listing page ────────────────────────────────────────────────────────────
cards = []
for i, a in enumerate(articles):
    cards.append(f"""          <article class="glass news-card" style="--i:{i}">
            <a class="news-thumb" href="news-{a['slug']}.html" tabindex="-1" aria-hidden="true">
              <img src="assets/img/news/{a['image']}.webp" alt="" loading="lazy" decoding="async">
            </a>
            <div class="news-body">
              <p class="news-date"><time datetime="{a['iso']}">{a['date']}</time></p>
              <h3><a href="news-{a['slug']}.html">{a['title']}</a></h3>
              <p>{a['excerpt']}</p>
              <a class="card-link" href="news-{a['slug']}.html">Read more{ICON % 'arrow'}</a>
            </div>
          </article>""")

listing_main = f"""
  <main id="main">
    <!-- ═══════════ Page header ═══════════ -->
    <section class="page-hero" aria-labelledby="page-title">
      <div class="container">
        <p class="eyebrow"><span class="dot"></span>News &amp; Events</p>
        <h1 id="page-title">Conferences, workshops <span class="grad">and milestones</span></h1>
        <p class="page-lede">Where we have been speaking, exhibiting and learning — and what we have been running in-house.</p>
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="index.html">Home</a>
          <span class="sep" aria-hidden="true">/</span>
          <span aria-current="page">News &amp; Events</span>
        </nav>
      </div>
    </section>

    <!-- ═══════════ Listing ═══════════ -->
    <section class="features" aria-label="News and events">
      <div class="container">
        <div class="news-grid" data-reveal>
{chr(10).join(cards)}
        </div>
      </div>
    </section>
  </main>
"""

(ROOT / "news-events.html").write_text(
    shell("News &amp; Events — Raster Images",
          "Conferences, workshops and milestones from Raster Images — the DICOM Educational Conference, CAHOTECH, CII Salem's Healthcare Conference and our in-house workshops.",
          listing_main))

# ── detail pages ────────────────────────────────────────────────────────────
for i, a in enumerate(articles):
    prev_a = articles[i - 1] if i > 0 else None
    next_a = articles[i + 1] if i < len(articles) - 1 else None

    body = "\n".join(f"            <p>{p}</p>" for p in a["body"])
    if a.get("list"):
        items = "\n".join(f"              <li>{x}</li>" for x in a["list"])
        body += (f"\n            <h3>{a['listTitle']}</h3>\n"
                 f"            <ul class=\"article-list\">\n{items}\n            </ul>")

    shots = []
    for g in a["gallery"]:
        shots.append(f"""            <button class="gallery-item" type="button"
              data-full="assets/img/news/{g['file']}.webp"
              data-caption="{g['caption']}">
              <img src="assets/img/news/{g['file']}.webp" alt="{g['caption']}" loading="lazy" decoding="async">
            </button>""")

    gallery = f"""
        <section class="gallery-section" aria-labelledby="gallery-h" style="margin-top:44px">
          <h3 id="gallery-h" style="font-size:20px">Gallery</h3>
          <!-- Add another photo by copying one .gallery-item button and pointing
               it at a new file in assets/img/news/. The lightbox picks it up
               automatically; arrows appear once there is more than one. -->
          <div class="gallery" data-gallery>
{chr(10).join(shots)}
          </div>
        </section>"""

    foot = []
    if prev_a:
        foot.append(f'          <a class="btn btn-ghost" href="news-{prev_a["slug"]}.html">Newer: {prev_a["title"]}</a>')
    if next_a:
        foot.append(f'          <a class="btn btn-ghost" href="news-{next_a["slug"]}.html">Older: {next_a["title"]}</a>')
    foot.append(f'          <a class="btn btn-primary" href="news-events.html">All news &amp; events{ICON % "arrow"}</a>')

    detail_main = f"""
  <main id="main">
    <!-- ═══════════ Page header ═══════════ -->
    <section class="page-hero" aria-labelledby="page-title">
      <div class="container">
        <p class="eyebrow"><span class="dot"></span><time datetime="{a['iso']}">{a['date']}</time></p>
        <h1 id="page-title">{a['title']}</h1>
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="index.html">Home</a>
          <span class="sep" aria-hidden="true">/</span>
          <a href="news-events.html">News &amp; Events</a>
          <span class="sep" aria-hidden="true">/</span>
          <span aria-current="page">{a['title']}</span>
        </nav>
      </div>
    </section>

    <!-- ═══════════ Article ═══════════ -->
    <section class="features">
      <div class="container">
        <article class="article">
          <div class="article-hero">
            <img src="assets/img/news/{a['image']}.webp" alt="{a['gallery'][0]['caption']}" width="500" height="281" decoding="async">
          </div>
          <div class="article-body">
{body}
          </div>
{gallery}
          <div class="article-foot">
{chr(10).join(foot)}
          </div>
        </article>
      </div>
    </section>
  </main>

  <!-- ═══════════ Lightbox ═══════════ -->
  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo viewer" hidden>
    <figure class="lightbox-figure">
      <img src="" alt="">
      <figcaption class="lightbox-cap"></figcaption>
    </figure>
    <button class="lightbox-btn lightbox-close" type="button" aria-label="Close photo viewer">{ICON % 'close'}</button>
    <button class="lightbox-btn lightbox-prev" type="button" aria-label="Previous photo">{ICON % 'chevron'}</button>
    <button class="lightbox-btn lightbox-next" type="button" aria-label="Next photo">{ICON % 'chevron'}</button>
  </div>
"""

    desc = re.sub("<[^>]+>", "", a["excerpt"])
    (ROOT / f"news-{a['slug']}.html").write_text(
        shell(f"{a['title']} — Raster Images", desc, detail_main))

print("wrote news-events.html and", len(articles), "detail pages")
