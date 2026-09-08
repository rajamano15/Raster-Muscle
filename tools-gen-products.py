#!/usr/bin/env python3
"""Generate one solution page per product from products-data.json, plus the
healthcare-solutions.html hub that lists every product by category.

Edit products-data.json, then run:  python3 tools-gen-products.py

The shell (sprite, header, mobile menu, footer) is sliced out of about.html
verbatim so the pages cannot drift from the rest of the site. Each page gets
the sticky product side menu, the sections listed in its data, a "works
alongside" block of the other products in its category, and a CTA band.
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
PRODUCTS = json.loads((ROOT / "products-data.json").read_text())

CATEGORIES = {
    "radiology":           ("i-radiology", "Radiology",                "healthcare-solutions.html#radiology"),
    "hospital-management": ("i-hospital",  "Hospital Management",      "healthcare-solutions.html#hospital-management"),
    "interfacing":         ("i-interface", "Interfacing Applications", "healthcare-solutions.html#interfacing"),
    "other":               ("i-apps",      "Other Applications",       "healthcare-solutions.html#other-applications"),
}
# one-line blurbs for the "works alongside" cards
BLURB = {
    "pacs": "Vendor-neutral archive and zero-footprint viewer at the heart of the radiology suite.",
    "ris": "Scheduling, work-lists, billing and reporting for the department, sharing one vendor with iPACS.",
    "teleradiology": "Studies routed securely to off-site radiologists, with on-site performance over low bandwidth.",
    "dicom-burner": "CD/DVD publishing of studies straight from the archive, with a viewer on every disc.",
    "dicom-camera": "Clinical photographs captured on a phone and stored as DICOM alongside the imaging.",
    "ihms": "Desktop transaction entry plus a web dashboard and EMR, scalable from clinic to enterprise.",
    "pharmacy-management": "Barcoded, batch-aware inventory with alerts and error-free dispensing and billing.",
    "blood-bank-management": "Donors, camps, bag inventories and transfusion services in one web-based system.",
    "emr": "Standards-based records with SNOMED CT embedded, open to doctors, staff and patients.",
    "lis": "Sample and result flow for the laboratory, with analysers integrated through Raster IoMT.",
    "neopead-emr": "Paperless neonatal and paediatric records, growth charts and instant discharge summaries.",
    "asset-management": "A lifecycle register of the hospital's equipment and infrastructure within the iHMS suite.",
    "lab-equipment-interfacing": "Uni- and bi-directional analyser integration from a portfolio of 230+ instruments.",
    "iomt-interfacing": "A small box that replaces the interfacing PC and links devices to the LIS and HIS 24x7.",
    "electronic-charting": "Centralised ICU monitoring with inline data from ventilators and monitors.",
    "ot-video-broadcasting": "HD theatre feeds recorded, streamed and shared to classrooms and conference rooms.",
    "telemedicine": "Video consultations, e-prescriptions and follow-ups through a patient app and doctor web portal.",
    "patient-id-wristbands": "Thermal, laser and RFID printable wristbands that survive the ward.",
}
ICON_BY_SLUG = {  # icon on the "works alongside" card
    "pacs": "i-radiology", "ris": "i-hospital", "teleradiology": "i-cloud", "dicom-burner": "i-chip", "dicom-camera": "i-apps",
    "ihms": "i-hospital", "pharmacy-management": "i-layers", "blood-bank-management": "i-badge", "emr": "i-shield",
    "lis": "i-interface", "neopead-emr": "i-support", "asset-management": "i-layers",
    "lab-equipment-interfacing": "i-plug", "iomt-interfacing": "i-chip", "electronic-charting": "i-interface",
    "ot-video-broadcasting": "i-apps", "telemedicine": "i-cloud", "patient-id-wristbands": "i-badge",
}
BY_SLUG = {p["slug"]: p for p in PRODUCTS}
ICON = '<svg class="icon" aria-hidden="true"><use href="#%s"/></svg>'
ARROW = ICON % "i-arrow"

# ── shell ──
about = (ROOT / "about.html").read_text()
SHELL_HEAD = about[:about.index('  <main id="main">')]
SHELL_FOOT = about[about.index("  <!-- ═══════════ Footer ═══════════ -->"):]

EXTRA_SYMBOLS = """      <symbol id="i-check" viewBox="0 0 24 24">
        <path d="M5 12.6l4.4 4.4L19 7.4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </symbol>
      <symbol id="i-download" viewBox="0 0 24 24">
        <path d="M12 3.6v10.6M8.2 10.6l3.8 3.8 3.8-3.8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M4.4 16.4v2.2a1.8 1.8 0 0 0 1.8 1.8h11.6a1.8 1.8 0 0 0 1.8-1.8v-2.2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
      </symbol>
      <symbol id="i-search" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.7"/>
        <path d="M15.8 15.8L20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
      </symbol>
