import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H, FPS = 1080, 1920, 30
S = 2                      # supersample
PW, PH = 960, 1250         # panel size (1x)
PX = 60                    # panel left in screen
GUT = 150
FD = '/usr/share/fonts/opentype/noto/'
def F(w, s):
    sz = int(s * 1.18)
    return ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts/gaegu.ttf'), sz)

INK = (34, 30, 28)
WHITE = (255, 255, 255)
PAPER = (246, 243, 236)
YEL = (247, 202, 72)
PINK = (255, 196, 196)
GREY = (200, 196, 190)
MOLD = (150, 160, 132)
BLUE = (160, 205, 240)
LW = 6                      # base line width (1x)

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def inout(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def back(t):
    t = max(0.0, min(1.0, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ---------------- pen (draws at S x) ----------------
_STRIPE = None
def stripe():
    global _STRIPE
    if _STRIPE is None:
        m = Image.new('L', (PW * S, PH * S), 0); d = ImageDraw.Draw(m)
        rr = random.Random(2)
        x = -PH * S
        while x < PW * S:
            d.line([(x, PH * S), (x + PH * S, 0)], fill=rr.randint(120, 255), width=rr.randint(3, 7))
            x += rr.randint(9, 16)
        _STRIPE = m
    return _STRIPE

def lighten(c, k=0.35): return tuple(int(v + (255 - v) * k) for v in c)

class Pen:
    def __init__(self, img, seed=1):
        self.img = img; self.d = ImageDraw.Draw(img); self.r = random.Random(seed)
    def _wob(self, pts, amp=2.6, closed=False):
        if closed: pts = pts + [pts[0]]
        out = []
        ph = self.r.random() * 10; f1 = 0.12 + self.r.random() * 0.1
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / 10))
            nx, ny = (-(y1 - y0) / L, (x1 - x0) / L) if L else (0, 0)
            for k in range(n):
                u = k / n; s = len(out)
                o = amp * (math.sin(s * f1 + ph) * 0.65 + math.sin(s * 0.47 + ph * 2) * 0.35)
                out.append((x0 + (x1 - x0) * u + nx * o, y0 + (y1 - y0) * u + ny * o))
        out.append(out[0] if closed else pts[-1])
        return out
    def _stroke(self, q, w, fill, closed=False, taper=True, var=0.3, ph=None):
        n = len(q); ph = self.r.random() * 6 if ph is None else ph
        r0 = w * (0.45 if taper and not closed else 1) / 2
        self.d.ellipse([q[0][0] - r0, q[0][1] - r0, q[0][0] + r0, q[0][1] + r0], fill=fill)
        for i in range(n - 1):
            u = i / max(1, n - 2)
            k = 1 - var * 0.6 + var * math.sin(i * 0.17 + ph)
            if taper and not closed: k *= min(1.0, 0.45 + u * 6, 0.45 + (1 - u) * 6)
            ww = max(2, w * k)
            self.d.line([q[i], q[i + 1]], fill=fill, width=int(ww))
            r = ww / 2
            x, y = q[i + 1]
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    def line(self, pts, w=LW, fill=INK, wob=True, taper=True):
        p = [(x * S, y * S) for x, y in pts]
        q = self._wob(p) if wob and len(p) > 1 else self._wob(p, amp=1.2)
        self._stroke(q, w * S, fill, taper=taper)
    def shape(self, pts, fill=WHITE, w=LW, outline=INK, sketch=True):
        p = [(x * S, y * S) for x, y in pts]
        if fill is not None:
            if fill != WHITE and fill != INK:
                dx, dy = self.r.uniform(-5, 5) * S / 2, self.r.uniform(-5, 5) * S / 2
                fp = [(x + dx, y + dy) for x, y in p]
                self.d.polygon(fp, fill=fill)
                m = Image.new('L', self.img.size, 0); ImageDraw.Draw(m).polygon(fp, fill=255)
                self.img.paste(lighten(fill), (0, 0), ImageChops.multiply(m, stripe()) if self.img.size == stripe().size else m.point(lambda v: 0))
            else:
                self.d.polygon(p, fill=fill)
        if w and outline is not None:
            q = self._wob(p, closed=True)
            self._stroke(q, w * S, outline, closed=True)
            if sketch and w >= 4 and outline == INK:
                q2 = self._wob([(x + self.r.uniform(-1, 1) * S, y + self.r.uniform(-1, 1) * S) for x, y in p], amp=4.5, closed=True)
                # sketchy second pass on part of the outline
                a = self.r.randint(0, max(1, len(q2) // 2)); b = min(len(q2), a + len(q2) // 3)
                if b - a > 2: self._stroke(q2[a:b], max(2, w * S * 0.35), (70, 64, 60))
    def ell(self, cx, cy, rx, ry, fill=WHITE, w=LW, outline=INK, a0=0, a1=360):
        self.shape(ell_pts(cx, cy, rx, ry, a0, a1), fill, w, outline)
    def dot(self, x, y, r, fill=INK):
        pts = [(x * S + r * S * (1 + self.r.uniform(-0.12, 0.12)) * math.cos(a / 8 * math.pi),
                y * S + r * S * (1 + self.r.uniform(-0.12, 0.12)) * math.sin(a / 8 * math.pi)) for a in range(16)]
        self.d.polygon(pts, fill=fill)
    def tube(self, pts, w=42, fill=WHITE):
        p = [(x * S, y * S) for x, y in pts]
        dense = self._wob(p, amp=1.8)
        self._stroke(dense, (w + 2 * LW) * S, INK, taper=False, var=0.04, ph=0)
        self._stroke(dense, w * S, fill, taper=False, var=0.0, ph=0)
    def text(self, xy, txt, font, fill=INK, anchor='mm', spacing=10, align='center'):
        f = font.font_variant(size=int(font.size * S))
        self.d.multiline_text((xy[0] * S, xy[1] * S), txt, font=f, fill=fill, anchor=anchor,
                              spacing=spacing * S, align=align)

def ell_pts(cx, cy, rx, ry, a0=0, a1=360, n=72):
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return out

def rrect_pts(x0, y0, x1, y1, r):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += ell_pts(cx, cy, r, r, a0, a0 + 90, 10)
    return pts

# ---------------- character ----------------
def character(p, cx, cy, s=1.0, expr='smile', shirt=WHITE, bandana=False, mask=False, apron=False):
    k = lambda v: v * s
    # body
    by = cy + k(150)
    body = [(cx - k(55), by), (cx - k(190), by + k(55)), (cx - k(235), by + k(140)), (cx - k(255), 2000),
            (cx + k(255), 2000), (cx + k(235), by + k(140)), (cx + k(190), by + k(55)), (cx + k(55), by)]
    p.shape(body, shirt)
    p.line([(cx - k(55), by + k(5)), (cx, by + k(55)), (cx + k(55), by + k(5))])  # collar
    if apron:
        p.shape([(cx - k(150), by + k(150)), (cx + k(150), by + k(150)), (cx + k(175), 2000), (cx - k(175), 2000)], YEL)
        p.line([(cx - k(150), by + k(150)), (cx - k(70), by + k(10))])
        p.line([(cx + k(150), by + k(150)), (cx + k(70), by + k(10))])
        p.shape(rrect_pts(cx - k(70), by + k(230), cx + k(70), by + k(320), k(14)), (250, 220, 120))
    # neck
    p.shape([(cx - k(32), cy + k(100)), (cx + k(32), cy + k(100)), (cx + k(36), by + k(8)), (cx - k(36), by + k(8))])
    # hair back
    hb = ell_pts(cx, cy - k(5), k(168), k(165), 180, 360, 40)
    hb = [(cx - k(172), cy + k(105)), (cx - k(150), cy + k(118))] + [(cx - k(168), cy + k(60))] + hb + \
         [(cx + k(168), cy + k(60)), (cx + k(150), cy + k(118)), (cx + k(172), cy + k(105))]
    p.shape(hb, INK)
    # face
    p.ell(cx, cy + k(10), k(132), k(126))
    # bangs
    bg = ell_pts(cx, cy + k(4), k(140), k(136), 192, 348, 30)
    jag = []
    n = 7
    for i in range(n + 1):
        x = cx + k(128) - k(256) * i / n
        y = cy - k(38) + (k(16) if i % 2 else 0)
        jag.append((x, y))
    p.shape(bg + jag, INK, w=0)
    if bandana:
        band = ell_pts(cx, cy + k(4), k(150), k(150), 185, 355, 30)
        p.shape(band + [(cx + k(140), cy - k(30)), (cx - k(140), cy - k(30))], YEL)
        for i in range(4):
            p.dot(cx - k(80) + k(55) * i, cy - k(85) + (k(20) if i % 2 else 0), k(9), (255, 255, 255))
        p.shape([(cx + k(130), cy - k(55)), (cx + k(210), cy - k(95)), (cx + k(200), cy - k(20))], YEL)
    ex, ey = k(52), cy + k(22)
    # blush
    for sx in (-1, 1):
        p.d.ellipse([(cx + sx * k(82) - k(26)) * S, (cy + k(58) - k(13)) * S,
                     (cx + sx * k(82) + k(26)) * S, (cy + k(58) + k(13)) * S], fill=PINK)
    if expr in ('smile', 'determined'):
        for sx in (-1, 1): p.dot(cx + sx * ex, ey, k(12))
    if expr == 'determined':
        for sx in (-1, 1):
            p.line([(cx + sx * k(28), ey - k(26)), (cx + sx * k(78), ey - k(42))], w=7)
    if expr in ('happy', 'cry', 'proud'):
        for sx in (-1, 1):
            if expr == 'proud':
                p.line(ell_pts(cx + sx * ex, ey - k(6), k(20), k(14), 20, 160, 12), w=7)
            else:
                p.line(ell_pts(cx + sx * ex, ey + k(6), k(20), k(18), 200, 340, 12), w=7)
    if expr == 'cry':
        for sx in (-1, 1):
            x = cx + sx * ex
            p.shape([(x - k(10), ey + k(10)), (x + k(10), ey + k(10)), (x + k(16), cy + k(160)), (x - k(16), cy + k(160))], BLUE, w=4)
    if mask:
        p.shape(rrect_pts(cx - k(85), cy + k(48), cx + k(85), cy + k(118), k(22)), WHITE)
        for yy in (70, 92): p.line([(cx - k(55), cy + k(yy)), (cx + k(55), cy + k(yy))], w=3)
        p.line([(cx - k(85), cy + k(62)), (cx - k(128), cy + k(30))], w=4)
        p.line([(cx + k(85), cy + k(62)), (cx + k(128), cy + k(30))], w=4)
    else:
        my = cy + k(78)
        if expr == 'smile':
            p.line(ell_pts(cx, my - k(12), k(22), k(14), 20, 160, 12), w=6)
        elif expr == 'determined':
            p.line([(cx - k(20), my), (cx + k(20), my - k(3))], w=6)
        elif expr in ('happy', 'cry'):
            p.shape(ell_pts(cx, my - k(8), k(30), k(30), 0, 180, 16), (230, 110, 110), w=6)
        elif expr == 'proud':
            p.line(ell_pts(cx + k(8), my - k(14), k(26), k(16), 20, 150, 12), w=6)
    return dict(ls=(cx - k(205), by + k(70)), rs=(cx + k(205), by + k(70)))

def hand(p, x, y, r=28, fill=WHITE):
    p.ell(x, y, r, r, fill)

def sparkle(p, x, y, r, fill=YEL):
    pts = []
    for i in range(8):
        a = math.radians(i * 45 - 90); rr = r if i % 2 == 0 else r * 0.32
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    p.shape(pts, fill, w=4)

def drop(p, x, y, r=16):
    p.shape([(x, y - r * 2)] + ell_pts(x, y, r, r, -30, 210, 16), BLUE, w=4)

# ---------------- overlay elements ----------------
def layer(): return Image.new('RGBA', (PW * S, PH * S), (0, 0, 0, 0))

def finish(img, t, kind='pop'):
    """crop supersampled layer to bbox, downscale, return element dict (1x coords)."""
    bb = img.getbbox()
    x0, y0 = bb[0] // S * S, bb[1] // S * S
    x1, y1 = -(-bb[2] // S) * S, -(-bb[3] // S) * S
    c = img.crop((x0, y0, x1, y1)).resize(((x1 - x0) // S, (y1 - y0) // S), Image.LANCZOS)
    return dict(img=c, x=x0 // S, y=y0 // S, t=t, kind=kind)

def bubble(txt, cx, cy, tail, t, size=44, shout=False):
    L = layer(); p = Pen(L, int(cx + cy))
    f = F('Bold', size)
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    b = tmp.multiline_textbbox((0, 0), txt, font=f, spacing=12, align='center')
    tw, th = b[2] - b[0], b[3] - b[1]
    rx, ry = tw / 2 + 62, th / 2 + 46
    if shout:
        pts = []
        n = 26
        for i in range(n):
            a = math.radians(360 * i / n); rr = 1.0 if i % 2 == 0 else 1.13
            pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
        p.shape(pts, WHITE)
    else:
        p.ell(cx, cy, rx, ry)
    # tail
    ang = math.atan2(tail[1] - cy, tail[0] - cx)
    bx, by = cx + rx * 0.8 * math.cos(ang), cy + ry * 0.8 * math.sin(ang)
    px, py = -math.sin(ang) * 26, math.cos(ang) * 26
    a, c = (bx + px, by + py), (bx - px, by - py)
    p.shape([a, tail, c], WHITE, w=0)
    p.line([a, tail], w=LW); p.line([tail, c], w=LW)
    p.shape([(bx + px * 0.75, by + py * 0.75), (bx - px * 0.75, by - py * 0.75),
             (cx, cy)], WHITE, w=0)
    p.text((cx, cy), txt, f, spacing=12)
    return finish(L, t)

def narration(txt, t=0.0, x=36, y=36, size=40):
    L = layer(); p = Pen(L, 7)
    f = F('Bold', size)
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    b = tmp.multiline_textbbox((0, 0), txt, font=f, spacing=10)
    tw, th = b[2] - b[0], b[3] - b[1]
    p.shape([(x, y), (x + tw + 56, y), (x + tw + 56, y + th + 44), (x, y + th + 44)], YEL)
    p.text((x + 28, y + 22 - b[1]), txt, f, anchor='la', spacing=10, align='left')
    return finish(L, t, 'slide')

def sfx(txt, x, y, t, rot=-10, size=64, fill=INK):
    L = layer(); p = Pen(L, 3)
    f = F('Black', size)
    p.d.text((x * S, y * S), txt, font=f.font_variant(size=size * S), fill=fill, anchor='mm',
             stroke_width=7 * S, stroke_fill=WHITE)
    L = L.rotate(rot, center=(x * S, y * S), resample=Image.BICUBIC)
    return finish(L, t)

def drawn(fn, t, kind='pop'):
    L = layer(); p = Pen(L, 11); fn(p); return finish(L, t, kind)

def stamp_el(cx, cy, t):
    def fn(p):
        col = (214, 64, 69)
        p.ell(cx, cy, 120, 120, (255, 255, 255), w=10, outline=col)
        p.ell(cx, cy, 98, 98, None, w=4, outline=col)
        p.text((cx, cy), '참 잘\n했어요', F('Black', 52), fill=col, spacing=4)
    L = layer(); p = Pen(L, 5); fn(p)
    L = L.rotate(14, center=(cx * S, cy * S), resample=Image.BICUBIC)
    return finish(L, t)

# ---------------- panels ----------------
def new_panel():
    img = Image.new('RGB', (PW * S, PH * S), WHITE)
    return img, Pen(img, random.randint(0, 999))

def panel_title():
    img, p = new_panel()
    # little dots background
    for i in range(14):
        for j in range(5):
            if (i + j) % 2 == 0: p.dot(40 + i * 68, 40 + j * 64, 4, (232, 228, 220))
    ch = character(p, 480, 830, 1.0, 'smile')
    # notebook
    p.shape(rrect_pts(320, 990, 640, 1250 + 20, 14), YEL)
    p.line([(345, 990), (345, 1250)], w=5)
    p.text((492, 1085), '칭찬 일기', F('Black', 52))
    for x in (380, 600): pass
    p.tube([ch['ls'], (300, 1110)]); p.tube([ch['rs'], (660, 1110)])
    hand(p, 330, 1105); hand(p, 630, 1105)
    sparkle(p, 175, 700, 34); sparkle(p, 790, 650, 26); sparkle(p, 820, 760, 16)
    els = []
    def title(pp):
        pp.d.rounded_rectangle([140 * S, 250 * S, 820 * S, 330 * S], radius=20 * S, fill=YEL)
        pp.text((480, 150), '일주일에 한 번은', F('Bold', 66))
        pp.text((480, 268), '나를 칭찬해', F('Black', 128))
    els.append(drawn(title, 0.15, 'slide'))
    els.append(bubble('이번 주 칭찬\n시작해 볼까?', 770, 520, (640, 650), 0.9, size=38))
    return img, els, None

def panel_deck():
    img, p = new_panel()
    # deck planks
    p.shape([(0, 760), (960, 760), (960, 1250), (0, 1250)], (238, 222, 196), w=0)
    for i, y in enumerate(range(760, 1260, 82)):
        p.line([(0, y), (960, y)], w=5)
        off = 140 if i % 2 else 380
        for x in range(off, 960, 480): p.line([(x, y), (x, y + 82)], w=4)
    # mold on right side
    rnd = random.Random(4)
    for _ in range(26):
        x = rnd.uniform(730, 945); y = rnd.uniform(790, 1230); r = rnd.uniform(14, 40)
        p.ell(x, y, r, r * 0.7, MOLD, w=3)
    # character (kneeling, bust at left)
    ch = character(p, 330, 470, 0.92, 'determined', mask=True)
    p.tube([ch['ls'], (150, 900)]); hand(p, 150, 905, 30, YEL)
    # brush
    bx, by = 600, 900
    p.shape([(bx - 20, by - 150), (bx + 18, by - 150), (bx + 22, by + 10), (bx - 24, by + 10)], (200, 150, 100))
    p.shape(rrect_pts(bx - 90, by, bx + 90, by + 50, 10), (200, 150, 100))
    for x in range(bx - 80, bx + 90, 20): p.line([(x, by + 50), (x + 6, by + 85)], w=4)
    p.tube([ch['rs'], (bx, by - 90)]); hand(p, bx, by - 90, 32, YEL)
    drop(p, 520, 330, 14); drop(p, 130, 360, 12)
    # motion lines
    for k in range(3):
        p.line([(bx + 110, by + 30 + k * 26), (bx + 170, by + 20 + k * 26)], w=5)
    els = [narration('1. 테라스 데크 곰팡이, 직접 제거', 0.05),
           bubble('업체 부르면 얼마야?\n내가 한다!!', 720, 360, (560, 470), 0.4, size=42, shout=True),
           sfx('박박박!', 800, 1010, 1.0, rot=-12, size=70),
           drawn(lambda q: [sparkle(q, 640, 1110, 38, WHITE), sparkle(q, 600, 1200, 22, WHITE),
                            sparkle(q, 690, 1190, 18, WHITE)], 1.5)]
    return img, els, None

def panel_game():
    img, p = new_panel()
    ch = character(p, 480, 600, 0.95, 'determined')
    # table
    p.shape([(0, 930), (960, 930), (960, 1250), (0, 1250)], (236, 232, 224))
    for x in range(40, 960, 90): p.line([(x, 960), (x + 50, 960)], w=3, fill=GREY)
    # rulebook (thick)
    x0, y0, x1, y1 = 70, 820, 370, 1000
    p.shape([(x0, y1), (x0 + 40, y1 + 40), (x1 + 40, y1 + 40), (x1, y1)], WHITE)
    for k in range(1, 6): p.line([(x0 + 8 * k, y1 + 8 * k), (x1 + 8 * k, y1 + 8 * k)], w=2)
    p.shape([(x1, y0), (x1 + 40, y0 + 40), (x1 + 40, y1 + 40), (x1, y1)], WHITE)
    p.shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (70, 62, 120))
    p.text(((x0 + x1) / 2, (y0 + y1) / 2), 'RULE\nBOOK', F('Black', 40), fill=WHITE, spacing=2)
    # board
    bd = [(560, 990), (920, 990), (950, 1200), (520, 1200)]
    p.shape(bd, (250, 240, 214))
    for k in range(1, 5):
        u = k / 5
        p.line([(560 + 360 * u - 40 * u * 0, 990), (520 + 430 * u, 1200)], w=3)
    for k in range(1, 4):
        v = k / 4; y = 990 + 210 * v
        p.line([(560 - 40 * v, y), (920 + 30 * v, y)], w=3)
    rnd = random.Random(9)
    for _ in range(7):
        x = rnd.uniform(600, 880); y = rnd.uniform(1020, 1170)
        p.shape([(x, y), (x + 26, y), (x + 26, y + 26), (x, y + 26)], rnd.choice([YEL, (214, 64, 69), INK]), w=4)
    # arms
    p.tube([ch['ls'], (250, 830)]); hand(p, 250, 830)
    p.tube([ch['rs'], (760, 640)]); hand(p, 760, 640)
    p.tube([(760, 630), (765, 580)], w=16)  # finger up
    els = [narration('2. 어려운 전략게임\n<전국: 첫번째 제국> 룰 마스터', 0.05),
           bubble('룰북 두께 실화...?', 760, 300, (640, 450), 0.4, size=40),
           drawn(lambda q: (q.ell(480, 345, 40, 44, YEL), q.shape([(462, 385), (498, 385), (495, 410), (465, 410)], GREY, w=5),
                            [q.line([(480 + 62 * math.cos(math.radians(a)), 345 + 62 * math.sin(math.radians(a))),
                                     (480 + 86 * math.cos(math.radians(a)), 345 + 86 * math.sin(math.radians(a)))], w=6)
                             for a in (-150, -120, -90, -60, -30)]), 1.4),
           bubble('...다 이해했다.\n덤벼!', 215, 440, (330, 540), 1.6, size=40, shout=True)]
    return img, els, None

def panel_speak():
    img, p = new_panel()
    # calendar
    cx0, cy0, cx1, cy1 = 560, 210, 920, 600
    p.shape([(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)], WHITE)
    p.shape([(cx0, cy0), (cx1, cy0), (cx1, cy0 + 70), (cx0, cy0 + 70)], YEL)
    for k in range(1, 7): p.line([(cx0 + (cx1 - cx0) * k / 7, cy0 + 70), (cx0 + (cx1 - cx0) * k / 7, cy1)], w=3)
    for k in range(1, 5): p.line([(cx0, cy0 + 70 + (cy1 - cy0 - 70) * k / 5), (cx1, cy0 + 70 + (cy1 - cy0 - 70) * k / 5)], w=3)
    cw, chh = (cx1 - cx0) / 7, (cy1 - cy0 - 70) / 5
    for i in range(7):
        for j in range(5):
            x = cx0 + cw * i + cw / 2; y = cy0 + 70 + chh * j + chh / 2
            p.line([(x - 14, y), (x - 3, y + 12), (x + 16, y - 14)], w=5, fill=(214, 64, 69))
    for x in (620, 860): p.ell(x, cy0, 10, 18, INK, w=0)
    ch = character(p, 320, 640, 0.95, 'happy')
    # phone
    X0, Y0, X1, Y1 = 520, 700, 790, 1180
    p.tube([ch['rs'], (700, 1150)])
    p.shape(rrect_pts(X0, Y0, X1, Y1, 36), INK)
    p.shape(rrect_pts(X0 + 16, Y0 + 30, X1 - 16, Y1 - 30, 22), WHITE, w=0)
    fx, fy = 655, 820
    p.shape([(fx, fy - 70)] + ell_pts(fx, fy, 46, 50, -20, 200, 16), (247, 150, 60), w=5)
    p.shape([(fx, fy - 20)] + ell_pts(fx, fy + 15, 22, 26, -20, 200, 12), YEL, w=0)
    hand(p, 560, 1150, 30); hand(p, 770, 1100, 30)
    p.tube([ch['ls'], (110, 1060)]); hand(p, 110, 1060)
    numf = F('Black', 96); subf = F('Bold', 34)
    def dyn(frame, tl, ox, oy):
        v = int(round(222 * ease((tl - 0.3) / 1.3))) if tl > 0.3 else 0
        d = ImageDraw.Draw(frame)
        d.text((ox + 655, oy + 960), str(v), font=numf, fill=(230, 110, 40), anchor='mm')
        d.text((ox + 655, oy + 1045), '일 연속 학습', font=subf, fill=INK, anchor='mm')
    els = [narration('3. 영어공부 앱 스픽, 222일 연속', 0.05),
           bubble('오늘도\n출석 완료!', 230, 330, (300, 460), 0.5, size=42),
           drawn(lambda q: (sparkle(q, 830, 760, 36), sparkle(q, 870, 860, 20)), 1.7)]
    return img, els, dyn

def panel_pay():
    img, p = new_panel()
    for i in range(0, 960, 60):  # soft rays
        pass
    ch = character(p, 480, 640, 0.95, 'cry', bandana=True, apron=True)
    # phone held at chest
    X0, Y0, X1, Y1 = 400, 960, 560, 1200
    p.shape(rrect_pts(X0, Y0, X1, Y1, 24), INK)
    p.shape(rrect_pts(X0 + 12, Y0 + 22, X1 - 12, Y1 - 22, 14), (255, 248, 220), w=0)
    p.text((480, 1080), '₩', F('Black', 70), fill=(230, 110, 40))
    p.tube([ch['ls'], (395, 1100)]); hand(p, 395, 1100)
    p.tube([ch['rs'], (565, 1100)]); hand(p, 565, 1100)
    for (x, y) in ((250, 900), (720, 880)):
        p.line([(x - 30, y), (x + 30, y)], w=5); p.line([(x, y - 30), (x, y + 30)], w=5)
    def noti(q):
        x0, y0, x1, y1 = 500, 210, 930, 400
        q.shape(rrect_pts(x0, y0, x1, y1, 28), WHITE)
        q.shape(rrect_pts(x0 + 26, y0 + 30, x0 + 96, y0 + 100, 16), YEL, w=4)
        q.text((x0 + 61, y0 + 65), '₩', F('Black', 40))
        q.text((x0 + 118, y0 + 40), '입금 알림', F('Bold', 30), anchor='la', fill=(120, 112, 104))
        q.text((x0 + 118, y0 + 88), '첫 급여가\n입금되었습니다', F('Black', 38), anchor='la', align='left', spacing=6)
    els = [narration('4. 요식업 알바, 첫 급여 입금', 0.05),
           drawn(noti, 0.4),
           bubble('몸으로 번 첫 월급...\n수고했다, 나!', 230, 340, (370, 500), 1.3, size=38)]
    return img, els, None

def panel_end():
    img, p = new_panel()
    for i in range(14):
        for j in range(4):
            if (i + j) % 2 == 0: p.dot(40 + i * 68, 1050 + j * 64, 4, (232, 228, 220))
    ch = character(p, 470, 760, 1.0, 'proud')
    p.tube([ch['ls'], (180, 720), (330, 610)]); hand(p, 335, 605)
    p.tube([ch['rs'], (760, 1060)]); hand(p, 760, 1060, 32)
    p.tube([(760, 1050), (762, 995)], w=18)
    for (x, y) in ((150, 520), (310, 520)):
        p.line(ell_pts(x + 40, y + 10, 40, 30, 200, 340, 8), w=5)
    els = [drawn(lambda q: (q.d.rounded_rectangle([170 * S, 300 * S, 790 * S, 380 * S], radius=20 * S, fill=YEL),
                            q.text((480, 190), '이번 주도', F('Bold', 70)),
                            q.text((480, 315), '잘했어, 나.', F('Black', 120))), 0.15, 'slide'),
           stamp_el(780, 760, 1.0)]
    return img, els, None

# ---------------- assemble ----------------
def build():
    panels = [panel_title(), panel_deck(), panel_game(), panel_speak(), panel_pay(), panel_end()]
    holds = [2.6, 3.0, 3.4, 3.0, 3.2, 3.4]
    top = 960 - PH // 2  # first panel centred
    stripH = top + len(panels) * (PH + GUT) + 960
    strip = Image.new('RGB', (W, stripH), PAPER)
    sp = Pen(Image.new('RGB', (1, 1)))
    info = []
    y = top
    for img, els, dyn in panels:
        bp = Pen(img, y)
        e = 5
        for a, b in (((e, e), (PW - e, e)), ((PW - e, e), (PW - e, PH - e)), ((PW - e, PH - e), (e, PH - e)), ((e, PH - e), (e, e))):
            bp.line([a, b], w=7, taper=False)
        small = img.resize((PW, PH), Image.LANCZOS)
        grain = Image.effect_noise((PW, PH), 22).point(lambda v: 235 + int(v / 255 * 20))
        small = ImageChops.multiply(small, Image.merge('RGB', (grain, grain, grain)))
        strip.paste(small, (PX, y))
        info.append(dict(y=y, els=els, dyn=dyn))
        y += PH + GUT
    # timeline
    SCR = 0.75
    t = 0.0
    for i, it in enumerate(info):
        it['arrive'] = t
        it['hold'] = holds[i]
        t += holds[i] + (SCR if i < len(info) - 1 else 0)
    total = t
    def cam(T):
        for i, it in enumerate(info):
            a, h = it['arrive'], it['hold']
            c = it['y'] + PH / 2
            if T < a + h or i == len(info) - 1: return c
            if T < a + h + SCR:
                n = info[i + 1]['y'] + PH / 2
                return c + (n - c) * inout((T - a - h) / SCR)
        return info[-1]['y'] + PH / 2
    def frame(T):
        cy = cam(T)
        top_y = int(round(cy - H / 2))
        f = strip.crop((0, top_y, W, top_y + H))
        for it in info:
            if T < it['arrive']: continue
            tl = T - it['arrive']
            oy = it['y'] - top_y
            if oy > H or oy + PH < 0: continue
            if it['dyn']: it['dyn'](f, tl, PX, oy)
            for e in it['els']:
                pt = (tl - e['t'])
                if pt <= 0: continue
                im = e['img']
                if e['kind'] == 'slide':
                    q = ease(pt / 0.45)
                    if q < 1:
                        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * q)))
                    f.paste(im, (PX + e['x'], int(oy + e['y'] + (1 - q) * 40)), im)
                else:
                    q = pt / 0.35
                    if q < 1:
                        s = 0.5 + 0.5 * back(q)
                        w2, h2 = max(1, int(im.width * s)), max(1, int(im.height * s))
                        im = im.resize((w2, h2), Image.BICUBIC)
                        a = ease(q * 2)
                        im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
                        cx = PX + e['x'] + e['img'].width / 2; cyy = oy + e['y'] + e['img'].height / 2
                        f.paste(im, (int(cx - w2 / 2), int(cyy - h2 / 2)), im)
                    else:
                        f.paste(im, (PX + e['x'], oy + e['y']), im)
        # global fades
        a = min(1.0, T / 0.3, (total - T) / 0.6)
        if a < 1: f = Image.blend(Image.new('RGB', (W, H), PAPER), f, max(0.0, a))
        return f
    return info, frame, total, SCR

def render_seg(name, T0, T1, frame):
    tmp = f'{name}.tmp.mp4'
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                           '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    n0, n1 = int(round(T0 * FPS)), int(round(T1 * FPS))
    for i in range(n0, n1):
        pr.stdin.write(frame(i / FPS).tobytes())
    pr.stdin.close()
    if pr.wait() != 0: sys.exit(1)
    os.replace(tmp, f'{name}.mp4')

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    info, frame, total, SCR = build()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if mode == 'preview':
        shots = [it['arrive'] + it['hold'] - 0.1 for it in info] + [info[1]['arrive'] + info[1]['hold'] + SCR / 2]
        ims = [frame(T).resize((360, 640)) for T in shots]
        m = Image.new('RGB', (360 * 4, 640 * 2), WHITE)
        for i, im in enumerate(ims): m.paste(im, ((i % 4) * 360, (i // 4) * 640))
        m.save('toon_sheet.png')
        for i, T in enumerate(shots[:6]): frame(T).save(f'toon_full_{i}.png')
        sys.exit(0)
    names = []
    for i, it in enumerate(info):
        T0 = it['arrive']; T1 = info[i + 1]['arrive'] if i + 1 < len(info) else total
        nm = f't{i}'; render_seg(nm, T0, T1, frame); names.append(nm)
    with open('tlist.txt', 'w') as fh:
        for nm in names: fh.write(f"file '{nm}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'tlist.txt', '-c', 'copy', 'tsilent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'tsilent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', '나칭찬_웹툰릴스.mp4'], check=True)
    print('done', total)
