import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
def jua(s): return ImageFont.truetype('fonts/nunito-latin-800-normal.ttf', int(s * 0.9))
def dodum(s): return ImageFont.truetype('fonts/nunito-latin-700-normal.ttf', int(s * 0.92))
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

S = 2
SRC = Image.open('src.png').convert('RGB')
BIG = SRC.resize((SRC.width * S, SRC.height * S), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
GOLD, WHITE, CREAM = (250, 196, 110), (255, 255, 255), (255, 240, 220)

def cam(cx, cy, h):
    h = min(h, SRC.height); w = h * 9 / 16
    cx = min(max(cx, w / 2), SRC.width - w / 2); cy = min(max(cy, h / 2), SRC.height - h / 2)
    box = ((cx - w / 2) * S, (cy - h / 2) * S, (cx + w / 2) * S, (cy + h / 2) * S)
    return BIG.resize((W, H), Image.BICUBIC, box=box)

def text_el(txt, font, fill, spacing=18, align='center'):
    b = ImageDraw.Draw(Image.new('L', (1, 1))).multiline_textbbox((0, 0), txt, font=font, spacing=spacing, align=align)
    b = [int(math.ceil(v)) for v in b]; pad = 40
    im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0)); o = (pad - b[0], pad - b[1])
    s = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).multiline_text(o, txt, font=font, fill=(0, 0, 0, 230), spacing=spacing, align=align, stroke_width=6, stroke_fill=(0, 0, 0, 230))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).multiline_text(o, txt, font=font, fill=fill, spacing=spacing, align=align)
    return im

def scrim(where, strength=0.7):
    y = np.linspace(0, 1, H)[:, None]
    m = np.clip((0.45 - y) / 0.45, 0, 1) if where == 'top' else np.clip((y - 0.55) / 0.45, 0, 1)
    a = np.zeros((H, W, 4), np.uint8); a[..., 3] = (m ** 1.2 * strength * 255 * np.ones((1, W))).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')
SCRIM = {'top': scrim('top'), 'bottom': scrim('bottom')}

def card(dur, a, b, where, small, big, small_size=60, big_size=104, gold_big=False):
    els = []
    base = 330 if where == 'top' else 1420
    if small: els.append((text_el(small, jua(small_size), GOLD if not gold_big else CREAM, spacing=16), base, 0.2))
    bg = text_el(big, jua(big_size) if big_size > 70 else dodum(big_size), GOLD if gold_big else WHITE, spacing=20)
    els.append((bg, base + 90 + bg.height / 2 - 40 if small else base + bg.height / 2 - 40, 0.5))
    return dict(dur=dur, a=a, b=b, where=where, els=els)

CARDS = [
    card(3.4, (455, 1045, 430), (450, 600, 1100), 'top', None, 'The Hidden Self\nin the Water', big_size=128, gold_big=True),
    card(2.8, (470, 300, 500), (470, 420, 620), 'bottom', 'What you see', 'An ordinary person\nby the water'),
    card(2.8, (460, 560, 560), (460, 900, 620), 'top', 'But beneath the surface...', 'A golden\nclockwork bird', gold_big=True),
    card(4.0, (465, 870, 480), (465, 850, 400), 'bottom', 'The engineer inside',
         'ML pipeline architecture\nPython backend\nCrawling & data analysis', big_size=76),
    card(3.0, (465, 880, 520), (455, 1000, 560), 'top', 'How I work', 'Meticulous\nand structured'),
    card(4.2, (340, 880, 540), (590, 880, 540), 'bottom', 'Between cold tech and warm heart',
         'Code, data, algorithms\nand\nboard games, interiors,\nwarm leadership', big_size=62),
    card(4.2, (460, 930, 760), (460, 930, 640), 'top', 'Why a mechanical bird?',
         'Weaving scattered data\ninto one flow is like\nan automaton, where gears\nmesh and come alive', big_size=62),
    card(3.6, (465, 850, 460), (605, 880, 520), 'bottom', 'Gears: precise systems', 'Feathers:\nwarmth that\nholds people', gold_big=False),
    card(3.4, (455, 1060, 440), (455, 1045, 380), 'top', 'The beauty of contrast', 'Portrait of a\nthoughtful architect', big_size=96, gold_big=True),
    card(4.4, (455, 820, 820), (448, 600, 1100), 'top', 'If you looked into the water,', 'what would\nyou see?', big_size=110),
]
t = 0.0
for c in CARDS: c['t0'] = t; t += c['dur']
TOTAL = t
XF = 0.3

def raw(c, tl):
    p = smooth(tl / c['dur'])
    k = [c['a'][j] + (c['b'][j] - c['a'][j]) * p for j in range(3)]
    return cam(*k)

def frame(T):
    i = max(j for j, c in enumerate(CARDS) if c['t0'] <= T + 1e-6)
    c = CARDS[i]; tl = T - c['t0']
    f = raw(c, tl)
    if i > 0 and tl < XF:
        f = Image.blend(raw(CARDS[i - 1], CARDS[i - 1]['dur']), f, smooth(tl / XF))
    f = f.convert('RGBA'); f.alpha_composite(SCRIM[c['where']])
    for el, cy, t0 in c['els']:
        p = ease((tl - t0) / 0.5)
        if p <= 0: continue
        im = el
        if p < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
        f.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy - im.height / 2 + (1 - p) * 30)))
    f = f.convert('RGB')
    a = min(1.0, T / 0.3, (TOTAL - T) / 0.7)
    if a < 1: f = Image.blend(Image.new('RGB', (W, H)), f, max(0, a))
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
        m = Image.new('RGB', (216 * 5, 384 * 2))
        for k, c in enumerate(CARDS): m.paste(frame(c['t0'] + c['dur'] - 0.15).resize((216, 384)), ((k % 5) * 216, (k // 5) * 384))
        m.save('sheet_en.png'); frame(CARDS[3]['t0'] + 2).resize((540, 960)).save('gear.png'); sys.exit(0)
    names = []
    for i, c in enumerate(CARDS):
        render(f'e{i}', c['t0'], c['t0'] + c['dur']); names.append(f'e{i}')
    open('list_en.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in names))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list_en.txt', '-c', 'copy', 'silent_en.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent_en.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', 'mirror_reel_en.mp4'], check=True)
    frame(CARDS[0]['t0'] + CARDS[0]['dur'] - 0.1).save('cover_mirror_en.jpg', quality=93)
    print('done', TOTAL)
