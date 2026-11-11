import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {'__name__': 'base', '__file__': os.path.join(HERE, 'base.py')}
exec(compile(open(os.path.join(HERE, 'base.py')).read(), 'base', 'exec'), ns)
os.chdir(HERE)
g = ns
W, H, BW, BH = g['W'], g['H'], g['BW'], g['BH']
jua, dodum, nunito = g['jua'], g['dodum'], g['nunito']
vgrad, to_img, blend, radial_mask, grain = g['vgrad'], g['to_img'], g['blend'], g['radial_mask'], g['grain']

g['EP'] = 'SPIN-OFF'
g['BYLINE'] = 'by Claude'
g['AI_KO'] = 'Claude가'
g['COVER_Q_SIZE'] = 36
g['COVER_Q'] = '문장부호 · 시간대 · 키보드 키 · 파일명\n게임 캐릭터 · 지하철역 · 주방 도구\n앱 알림 · 보드게임 행동 · 드라마'
g['END_IDX'] = 1

OX, OY = (BW - W) // 2, (BH - H) // 2
def P(x, y): return (x + OX, y + OY)
def R(x0, y0, x1, y1): return [x0 + OX, y0 + OY, x1 + OX, y1 + OY]
def lay(): return Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
def comp(img, L): img = img.convert('RGBA'); img.alpha_composite(L); return img.convert('RGB')
def olay(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))

# ---------- 1. 물음표 ----------
def bg_question():
    a = vgrad([(0, (30, 26, 80)), (1, (12, 10, 36))])
    a = blend(a, (90, 80, 200), radial_mask(BW / 2, BH * 0.5, 800, power=1.6) * 0.5)
    img = to_img(a)
    L = lay(); d = ImageDraw.Draw(L)
    d.text(P(540, 1250), '?', font=nunito(800, 1100), fill=(140, 130, 255, 55), anchor='mm')
    return comp(img, L.filter(ImageFilter.GaussianBlur(2)))
def ov_question(f, t):
    L = olay(); d = ImageDraw.Draw(L)
    for k in range(16):
        ph = (t * 0.14 + k * 0.0625) % 1
        x = (k * 173) % W + 30 * math.sin(t + k); y = H + 80 - ph * (H + 160)
        d.text((x, y), '?', font=jua(40 + (k % 4) * 22), fill=(200, 195, 255, int(150 * math.sin(math.pi * ph))), anchor='mm')
    f.alpha_composite(L)

# ---------- 2. 새벽 두 시 ----------
STARS = [(random.Random(i).uniform(0, W), random.Random(i + 99).uniform(0, 1100), random.Random(i + 7).uniform(1.5, 4)) for i in range(90)]
def bg_night():
    a = vgrad([(0, (8, 10, 34)), (0.6, (34, 28, 80)), (1, (60, 40, 90))])
    img = to_img(a)
    L = lay(); d = ImageDraw.Draw(L)
    cx, cy = P(840, 330)
    d.ellipse([cx - 110, cy - 110, cx + 110, cy + 110], fill=(255, 244, 200, 255))
    d.ellipse([cx - 60, cy - 140, cx + 160, cy + 80], fill=(0, 0, 0, 0))
    img = comp(img, L)
    m = Image.new('L', (BW, BH), 0); ImageDraw.Draw(m).ellipse([cx - 60, cy - 140, cx + 160, cy + 80], fill=255)
    img.paste(to_img(vgrad([(0, (8, 10, 34)), (0.6, (34, 28, 80)), (1, (60, 40, 90))])), (0, 0), m)
    glow = lay(); ImageDraw.Draw(glow).ellipse([cx - 200, cy - 200, cx + 200, cy + 200], fill=(255, 240, 200, 50))
    img = comp(img, glow.filter(ImageFilter.GaussianBlur(60)))
    L = lay(); d = ImageDraw.Draw(L); r = random.Random(3); x = 0
    while x < BW:
        bw = r.randint(90, 180); bh = r.randint(300, 650)
        d.rectangle([x, BH - bh, x + bw, BH], fill=(14, 12, 30, 255))
        for wy in range(BH - bh + 30, BH - 20, 56):
            for wx in range(x + 18, x + bw - 20, 40):
                if r.random() < 0.1: d.rectangle([wx, wy, wx + 18, wy + 26], fill=(255, 210, 120, 220))
        x += bw + r.randint(4, 14)
    lx, ly = P(560, 1640)
    d.rectangle([lx, ly, lx + 26, ly + 34], fill=(255, 226, 150, 255))
    img = comp(img, L)
    L = lay(); ImageDraw.Draw(L).text(P(540, 1330), 'AM 2:00', font=nunito(800, 150), fill=(170, 160, 255, 70), anchor='mm')
    return comp(img, L)
