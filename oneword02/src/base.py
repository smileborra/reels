import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
BW, BH = 1188, 2112  # base canvas (10% larger) for slow zoom

NOTO = '/usr/share/fonts/opentype/noto/'
def sans(w, s): return ImageFont.truetype(NOTO + f'NotoSansCJK-{w}.ttc', int(s), index=1)
def serif(w, s): return ImageFont.truetype(NOTO + f'NotoSerifCJK-{w}.ttc', int(s), index=1)
def free(style, s):
    return ImageFont.truetype(f'/usr/share/fonts/truetype/freefont/FreeSerif{style}.ttf', int(s))
FDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
def jua(s): return ImageFont.truetype(FDIR + '/jua.ttf', int(s))
def dodum(s): return ImageFont.truetype(FDIR + '/gowun-dodum.ttf', int(s))
def nunito(w, s, italic=False): return ImageFont.truetype(FDIR + f"/nunito-latin-{w}-{'italic' if italic else 'normal'}.ttf", int(s))
def inter(w, s): return ImageFont.truetype(f'/usr/share/fonts/opentype/inter/Inter-{w}.otf', int(s))

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def inout(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

# ---------- numpy helpers ----------
def vgrad(stops, w=BW, h=BH):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3))
    pos = [p for p, _ in stops]; cols = np.array([c for _, c in stops], float)
    for k in range(3): out[:, k] = np.interp(ys, pos, cols[:, k])
    return np.repeat(out[:, None, :], w, axis=1)

def radial_mask(cx, cy, r, w=BW, h=BH, power=1.0):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** power

def blend(arr, col, m):
    m = m[..., None]
    return arr * (1 - m) + np.array(col, float) * m

def to_img(arr): return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def vignette(arr, k=0.55):
    m = radial_mask(BW / 2, BH / 2, math.hypot(BW, BH) / 1.7, power=0.9)
    return arr * (1 - k + k * m[..., None])

def grain(img, amt=10, seed=0):
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.int16)
    n = rng.normal(0, amt, a.shape[:2])[..., None]
    return to_img(a + n)

def layer(): return Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
def comp(base, lay): base = base.convert('RGBA'); base.alpha_composite(lay); return base.convert('RGB')

# ---------- backgrounds (static base) + per-frame overlay ----------
def bg_jjamppong():
    a = vgrad([(0, (120, 18, 10)), (0.5, (196, 52, 20)), (1, (70, 8, 6))])
    a = blend(a, (240, 110, 40), radial_mask(BW * 0.5, BH * 0.62, 900, power=1.6) * 0.75)
    img = to_img(vignette(a, 0.5))
    L = layer(); d = ImageDraw.Draw(L); r = random.Random(1)
    # noodle waves (soft, lower half)
    for i in range(9):
        y0 = 1450 + i * 70 + r.uniform(-15, 15); per = r.uniform(160, 240); ph = r.uniform(0, 6)
        pts = [(x, y0 + 30 * math.sin(x / per + ph)) for x in range(-40, BW + 40, 8)]
        d.line(pts, fill=(255, 220, 160, 55), width=22, joint='curve')
    L = L.filter(ImageFilter.GaussianBlur(6))
    img = comp(img, L)
    L = layer(); d = ImageDraw.Draw(L)
    for _ in range(70):  # oil droplets
        x, y, rr = r.uniform(0, BW), r.uniform(0, BH), r.uniform(10, 60)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 190, 90, 120), width=3)
        d.ellipse([x - rr * 0.5, y - rr * 0.7, x - rr * 0.1, y - rr * 0.35], fill=(255, 235, 200, 110))
    for _ in range(140):  # chili flakes
        x, y, rr = r.uniform(0, BW), r.uniform(0, BH), r.uniform(3, 8)
        d.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], fill=(150, 10, 6, 200))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(1.2)))
    return grain(img, 6, 1)

def ov_steam(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(5):
        x0 = 150 + k * 200
        ph = (t * 0.35 + k * 0.23) % 1
        for j in range(18):
            u = j / 18
            y = 1700 - (ph + u) % 1 * 1500
            x = x0 + 60 * math.sin(y / 140 + k)
            a = int(60 * math.sin(math.pi * ((ph + u) % 1)))
            d.ellipse([x - 70, y - 70, x + 70, y + 70], fill=(255, 245, 235, max(0, a)))
    f.alpha_composite(L.filter(ImageFilter.GaussianBlur(28)))

def bg_americano():
    a = vgrad([(0, (232, 216, 196)), (0.28, (176, 128, 86)), (0.55, (84, 50, 30)), (1, (28, 16, 10))])
    img = to_img(vignette(a, 0.35))
    L = layer(); d = ImageDraw.Draw(L); r = random.Random(3)
    for _ in range(220):  # condensation droplets on glass
        x, y, rr = r.uniform(0, BW), r.uniform(0, BH), r.uniform(4, 16)
        d.ellipse([x - rr, y - rr * 1.2, x + rr, y + rr * 1.2], fill=(255, 255, 255, 40), outline=(255, 255, 255, 90), width=2)
        d.ellipse([x - rr * 0.4, y - rr * 0.8, x, y - rr * 0.3], fill=(255, 255, 255, 150))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(0.8)))
    return grain(img, 5, 3)

