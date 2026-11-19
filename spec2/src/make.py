import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
FD = 'fonts/'
def jua(s): return ImageFont.truetype(FD + 'jua.ttf', int(s))
def dodum(s): return ImageFont.truetype(FD + 'gowun-dodum.ttf', int(s))
def gaegu(s): return ImageFont.truetype(FD + 'gaegu.ttf', int(s))
def nun(w, s, it=False): return ImageFont.truetype(FD + f"nunito-latin-{w}-{'italic' if it else 'normal'}.ttf", int(s))
def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def inout(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

SRC = Image.open('src.png').convert('RGB')
INK, BROWN, TOMATO, CREAM = (60, 40, 32), (120, 80, 60), (226, 72, 52), (248, 239, 226)

def crop(box, w):
    c = SRC.crop(box); c = c.resize((w, round(c.height * w / c.width)), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

def panel(im, r=36):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=r, fill=255)
    out = Image.new('RGBA', (im.width + 40, im.height + 50), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 34, im.width + 20, im.height + 34], radius=r, fill=(120, 80, 50, 70))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    body = Image.new('RGBA', im.size, (0, 0, 0, 0)); body.paste(im, (0, 0), m)
    ImageDraw.Draw(body).rounded_rectangle([2, 2, im.width - 3, im.height - 3], radius=r, outline=INK, width=6)
    out.alpha_composite(body, (20, 20))
    return out

def text_el(txt, font, fill, spacing=16, stroke=0):
    b = ImageDraw.Draw(Image.new('L', (1, 1))).multiline_textbbox((0, 0), txt, font=font, spacing=spacing, align='center', stroke_width=stroke)
    b = [int(math.ceil(v)) for v in b]; pad = 30
    im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((pad - b[0], pad - b[1]), txt, font=font, fill=fill, spacing=spacing, align='center',
                                      stroke_width=stroke, stroke_fill=(255, 255, 255))
    return im