def ov_night(f, t):
    d = ImageDraw.Draw(f)
    for i, (x, y, s) in enumerate(STARS):
        a = int(140 + 115 * math.sin(t * 2.5 + i * 1.3))
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 240, max(0, a)))

# ---------- 3. Enter ----------
def key(d, x0, y0, x1, y1, label='', col=(250, 250, 252), txt=(120, 120, 130), font=None, depth=14):
    d.rounded_rectangle([x0, y0 + depth, x1, y1 + depth], radius=22, fill=tuple(int(c * 0.78) for c in col) + (255,))
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=col + (255,), outline=(210, 210, 216, 255), width=2)
    if label: d.text(((x0 + x1) / 2, (y0 + y1) / 2), label, font=font or nunito(700, 40), fill=txt, anchor='mm')
def bg_enter():
    img = to_img(vgrad([(0, (246, 240, 236)), (1, (226, 220, 220))]))
    L = lay(); d = ImageDraw.Draw(L)
    d.rounded_rectangle(R(-40, 1100, 1120, 2100), radius=50, fill=(206, 200, 204, 255))
    rows = [['Q', 'W', 'E', 'R', 'T', 'Y'], ['A', 'S', 'D', 'F', 'G', 'H'], ['Z', 'X', 'C', 'V', 'B', 'N']]
    for ri, row in enumerate(rows):
        for ci, k in enumerate(row):
            x0, y0 = P(-60 + ri * 40 + ci * 132, 1160 + ri * 150)
            key(d, x0, y0, x0 + 118, y0 + 118, k)
    return comp(img, L)
def ov_enter(f, t):
    L = olay(); d = ImageDraw.Draw(L)
    ph = (t % 1.25) / 1.25
    press = 12 if 0.55 < ph < 0.7 else 0
    x0, y0 = 760, 1150 + press
    d.rounded_rectangle([x0, 1164 + 14, x0 + 300, 1580 + 14], radius=26, fill=(170, 40, 30, 255))
    d.rounded_rectangle([x0, y0, x0 + 300, y0 + 416], radius=26, fill=(230, 64, 48, 255))
    d.text((x0 + 150, y0 + 170), 'Enter', font=nunito(800, 64), fill=(255, 255, 255), anchor='mm')
    ax, ay = x0 + 190, y0 + 250
    d.line([(ax, ay - 40), (ax, ay), (ax - 80, ay)], fill=(255, 230, 220), width=10, joint='curve')
    d.polygon([(ax - 100, ay), (ax - 70, ay - 22), (ax - 70, ay + 22)], fill=(255, 230, 220))
    if press:
        for k in range(6):
            an = math.radians(-160 + k * 28)
            d.line([(x0 + 150 + 230 * math.cos(an), y0 + 200 + 230 * math.sin(an)),
                    (x0 + 150 + 290 * math.cos(an), y0 + 200 + 290 * math.sin(an))], fill=(230, 64, 48, 255), width=8)
    f.alpha_composite(L)