CUBES = [(170, 1500, 210, 12), (820, 1380, 240, -18), (520, 1720, 200, 30), (930, 1820, 170, 8), (90, 1880, 160, -25)]
def ov_ice(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for i, (x, y, s, rot) in enumerate(CUBES):
        yy = y + 18 * math.sin(t * 1.4 + i); rr = rot + 6 * math.sin(t * 0.9 + i)
        c = Image.new('RGBA', (s + 60, s + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
        d.rounded_rectangle([30, 30, 30 + s, 30 + s], radius=s // 5, fill=(220, 240, 255, 70), outline=(255, 255, 255, 170), width=5)
        d.rounded_rectangle([46, 46, 30 + s * 0.55, 30 + s * 0.38], radius=s // 8, fill=(255, 255, 255, 90))
        d.line([(30 + s * 0.8, 40), (30 + s - 6, 30 + s * 0.6)], fill=(255, 255, 255, 120), width=6)
        c = c.rotate(rr, resample=Image.BICUBIC, expand=True)
        L.alpha_composite(c, (int(x - c.width / 2), int(yy - c.height / 2)))
    d = ImageDraw.Draw(L)
    for k in range(40):  # bubbles
        bx = (k * 137) % W; ph = (t * 0.25 + k * 0.071) % 1
        by = H - ph * 1100; rr = 4 + (k % 4) * 3
        d.ellipse([bx - rr, by - rr, bx + rr, by + rr], outline=(255, 255, 255, int(160 * (1 - ph))), width=2)
    f.alpha_composite(L)

def bg_arnak():
    a = vgrad([(0, (8, 40, 40)), (0.5, (16, 70, 62)), (1, (6, 26, 24))])
    a = blend(a, (60, 130, 100), radial_mask(BW / 2, BH * 0.45, 800, power=1.5) * 0.5)
    img = to_img(vignette(a, 0.6))
    L = layer(); d = ImageDraw.Draw(L)
    gold = (214, 168, 74)
    cx, cy = BW / 2, BH * 0.47
    for k, rr in enumerate([520, 470, 380, 300]):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=gold + (90 if k % 2 else 140,), width=4 if k % 2 else 7)
    for i in range(24):  # glyph ticks around ring
        an = i * math.pi / 12
        d.line([(cx + 470 * math.cos(an), cy + 470 * math.sin(an)), (cx + 520 * math.cos(an), cy + 520 * math.sin(an))], fill=gold + (150,), width=5)
    for i in range(8):
        an = i * math.pi / 4 + math.pi / 8
        px, py = cx + 340 * math.cos(an), cy + 340 * math.sin(an)
        d.regular_polygon((px, py, 26), 3 + (i % 3), rotation=i * 15, outline=gold + (150,), width=4)
    # stepped pyramid at bottom
    for s in range(6):
        w2 = 820 - s * 120; y = BH - 120 - s * 70
        d.rectangle([cx - w2 / 2, y - 70, cx + w2 / 2, y], fill=(10, 34, 30, 230), outline=gold + (110,), width=3)
    img = comp(img, L)
    # jungle leaves at edges
    L = layer(); d = ImageDraw.Draw(L); r = random.Random(5)
    for _ in range(26):
        side = r.choice([0, 1]); x = r.uniform(-80, 160) if side == 0 else r.uniform(BW - 160, BW + 80)
        y = r.uniform(0, BH); s = r.uniform(120, 260); an = r.uniform(0, 6.28)
        pts = []
        for j in range(21):
            u = j / 20; w2 = math.sin(math.pi * u) * s * 0.32
            pts.append((u * s, w2))
        pts += [(u, -w) for u, w in reversed(pts)]
        rot = [(x + px * math.cos(an) - py * math.sin(an), y + px * math.sin(an) + py * math.cos(an)) for px, py in pts]
        d.polygon(rot, fill=(4, 40 + r.randint(0, 30), 26, 235))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(2)))
    return grain(img, 7, 5)

def ov_dust(col):
    def fn(f, t):
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        for k in range(60):
            x = (k * 211 + 40 * math.sin(t * 0.7 + k)) % W
            y = (k * 397 - t * (25 + k % 5 * 8)) % H
            rr = 2 + k % 4; a = int(120 + 100 * math.sin(t * 2 + k))
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (max(0, a),))
        f.alpha_composite(L.filter(ImageFilter.GaussianBlur(1)))
    return fn

def bg_autumn():
    a = vgrad([(0, (70, 150, 230)), (0.55, (150, 200, 245)), (1, (236, 232, 214))])
    a = blend(a, (255, 250, 230), radial_mask(BW * 0.82, BH * 0.1, 700, power=1.4) * 0.8)
    img = to_img(a)
    L = layer(); d = ImageDraw.Draw(L); r = random.Random(7)
    for cx, cy, s in [(250, 420, 1.0), (880, 700, 0.8), (420, 1050, 0.6)]:
        for _ in range(9):
            ox, oy = r.uniform(-200, 200) * s, r.uniform(-50, 50) * s; rr = r.uniform(80, 140) * s
            d.ellipse([cx + ox - rr, cy + oy - rr * 0.7, cx + ox + rr, cy + oy + rr * 0.7], fill=(255, 255, 255, 170))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(26)))
    # distant hills
    L = layer(); d = ImageDraw.Draw(L)
    pts = [(x, BH - 380 - 60 * math.sin(x / 260) - 30 * math.sin(x / 90)) for x in range(0, BW + 20, 20)]
    d.polygon(pts + [(BW, BH), (0, BH)], fill=(206, 150, 70, 255))
    pts = [(x, BH - 250 - 40 * math.sin(x / 200 + 2)) for x in range(0, BW + 20, 20)]
    d.polygon(pts + [(BW, BH), (0, BH)], fill=(170, 96, 46, 255))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(2)))
    return grain(img, 4, 7)

