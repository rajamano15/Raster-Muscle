#!/usr/bin/env python3
"""Generate clients.html from clients-data.json + clients-image-map.json.

Edit the JSON, then run:  python3 tools-gen-clients.py
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
pairs = json.loads((ROOT / "clients-data.json").read_text())
slugs = json.loads((ROOT / "clients-image-map.json").read_text())

lines = (ROOT / "index.html").read_text().splitlines(keepends=True)
sl = lambda a, b: "".join(lines[a - 1:b])
SPRITE, HEADER, FOOTER = sl(19, 85), sl(89, 149), sl(294, 344)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

cards = []
for i, (name, fn, loc) in enumerate(pairs):
    slug = slugs[fn]
    cards.append(
        f'          <article class="glass client-card" style="--i:{i % 12}">\n'
        f'            <div class="client-plate"><img src="assets/img/clients/{slug}.webp" '
        f'alt="{esc(name)} logo" loading="lazy" decoding="async"></div>\n'
        f'            <div class="client-meta">\n'
        f'              <p class="client-name">{esc(name)}</p>\n'
        f'              <p class="client-loc"><svg class="icon" aria-hidden="true"><use href="#i-pin"/></svg>{esc(loc)}</p>\n'
        f'            </div>\n'
        f'          </article>'
    )

main = f"""
  <main id="main">
    <!-- ═══════════ Page header ═══════════ -->
    <section class="page-hero" aria-labelledby="page-title">
      <div class="container">
        <p class="eyebrow"><span class="dot"></span>Clients</p>
        <h1 id="page-title">{len(pairs)} healthcare providers <span class="grad">running Raster</span></h1>
        <p class="page-lede">Our team of talented experts provide the best customer experience and service — and we let our customers do the marketing for us, through word of mouth.</p>\n        <p class="page-lede" style="margin-top:10px">Across {len(set(l for _, _, l in pairs))} locations in India, Malaysia, Australia and Afghanistan.</p>
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="index.html">Home</a>
          <span class="sep" aria-hidden="true">/</span>
          <span aria-current="page">Clients</span>
        </nav>
      </div>
    </section>

    <!-- ═══════════ Client grid ═══════════ -->
    <section class="features" aria-labelledby="clients-h">
      <div class="container">
        <div class="section-head" data-reveal>
          <p class="eyebrow" style="--i:0"><span class="dot"></span>Our clients</p>
          <h2 id="clients-h" style="--i:1">Hospitals, scan centres and laboratories</h2>
          <p class="section-sub" style="--i:2">From single-speciality clinics to multi-speciality referral centres and national institutes — across Tamil Nadu, India and beyond.</p>
        </div>
        <div class="client-grid" data-reveal>
{chr(10).join(cards)}
        </div>
      </div>
    </section>

    <!-- ═══════════ CTA ═══════════ -->
    <section class="cta-band" aria-labelledby="cta-h">
      <div class="container">
        <div class="glass cta-card" data-reveal>
          <div style="--i:0">
            <h2 id="cta-h">Join them</h2>
            <p>Tell us about your institute and we will show you what our imaging, hospital management and interfacing software can do for it.</p>
          </div>
          <div class="cta-actions" style="--i:1">
            <a class="btn btn-primary" href="contact.html">Talk to us<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg></a>
            <a class="btn btn-ghost" href="healthcare-solutions.html">Healthcare solutions</a>
          </div>
        </div>
      </div>
    </section>
  </main>
"""

head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Clients — Raster Images</title>
  <meta name="description" content="{len(pairs)} hospitals, scan centres and laboratories running Raster Images software and hardware — including AIIMS, Kauvery, Velammal, SKS Hospital and Adyar Cancer Institute.">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23041109'/%3E%3Ccircle cx='32' cy='32' r='15' fill='%2300A87B'/%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bai+Jamjuree:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
"""

header = HEADER.replace(
    '<li><a href="index.html" class="active" aria-current="page">Home</a></li>',
    '<li><a href="index.html">Home</a></li>'
).replace(
    '<li><a href="index.html" aria-current="page">Home</a></li>',
    '<li><a href="index.html">Home</a></li>'
).replace(
    '<li><a href="clients.html">Clients</a></li>',
    '<li><a href="clients.html" class="active" aria-current="page">Clients</a></li>', 1
)

PIN = """      <symbol id="i-pin" viewBox="0 0 24 24">
        <path d="M12 21.2s6.6-6.1 6.6-11a6.6 6.6 0 0 0-13.2 0c0 4.9 6.6 11 6.6 11z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
        <circle cx="12" cy="10.1" r="2.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
      </symbol>
"""

(ROOT / "clients.html").write_text(
    head + "\n" + SPRITE + PIN + "    </defs>\n  </svg>\n\n" + header + main + "\n" + FOOTER)
print("wrote clients.html with", len(pairs), "entries")