# ---------- 4. 파일명 ----------
FILES = ['기획서_최종.pptx', '기획서_최종_수정.pptx', '기획서_진짜최종.pptx', '기획서_진짜최종_찐.pptx', '최종_진짜최종_v3.pptx']
def bg_files():
    a = vgrad([(0, (226, 236, 250)), (1, (196, 212, 240))])
    img = to_img(a)
    L = lay(); d = ImageDraw.Draw(L)
    d.rounded_rectangle(R(80, 1000, 1000, 1800), radius=34, fill=(255, 255, 255, 245), outline=(180, 196, 226, 255), width=3)
    d.rounded_rectangle(R(80, 1000, 1000, 1080), radius=34, fill=(236, 240, 248, 255))
    d.rectangle(R(80, 1050, 1000, 1080), fill=(236, 240, 248, 255))
    for k, c in enumerate([(255, 96, 86), (255, 190, 46), (40, 200, 64)]):
        x, y = P(130 + k * 46, 1040); d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=c + (255,))
    return comp(img, L)
def ov_files(f, t):
    L = olay(); d = ImageDraw.Draw(L)
    for i, name in enumerate(FILES):
        p = g['ease']((t - 0.3 - i * 0.22) / 0.35)
        if p <= 0: continue
        y = 1130 + i * 128
        last = i == len(FILES) - 1
        if last: d.rounded_rectangle([110, y - 10, 970, y + 100], radius=18, fill=(214, 228, 255, int(255 * p)))
        x = 140
        d.polygon([(x, y), (x + 54, y), (x + 74, y + 20), (x + 74, y + 90), (x, y + 90)], fill=(232, 110, 60, int(255 * p)))
        d.text((x + 37, y + 58), 'P', font=nunito(800, 34), fill=(255, 255, 255, int(255 * p)), anchor='mm')
        d.text((x + 110, y + 45), name, font=(jua(48) if last else dodum(42)), fill=((30, 50, 110) if last else (90, 96, 110)) + (int(255 * p),), anchor='lm')
    f.alpha_composite(L)

# ---------- 5. 멀티클래스 ----------
CLASSES = [('기획자', 'Lv.15', 0.92, (110, 150, 255)), ('알바생', 'Lv.1', 0.35, (255, 160, 80)), ('크리에이터', 'Lv.3', 0.55, (240, 90, 150))]
def icon(d, kind, cx, cy, col):
    if kind == 0:  # clipboard
        d.rounded_rectangle([cx - 50, cy - 62, cx + 50, cy + 66], radius=10, fill=(255, 255, 255, 255))
        d.rounded_rectangle([cx - 24, cy - 76, cx + 24, cy - 52], radius=8, fill=col + (255,))
        for k in range(3): d.line([(cx - 32, cy - 22 + k * 30), (cx + 32, cy - 22 + k * 30)], fill=(150, 150, 170, 255), width=7)
    elif kind == 1:  # apron
        d.polygon([(cx - 34, cy - 70), (cx + 34, cy - 70), (cx + 34, cy - 30), (cx + 58, cy - 20), (cx + 48, cy + 74), (cx - 48, cy + 74), (cx - 58, cy - 20), (cx - 34, cy - 30)], fill=(255, 255, 255, 255))
        d.rounded_rectangle([cx - 26, cy + 4, cx + 26, cy + 40], radius=6, fill=col + (255,))
    else:  # camera / phone
        d.rounded_rectangle([cx - 62, cy - 42, cx + 62, cy + 56], radius=16, fill=(255, 255, 255, 255))
        d.rounded_rectangle([cx - 26, cy - 60, cx + 26, cy - 38], radius=6, fill=(255, 255, 255, 255))
        d.ellipse([cx - 30, cy - 22, cx + 30, cy + 38], fill=col + (255,))
        d.ellipse([cx - 14, cy - 6, cx + 14, cy + 22], fill=(255, 255, 255, 255))