LEAFC = [(232, 120, 40), (240, 170, 50), (200, 70, 40), (226, 150, 60)]
def ov_leaves(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(14):
        ph = (t * 0.12 + k * 0.073) % 1
        x = (k * 173 + 90 * math.sin(t * 0.8 + k)) % W; y = -80 + ph * (H + 160)
        s = 26 + k % 3 * 10; an = t * 1.5 + k
        pts = []
        for j in range(13):
            u = j / 12; w2 = math.sin(math.pi * u) * s * 0.45
            pts.append((u * s * 2 - s, w2))
        pts += [(u, -w) for u, w in reversed(pts)]
        rot = [(x + px * math.cos(an) - py * math.sin(an), y + px * math.sin(an) + py * math.cos(an)) for px, py in pts]
        d.polygon(rot, fill=LEAFC[k % 4] + (230,))
    f.alpha_composite(L)

def bg_study():
    a = vgrad([(0, (40, 24, 14)), (1, (22, 12, 8))])
    img = to_img(a)
    L = layer(); d = ImageDraw.Draw(L); r = random.Random(9)
    cols = [(110, 36, 30), (40, 60, 52), (150, 110, 60), (60, 44, 80), (180, 150, 110), (90, 70, 50), (30, 50, 80), (130, 80, 40)]
    shelf_h = 300
    for row in range(BH // shelf_h + 1):
        y1 = row * shelf_h + 40; x = 20
        while x < BW - 20:
            bw = r.randint(36, 78); bh = r.randint(190, 245); c = r.choice(cols)
            d.rectangle([x, y1 + shelf_h - 40 - bh, x + bw, y1 + shelf_h - 40], fill=c + (255,))
            d.line([(x + 6, y1 + shelf_h - 40 - bh + 30), (x + bw - 6, y1 + shelf_h - 40 - bh + 30)], fill=(214, 180, 110, 160), width=3)
            d.line([(x + 6, y1 + shelf_h - 70), (x + bw - 6, y1 + shelf_h - 70)], fill=(214, 180, 110, 160), width=3)
            x += bw + r.randint(2, 6)
        d.rectangle([0, y1 + shelf_h - 40, BW, y1 + shelf_h - 6], fill=(86, 52, 26, 255))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(5)))
    a = np.asarray(img).astype(float) * 0.55
    a = blend(a, (255, 190, 110), radial_mask(BW * 0.3, BH * 0.3, 1200, power=1.8) * 0.45)
    return grain(to_img(vignette(a, 0.6)), 6, 9)

def bg_velvet():
    y, x = np.mgrid[0:BH, 0:BW].astype(float)
    f = (np.sin(x / 140 + y / 260) * 0.5 + np.sin(x / 70 - y / 410 + 1.3) * 0.3 + np.sin((x + y) / 520) * 0.4)
    f = (f - f.min()) / (f.max() - f.min())
    dark, mid, hi = np.array([40, 4, 18.]), np.array([110, 14, 44.]), np.array([196, 70, 110.])
    a = np.where(f[..., None] < 0.6, dark + (mid - dark) * (f[..., None] / 0.6), mid + (hi - mid) * ((f[..., None] - 0.6) / 0.4) ** 2)
    img = to_img(vignette(a, 0.5))
    return grain(img, 9, 11)

