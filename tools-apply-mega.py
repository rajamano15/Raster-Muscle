#!/usr/bin/env python3
"""Swap the plain "Healthcare Solutions" nav item for a mega dropdown, and add
the same sections to the mobile menu as <details>. Runs across every page and
preserves whatever active state each page already carries."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent

SECTIONS = [
    ("Radiology", "radiology", "i-radiology", [
        ("PACS", "pacs"), ("RIS", "ris"), ("Teleradiology", "teleradiology"),
        ("DICOM Burner", "dicom-burner"), ("DICOM Camera", "dicom-camera")]),
    ("Hospital Management", "hospital-management", "i-hospital", [
        ("IHMS", "ihms"), ("Pharmacy Management", "pharmacy"),
        ("Blood Bank Management", "blood-bank"), ("EMR", "emr"),
        ("Lab Information System", "lis"), ("Neopead EMR &amp; Charting", "neopead"),
        ("Asset Management", "asset-management")]),
    ("Interfacing Applications", "interfacing", "i-interface", [
        ("Lab Equipment Interfacing", "lab-interfacing"),
        ("IoMT &amp; Interfacing", "iomt"), ("Electronic Charting", "electronic-charting")]),
    ("Other Applications", "other-applications", "i-apps", [
        ("OT – Video Broadcasting", "ot-broadcast"), ("Telemedicine", "telemedicine"),
        ("Patient ID Wristbands", "wristbands")]),
]
H = "healthcare-solutions.html"
ICON = '<svg class="icon" aria-hidden="true"><use href="#%s"/></svg>'


def mega_panel():
    cols = []
    for title, slug, icon, items in SECTIONS:
        lis = "\n".join(
            f'                  <li><a href="{H}#{a}">{label}</a></li>'
            for label, a in items)
        cols.append(
            f'              <div class="mega-col">\n'
            f'                <a class="mega-head" href="{H}#{slug}">{ICON % icon}{title}</a>\n'
            f'                <ul>\n{lis}\n                </ul>\n'
            f'              </div>')
    return (
        '            <div class="mega glass" id="megaSolutions">\n'
        '              <div class="mega-grid">\n'
        + "\n".join(cols) + "\n"
        '              </div>\n'
        '              <div class="mega-foot">\n'
        '                <p>Radiology, hospital administration, device interfacing and more — engineered around patient care.</p>\n'
        f'                <a class="btn btn-primary" href="{H}">All healthcare solutions'
        f'<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg></a>\n'
        '              </div>\n'
        '            </div>')


def mobile_details():
    blocks = []
    for title, slug, icon, items in SECTIONS:
        links = "\n".join(
            f'            <a href="{H}#{a}">{label}</a>' for label, a in items)
        blocks.append(
            f'            <h4>{title}</h4>\n{links}')
    return (
        '        <li>\n'
        '          <details class="mobile-sub">\n'
        '            <summary>Healthcare Solutions'
        '<svg class="icon" aria-hidden="true"><use href="#i-chevron"/></svg></summary>\n'
        '            <div class="mobile-sub-body">\n'
        + "\n".join(blocks) + "\n"
        f'              <a class="btn btn-primary mobile-sub-all" href="{H}">All healthcare solutions'
        f'<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg></a>\n'
        '            </div>\n'
        '          </details>\n'
        '        </li>')


PANEL, MOBILE = mega_panel(), mobile_details()
changed = []

for page in sorted(ROOT.glob("*.html")):
    s = page.read_text()
    if 'class="mega' in s:
        continue                                    # already applied

    # ── desktop: wrap the nav item in a .has-mega li and append the panel ──
    # keep whatever classes/attributes that page already has on the link
    pat = re.compile(
        r'(?P<indent>[ \t]*)<li><a href="healthcare-solutions\.html"(?P<attrs>[^>]*)>'
        r'Healthcare Solutions</a></li>')
    m = pat.search(s)
    if not m:
        print("  ! main-nav item not found in", page.name); continue
    ind = m.group("indent")
    attrs = m.group("attrs")
    repl = (f'{ind}<li class="has-mega">\n'
            f'{ind}  <a href="{H}"{attrs} aria-describedby="megaSolutions">Healthcare Solutions'
            f'<svg class="icon nav-caret" aria-hidden="true"><use href="#i-chevron"/></svg></a>\n'
            f'{PANEL}\n'
            f'{ind}</li>')
    s = s[:m.start()] + repl + s[m.end():]

    # ── mobile: replace the flat item inside .mobile-primary ──
    mob = re.compile(
        r'[ \t]*<li><a href="healthcare-solutions\.html"[^>]*>Healthcare Solutions</a></li>')
    m2 = mob.search(s)
    if m2:
        s = s[:m2.start()] + MOBILE + s[m2.end():]
    else:
        print("  ! mobile item not found in", page.name)

    page.write_text(s)
    changed.append(page.name)

print("updated", len(changed), "pages:", " ".join(changed))
