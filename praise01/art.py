import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toon
from toon import ease, inout, back, W, H, FPS

os.chdir(os.path.dirname(os.path.abspath(__file__)))
BG = (250, 244, 232)
GUT = 110

def rounded(im, r=34, border=6):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=r, fill=255)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    if border:
        ImageDraw.Draw(out).rounded_rectangle([1, 1, im.width - 2, im.height - 2], radius=r, outline=(70, 50, 40), width=border)
    return out

def scaled(im, w):
    h = round(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    if w > 600: im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    return im

col = Image.open('src/collage.png').convert('RGB')
panels = [
    dict(img=scaled(Image.open('src/deck.png').convert('RGB'), 1000), hold=3.6, stamp=None),
    dict(img=scaled(col.crop((495, 862, 927, 1247)), 960), hold=2.7, stamp=(820, 700)),
    dict(img=scaled(col.crop((12, 1258, 464, 1655)), 960), hold=2.7, stamp=(830, 690)),
    dict(img=scaled(col.crop((470, 1250, 932, 1655)), 960), hold=2.7, stamp=(130, 540)),
    dict(img=scaled(Image.open('src/end.png').convert('RGB'), 1000), hold=3.8, stamp=None),
]

# stamp element (1x) reused
st = toon.stamp_el(150, 150, 0)
stamp_img = st['img']

top = H // 2 - panels[0]['img'].height // 2
y = top
for p in panels:
    p['y'] = y; y += p['img'].height + GUT
stripH = y + H
strip = Image.new('RGB', (W, stripH), BG)
d = ImageDraw.Draw(strip)
for i in range(0, stripH, 46):  # faint dotted paper
    for j in range(0, W, 46):
        if (i // 46 + j // 46) % 2 == 0: d.ellipse([j - 3, i - 3, j + 3, i + 3], fill=(238, 228, 210))
for p in panels:
    im = rounded(p['img'])
    p['x'] = (W - im.width) // 2
    sh = Image.new('RGBA', (im.width + 40, im.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 28, im.width + 20, im.height + 28], radius=34, fill=(120, 90, 60, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    strip.paste(sh, (p['x'] - 20, p['y'] - 20), sh)
    strip.paste(im, (p['x'], p['y']), im)

SCR = 0.8
t = 0
for i, p in enumerate(panels):
    p['arrive'] = t; t += p['hold'] + (SCR if i < len(panels) - 1 else 0)
total = t

def center(p): return p['y'] + p['img'].height / 2

def cam(T):
    for i, p in enumerate(panels):
        a, h = p['arrive'], p['hold']
        if T < a + h or i == len(panels) - 1:
            c = center(p)
            if i == 0:  # gentle drift on the tall first panel
                return c
            return c
        if T < a + h + SCR:
            n = center(panels[i + 1])
            return center(p) + (n - center(p)) * inout((T - a - h) / SCR)
    return center(panels[-1])

def frame(T):
    top_y = int(round(cam(T) - H / 2))
    f = strip.crop((0, top_y, W, top_y + H))
    for p in panels:
        if p['stamp'] is None or T < p['arrive']: continue
        pt = T - p['arrive'] - 0.7
        if pt <= 0: continue
        sx, sy = p['x'] + p['stamp'][0], p['y'] - top_y + p['stamp'][1]
        im = stamp_img
        q = pt / 0.35
        if q < 1:
            s = 1.8 - 0.8 * back(q)
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
            a = ease(q * 2)
            im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
        f.paste(im, (int(sx - im.width / 2), int(sy - im.height / 2)), im)
    a = min(1.0, T / 0.3, (total - T) / 0.6)
    if a < 1: f = Image.blend(Image.new('RGB', (W, H), BG), f, max(0.0, a))
    return f

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        shots = [p['arrive'] + p['hold'] - 0.1 for p in panels] + [panels[0]['arrive'] + panels[0]['hold'] + SCR / 2]
        m = Image.new('RGB', (360 * 3, 640 * 2), (255, 255, 255))
        for i, T in enumerate(shots): m.paste(frame(T).resize((360, 640)), ((i % 3) * 360, (i // 3) * 640))
        m.save('art_sheet.png'); frame(shots[2]).save('art_full2.png'); sys.exit(0)
    names = []
    for i, p in enumerate(panels):
        T0 = p['arrive']; T1 = panels[i + 1]['arrive'] if i + 1 < len(panels) else total
        nm = f'a{i}'; toon.render_seg(nm, T0, T1, frame); names.append(nm)
    with open('alist.txt', 'w') as fh:
        for nm in names: fh.write(f"file '{nm}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'alist.txt', '-c', 'copy', 'asilent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'asilent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', '나칭찬_웹툰릴스_그림버전.mp4'], check=True)
    print('done', total)