def bg_multi():
    a = vgrad([(0, (20, 22, 40)), (1, (10, 10, 22))])
    img = to_img(a)
    L = lay(); d = ImageDraw.Draw(L)
    for x in range(0, BW, 60): d.line([(x, 0), (x, BH)], fill=(60, 70, 120, 40), width=2)
    for y in range(0, BH, 60): d.line([(0, y), (BW, y)], fill=(60, 70, 120, 40), width=2)
    for i, (name, lv, _, col) in enumerate(CLASSES):
        x0 = 60 + i * 330; y0 = 1060
        d.rounded_rectangle(R(x0, y0, x0 + 300, y0 + 560), radius=30, fill=(30, 34, 64, 240), outline=col + (255,), width=5)
        icon(d, i, *P(x0 + 150, y0 + 150), col)
        d.text(P(x0 + 150, y0 + 300), name, font=jua(50), fill=(255, 255, 255), anchor='mm')
        d.text(P(x0 + 150, y0 + 370), lv, font=nunito(800, 44), fill=col, anchor='mm')
        d.rounded_rectangle(R(x0 + 36, y0 + 440, x0 + 264, y0 + 466), radius=13, fill=(60, 64, 100, 255))
    return comp(img, L)
def ov_multi(f, t):
    d = ImageDraw.Draw(f)
    for i, (_, _, xp, col) in enumerate(CLASSES):
        x0 = 60 + i * 330; y0 = 1060
        p = g['ease']((t - 0.4) / 1.4) * xp
        if p > 0.02: d.rounded_rectangle([x0 + 36, y0 + 440, x0 + 36 + 228 * p, y0 + 466], radius=13, fill=col + (255,))
        if t > 1.9 and i == 1:
            d.text((x0 + 150, y0 + 520), 'LEVEL UP!', font=nunito(800, 34), fill=(255, 220, 90), anchor='mm')

# ---------- 6. 환승역 ----------
def bg_subway():
    img = to_img(vgrad([(0, (250, 250, 247)), (1, (238, 238, 232))]))
    L = lay(); d = ImageDraw.Draw(L)
    for x in range(0, BW, 70): d.line([(x, 0), (x, BH)], fill=(225, 225, 220, 255), width=1)
    for y in range(0, BH, 70): d.line([(0, y), (BW, y)], fill=(225, 225, 220, 255), width=1)
    lines = [((60, 170, 80), [(-80, 1500), (540, 1500), (1160, 1500)]),
             ((150, 80, 200), [(540, 2080), (540, 1500), (760, 1180), (1160, 1180)]),
             ((240, 140, 40), [(-80, 1120), (300, 1120), (540, 1500), (760, 1900), (1160, 1900)])]
    for col, pts in lines:
        d.line([P(*p) for p in pts], fill=col + (255,), width=34, joint='curve')
    for col, pts in lines:
        for p in pts[1:-1]:
            if p != (540, 1500):
                x, y = P(*p); d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(255, 255, 255, 255), outline=col + (255,), width=8)
    x, y = P(540, 1500)
    d.ellipse([x - 52, y - 52, x + 52, y + 52], fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=12)
    d.rounded_rectangle([x + 70, y - 110, x + 330, y - 40], radius=14, fill=(30, 30, 30, 255))
    d.text((x + 200, y - 75), '환승역', font=jua(44), fill=(255, 255, 255), anchor='mm')
    return comp(img, L)
def ov_subway(f, t):
    L = olay(); d = ImageDraw.Draw(L)
    for k in range(2):
        ph = ((t * 0.7) + k * 0.5) % 1
        r = 60 + ph * 140
        d.ellipse([540 - r, 1500 - r, 540 + r, 1500 + r], outline=(30, 30, 30, int(160 * (1 - ph))), width=6)
    x = -80 + ((t * 0.35) % 1) * 1240
    d.rounded_rectangle([x - 50, 1478, x + 50, 1522], radius=18, fill=(40, 120, 60, 255))
    f.alpha_composite(L)