def pill(txt, bg, fg, font, padx=28, pady=12):
    t = text_el(txt, font, fg)
    im = Image.new('RGBA', (t.width - 60 + padx * 2, t.height - 60 + pady * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg)
    im.alpha_composite(t, (padx - 30, pady - 30)); return im

BG = Image.new('RGB', (W, H), CREAM)
d = ImageDraw.Draw(BG)
for y in range(0, H, 54):
    for x in range(0, W, 54):
        if (x // 54 + y // 54) % 2 == 0: d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(236, 222, 204))

HEADER = text_el('신계 공식 등록증  EP.2', jua(40), BROWN)

def en_box(lines, maxw=980):
    rows = [text_el(t, f, c, spacing=8) for t, f, c in lines]
    W2 = min(maxw, max(r.width for r in rows) + 20); H2 = sum(r.height for r in rows) - 44 * (len(rows) - 1) - 20
    im = Image.new('RGBA', (W2, H2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W2 - 1, H2 - 1], radius=32, fill=(255, 255, 255, 240), outline=INK, width=4)
    y = -10
    for r in rows: im.alpha_composite(r, ((W2 - r.width) // 2, y)); y += r.height - 44
    return im

def cond(box, n, name, en, quote, pw=1040, col=None):
    p = panel(crop(box, pw)); ph = p.height; py = 1010
    eb = en_box([(en, nun(800, 46), INK), (quote, nun(700, 42, True), BROWN)])
    return [(HEADER, 540, 150, 0.0, 'none'),
            (pill(f'조건 {n} / 5', INK + (255,), (255, 255, 255), jua(36)), 540, 240, 0.0, 'none'),
            (text_el(name, jua(96), col or INK, spacing=12), 540, 455, 0.05, 'pop'),
            (p, 540, py, 0.25, 'up'),
            (eb, 540, py + ph / 2 + eb.height / 2 + 10, 0.7, 'up')]

face = panel(crop((524, 492, 852, 756), 940))
full = SRC.resize((640, 960), Image.LANCZOS)
SCENES = [
    ([(text_el('나라는 제품의\n정상 작동 조건', jua(112), INK, spacing=16), 540, 300, -1, 'none'),
      (face, 540, 900, -1, 'none'),
      (pill('EP.2', TOMATO + (255,), (255, 255, 255), nun(800, 46)), 540, 1420, 0.2, 'pop'),
      (en_box([('Normal Operating Conditions', nun(800, 50), INK), ('for a product called "me"', nun(700, 44, True), BROWN)]), 540, 1580, 0.5, 'up')], 2.8),
    ([(HEADER, 540, 150, 0.0, 'none'),
      (text_el('제품 사용설명서', jua(56), BROWN), 540, 330, 0.05, 'up'),
      (text_el('정상 작동 조건', jua(116), TOMATO), 540, 470, 0.15, 'pop'),
      (panel(crop((0, 0, 1024, 390), 1040)), 540, 920, 0.35, 'up'),
      (en_box([('"Keep these conditions,', nun(800, 48), INK), ('and I work perfectly!"', nun(800, 48), INK)]), 540, 1360, 0.9, 'up')], 3.4),
    (cond((5, 395, 515, 758), 1, '원하는 대로\n선택할 수 있는 환경', 'Freedom to choose', '"Let\'s do everything I want!"'), 3.3),
    (cond((522, 395, 1020, 758), 2, '적당한 자극과\n새로운 경험', 'A little thrill & new experiences', '"Wow~ Something new!"'), 3.3),
    (cond((5, 765, 505, 1122), 3, '맛있는 음식과\n커피', 'Good food & coffee', '"Tasty food is the best!"'), 3.3),
    (cond((510, 765, 1020, 1122), 4, '믿고 맡길 수 있는\n사람과의 시간', 'Time with people I trust', '"Better together!"'), 3.3),
    (cond((10, 1135, 920, 1536), 5, '혼자만의\n여유 시간', 'Time all to myself', '"This one\'s a must, too!"', col=TOMATO), 3.6),
    ([(HEADER, 540, 150, 0.0, 'none'),
      (text_el('5가지 조건 충족 시\n완벽 작동 보장!', jua(92), INK, spacing=14), 540, 360, 0.05, 'pop'),
      (panel(full, r=28), 540, 1020, 0.3, 'up'),
      (text_el('여러분의 정상 작동 조건은?', jua(76), TOMATO), 540, 1560, 1.0, 'up'),
      (text_el("What keeps YOU running? Tell me below", nun(800, 40), BROWN), 540, 1650, 1.4, 'up')], 4.6),
]

SCR = 0.6
SEC = []; t = 0.0
for i, (els, hold) in enumerate(SCENES):
    SEC.append(dict(els=els, arrive=t, hold=hold, y=i * H)); t += hold + (SCR if i < len(SCENES) - 1 else 0)
TOTAL = t

def cam(T):
    for i, s in enumerate(SEC):
        if T < s['arrive'] + s['hold'] or i == len(SEC) - 1: return s['y']
        if T < s['arrive'] + s['hold'] + SCR: return s['y'] + H * inout((T - s['arrive'] - s['hold']) / SCR)
    return SEC[-1]['y']

def draw_sec(s, T, oy, f):
    f.paste(BG, (0, oy))
    tl = T - s['arrive']
    for el, cx, cy, t0, kind in s['els']:
        p = 1.0 if kind == 'none' else ease((tl - t0) / 0.45)
        if p <= 0: continue
        im = el
        if kind == 'pop' and p < 1:
            sc = 0.85 + 0.15 * p
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
        if p < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
        dy = (1 - p) * 40 if kind == 'up' else 0
        f.alpha_composite(im, (int(cx - im.width / 2), int(oy + cy - im.height / 2 + dy)))

def frame(T):
    y = cam(T); f = Image.new('RGBA', (W, H), CREAM + (255,))
    for s in SEC:
        oy = int(round(s['y'] - y))
        if -H < oy < H: draw_sec(s, T if oy == 0 else max(T, s['arrive'] + 5), oy, f) if oy < 0 else draw_sec(s, T, oy, f)
    f = f.convert('RGB')
    a = min(1.0, T / 0.25, (TOTAL - T) / 0.6)
    if a < 1: f = Image.blend(Image.new('RGB', (W, H), CREAM), f, max(0, a))
    return f

def render(name, T0, T1):
    tmp = name + '.tmp.mp4'
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for k in range(int(round(T0 * FPS)), int(round(T1 * FPS))): pr.stdin.write(frame(k / FPS).tobytes())
    pr.stdin.close()
    if pr.wait() != 0: sys.exit(1)
    os.replace(tmp, name + '.mp4')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        shots = [s['arrive'] + s['hold'] - 0.05 for s in SEC[:-1]] + [SEC[-1]['arrive'] + 3.0]
        m = Image.new('RGB', (216 * 4, 384 * 2))
        for k, T in enumerate(shots): m.paste(frame(T).resize((216, 384)), ((k % 4) * 216, (k // 4) * 384))
        m.save('sheet.png'); sys.exit(0)
    names = []
    for i, s in enumerate(SEC):
        T1 = SEC[i + 1]['arrive'] if i + 1 < len(SEC) else TOTAL
        render(f's{i}', s['arrive'], T1); names.append(f's{i}')
    open('list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in names))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', 'spec2_reel.mp4'], check=True)
    frame(SEC[0]['hold'] - 0.1).save('cover_spec2.jpg', quality=93)
    print('done', TOTAL)