def ov_sweep(col, width=380, alpha=60, speed=0.45):
    def fn(f, t):
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        cx = -600 + ((t * speed) % 1.6) * (W + 1200)
        d.polygon([(cx - width, 0), (cx + width, 0), (cx + width - 900, H), (cx - width - 900, H)], fill=col + (alpha,))
        f.alpha_composite(L.filter(ImageFilter.GaussianBlur(120)))
    return fn

def bg_brass():
    rng = np.random.default_rng(13)
    n = rng.normal(0, 1, (BH, BW // 8))
    n = np.asarray(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).resize((BW, BH), Image.BILINEAR)).astype(float) / 255
    y = np.linspace(0, 1, BH)[:, None]
    band = 0.55 + 0.45 * np.sin(y * 7 + 1.2) * np.sin(y * 2.3)
    v = np.clip(band * 0.8 + (n - 0.5) * 0.35, 0, 1)[..., None]
    lo, hi = np.array([126, 80, 18.]), np.array([255, 226, 150.])
    a = lo + (hi - lo) * v
    img = to_img(vignette(a, 0.45))
    L = layer(); d = ImageDraw.Draw(L)
    for k, (cx, cy) in enumerate([(130, 160), (BW - 130, 160), (130, BH - 160), (BW - 130, BH - 160)]):  # rivets
        d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(150, 104, 40, 255), outline=(255, 230, 160, 200), width=4)
    return comp(img, L)

def bg_carbon():
    a = vgrad([(0, (22, 24, 28)), (1, (8, 9, 11))])
    a = blend(a, (40, 60, 70), radial_mask(BW / 2, BH * 0.45, 900, power=1.3) * 0.6)
    img = to_img(a)
    L = layer(); d = ImageDraw.Draw(L)
    s = 70; hgt = s * math.sqrt(3)
    for row in range(-1, int(BH / hgt) + 2):
        for col in range(-1, int(BW / (s * 3)) + 2):
            for off in (0, 1):
                cx = col * s * 3 + off * s * 1.5; cy = row * hgt + off * hgt / 2
                pts = [(cx + s * math.cos(math.radians(60 * i)), cy + s * math.sin(math.radians(60 * i))) for i in range(6)]
                d.line(pts + [pts[0]], fill=(110, 200, 220, 70), width=3)
                for px, py in pts: d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(150, 230, 245, 120))
    img = comp(img, L)
    img = comp(img, L.filter(ImageFilter.GaussianBlur(8)))
    return grain(img, 6, 15)

def ov_pulse(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(12):
        x = (k * 263) % W; y = (k * 491) % H
        a = int(140 * max(0, math.sin(t * 2.2 + k * 1.7)))
        d.ellipse([x - 40, y - 40, x + 40, y + 40], fill=(140, 230, 250, a))
    f.alpha_composite(L.filter(ImageFilter.GaussianBlur(18)))

def bg_dusk():
    a = vgrad([(0, (36, 30, 84)), (0.35, (120, 60, 120)), (0.6, (236, 110, 80)), (0.78, (250, 180, 90)), (1, (60, 30, 40))])
    a = blend(a, (255, 220, 150), radial_mask(BW / 2, BH * 0.74, 650, power=1.5) * 0.85)
    img = to_img(a)
    L = layer(); d = ImageDraw.Draw(L)
    d.ellipse([BW / 2 - 150, BH * 0.74 - 150, BW / 2 + 150, BH * 0.74 + 150], fill=(255, 236, 190, 255))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(6)))
    L = layer(); d = ImageDraw.Draw(L)
    pts = [(x, BH * 0.8 - 40 * math.sin(x / 220) - 20 * math.sin(x / 70)) for x in range(0, BW + 20, 20)]
    d.polygon(pts + [(BW, BH), (0, BH)], fill=(40, 20, 34, 255))
    # city silhouettes
    r = random.Random(17); x = 0
    while x < BW:
        bw = r.randint(40, 110); bh = r.randint(40, 200)
        d.rectangle([x, BH * 0.84 - bh, x + bw, BH], fill=(26, 12, 24, 255)); x += bw + r.randint(0, 20)
    img = comp(img, L)
    return grain(img, 5, 17)