# ---------- 7. 체 ----------
def bg_sieve():
    img = to_img(vgrad([(0, (246, 236, 220)), (1, (226, 210, 188))]))
    L = lay(); d = ImageDraw.Draw(L)
    cx, cy = P(540, 1380); r = 360
    d.rounded_rectangle([cx + r - 20, cy - 40, cx + r + 360, cy + 40], radius=40, fill=(150, 104, 60, 255))
    d.ellipse([cx - r - 34, cy - r - 34, cx + r + 34, cy + r + 34], fill=(190, 196, 204, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 110, 100, 255))
    mesh = Image.new('RGBA', (BW, BH), (0, 0, 0, 0)); md = ImageDraw.Draw(mesh)
    for k in range(-r, r, 18):
        md.line([(cx + k, cy - r), (cx + k, cy + r)], fill=(225, 228, 232, 255), width=4)
        md.line([(cx - r, cy + k), (cx + r, cy + k)], fill=(225, 228, 232, 255), width=4)
    m = Image.new('L', (BW, BH), 0); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    L.paste(mesh, (0, 0), Image.fromarray(np.minimum(np.asarray(m), np.asarray(mesh.getchannel('A')))))
    rr = random.Random(5)
    for _ in range(18):  # little gems kept in sieve
        x, y = cx + rr.uniform(-250, 250), cy + rr.uniform(-250, 250)
        if (x - cx) ** 2 + (y - cy) ** 2 < 240 ** 2:
            s = rr.uniform(16, 28); d.ellipse([x - s, y - s, x + s, y + s], fill=rr.choice([(255, 200, 80), (250, 120, 110), (255, 240, 200)]) + (255,))
    d.ellipse([cx - r - 34, cy - r - 34, cx + r + 34, cy + r + 34], outline=(225, 230, 236, 255), width=10)
    return comp(img, L)
def ov_sieve(f, t):
    d = ImageDraw.Draw(f)
    for k in range(70):
        x = 240 + (k * 53) % 600; ph = (t * 0.6 + k * 0.137) % 1
        y = 1700 + ph * 300
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255))

# ---------- 8. 연속 기록 ----------
def bg_streak():
    a = vgrad([(0, (255, 170, 80)), (0.6, (236, 90, 50)), (1, (120, 30, 30))])
    img = to_img(a)
    L = lay(); d = ImageDraw.Draw(L)
    d.rounded_rectangle(R(90, 220, 990, 420), radius=40, fill=(255, 255, 255, 230))
    d.rounded_rectangle(R(130, 260, 250, 380), radius=26, fill=(250, 110, 50, 255))
    d.text(P(190, 320), '🔥' if False else 'S', font=nunito(800, 70), fill=(255, 255, 255), anchor='mm')
    d.text(P(280, 285), 'Speak · 지금', font=dodum(34), fill=(130, 120, 120), anchor='lm')
    d.text(P(280, 345), '222일 연속 학습 중이에요!', font=jua(46), fill=(40, 30, 30), anchor='lm')
    return comp(img, L)
def flame(d, cx, by, s, col):
    pts = []
    for i in range(60):
        u = i / 59 * 2 * math.pi
        x = math.sin(u) * (1 - 0.3 * math.cos(u))
        y = -math.cos(u) * 1.0 - 0.7 * (1 - abs(math.sin(u / 2))) ** 3
        pts.append((cx + x * s * 0.55, by - s * 0.6 + y * s * 0.75))
    d.polygon(pts, fill=col)
def ov_streak(f, t):
    L = olay(); d = ImageDraw.Draw(L)
    w = 1 + 0.04 * math.sin(t * 9) + 0.02 * math.sin(t * 17)
    flame(d, 540, 1840, 620 * w, (255, 120, 40, 255))
    flame(d, 540, 1840, 430 * w, (255, 190, 60, 255))
    flame(d, 540, 1840, 240 * w, (255, 240, 170, 255))
    d.text((540, 1650), '222', font=nunito(800, 130), fill=(160, 40, 20), anchor='mm')
    f.alpha_composite(L)