"""
assert SHELL_HEAD.count("    </defs>") == 1
SHELL_HEAD = SHELL_HEAD.replace("    </defs>", EXTRA_SYMBOLS + "    </defs>")
# about.html's own active marks come off; Healthcare Solutions goes on
SHELL_HEAD = SHELL_HEAD.replace('<li><a href="about.html" class="active" aria-current="page">About</a></li>', '<li><a href="about.html">About</a></li>')
SHELL_HEAD = SHELL_HEAD.replace('<li><a href="about.html" aria-current="page">About</a></li>', '<li><a href="about.html">About</a></li>')
SHELL_HEAD = SHELL_HEAD.replace('<a href="healthcare-solutions.html" aria-describedby="megaSolutions">Healthcare Solutions',
                                '<a href="healthcare-solutions.html" class="active" aria-describedby="megaSolutions">Healthcare Solutions')

LIGHTBOX = """  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo viewer" hidden>
    <figure class="lightbox-figure">
      <img src="" alt="">
      <figcaption class="lightbox-cap"></figcaption>
    </figure>
    <button class="lightbox-btn lightbox-close" type="button" aria-label="Close photo viewer">%s</button>
    <button class="lightbox-btn lightbox-prev" type="button" aria-label="Previous photo">%s</button>
    <button class="lightbox-btn lightbox-next" type="button" aria-label="Next photo">%s</button>
  </div>

