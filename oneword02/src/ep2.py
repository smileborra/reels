import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {'__name__': 'base', '__file__': os.path.join(HERE, 'base.py')}
exec(compile(open(os.path.join(HERE, 'base.py')).read(), 'base', 'exec'), ns)
os.chdir(HERE)
g = ns
W, H, BW, BH = g['W'], g['H'], g['BW'], g['BH']

g['EP'] = 'EP.2'
g['COVER_Q'] = '색 · 식물 · 동물 · 과일 · 채소\n꽃 · 물고기 · 새 · 사물 · 음악'
g['END_IDX'] = 0

def fit(fn):
    im = Image.open('photos/' + fn).convert('RGB')
    w, h = im.size
    tw = int(h * 9 / 16)
    if tw <= w:
        x0 = (w - tw) // 2; im = im.crop((x0, 0, x0 + tw, h))
    else:
        th = int(w * 16 / 9); y0 = (h - th) // 2; im = im.crop((0, y0, w, y0 + th))
    return im.resize((BW, BH), Image.LANCZOS)

def pepper_grid():
    gap = 8; rh = (BH - gap) // 2
    m = Image.new('RGB', (BW, BH), (10, 20, 10))
    for i, (fn, box) in enumerate([('pepper_a.jpg', (294, 0, 2058, 1568)), ('pepper_b.jpg', (400, 0, 2164, 1568))]):
        m.paste(Image.open('photos/' + fn).convert('RGB').crop(box).resize((BW, rh), Image.LANCZOS), (0, i * (rh + gap)))
    return m

def ov_none(f, t): pass

def ov_bubbles(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(34):
        bx = (k * 137 + 25 * math.sin(t * 1.5 + k)) % W; ph = (t * 0.22 + k * 0.083) % 1
        by = H - ph * (H + 80); rr = 5 + (k % 5) * 4
        d.ellipse([bx - rr, by - rr, bx + rr, by + rr], outline=(255, 255, 255, int(170 * (1 - ph))), width=3)
        d.ellipse([bx - rr * 0.5, by - rr * 0.6, bx - rr * 0.1, by - rr * 0.2], fill=(255, 255, 255, int(150 * (1 - ph))))
    f.alpha_composite(L)

def ov_rain(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(90):
        x = (k * 97) % W; y = ((k * 211) + t * 1600) % (H + 200) - 100
        d.line([(x, y), (x - 8, y + 46)], fill=(200, 220, 255, 70), width=2)
    f.alpha_composite(L)

def card(q, a, en, bg, ov, **kw):
    return dict(q=q, a=a, en=en, bg=bg, ov=ov, theme='dark', **kw)

dust = g['ov_dust']
CARDS = [
    card('색이라면?', '청록', 'Teal', lambda: fit('teal.jpg'), dust((220, 255, 250)), cy=900),
    card('식물이라면?', '대나무', 'Bamboo', lambda: fit('forest.jpg'), dust((255, 240, 180)), cy=960),
    card('동물이라면?', '고양이', 'Cat', lambda: fit('cat.jpg'), ov_none, cy=1300, panel=True),
    card('과일이라면?', '자두', 'Plum', lambda: fit('plum.jpg'), dust((255, 230, 200)), cy=1370, panel=True),
    card('채소라면?', '청양고추', 'Cheongyang chili', pepper_grid, ov_none, cy=960, panel=True),
    card('꽃이라면?', '동백', 'Camellia', lambda: fit('camellia.jpg'), dust((255, 200, 190)), cy=560),
    card('물고기라면?', '복어', 'Pufferfish', lambda: fit('puffer.jpg'), ov_bubbles, cy=1390),
    card('새라면?', '까치', 'Magpie', lambda: fit('magpie.jpg'), ov_none, cy=1400, panel=True),
    card('사물이라면?', '돋보기', 'Magnifying glass', lambda: fit('magnifier.jpg'), dust((255, 235, 200)), cy=540),
    card('음악이라면?', '시티팝', 'City pop', lambda: fit('citypop.jpg'), ov_rain, cy=760),
]

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    scenes = [g['card_scene'](i, c) for i, c in enumerate(CARDS)]
    cover = g['photo_cover']()
    cover(2.7).save('cover_ep2.jpg', quality=93)
    end = g['end_scene']([b for _, b in scenes])
    if mode == 'preview':
        frames = [cover(2.7)] + [d(2.3) for d, _ in scenes] + [end(2.5)]
        m = Image.new('RGB', (240 * 6, 427 * 2))
        for k, fr in enumerate(frames): m.paste(fr.resize((240, 427)), ((k % 6) * 240, (k // 6) * 427))
        m.save('sheet.png'); sys.exit(0)
    R = g['render']; names = []
    R('c00', 2.8, cover, fin=0.2); names.append('c00')
    for i, (d, _) in enumerate(scenes):
        R(f'c{i + 1:02d}', g['CARD_DUR'], d); names.append(f'c{i + 1:02d}')
    R('c11', 3.0, end, fout=0.6); names.append('c11')
    with open('list.txt', 'w') as fh:
        for nm in names: fh.write(f"file '{nm}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', 'me_in_one_word_ep2.mp4'], check=True)
    print('done')
