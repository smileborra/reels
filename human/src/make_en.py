import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
FD = 'fonts/'
def jua(s): return ImageFont.truetype(FD + 'nunito-latin-800-normal.ttf', int(s * 0.92))
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

HEADER = text_el('My Unfiltered Humanity  ·  by AI', jua(40), BROWN)

def scene(box, small, big, idx, total, pw=900, big_col=INK):
    p = panel(crop(box, pw)); ph = p.height
    block = 70 + ph + 200
    top = max(330, 1000 - block / 2); py = top + 70 + ph / 2
    return [
        (HEADER, 540, 150, 0.0, 'none'),
        (pill(f'{idx} / {total}', INK + (255,), (255, 255, 255), nun(800, 34)), 540, 230, 0.0, 'none'),
        (text_el(small, gaegu(64), BROWN), 540, top, 0.1, 'up'),
        (p, 540, py, 0.25, 'pop'),
        (text_el(big, jua(104), big_col), 540, py + ph / 2 + 110, 0.75, 'pop'),
    ]

SCENES = [
    ([(text_el('My Unfiltered', jua(110), INK), 540, 250, 0.1, 'up'),
      (text_el('Humanity', jua(170), TOMATO), 540, 390, 0.3, 'pop'),
      (pill('by AI', INK + (255,), (255, 255, 255), nun(800, 44)), 540, 520, 0.5, 'up'),
      (panel(crop((360, 280, 900, 800), 880)), 540, 1050, 0.6, 'up'),
      (text_el('Drawn by AI, zero retouching', gaegu(70), BROWN), 540, 1560, 1.1, 'up')], 3.0),
    (scene((215, 25, 525, 335), 'When I start working', 'Peak confidence', 1, 7), 2.6),
    (scene((610, 25, 905, 320), '...5 minutes later', 'Total meltdown', 2, 7, big_col=(70, 90, 160)), 2.6),
    (scene((830, 150, 1312, 420), 'Give me a board game', 'Pure sunshine', 3, 7, pw=960), 2.6),
    (scene((960, 395, 1270, 640), 'One drink in', 'Melting away', 4, 7), 2.6),
    (scene((1020, 610, 1312, 880), 'Feelings hurt?', 'Blanket protest', 5, 7), 2.6),
    (scene((0, 280, 400, 620), 'But in the end', 'Nap with my tomato', 6, 7, big_col=TOMATO), 2.6),
    (scene((300, 770, 1110, 1199), 'Desk reality', 'Salad... and ramen', 7, 7, pw=980), 2.8),
    ([(text_el('So yes, all of this is', gaegu(80), BROWN), 540, 230, 0.05, 'up'),
      (text_el('ME', jua(170), TOMATO), 540, 360, 0.3, 'pop'),
      (panel(crop((0, 0, 1312, 1199), 960)), 540, 1000, 0.5, 'up'),
      (text_el('Unfiltered, just as I am', jua(70), INK), 540, 1560, 1.2, 'up'),
      (text_el('Which number is the most YOU?', gaegu(64), BROWN), 540, 1660, 1.7, 'up')], 4.2),
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
        shots = [s['arrive'] + s['hold'] - 0.05 for s in SEC]
        m = Image.new('RGB', (216 * 5, 384 * 2))
        for k, T in enumerate(shots): m.paste(frame(T).resize((216, 384)), ((k % 5) * 216, (k // 5) * 384))
        m.save('sheet_en.png'); sys.exit(0)
    names = []
    for i, s in enumerate(SEC):
        T1 = SEC[i + 1]['arrive'] if i + 1 < len(SEC) else TOTAL
        render(f'e{i}', s['arrive'], T1); names.append(f'e{i}')
    open('list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in names))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', 'human_reel_en.mp4'], check=True)
    frame(SEC[0]['hold'] - 0.1).save('cover_human_en.jpg', quality=93)
    print('done', TOTAL)