def ov_birds(f, t):
    d = ImageDraw.Draw(f)
    for k in range(5):
        x = (200 + k * 110 + t * 60) % (W + 200) - 100; y = 520 + k * 40 + 20 * math.sin(t * 2 + k)
        fl = 14 * math.sin(t * 9 + k)
        d.line([(x - 26, y - fl), (x, y), (x + 26, y - fl)], fill=(30, 16, 30), width=5, joint='curve')

def bg_flutter():
    a = vgrad([(0, (255, 214, 220)), (0.5, (255, 184, 196)), (1, (250, 160, 170))])
    a = blend(a, (255, 240, 220), radial_mask(BW * 0.3, BH * 0.25, 900, power=1.3) * 0.7)
    img = to_img(a)
    L = layer(); d = ImageDraw.Draw(L); r = random.Random(19)
    for _ in range(30):
        x, y, rr = r.uniform(0, BW), r.uniform(0, BH), r.uniform(40, 150)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, r.randint(30, 80)))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(10)))
    return grain(img, 4, 19)

def heart(d, x, y, s, fill):
    pts = []
    for i in range(40):
        tt = i / 40 * 2 * math.pi
        hx = 16 * math.sin(tt) ** 3; hy = -(13 * math.cos(tt) - 5 * math.cos(2 * tt) - 2 * math.cos(3 * tt) - math.cos(4 * tt))
        pts.append((x + hx * s / 16, y + hy * s / 16))
    d.polygon(pts, fill=fill)

def ov_hearts(f, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(16):
        ph = (t * 0.18 + k * 0.0625) % 1
        x = (k * 151) % W + 30 * math.sin(t * 1.3 + k); y = H + 60 - ph * (H + 120)
        s = 18 + (k % 4) * 10
        heart(d, x, y, s, (255, 255, 255, int(210 * math.sin(math.pi * ph))) if k % 3 else (235, 80, 110, int(200 * math.sin(math.pi * ph))))
    f.alpha_composite(L)

def bg_arnak_photo():
    crops = [('base.jpg', (100, 235, 730, 515)), ('missing.jpg', (0, 415, 656, 706)),
             ('leaders.png', (0, 360, 656, 651)), ('plane.jpg', (0, 330, 1094, 816))]
    gap = 8; rh = (BH - gap * 3) // 4
    m = Image.new('RGB', (BW, BH), (18, 12, 8))
    for i, (fn, b) in enumerate(crops):
        im = Image.open('arnak/' + fn).convert('RGB').crop(b).resize((BW, rh), Image.LANCZOS)
        m.paste(im, (0, i * (rh + gap)))
    return m

def photo_bg(fn, box):
    im = Image.open('photos/' + fn).convert('RGB').crop(box)
    return im.resize((BW, BH), Image.LANCZOS)

def bg_jjamppong_photo(): return photo_bg('jjamppong.jpg', (70, 0, 1133, 1890))
def bg_americano_photo(): return photo_bg('americano.jpg', (70, 0, 970, 1600))
def bg_autumn_photo(): return photo_bg('autumn.jpg', (200, 0, 910, 1262))
def bg_study_photo():
    gap = 8; rh = (BH - gap) // 2
    m = Image.new('RGB', (BW, BH), (18, 12, 8))
    for i, (fn, b) in enumerate([('study_a.jpg', (150, 0, 1050, 800)), ('study_b.jpg', (60, 0, 960, 800))]):
        m.paste(Image.open('photos/' + fn).convert('RGB').crop(b).resize((BW, rh), Image.LANCZOS), (0, i * (rh + gap)))
    return m

def bg_velvet_photo(): return photo_bg('velvet.jpg', (375, 0, 825, 800))
def bg_dusk_photo(): return photo_bg('sunset.jpg', (94, 0, 1106, 1800))
def bg_flutter_photo():
    gap = 8; rh = (BH - gap) // 2
    m = Image.new('RGB', (BW, BH), (250, 230, 232))
    for i, (fn, b) in enumerate([('blossom.jpg', (0, 330, 1200, 1397)), ('hydrangea.jpg', (150, 0, 1050, 800))]):
        m.paste(Image.open('photos/' + fn).convert('RGB').crop(b).resize((BW, rh), Image.LANCZOS), (0, i * (rh + gap)))
    return m

CARDS = [
    dict(q='음식이라면?', a='짬뽕', en='Jjamppong', bg=bg_jjamppong_photo, ov=ov_steam, theme='dark', cy=700),
    dict(q='음료라면?', a='아이스 아메리카노', en='Iced Americano', bg=bg_americano_photo, ov=ov_dust((255, 255, 255)), theme='dark', cy=600),
    dict(q='보드게임이라면?', a='아르낙', en='Lost Ruins of Arnak', bg=bg_arnak_photo, ov=ov_dust((240, 200, 110)), theme='dark', panel=True),
    dict(q='날씨라면?', a='초가을의\n맑은 날', en='A clear day in early autumn', bg=bg_autumn_photo, ov=ov_leaves, theme='dark', cy=700),
    dict(q='집이라면?', a='서재', en='A study', bg=bg_study_photo, ov=ov_dust((255, 220, 160)), theme='dark', panel=True),
    dict(q='질감이라면?', a='벨벳', en='Velvet', bg=bg_velvet_photo, ov=ov_sweep((255, 160, 200), alpha=40), theme='dark'),
    dict(q='소재라면?', a='황동', en='Brass', bg=bg_brass, ov=ov_sweep((255, 250, 220), width=260, alpha=110, speed=0.55), theme='brass'),
    dict(q='원소라면?', a='탄소', en='Carbon · C', bg=bg_carbon, ov=ov_pulse, theme='dark'),
    dict(q='순간이라면?', a='해 질 무렵', en='Dusk', bg=bg_dusk_photo, ov=ov_dust((255, 220, 170)), theme='dark', cy=600),
    dict(q='분위기라면?', a='설렘', en='Flutter', bg=bg_flutter_photo, ov=ov_hearts, theme='light', panel=True),
]

# ---------- text ----------
def text_el(txt, font, fill, spacing=14, shadow=None, stroke=0, stroke_fill=None):
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    b = [int(math.ceil(v)) for v in tmp.multiline_textbbox((0, 0), txt, font=font, spacing=spacing, align='center', stroke_width=stroke)]
    pad = 60
    im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0))
    org = (pad - b[0], pad - b[1])
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).multiline_text(org, txt, font=font, fill=shadow, spacing=spacing, align='center', stroke_width=stroke + 4, stroke_fill=shadow)
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).multiline_text(org, txt, font=font, fill=fill, spacing=spacing, align='center', stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def fit_font(txt, maker, size, maxw):
    while size > 40:
        f = maker(size)
        b = ImageDraw.Draw(Image.new('L', (1, 1))).multiline_textbbox((0, 0), txt, font=f, spacing=14, align='center')
        if b[2] - b[0] <= maxw: return f
        size -= 6
    return maker(size)

def palette(theme):
    if theme == 'light': return dict(q=(70, 40, 50), a=(40, 20, 30), en=(90, 60, 70), sh=(255, 255, 255, 200), scrim=(255, 255, 255))
    if theme == 'brass': return dict(q=(60, 36, 8), a=(40, 22, 4), en=(70, 44, 12), sh=(255, 240, 200, 210), scrim=(255, 240, 200))
    return dict(q=(255, 240, 225), a=(255, 255, 255), en=(255, 228, 200), sh=(0, 0, 0, 200), scrim=(0, 0, 0))

def put(f, el, cy, p, rise=50, scale_from=None):
    if p <= 0: return
    im = el
    if scale_from and p < 1:
        s = scale_from + (1 - scale_from) * p
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if p < 1:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
    f.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy - im.height / 2 + (1 - p) * rise)))