# ---------- 9. 탐험 ----------
PATH = [(170, 1820), (260, 1640), (420, 1600), (520, 1460), (420, 1300), (560, 1180), (760, 1220), (860, 1080)]
def bg_map():
    a = vgrad([(0, (240, 222, 180)), (1, (220, 196, 150))])
    a = blend(a, (190, 150, 100), (1 - radial_mask(BW / 2, BH / 2, 1300, power=1.0)) * 0.6)
    img = grain(to_img(a), 8, 21)
    L = lay(); d = ImageDraw.Draw(L)
    r = random.Random(4)
    for cx, cy, s in [(380, 1500, 380), (850, 1150, 220)]:
        pts = []
        for i in range(48):
            an = i / 48 * 2 * math.pi; rr = s * (1 + 0.18 * math.sin(an * 3 + cx) + r.uniform(-0.06, 0.06))
            pts.append(P(cx + rr * math.cos(an), cy + rr * 0.8 * math.sin(an)))
        d.polygon(pts, fill=(196, 210, 150, 255), outline=(120, 90, 50, 255))
        d.line(pts + [pts[0]], fill=(120, 90, 50, 255), width=5)
    for k in range(4):
        x, y = P(300 + k * 40, 1450 - (k % 2) * 30); d.polygon([(x, y - 40), (x - 30, y + 10), (x + 30, y + 10)], fill=(140, 120, 80, 255))
    cx, cy = P(880, 1720)
    d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], outline=(120, 90, 50, 255), width=5)
    d.polygon([(cx, cy - 130), (cx - 22, cy), (cx, cy + 130), (cx + 22, cy)], fill=(160, 60, 40, 255))
    d.polygon([(cx - 130, cy), (cx, cy - 22), (cx + 130, cy), (cx, cy + 22)], fill=(120, 90, 50, 255))
    d.text((cx, cy - 165), 'N', font=nunito(800, 40), fill=(120, 90, 50), anchor='mm')
    return comp(img, L)
def ov_map(f, t):
    d = ImageDraw.Draw(f)
    p = g['ease']((t - 0.2) / 1.8)
    pts = []
    for i in range(len(PATH) - 1):
        (x0, y0), (x1, y1) = PATH[i], PATH[i + 1]
        for k in range(12): pts.append((x0 + (x1 - x0) * k / 12, y0 + (y1 - y0) * k / 12))
    pts.append(PATH[-1])
    n = int(len(pts) * p)
    for i in range(0, n, 2): x, y = pts[i]; d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(150, 50, 40))
    if p > 0.98:
        x, y = PATH[-1]
        d.line([(x - 34, y - 34), (x + 34, y + 34)], fill=(200, 40, 30), width=14)
        d.line([(x - 34, y + 34), (x + 34, y - 34)], fill=(200, 40, 30), width=14)

# ---------- 10. 시즌 2 ----------
def bg_season():
    a = vgrad([(0, (16, 12, 20)), (1, (36, 20, 30))])
    img = to_img(a)
    L = lay(); d = ImageDraw.Draw(L)
    d.polygon([P(400, -100), P(680, -100), P(980, 1700), P(100, 1700)], fill=(255, 230, 180, 40))
    img = comp(img, L.filter(ImageFilter.GaussianBlur(40)))
    L = lay(); d = ImageDraw.Draw(L)
    d.ellipse(R(140, 1640, 940, 1780), fill=(255, 220, 160, 50))
    x0, y0 = P(270, 1180)
    d.rounded_rectangle([x0, y0 + 110, x0 + 540, y0 + 470], radius=16, fill=(30, 30, 34, 255))
    d.text((x0 + 270, y0 + 250), 'SEASON 2', font=nunito(800, 66), fill=(255, 215, 120), anchor='mm')
    d.text((x0 + 270, y0 + 360), 'EP.01  ·  TAKE 1', font=nunito(700, 34), fill=(220, 220, 220), anchor='mm')
    return comp(img, L)
