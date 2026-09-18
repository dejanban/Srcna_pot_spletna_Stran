"""Regenerate web images, four-page brochure PDF and route data from original files.
Requires Pillow; the website itself needs only a static web server.
"""
from pathlib import Path
from shutil import copyfile
from PIL import Image
import xml.etree.ElementTree as ET
import math, json
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
# Keep the supplied trail artwork intact; CSS frames the three square signs.
for source, target in [
    ('UsmerjevalneTablice_9x9.jpg', 'trail-signs.jpg'),
    ('KotičekZaSproščanje_15x30.jpg', 'relaxation-sign.jpg'),
]:
    copyfile(ROOT / 'source/images' / source, OUT / 'images' / target)
board = Image.open(ROOT / 'source/images/InfoTabla_130x120.jpg').convert('RGB')
board.save(OUT / 'images/information-board.webp', quality=90)
# Crop the original photographs without changing their content.
for name, box in {
    'panda': (43,1185,375,1360), 'bridge': (398,1185,727,1360),
    'lake': (753,1185,1082,1360), 'solar': (1108,1185,1436,1360),
    'partners': (185,1650,1730,1745),
}.items():
    board.crop(box).save(OUT / f'images/{name}.webp', quality=95)
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