def scrim_img(col, strength, cy=960):
    m = np.zeros((H, W))
    y = np.linspace(0, 1, H)[:, None]
    band = np.exp(-((y - cy / H) / 0.17) ** 2)
    m = (band * np.ones((1, W))) * strength
    a = np.zeros((H, W, 4), np.uint8); a[..., :3] = col; a[..., 3] = (m * 255).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')

# ---------- scenes ----------
CARD_DUR = 2.5
EP = 'EP.1'
COVER_Q = ''
END_IDX = 8
def card_scene(i, c):
    base = c['bg']()
    pal = palette(c['theme'])
    scr = scrim_img(pal['scrim'], {'dark': 0.42, 'light': 0.5, 'brass': 0.22}[c['theme']] + (0.12 if 'cy' in c else 0), c.get('cy', 960))
    lab = text_el(f'ME IN ONE WORD  ·  {i + 1:02d} / 10', nunito(800, 34), pal['q'] + (230,), shadow=pal['sh'])
    q = text_el(c['q'], jua(70), pal['q'], shadow=pal['sh'])
    af = fit_font(c['a'], lambda s: jua(s), 200, 920)
    a = text_el(c['a'], af, pal['a'], spacing=26, shadow=pal['sh'])
    en = text_el(c['en'], nunito(700, 54, True), pal['en'], shadow=pal['sh'])
    lines = c['a'].count('\n') + 1
    cy_a = c.get('cy', 960 if lines == 1 else 990)
    def draw(t):
        z = 1.0 + 0.05 * (t / CARD_DUR)
        cw, ch = int(W * 1.1 / z), int(H * 1.1 / z)
        x0, y0 = (BW - cw) // 2, (BH - ch) // 2
        f = base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert('RGBA')
        c['ov'](f, t + i * 3)
        f.alpha_composite(scr)
        if c.get('panel'):
            pn = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(pn).rounded_rectangle([70, cy_a - 350, W - 70, cy_a + 270], radius=50, fill=(255, 246, 246, 190) if c['theme'] == 'light' else (12, 10, 8, 165))
            f.alpha_composite(pn)
        put(f, lab, cy_a - a.height / 2 - 150, ease((t - 0.05) / 0.4), rise=20)
        put(f, q, cy_a - a.height / 2 - 10, ease((t - 0.1) / 0.45))
        put(f, a, cy_a + 20, ease((t - 0.35) / 0.5), rise=30, scale_from=0.9)
        put(f, en, cy_a + a.height / 2 + 40, ease((t - 0.7) / 0.5), rise=20)
        return f.convert('RGB')
    return draw, base

