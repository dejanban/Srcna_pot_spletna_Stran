"""Regenerate web images, four-page brochure PDF and route data from original files.
Requires Pillow; the website itself needs only a static web server.
"""
from pathlib import Path
from PIL import Image, ImageOps
import xml.etree.ElementTree as ET
import math, json
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
board = Image.open(ROOT / 'source/images/InfoTabla_130x120.jpg').convert('RGB')
board.save(OUT / 'images/information-board.webp', quality=90)
# Crop the original photographs without changing their content.
for name, box in {
    'panda': (43,1185,375,1360), 'bridge': (398,1185,727,1360),
    'lake': (753,1185,1082,1360), 'solar': (1108,1185,1436,1360),
}.items():
    board.crop(box).save(OUT / f'images/{name}.webp', quality=95)
# Hero: the board's map with both trails, inside its white frame.
board.crop((52,249,1428,1148)).save(OUT / 'images/hero-map.webp', quality=90)
# Trail marker photos: 3:4 crops around the posts, scaled for the web.
for name, (src, box) in {
    'marker-junction': ('22014', (300,1000,2550,4000)),
    'marker-forest': ('22015', (300,700,2700,3900)),
    'marker-exercise': ('22016', (450,600,2850,3800)),
}.items():
    photo = ImageOps.exif_transpose(Image.open(ROOT / f'source/images/{src}.jpg')).convert('RGB').crop(box)
    photo.resize((900,1200), Image.LANCZOS).save(OUT / f'images/{name}.webp', quality=82)
# Vector logos: drop the embedded CMYK ICC profile and Inkscape editor data (~750 KB each).
SVG, XLINK = 'http://www.w3.org/2000/svg', 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG); ET.register_namespace('xlink', XLINK)
EDITOR = ('http://www.inkscape.org/namespaces/inkscape', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')
(OUT / 'images/logos').mkdir(exist_ok=True)
for name, src in {
    'obcina-crnomelj': 'Obcina_Crnomelj', 'zveza-koronarnih-drustev': 'Zveza koronarnih društev in klubov Slovenije',
    'drustvo-koronarnih-bolnikov': 'Društvo koronarnih bolnikov Dolenjske in Bele krajine',
    'ks-crnomelj': 'Krajevna skupnost Črnomelj', 'zd-crnomelj': 'Zdravstveni dom Črnomelj',
    'ckz-crnomelj': 'Center za krepitev zdravja Črnomelj',
}.items():
    tree = ET.parse(ROOT / f'source/Logos/{src}.svg')
    for parent in tree.iter():
        for child in list(parent):
            if child.tag in (f'{{{SVG}}}color-profile', f'{{{SVG}}}metadata') or child.tag.split('}')[0][1:] in EDITOR:
                parent.remove(child)
        for key in [k for k in parent.attrib if k.split('}')[0][1:] in EDITOR]:
            del parent.attrib[key]
    tree.write(OUT / f'images/logos/{name}.svg', encoding='utf-8', xml_declaration=False)
brochure = Image.open(ROOT / 'source/images/TableZaRazgibavanje.jpg').convert('RGB')
brochure.thumbnail((2600,2600))
brochure.save(OUT / 'images/exercises.webp', quality=88)
original = Image.open(ROOT / 'source/images/TableZaRazgibavanje.jpg').convert('RGB')
# Four portrait pages preserve each panel's complete instructions at readable size.
# Panel boundaries follow the supplied artwork, rather than cutting through text.
bounds = [0,1240,2560,3870,5114]
pages = [original.crop((bounds[i],0,bounds[i+1],original.height)) for i in range(4)]
pages[0].save(OUT / 'documents/vaje-za-razgibavanje.pdf', 'PDF', save_all=True,
              append_images=pages[1:], resolution=150, title='Vaje za razgibavanje – Srčna pot Svibnik')
for i, page in enumerate(pages):
    page.thumbnail((850,1250)); page.save(OUT / f'images/exercise-{i+1}.webp', quality=88)
ns={'g':'http://www.topografix.com/GPX/1/1'}
def distance(a,b):
    lat1,lat2=map(math.radians,[a[0],b[0]])
    dlat=lat2-lat1; dlon=math.radians(b[1]-a[1])
    h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000*2*math.atan2(math.sqrt(h),math.sqrt(1-h))
data={}
for key,filename in [('short','ribja-pot'),('long','ucna-pot')]:
    root=ET.parse(OUT / f'gpx/{filename}.gpx').getroot()
    segments=[]; total=ascent=descent=0
    for seg in root.findall('.//g:trkseg',ns):
        points=[]
        for p in seg.findall('g:trkpt',ns):
            ele=p.find('g:ele',ns)
            if ele is None: raise ValueError('Missing elevation')
            point=[float(p.attrib['lat']),float(p.attrib['lon']),float(ele.text)]
            if points:
                total+=distance(points[-1],point)
                delta=point[2]-points[-1][2]
                ascent+=max(delta,0); descent+=max(-delta,0)
            points.append(point+[round(total,2)])
        segments.append(points)
    flat=[p for s in segments for p in s]; heights=[p[2] for p in flat]
    data[key]={'segments':segments,'distance':round(total),'min':round(min(heights),1),'max':round(max(heights),1),
               'ascent':round(ascent),'descent':round(descent),'file':f'assets/gpx/{filename}.gpx'}
    print(key,{k:v for k,v in data[key].items() if k!='segments'})
(OUT / 'data/routes.js').write_text('window.ROUTES = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
