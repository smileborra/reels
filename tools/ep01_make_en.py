"""EP.1 English: re-letter speech bubbles over the published reel."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
SRC = '/home/claude/reels/ep01/reel.mp4'
FD = '/home/claude/onewordc/fonts/'
def hand(s): return ImageFont.truetype('/home/claude/reel/fonts/gaegu.ttf', int(s))
def nun(s): return ImageFont.truetype(FD + 'nunito-latin-800-normal.ttf', int(s))
INK = (40, 32, 30)

SERIES = [("A 15-year IT planner's", 60, (255, 255, 255)), ("Isekai'd into the Restaurant Biz · EP.1", 54, (255, 214, 102))]
HOOK = [("15-year IT planner,", 80, (255, 255, 255)), ("4 hours into a salad café shift...", 58, (255, 214, 102))]

# key, start, dur, z0, z1, top, bubbles[(ellipse box, text)], notes[(box, text)]
SHOTS = [
    ('hook', 0.0, 1.6, 1.0, 1.07, HOOK, [((20, -40, 960, 410), "Only 4 hours of work\nand my body feels\nlike it's crumbling!")], [((770, 410, 1050, 550), 'Ugh...')]),
    ('cover', 1.6, 1.8, 1.0, 1.08, [], [], []),
    ('p1', 3.4, 2.4, 1.0, 1.05, SERIES, [((-20, -30, 950, 400), "Such clean food...\nfrom such a\ndirty kitchen?!")], []),
    ('p2', 5.8, 2.4, 1.0, 1.05, SERIES, [((0, -40, 1010, 330), "Humans can work\n4 hours straight\nwithout sitting?!")], [((760, 360, 1060, 620), 'No potty\nbreaks\neither...')]),
    ('p3', 8.2, 2.4, 1.0, 1.05, SERIES, [((-20, -40, 1010, 315), "The boss vents stress\nby picking on\npart-timers?!")], [((600, 300, 1065, 500), '(Never on\nthe manager)')]),
    ('p4', 10.6, 2.4, 1.0, 1.05, SERIES, [((0, -40, 990, 340), "Sweeping hurts\nmy back THIS much?!")], [((780, 330, 1000, 450), 'Ouch...')]),
    ('p5', 13.0, 2.4, 1.0, 1.05, SERIES, [((-20, -20, 1010, 310), "Luckily, hardly any\nnightmare customers...")], []),
    ('p6', 15.4, 2.4, 1.0, 1.05, SERIES, [((0, -20, 990, 330), "The boss only has to\nwork 1 hour a day?!")], []),
    ('p7', 17.8, 2.4, 1.0, 1.05, SERIES, [((20, -40, 960, 410), "Only 4 hours of work\nand my body feels\nlike it's crumbling!")], [((770, 410, 1050, 550), 'Ugh...')]),
    ('p8', 20.2, 2.4, 1.0, 1.05, SERIES, [((0, -40, 1010, 370), "A good night's sleep\nand I'm alive again?!")], [((740, 320, 1040, 500), 'Amazing,\nas always...')]),
    ('p9', 22.6, 3.2, 1.0, 1.06, SERIES, [((-10, -20, 1070, 310), "I really want to go back\nand grind at IT like crazy.")], []),
]
COVER_TITLE = ((40, 40, 1030, 410), ["A 15-year IT planner", "isekai'd into the", "restaurant biz"], "All my stats are useless?!")

def fit_font(txt, box_w, box_h, maker, start):
    s = start
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    while s > 20:
        b = d.multiline_textbbox((0, 0), txt, font=maker(s), spacing=s * 0.15, align='center')
        if b[2] - b[0] <= box_w and b[3] - b[1] <= box_h: return maker(s)
        s -= 2
    return maker(s)

def overlay(key, bubbles, notes):
    L = Image.new('RGBA', (1080, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for (x0, y0, x1, y1), txt in bubbles:
        d.ellipse([x0, y0, x1, y1], fill=(255, 255, 255, 255), outline=INK, width=7)
        cx, cy = (x0 + x1) / 2, (max(y0, 0) + y1) / 2 + 8
        f = fit_font(txt, (x1 - x0) * 0.78, (y1 - max(y0, 0)) * 0.78, hand, 88)
        d.multiline_text((cx, cy), txt, font=f, fill=INK, anchor='mm', align='center', spacing=f.size * 0.15)
    for (x0, y0, x1, y1), txt in notes:
        d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(255, 255, 255, 255), outline=INK, width=5)
        f = fit_font(txt, (x1 - x0) * 0.85, (y1 - y0) * 0.8, hand, 72)
        d.multiline_text(((x0 + x1) / 2, (y0 + y1) / 2 + 4), txt, font=f, fill=INK, anchor='mm', align='center', spacing=f.size * 0.12)
    if key == 'cover':
        (x0, y0, x1, y1), lines, sub = COVER_TITLE
        d.rounded_rectangle([x0, y0, x1, y1], radius=40, fill=(255, 250, 240, 255), outline=INK, width=6)
        cols = [(40, 40, 60), (60, 90, 200), (220, 70, 60)]
        y = y0 + 55
        for ln, c in zip(lines, cols):
            d.text(((x0 + x1) / 2, y), ln, font=nun(66), fill=c, anchor='mm'); y += 80
        d.text(((x0 + x1) / 2, y + 10), sub, font=hand(52), fill=(90, 80, 160), anchor='mm')
    return L

def bg_band(sq):
    b = sq.resize((H, H)).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    b = b.filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(b).enhance(0.55)

PREP = []
for key, st, dur, z0, z1, top, bubbles, notes in SHOTS:
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{st + 0.02:.3f}', '-i', SRC, '-frames:v', '1', f'first_{key}.png'], check=True)
    sq = Image.open(f'first_{key}.png').convert('RGB').crop((0, 420, 1080, 1500))
    band = bg_band(sq)
    top_img = band.crop((0, 0, W, 420)).convert('RGBA')
    td = ImageDraw.Draw(top_img)
    y = 110 if len(top) > 1 else 200
    for txt, size, col in top:
        f = nun(size)
        while td.textlength(txt, font=f) > 1000: size -= 2; f = nun(size)
        td.text((W / 2, y), txt, font=f, fill=col, anchor='mt', stroke_width=9, stroke_fill=(30, 20, 20))
        y += int(size * 1.35)
    PREP.append(dict(key=key, st=st, dur=dur, z0=z0, z1=z1, top=top_img, ov=overlay(key, bubbles, notes)))

def apply(fr, T):
    s = max(p for p in PREP if p['st'] <= T + 1e-6) if False else None
    p = [q for q in PREP if q['st'] <= T + 1e-6][-1]
    n = int(round(p['dur'] * FPS)); i = int(round((T - p['st']) * FPS))
    t = i / max(n - 1, 1); t = t * t * (3 - 2 * t)
    sc = p['z0'] + (p['z1'] - p['z0']) * t
    sz = int(W * sc); off = (sz - W) // 2
    ov = p['ov'].resize((sz, sz), Image.BICUBIC).crop((off, off, off + W, off + W))
    fr = fr.convert('RGBA')
    fr.alpha_composite(p['top'], (0, 0))
    fr.alpha_composite(ov, (0, (H - W) // 2))
    return fr.convert('RGB')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        m = Image.new('RGB', (180 * 6, 320 * 2))
        for k, p in enumerate(PREP):
            fr = Image.open(f"first_{p['key']}.png").convert('RGB')
            m.paste(apply(fr, p['st'] + 0.02).resize((180, 320)), ((k % 6) * 180, (k // 6) * 320))
        m.save('prev.png')
        for k in ('cover', 'p3'):
            p = [q for q in PREP if q['key'] == k][0]
            apply(Image.open(f'first_{k}.png').convert('RGB'), p['st'] + 0.02).crop((0, 0, 1080, 1500)).resize((540, 750)).save(f'chk_{k}.png')
        sys.exit(0)
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', SRC, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                            '-c:a', 'copy', '-movflags', '+faststart', '-shortest', 'reel_en.tmp.mp4'], stdin=subprocess.PIPE)
    k = 0
    while True:
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        out.stdin.write(apply(Image.frombytes('RGB', (W, H), raw), k / FPS).tobytes()); k += 1
    out.stdin.close(); out.wait()
    os.replace('reel_en.tmp.mp4', 'reel_en.mp4')
    p = PREP[1]
    apply(Image.open('first_cover.png').convert('RGB'), p['st'] + 0.02).save('cover_en.jpg', quality=93)
    print('frames', k)