""" % (ICON % "i-close", ICON % "i-chevron", ICON % "i-chevron")


def esc_attr(s):
    return html.escape(html.unescape(s), quote=True)

def plain(s):
    """strip tags/entities for <title> and meta description"""
    return html.unescape(re.sub(r"<[^>]+>", "", s))

def section_head(sec, hid):
    out = ['        <div class="section-head" data-reveal>']
    if sec.get("eyebrow"):
        out.append(f'          <p class="eyebrow" style="--i:0"><span class="dot"></span>{sec["eyebrow"]}</p>')
    out.append(f'          <h2 id="{hid}" style="--i:1">{sec["heading"]}</h2>')
    if sec.get("sub"):
        out.append(f'          <p class="section-sub" style="--i:2">{sec["sub"]}</p>')
    out.append("        </div>")
    return "\n".join(out)

def side_nav(current):
    groups = []
    for key, (icon, name, href) in CATEGORIES.items():
        lis = "\n".join(
            '              <li><a href="%s.html"%s>%s</a></li>' % (p["slug"], ' aria-current="page"' if p["slug"] == current else "", p["short"])
            for p in PRODUCTS if p["category"] == key)
        groups.append(f"""          <div class="side-nav-group">
            <a class="side-nav-head" href="{href}">{ICON % icon}{name}</a>
            <ul>
{lis}
            </ul>
          </div>""")
    return "\n".join(groups)

# ── section renderers ──
def r_prose(sec, i):
    hid = f"s{i}-h"
    head = ""
    if sec.get("heading"):
        head = f'            <p class="eyebrow"><span class="dot"></span>{sec["eyebrow"]}</p>\n' if sec.get("eyebrow") else ""
        head += f'            <h2 id="{hid}">{sec["heading"]}</h2>\n'
    paras = "\n".join(f"            <p>{p}</p>" for p in sec["paragraphs"])
    badges = ""
    if sec.get("badges"):
        badges = '\n            <div class="store-badges">' + "".join(
            f'\n              <a href="{b["href"]}" target="_blank" rel="noopener"><img src="{b["src"]}" alt="{b["alt"]}" width="{b["w"]}" height="{b["h"]}" loading="lazy"></a>'
            for b in sec["badges"]) + "\n            </div>"
    label = f' aria-labelledby="{hid}"' if sec.get("heading") else ""
    return f"""    <section class="features"{label}>
      <div>
        <div class="prose solution-intro" data-reveal style="--i:0">
{head}{paras}{badges}
        </div>
      </div>
    </section>"""

def r_figure(sec, i):
    hid = f"s{i}-h"
    cls = "schematic" + (" narrow" if sec.get("narrow") else "") + (" photo" if sec.get("photo") else "")
    style = f' style="--ar: {sec["w"]} / {sec["h"]}"' if sec.get("photo") else ""
    head = section_head(sec, hid) + "\n" if sec.get("heading") else ""
    cap = f'\n          <figcaption style="--i:1">{sec["caption"]}</figcaption>' if sec.get("caption") else ""
    label = f' aria-labelledby="{hid}"' if sec.get("heading") else ""
    if sec.get("svg"):
        # an animated inline SVG recreation (so it inherits the page font and
        # theme tokens, and its CSS animations respect prefers-reduced-motion)
        svg = (ROOT / sec["svg"]).read_text().strip()
        svg = re.sub(r"<\?xml[^>]*>\s*", "", svg)
        body = f"""          <div class="glass diagram-card" style="--i:0">
{svg}
          </div>"""
        cls += " diagram"
    else:
        body = f"""          <div class="plate" style="--i:0"{style[7:] if style else ""}>
            <img src="{sec["src"]}" alt="{esc_attr(sec["alt"])}" width="{sec["w"]}" height="{sec["h"]}" loading="lazy" decoding="async">
          </div>"""
    return f"""    <section class="features"{label}>
      <div>
{head}        <figure class="{cls}" data-reveal>
{body}{cap}
        </figure>
      </div>
    </section>"""

def r_features(sec, i):
    hid = f"s{i}-h"
    items = "\n".join(f"""          <article class="feat" style="--i:{n}">
            <span class="feat-icon">{ICON % icon}</span>
            <h3>{h}</h3>
            <p>{p}</p>
          </article>""" for n, (icon, h, p) in enumerate(sec["items"]))
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <div class="feat-grid" data-reveal>
{items}
        </div>
      </div>
    </section>"""

def r_checklist(sec, i):
    hid = f"s{i}-h"
    items = "\n".join(f'          <li class="glass spec" style="--i:{n}">{ICON % "i-check"}{t}</li>' for n, t in enumerate(sec["items"]))
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <ul class="spec-grid" data-reveal aria-label="{esc_attr(plain(sec["heading"]))}">
{items}
        </ul>
      </div>
    </section>"""

def r_points(sec, i):
    hid = f"s{i}-h"
    items = []
    for n, it in enumerate(sec["items"]):
        lead = f'<strong>{it["lead"]}</strong>' if it.get("lead") else ""
        items.append(f'          <li class="glass point" style="--i:{n}">{ICON % "i-check"}<span>{lead}{it["text"]}</span></li>')
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <ul class="point-grid" data-reveal aria-label="{esc_attr(plain(sec["heading"]))}">
{chr(10).join(items)}
        </ul>
      </div>
    </section>"""

def r_screenshots(sec, i):
    hid = f"s{i}-h"
    tabs, panels = [], []
    for n, g in enumerate(sec["groups"]):
        key = g["label"].lower()
        tabs.append(f"""            <button class="tab" type="button" role="tab" id="tab-{key}" aria-controls="panel-{key}" aria-selected="{'true' if n == 0 else 'false'}">
              {g["label"]} <span class="tab-count" aria-hidden="true">{len(g["images"])}</span>
            </button>""")
        imgs = "\n".join(f'              <img src="{src}" alt="DICOM Camera on {g["label"]}, screen {k + 1}" width="{g["w"]}" height="{g["h"]}" loading="lazy" decoding="async">'
                         for k, src in enumerate(g["images"]))
        panels.append(f"""          <div class="tabpanel" id="panel-{key}" role="tabpanel" aria-labelledby="tab-{key}" tabindex="0"{'' if n == 0 else ' hidden'}>
            <div class="shots" style="--shot-h: {g["h"]}px">
{imgs}
            </div>
          </div>""")
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <div data-tabs>
          <div class="tablist" role="tablist" aria-label="Screenshots by device">
{chr(10).join(tabs)}
          </div>
{chr(10).join(panels)}
        </div>
      </div>
    </section>"""

def r_gallery(sec, i):
    hid = f"s{i}-h"
    items = "\n".join(f"""            <button class="gallery-item" type="button" data-full="{src}" data-caption="{esc_attr(cap)}">
              <img src="{src}" alt="{esc_attr(cap)}" loading="lazy" decoding="async">
            </button>""" for src, cap in sec["images"])
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <div class="gallery" data-gallery>
{items}
        </div>
      </div>
    </section>"""

