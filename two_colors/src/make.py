import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

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
def crop(box, w):
    c = SRC.crop(box)
    c = c.resize((w, round(c.height * w / c.width)), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))

def rounded(im, r=40, border=None):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=r, fill=255)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    if border: ImageDraw.Draw(out).rounded_rectangle([1, 1, im.width - 2, im.height - 2], radius=r, outline=border, width=5)
    return out

def text_el(txt, font, fill, spacing=14, align='center', glow=None):
    b = ImageDraw.Draw(Image.new('L', (1, 1))).multiline_textbbox((0, 0), txt, font=font, spacing=spacing, align=align)
    b = [int(math.ceil(v)) for v in b]
    pad = 40
    im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0))
    o = (pad - b[0], pad - b[1])
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).multiline_text(o, txt, font=font, fill=glow, spacing=spacing, align=align, stroke_width=6, stroke_fill=glow)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(im).multiline_text(o, txt, font=font, fill=fill, spacing=spacing, align=align)
    return im

def pill(txt, bg, fg, font, padx=34, pady=16, outline=None):
    t = text_el(txt, font, fg)
    im = Image.new('RGBA', (t.width - 80 + padx * 2, t.height - 80 + pady * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg, outline=outline, width=3 if outline else 0)
    im.alpha_composite(t, (padx - 40, pady - 40))
    return im

def row(items, gap=16):
    w = sum(i.width for i in items) + gap * (len(items) - 1); h = max(i.height for i in items)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); x = 0
    for i in items: im.alpha_composite(i, (x, (h - i.height) // 2)); x += i.width + gap
    return im

def swatch(hexcol, col, fg):
    sw = Image.new('RGBA', (130, 80), (0, 0, 0, 0))
    ImageDraw.Draw(sw).rounded_rectangle([0, 0, 129, 79], radius=16, fill=col, outline=(255, 255, 255, 200), width=3)
    return row([sw, text_el(hexcol, nun(800, 54), fg)], gap=6)

def reasons(lines, accent, fg):
    f = dodum(48)
    rows = []
    for ln in lines:
        ck = Image.new('RGBA', (60, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(ck)
        d.ellipse([4, 4, 56, 56], fill=accent)
        d.line([(17, 31), (27, 41), (44, 20)], fill=(255, 255, 255), width=7, joint='curve')
        rows.append(row([ck, text_el(ln, f, fg, align='left')], gap=0))
    w = max(r.width for r in rows); h = sum(r.height for r in rows) - 30 * (len(rows) - 1)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); y = 0
    for r in rows: im.alpha_composite(r, (0, y)); y += r.height - 30
    return im

def summary_box(txt, accent, bgcol, fg):
    lab = text_el('한 줄 요약', jua(40), accent)
    t = text_el(txt, jua(58), fg, spacing=12)
    w = max(t.width, 860); h = lab.height + t.height - 50
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([20, 20, w - 21, h - 21], radius=30, fill=bgcol, outline=accent, width=4)
    im.alpha_composite(lab, ((w - lab.width) // 2, 10)); im.alpha_composite(t, ((w - t.width) // 2, lab.height - 60))
    return im

# ---------------- backgrounds ----------------
def bg_from(box, tint, dark=0.55):
    b = SRC.crop(box).resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(26))
    b = ImageEnhance.Brightness(b).enhance(1 - dark)
    return Image.blend(b, Image.new('RGB', (W, H), tint), 0.25)

BLUE_BG = bg_from((0, 0, 700, 941), (10, 20, 60))
PINK_BG = bg_from((1000, 0, 1672, 941), (70, 20, 40), dark=0.5)
MID_BG = bg_from((400, 0, 1280, 941), (30, 20, 50), dark=0.5)

GOLD = (240, 205, 130, 255)
BLUE_A, PINK_A = (110, 160, 255, 255), (240, 130, 175, 255)

# ---------------- sections: (bg, [ (element, cx, cy, t0, kind) ]) ----------------
def sec_title():
    art = rounded(crop((560, 95, 1180, 760), 920), 40, GOLD)
    return MID_BG, [
        (text_el('나를 표현하는', jua(84), (255, 245, 225), glow=(0, 0, 0, 200)), 540, 300, 0.1, 'up'),
        (text_el('두 가지 색', jua(150), GOLD, glow=(0, 0, 0, 220)), 540, 420, 0.3, 'up'),
        (art, 540, 1110, 0.5, 'up'),
        (text_el('딥 블루  &  로즈 핑크', jua(58), (255, 255, 255), glow=(0, 0, 0, 220)), 540, 1660, 1.0, 'up'),
    ]

def sec_color(label, ko, en, hexcol, col, chips, artbox, accent, bg, kofill):
    c = SRC.crop(artbox); aw = min(880, int(900 * c.width / c.height))
    art = rounded(crop(artbox, aw), 40, accent); ah = art.height
    chip_row = row([pill(c, (0, 0, 0, 120), (255, 255, 255), jua(42), outline=accent) for c in chips], gap=14)
    return bg, [
        (pill(label, (0, 0, 0, 150), GOLD[:3], jua(42), outline=GOLD), 540, 200, 0.05, 'up'),
        (text_el(ko, jua(170), kofill, glow=accent[:3] + (160,)), 540, 350, 0.25, 'pop'),
        (text_el(en, nun(700, 62, True), (240, 240, 255)), 540, 470, 0.45, 'up'),
        (swatch(hexcol, col, (255, 255, 255)), 540, 570, 0.6, 'up'),
        (art, 540, 680 + ah / 2, 0.7, 'up'),
        (chip_row, 540, 680 + ah + 80, 1.1, 'up'),
    ]

def sec_reason(head_col, lines, summ, accent, bg, box_bg):
    head = text_el('- 선정 이유 -', jua(70), (255, 255, 255))
    rs = reasons(lines, accent, (250, 245, 240)); sb = summary_box(summ, accent[:3], box_bg, (255, 255, 255))
    return bg, [
        (text_el(head_col, jua(62), accent[:3], glow=(0, 0, 0, 200)), 540, 380, 0.05, 'up'),
        (head, 540, 500, 0.2, 'up'),
        (rs, 540, 580 + rs.height / 2, 0.4, 'up'),
        (sb, 540, 580 + rs.height + 40 + sb.height / 2, 1.2, 'pop'),
    ]

def sec_final():
    full = rounded(SRC.resize((1000, round(941 * 1000 / 1672)), Image.LANCZOS), 30, GOLD)
    return MID_BG, [
        (full, 540, 500, 0.05, 'up'),
        (text_el('차가운 머리로\n세상을 분석하고,', gaegu(96), (190, 210, 255), glow=(0, 0, 0, 220)), 540, 1000, 0.5, 'up'),
        (text_el('뜨거운 마음으로\n오늘을 살아가는 사람.', gaegu(96), (255, 190, 215), glow=(0, 0, 0, 220)), 540, 1240, 0.9, 'up'),
        (text_el('그래서, 나는', jua(64), (255, 245, 225), glow=(0, 0, 0, 200)), 540, 1450, 1.5, 'up'),
        (row([text_el('블루', jua(110), BLUE_A[:3], glow=(0, 0, 0, 200)), text_el('와', jua(64), (255, 245, 225)),
              text_el('핑크', jua(110), PINK_A[:3], glow=(0, 0, 0, 200))], gap=-40), 540, 1570, 1.8, 'pop'),
        (text_el('사이에 있어요', jua(64), (255, 245, 225), glow=(0, 0, 0, 200)), 540, 1700, 2.1, 'up'),
    ]

SECTIONS = [
    (sec_title(), 3.0),
    (sec_color('나에게 가장 잘 어울리는 색', '딥 블루', 'Deep Blue', '#0B2D6B', (11, 45, 107, 255),
               ['차분함', '지적인', '신뢰감', '세련됨'], (430, 110, 930, 750), BLUE_A, BLUE_BG, (170, 200, 255)), 3.4),
    (sec_reason('딥 블루를 고른 이유',
                ['복잡한 상황에서도\n침착하게 중심을 잡아요', '지적인 호기심과 분석력으로\n문제를 해결해요',
                 '성실하고 책임감 있는\n모습이 매력적이에요', '쿨해 보이지만,\n속은 따뜻한 반전이 있어요'],
                '차분한 지성과\n단단한 신뢰를 가진 사람!', BLUE_A, BLUE_BG, (10, 30, 80, 220)), 4.2),
    (sec_color('나를 가장 잘 표현하는 색', '로즈 핑크', 'Rose Pink', '#E07BA6', (224, 123, 166, 255),
               ['다정함', '열정적', '유쾌함', '창의적'], (930, 230, 1245, 745), PINK_A, PINK_BG, (255, 190, 215)), 3.4),
    (sec_reason('로즈 핑크를 고른 이유',
                ['작은 행복에도\n진심으로 기뻐해요', '좋아하는 것에 몰입하는\n열정이 강해요',
                 '솔직하고 수다스러운\n매력이 있어요', '지치고 힘든 순간에도\n다시 일어서는 힘이 있어요'],
                '언제나 다시 웃는,\n포기하지 않는 사람!', PINK_A, PINK_BG, (90, 20, 50, 220)), 4.2),
    (sec_final(), 4.4),
]

GAP = 0
SCR = 0.7
strip_secs = []
t = 0.0
for i, ((bg, els), hold) in enumerate(SECTIONS):
    strip_secs.append(dict(bg=bg, els=els, arrive=t, hold=hold, y=i * H))
    t += hold + (SCR if i < len(SECTIONS) - 1 else 0)
TOTAL = t

def cam(T):
    for i, s in enumerate(strip_secs):
        if T < s['arrive'] + s['hold'] or i == len(strip_secs) - 1: return s['y']
        if T < s['arrive'] + s['hold'] + SCR:
            return s['y'] + H * inout((T - s['arrive'] - s['hold']) / SCR)
    return strip_secs[-1]['y']

def draw_sec(s, T, oy, f):
    f.paste(s['bg'], (0, oy))
    tl = T - s['arrive']
    for el, cx, cy, t0, kind in s['els']:
        p = ease((tl - t0) / 0.5)
        if p <= 0: continue
        im = el
        if kind == 'pop' and p < 1:
            sc = 0.8 + 0.2 * p
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
        if p < 1:
            im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
        dy = (1 - p) * 40 if kind == 'up' else 0
        f.alpha_composite(im, (int(cx - im.width / 2), int(oy + cy - im.height / 2 + dy)))

def frame(T):
    y = cam(T)
    f = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for s in strip_secs:
        oy = int(round(s['y'] - y))
        if -H < oy < H:
            draw_sec(s, max(T, s['arrive']) if oy != 0 else T, oy, f)
    a = min(1.0, T / 0.3, (TOTAL - T) / 0.6)
    f = f.convert('RGB')
    if a < 1: f = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), f, max(0, a))
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
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        shots = [s['arrive'] + s['hold'] - 0.05 for s in strip_secs[:-1]] + [strip_secs[-1]['arrive'] + 3.2]
        m = Image.new('RGB', (270 * 6, 480))
        for k, T in enumerate(shots): m.paste(frame(T).resize((270, 480)), (k * 270, 0))
        m.save('sheet.png'); frame(shots[2]).resize((540, 960)).save('r.png'); sys.exit(0)
    names = []
    for i, s in enumerate(strip_secs):
        T1 = strip_secs[i + 1]['arrive'] if i + 1 < len(strip_secs) else TOTAL
        render(f's{i}', s['arrive'], T1); names.append(f's{i}')
    open('list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in names))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', 'two_colors_reel.mp4'], check=True)
    SECTIONS_cover = frame(strip_secs[0]['hold'] - 0.1); SECTIONS_cover.save('cover_two_colors.jpg', quality=93)
    print('done', TOTAL)