def cover_scene(bases, dur=2.8, for_still=False):
    # mosaic of the ten backgrounds
    tw, th = W // 2, H // 5
    mos = Image.new('RGB', (W, H))
    for k, b in enumerate(bases):
        tile = b.resize((tw, int(tw * BH / BW)), Image.BILINEAR)
        tile = tile.crop((0, (tile.height - th) // 2, tw, (tile.height - th) // 2 + th))
        mos.paste(tile, ((k % 2) * tw, (k // 2) * th))
    mos = mos.filter(ImageFilter.GaussianBlur(3))
    dark = Image.new('RGB', (W, H), (12, 10, 16))
    base = Image.blend(mos, dark, 0.5).convert('RGBA')
    d = ImageDraw.Draw(base)
    gold = (240, 204, 130)
    ep = text_el('EP.1', inter('Bold', 46), (20, 16, 10))
    pill = Image.new('RGBA', (ep.width - 40, ep.height - 70), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], radius=pill.height // 2, fill=gold + (255,))
    pill.alpha_composite(ep, (-20, -35))
    t1 = text_el('Me', free('BoldItalic', 210), (255, 255, 255), shadow=(0, 0, 0, 220))
    t2 = text_el('in one word', free('BoldItalic', 150), (255, 255, 255), shadow=(0, 0, 0, 220))
    t3 = text_el('by GPT', free('Italic', 78), gold, shadow=(0, 0, 0, 220))
    t4 = text_el('GPT가 본 나를 한 단어로', sans('Medium', 54), (255, 240, 225), shadow=(0, 0, 0, 220))
    t5 = text_el('음식 · 음료 · 보드게임 · 날씨 · 집\n질감 · 소재 · 원소 · 순간 · 분위기', sans('Regular', 40), (230, 220, 210), spacing=18, shadow=(0, 0, 0, 220))
    def draw(t):
        f = base.copy()
        put(f, pill, 560, ease((t - 0.05) / 0.4), rise=20)
        put(f, t1, 720, ease((t - 0.1) / 0.5))
        put(f, t2, 880, ease((t - 0.25) / 0.5))
        put(f, t3, 1010, ease((t - 0.45) / 0.5))
        # underline
        p = ease((t - 0.6) / 0.6)
        if p > 0: ImageDraw.Draw(f).rounded_rectangle([W / 2 - 300, 1085, W / 2 - 300 + 600 * p, 1093], radius=4, fill=gold + (255,))
        put(f, t4, 1170, ease((t - 0.75) / 0.5))
        put(f, t5, 1330, ease((t - 0.95) / 0.5))
        return f.convert('RGB')
    return draw

def end_scene(bases):
    base = bases[END_IDX].resize((W, H)).filter(ImageFilter.GaussianBlur(18))
    base = Image.blend(base, Image.new('RGB', (W, H), (20, 12, 18)), 0.45).convert('RGBA')
    t1 = text_el('당신을 한 단어로\n표현한다면?', jua(112), (255, 255, 255), spacing=22, shadow=(0, 0, 0, 220))
    t2 = text_el('댓글로 알려주세요', jua(58), (255, 228, 210), shadow=(0, 0, 0, 220))
    t3 = text_el('Me in one word by GPT · ' + EP, nunito(700, 46, True), (240, 204, 130), shadow=(0, 0, 0, 220))
    def draw(t):
        f = base.copy()
        ov_hearts(f, t)
        put(f, t1, 860, ease((t - 0.1) / 0.5))
        put(f, t2, 1080, ease((t - 0.5) / 0.5))
        put(f, t3, 1200, ease((t - 0.8) / 0.5))
        return f.convert('RGB')
    return draw

def render(name, dur, draw, fin=0.0, fout=0.0, flash=None):
    tmp = f'{name}.tmp.mp4'
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                           '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    n = int(round(dur * FPS))
    for k in range(n):
        t = k / FPS
        fr = draw(t)
        a = 1.0
        if fin: a = min(a, t / fin)
        if fout: a = min(a, (dur - t) / fout)
        if a < 1: fr = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), fr, max(0, a))
        if t < 0.18:  # quick wipe-in from black for card cuts
            pass
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    if pr.wait() != 0: sys.exit(1)
    os.replace(tmp, f'{name}.mp4')

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    scenes = [card_scene(i, c) for i, c in enumerate(CARDS)]
    bases = [b for _, b in scenes]
    cover = cover_scene(bases)
    end = end_scene(bases)
    cover(2.6).save('cover_ep1.png'); cover(2.6).save('cover_ep1.jpg', quality=93)
    if mode == 'preview':
        frames = [cover(2.6)] + [d(2.3) for d, _ in scenes] + [end(2.5)]
        m = Image.new('RGB', (240 * 6, 427 * 2))
        for k, fr in enumerate(frames): m.paste(fr.resize((240, 427)), ((k % 6) * 240, (k // 6) * 427))
        m.save('sheet.png')
        for k in (1, 4, 7): frames[k].save(f'full_{k}.png')
        sys.exit(0)
    names = []
    render('c00', 2.8, cover, fin=0.2); names.append('c00')
    for i, (d, _) in enumerate(scenes):
        render(f'c{i + 1:02d}', CARD_DUR, d); names.append(f'c{i + 1:02d}')
    render('c11', 3.0, end, fout=0.6); names.append('c11')
    with open('list.txt', 'w') as fh:
        for nm in names: fh.write(f"file '{nm}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', 'me_in_one_word_ep1.mp4'], check=True)
    print('done')

# ---------- photo cover (user-supplied background) ----------
def photo_cover(path='cover_bg.png'):
    src = Image.open(path).convert('RGB')
    big = src.resize((BW, int(src.height * BW / src.width)), Image.LANCZOS)
    if big.height < BH: big = src.resize((int(src.width * BH / src.height), BH), Image.LANCZOS)
    x0, y0 = (big.width - BW) // 2, (big.height - BH) // 2
    base = big.crop((x0, y0, x0 + BW, y0 + BH))
    PX0, PY0, PX1, PY1 = 90, 520, 990, 1440
    wine, tomato = (96, 18, 30), (226, 58, 40)
    ep = text_el(EP, nunito(800, 46), (255, 255, 255))
    pill = Image.new('RGBA', (ep.width - 40, ep.height - 70), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], radius=pill.height // 2, fill=tomato + (255,))
    pill.alpha_composite(ep, (-20, -35))
    t1 = text_el('Me', nunito(800, 200), wine)
    t2 = text_el('in one word', nunito(800, 132), wine)
    t3 = text_el('by GPT', nunito(700, 76, True), tomato)
    t4 = text_el('GPT가 본 나를 한 단어로', jua(60), (60, 30, 36))
    t5 = text_el(COVER_Q, dodum(42), (90, 60, 66), spacing=18)
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([PX0, PY0, PX1, PY1], radius=60, fill=255)
    def draw(t):
        z = 1.0 + 0.04 * (t / 2.8)
        cw, ch = int(W * 1.1 / z), int(H * 1.1 / z)
        bx, by = (BW - cw) // 2, (BH - ch) // 2
        f = base.crop((bx, by, bx + cw, by + ch)).resize((W, H), Image.BILINEAR)
        p = ease((t - 0.05) / 0.5)
        if p > 0:
            glass = f.filter(ImageFilter.GaussianBlur(28))
            glass = Image.blend(glass, Image.new('RGB', (W, H), (255, 250, 248)), 0.55)
            f.paste(glass, (0, 0), mask.point(lambda v: int(v * p)))
            ImageDraw.Draw(f).rounded_rectangle([PX0, PY0, PX1, PY1], radius=60, outline=(255, 255, 255), width=int(4 * p) or 1)
        f = f.convert('RGBA')
        put(f, pill, 610, ease((t - 0.15) / 0.4), rise=20)
        put(f, t1, 760, ease((t - 0.2) / 0.5))
        put(f, t2, 920, ease((t - 0.35) / 0.5))
        put(f, t3, 1050, ease((t - 0.5) / 0.5))
        q = ease((t - 0.65) / 0.6)
        if q > 0: ImageDraw.Draw(f).rounded_rectangle([W / 2 - 280, 1125, W / 2 - 280 + 560 * q, 1132], radius=4, fill=tomato + (255,))
        put(f, t4, 1205, ease((t - 0.8) / 0.5))
        put(f, t5, 1335, ease((t - 1.0) / 0.5))
        return f.convert('RGB')
    return draw

if __name__ == '__main__' and False:
    pass