def r_table(sec, i):
    hid = f"s{i}-h"
    ths = "".join(f"<th scope=\"col\">{c}</th>" for c in sec["columns"])
    trs = "\n".join("            <tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in sec["rows"])
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <div data-filter>
          <div class="eq-filter">
            <label class="eq-search">
              {ICON % "i-search"}
              <span class="sr-only">Filter the equipment list</span>
              <input type="search" placeholder="Filter by make, analyser or department…" autocomplete="off">
            </label>
            <span class="eq-count" data-filter-count aria-live="polite"></span>
          </div>
          <div class="table-wrap" tabindex="0">
            <table class="data-table">
              <thead><tr>{ths}</tr></thead>
              <tbody>
{trs}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>"""

def r_cards(sec, i):
    hid = f"s{i}-h"
    cards = []
    for n, c in enumerate(sec["items"]):
        shot = f'\n            <div class="hw-shot"><img src="{c["src"]}" alt="{esc_attr(c["alt"])}" width="{c["w"]}" height="{c["h"]}" loading="lazy" decoding="async"></div>' if c.get("src") else ""
        text = "\n".join(f"            <p>{t}</p>" for t in c["text"])
        cards.append(f"""          <article class="glass hw-card" style="--i:{n}">{shot}
            <h3>{c["title"]}</h3>
            <p class="card-sub">{c["sub"]}</p>
{text}
          </article>""")
    return f"""    <section class="features" aria-labelledby="{hid}">
      <div>
{section_head(sec, hid)}
        <div class="hw-grid range-grid" data-reveal>
{chr(10).join(cards)}
        </div>
      </div>
    </section>"""

RENDER = {"prose": r_prose, "figure": r_figure, "features": r_features, "checklist": r_checklist,
          "points": r_points, "screenshots": r_screenshots, "gallery": r_gallery, "table": r_table, "cards": r_cards}

def related(p):
    others = [q for q in PRODUCTS if q["category"] == p["category"] and q["slug"] != p["slug"]]
    cards = "\n".join(f"""          <article class="glass sol-card" style="--i:{n}">
            <span class="sol-icon">{ICON % ICON_BY_SLUG[q["slug"]]}</span>
            <h3>{q["short"]}</h3>
            <p>{BLURB[q["slug"]]}</p>
            <a class="card-link" href="{q["slug"]}.html">Explore the solution{ARROW}</a>
          </article>""" for n, q in enumerate(others))
    cat = CATEGORIES[p["category"]][1]
    return f"""    <section class="solutions" aria-labelledby="related-h">
      <div>
        <div class="section-head" data-reveal>
          <p class="eyebrow" style="--i:0"><span class="dot"></span>{cat}</p>
          <h2 id="related-h" style="--i:1">Works alongside</h2>
          <p class="section-sub" style="--i:2">{p["short"]} is one part of Raster's {cat} range. The rest plugs straight into it.</p>
        </div>
        <div class="vm-grid" data-reveal>
{cards}
        </div>
      </div>
    </section>"""

def cta(p):
    if p.get("brochure"):
        second = f'<a class="btn btn-ghost" href="{p["brochure"]}" target="_blank" rel="noopener">Download brochure{ICON % "i-download"}</a>'
        tail = " — or send you the brochure to start."
    else:
        second = '<a class="btn btn-ghost" href="healthcare-solutions.html">All healthcare solutions</a>'
        tail = "."
    return f"""    <section class="cta-band" aria-labelledby="cta-h">
      <div class="container">
        <div class="glass cta-card" data-reveal>
          <div style="--i:0">
            <h2 id="cta-h">See {p["short"]} at your institute</h2>
            <p>Tell us about your departments, workflow and existing systems, and we'll map {p["short"]} to them{tail}</p>
          </div>
          <div class="cta-actions" style="--i:1">
            <a class="btn btn-primary" href="contact.html" data-demo-open data-demo-solution="{p["slug"]}">Request a demo{ARROW}</a>
            {second}
          </div>
        </div>
      </div>
    </section>"""

def build(p):
    icon, cat_name, cat_href = CATEGORIES[p["category"]]
    head = SHELL_HEAD
    short, full = plain(p["short"]), plain(p["title"])
    page_title = full if short == full else f"{short} — {full}"
    head = head.replace("<title>About Raster — Healthcare Information Services &amp; Technology</title>",
                        f"<title>{html.escape(page_title)} | Raster</title>")
    head = re.sub(r'<meta name="description" content="[^"]*">',
                  f'<meta name="description" content="{esc_attr(plain(p["lede"]))}">', head)
    # current product in the mega dropdown and the mobile menu
    link = f'<a href="{p["slug"]}.html">{p["short"]}</a>'
    assert head.count(link) == 2, (p["slug"], head.count(link))
    head = head.replace(link, f'<a href="{p["slug"]}.html" aria-current="page">{p["short"]}</a>')

    title = p["title"].replace(p["grad"], f'<span class="grad">{p["grad"]}</span>', 1)
    note = f"    <!-- NOTE: {p['note']} -->\n" if p.get("note") else ""
    sections = "\n\n".join(RENDER[s["type"]](s, n) for n, s in enumerate(p["sections"]))
    has_gallery = any(s["type"] == "gallery" for s in p["sections"])

    main = f"""  <main id="main">
{note}    <!-- ═══════════ Page header ═══════════ -->
    <section class="page-hero" aria-labelledby="page-title">
      <div class="container">
        <p class="eyebrow"><span class="dot"></span>{cat_name} · {p["eyebrow"]}</p>
        <h1 id="page-title">{title}</h1>
        <p class="page-lede">{p["lede"]}</p>
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="index.html">Home</a>
          <span class="sep" aria-hidden="true">/</span>
          <a href="healthcare-solutions.html">Healthcare Solutions</a>
          <span class="sep" aria-hidden="true">/</span>
          <a href="{cat_href}">{cat_name}</a>
          <span class="sep" aria-hidden="true">/</span>
          <span aria-current="page">{p["short"]}</span>
        </nav>
      </div>
    </section>

    <!-- ═══════════ Product side menu + content ═══════════ -->
    <div class="container solution-layout">
      <!-- Always open beside the content on desktop (summary hidden); main.js
           collapses it to a toggle under 1024px. Mirrors the mega dropdown. -->
      <details class="glass side-nav" open>
        <summary>
          <span>{ICON % "i-layers"}All healthcare solutions</span>
          <svg class="icon side-nav-caret" aria-hidden="true"><use href="#i-chevron"/></svg>
        </summary>
        <nav class="side-nav-body" aria-label="Healthcare solutions">
{side_nav(p["slug"])}
        </nav>
      </details>

      <div class="solution-main">
{sections}

{related(p)}
      </div><!-- /.solution-main -->
    </div><!-- /.solution-layout -->

{cta(p)}
  </main>

"""
    return head + main + (LIGHTBOX if has_gallery else "") + SHELL_FOOT

CATEGORY_COPY = {
    "radiology": ("Imaging, archived and read anywhere",
                  "From the vendor-neutral iPACS archive to disc publishing and a DICOM camera in every pocket — one radiology suite, one vendor."),
    "hospital-management": ("The whole hospital on one platform",
                            "Transactions, records, pharmacy, blood bank, laboratory and assets — modules that share one open-source platform and one patient record."),
    "interfacing": ("Every device talking to the record",
                    "Analysers, ventilators and monitors connected to the LIS, HIS and EMR through Raster's interfacing software and the IoMT device."),
    "other": ("Beyond the department",
              "Theatre broadcasting, remote consultations and patient identification that extend care past the ward."),
}

def build_hub():
    """healthcare-solutions.html — every product by category, the target of the
    dropdown headings, footer links, breadcrumbs and CTA ghost buttons."""
    head = SHELL_HEAD
    head = head.replace("<title>About Raster — Healthcare Information Services &amp; Technology</title>",
                        "<title>Healthcare Solutions — PACS, hospital management, interfacing and more | Raster</title>")
    head = re.sub(r'<meta name="description" content="[^"]*">',
                  '<meta name="description" content="Raster\'s healthcare software range: radiology (PACS, RIS, teleradiology, DICOM burner and camera), hospital management (iHMS, pharmacy, blood bank, EMR, LIS, Neopead, assets), interfacing (lab equipment, IoMT, electronic charting) and OT broadcasting, telemedicine and patient ID wristbands.">',
                  head)
    sections = []
    for key, (icon, name, href) in CATEGORIES.items():
        anchor = href.split("#")[1]
        h2, sub = CATEGORY_COPY[key]
        cards = "\n".join(f"""          <article class="glass sol-card" style="--i:{n}">
            <span class="sol-icon">{ICON % ICON_BY_SLUG[q["slug"]]}</span>
            <h3>{q["short"]}</h3>
            <p>{BLURB[q["slug"]]}</p>
            <a class="card-link" href="{q["slug"]}.html">Explore the solution{ARROW}</a>
          </article>""" for n, q in enumerate(x for x in PRODUCTS if x["category"] == key))
        sections.append(f"""    <section class="solutions" id="{anchor}" aria-labelledby="{anchor}-h">
      <div class="container">
        <div class="section-head" data-reveal>
          <p class="eyebrow" style="--i:0"><span class="dot"></span>{name}</p>
          <h2 id="{anchor}-h" style="--i:1">{h2}</h2>
          <p class="section-sub" style="--i:2">{sub}</p>
        </div>
        <div class="sol-grid" data-reveal>
{cards}
        </div>
      </div>
    </section>""")
    main = f"""  <main id="main">
    <!-- ═══════════ Page header ═══════════ -->
    <section class="page-hero" aria-labelledby="page-title">
      <div class="container">
        <p class="eyebrow"><span class="dot"></span>Healthcare Solutions</p>
        <h1 id="page-title">Software for the whole <span class="grad">continuum of care</span></h1>
        <p class="page-lede">Eighteen products across radiology, hospital management, interfacing and beyond — built on open standards so every department shares one patient record.</p>
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="index.html">Home</a>
          <span class="sep" aria-hidden="true">/</span>
          <span aria-current="page">Healthcare Solutions</span>
        </nav>
      </div>
    </section>

{chr(10).join(sections)}

    <!-- ═══════════ CTA ═══════════ -->
    <section class="cta-band" aria-labelledby="cta-h">
      <div class="container">
        <div class="glass cta-card" data-reveal>
          <div style="--i:0">
            <h2 id="cta-h">Not sure where to start?</h2>
            <p>Tell us about your institute and we'll map the range to your departments, workflow and existing systems.</p>
          </div>
          <div class="cta-actions" style="--i:1">
            <a class="btn btn-primary" href="contact.html">Talk to us{ARROW}</a>
            <a class="btn btn-ghost" href="hardware-products.html">Hardware products</a>
          </div>
        </div>
      </div>
    </section>
  </main>

"""
    # the page is its own nav target: mark the trigger current
    head = head.replace('<a href="healthcare-solutions.html" class="active" aria-describedby="megaSolutions">Healthcare Solutions',
                        '<a href="healthcare-solutions.html" class="active" aria-current="page" aria-describedby="megaSolutions">Healthcare Solutions')
    return head + main + SHELL_FOOT

if __name__ == "__main__":
    for p in PRODUCTS:
        (ROOT / f"{p['slug']}.html").write_text(build(p))
        print("wrote", f"{p['slug']}.html")
    (ROOT / "healthcare-solutions.html").write_text(build_hub())
    print("wrote healthcare-solutions.html")