def ov_season(f, t):
    L = olay(); d = ImageDraw.Draw(L)
    x0, y0 = 270, 1180
    ph = (t % 1.6) / 1.6
    ang = 18 if ph < 0.45 else max(0, 18 - (ph - 0.45) * 400)
    stick = Image.new('RGBA', (560, 140), (0, 0, 0, 0)); sd = ImageDraw.Draw(stick)
    sd.rounded_rectangle([0, 20, 540, 110], radius=10, fill=(30, 30, 34, 255))
    for k in range(6): sd.polygon([(20 + k * 90, 20), (70 + k * 90, 20), (40 + k * 90, 110), (-10 + k * 90, 110)], fill=(240, 240, 240, 255))
    stick = stick.rotate(ang, center=(0, 110), resample=Image.BICUBIC, expand=False)
    L.alpha_composite(stick, (x0, y0 - 10))
    d.rounded_rectangle([x0, y0 + 90, x0 + 540, y0 + 130], radius=8, fill=(30, 30, 34, 255))
    for k in range(6): d.polygon([(x0 + 20 + k * 90, y0 + 90), (x0 + 70 + k * 90, y0 + 90), (x0 + 40 + k * 90, y0 + 130), (x0 - 10 + k * 90, y0 + 130)], fill=(240, 240, 240, 255))
    f.alpha_composite(L)

def card(q, a, en, bg, ov, theme='dark', **kw):
    return dict(q=q, a=a, en=en, bg=bg, ov=ov, theme=theme, nozoom=True, **kw)

CARDS = [
    card('문장부호라면?', '물음표', '일단 "왜?"부터 묻는 사람', bg_question, ov_question, cy=900),
    card('시간대라면?', '새벽 두 시', '하루는 끝나도\n아이디어는 안 끝나는 시간', bg_night, ov_night, cy=720),
    card('키보드 키라면?', 'Enter', '고민보다 실행이 먼저', bg_enter, ov_enter, theme='light', cy=640),
    card('문서 파일명이라면?', '최종_진짜최종_v3', '끝까지 한 번 더 다듬는\n15년 차 기획자', bg_files, ov_files, theme='light', cy=620),
    card('게임 캐릭터라면?', '멀티클래스', '기획자·알바생·크리에이터\n동시 육성 중', bg_multi, ov_multi, cy=640),
    card('지하철역이라면?', '환승역', '멈춘 게 아니라 갈아타는 중', bg_subway, ov_subway, theme='light', cy=640),
    card('주방 도구라면?', '체', '섬세하게 걸러서\n좋은 것만 남기는 감각', bg_sieve, ov_sieve, theme='light', cy=600),
    card('앱 알림이라면?', '연속 기록 중', '하루도 안 빠진 222일', bg_streak, ov_streak, cy=820),
    card('보드게임 행동이라면?', '탐험', '익숙한 판보다\n새 지도를 펼치는 쪽', bg_map, ov_map, theme='light', cy=620),
    card('드라마라면?', '시즌 2', '2막이 더 재밌어지는 이야기', bg_season, ov_season, cy=680),
]

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    scenes = [g['card_scene'](i, c) for i, c in enumerate(CARDS)]
    cover = g['photo_cover']()
    cover(2.7).save('cover_claude_spinoff.jpg', quality=93)
    end = g['end_scene']([b for _, b in scenes])
    if mode == 'preview':
        frames = [cover(2.7)] + [d(2.3) for d, _ in scenes] + [end(2.5)]
        m = Image.new('RGB', (240 * 6, 427 * 2))
        for k, fr in enumerate(frames): m.paste(fr.resize((240, 427)), ((k % 6) * 240, (k // 6) * 427))
        m.save('sheet.png')
        for k in (3, 4, 8): frames[k + 1].resize((540, 960)).save(f'full{k}.png')
        sys.exit(0)
    R_ = g['render']; names = []
    R_('c00', 2.8, cover, fin=0.2); names.append('c00')
    for i, (d, _) in enumerate(scenes):
        R_(f'c{i + 1:02d}', 2.7, d); names.append(f'c{i + 1:02d}')
    R_('c11', 3.0, end, fout=0.6); names.append('c11')
    with open('list.txt', 'w') as fh:
        for nm in names: fh.write(f"file '{nm}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', 'me_in_one_word_by_claude_spinoff.mp4'], check=True)
    print('done')
