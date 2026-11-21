from pathlib import Path
import json
import xml.etree.ElementTree as ET
import cairosvg

root = Path("smeny_pro_mobile_build")
www = root / "www"
config_path = root / "capacitor.config.json"
config = json.loads(config_path.read_text(encoding="utf-8"))
config["appName"] = "ROSTERA"
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

html_path = www / "index.html"
html = html_path.read_text(encoding="utf-8")
html = html.replace("<title>Směny PRO</title>", "<title>ROSTERA</title>")
html = html.replace('alt="Směny PRO"', 'alt="ROSTERA"')
html = html.replace("Směny PRO – mobile-first layer", "ROSTERA – mobile-first layer")
html_path.write_text(html, encoding="utf-8")

# ROSTERA monogram: a precise, modern R with a continuous shift-arrow motif.
svg = r'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#102b4b"/><stop offset=".58" stop-color="#09182d"/><stop offset="1" stop-color="#062d32"/></linearGradient>
 <linearGradient id="mark" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#70f4e0"/><stop offset=".48" stop-color="#39cbbb"/><stop offset="1" stop-color="#398dff"/></linearGradient>
 <filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="13"/></filter>
</defs>
<rect width="512" height="512" rx="112" fill="url(#bg)"/>
<circle cx="255" cy="255" r="165" fill="#24cdb9" opacity=".10" filter="url(#glow)"/>
<path d="M152 366V147h111c70 0 108 34 108 91 0 43-23 71-65 83l76 45" fill="none" stroke="#07101e" stroke-width="58" stroke-linecap="round" stroke-linejoin="round" opacity=".65"/>
<path d="M152 366V147h111c70 0 108 34 108 91 0 43-23 71-65 83l76 45" fill="none" stroke="url(#mark)" stroke-width="43" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M152 147h-32" stroke="#70f4e0" stroke-width="19" stroke-linecap="round"/>
<path d="M370 321l39 45-61 2" fill="none" stroke="#70f4e0" stroke-width="17" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="263" cy="238" r="14" fill="#f2fffd"/>
</svg>'''
(www / "app-icon.svg").write_text(svg, encoding="utf-8")

res = root / "android" / "app" / "src" / "main" / "res"
for folder, size in {
    "mipmap-mdpi": 48, "mipmap-hdpi": 72, "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144, "mipmap-xxxhdpi": 192
}.items():
    target = res / folder
    target.mkdir(parents=True, exist_ok=True)
    for name in ("ic_launcher.png", "ic_launcher_round.png"):
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(target / name), output_width=size, output_height=size)

# Android 8+ adaptive icon resources
foreground = svg.replace('<rect width="512" height="512" rx="112" fill="url(#bg)"/>', '')
drawable = res / "drawable-nodpi"
drawable.mkdir(parents=True, exist_ok=True)
cairosvg.svg2png(bytestring=foreground.encode(), write_to=str(drawable / "rostera_launcher_foreground.png"), output_width=432, output_height=432)
bg = res / "drawable" / "rostera_launcher_background.xml"
bg.parent.mkdir(parents=True, exist_ok=True)
bg.write_text('<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle"><corners android:radius="96dp"/><solid android:color="#09182D"/></shape>', encoding="utf-8")
adaptive = res / "mipmap-anydpi-v26"
adaptive.mkdir(parents=True, exist_ok=True)
adaptive_xml = '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android"><background android:drawable="@drawable/rostera_launcher_background"/><foreground android:drawable="@drawable/rostera_launcher_foreground"/></adaptive-icon>'
(adaptive / "ic_launcher.xml").write_text(adaptive_xml, encoding="utf-8")
(adaptive / "ic_launcher_round.xml").write_text(adaptive_xml, encoding="utf-8")

# Set the launcher label to ROSTERA.
strings = res / "values" / "strings.xml"
strings.parent.mkdir(parents=True, exist_ok=True)
if strings.exists():
    tree = ET.parse(strings)
    node = tree.getroot().find("string[@name='app_name']")
    if node is None:
        node = ET.SubElement(tree.getroot(), "string", {"name": "app_name"})
    node.text = "ROSTERA"
    tree.write(strings, encoding="utf-8", xml_declaration=True)
else:
    strings.write_text('<?xml version="1.0" encoding="utf-8"?><resources><string name="app_name">ROSTERA</string></resources>', encoding="utf-8")

print("ROSTERA branding applied: app label, web title, monogram logo and Android launcher icons.")
