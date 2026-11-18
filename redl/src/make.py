import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
BW, BH = 1188, 2112
def jua(s): return ImageFont.truetype('fonts/jua.ttf', int(s))
def dodum(s): return ImageFont.truetype('fonts/gowun-dodum.ttf', int(s))
def nun(w, s, it=False): return ImageFont.truetype(f"fonts/nunito-latin-{w}-{'italic' if it else 'normal'}.ttf", int(s))
def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

GOLD_OLD, WHITE, CREAM = (245, 190, 100), (255, 255, 255), (255, 236, 210)

def full_bleed(fn, cx=0.5, dark=0.5, blur=0):
    im = Image.open(fn).convert('RGB')
    w, h = im.size; tw = int(h * BW / BH)
    if tw <= w:
        x0 = int(max(0, min(w - tw, cx * w - tw / 2))); im = im.crop((x0, 0, x0 + tw, h))
    im = im.resize((BW, BH), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return ImageEnhance.Brightness(im).enhance(1 - dark)

def text_el(txt, font, fill, spacing=18, shadow=True, align='center'):
    b = ImageDraw.Draw(Image.new('L', (1, 1))).multiline_textbbox((0, 0), txt, font=font, spacing=spacing, align=align)
    b = [int(math.ceil(v)) for v in b]; pad = 40
    im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), (0, 0, 0, 0))
    o = (pad - b[0], pad - b[1])
    if shadow:
        s = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(s).multiline_text(o, txt, font=font, fill=(0, 0, 0, 220), spacing=spacing, align=align, stroke_width=5, stroke_fill=(0, 0, 0, 220))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).multiline_text(o, txt, font=font, fill=fill, spacing=spacing, align=align)
    return im

def pill(txt, bg, fg, font, padx=30, pady=12):
    t = text_el(txt, font, fg, shadow=False)
    im = Image.new('RGBA', (t.width - 80 + padx * 2, t.height - 80 + pady * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg)
    im.alpha_composite(t, (padx - 40, pady - 40)); return im

def info_table(rows):
    lab_f, val_f = jua(46), dodum(46)
    lw = 230; rh = 92; w = 900
    im = Image.new('RGBA', (w, rh * len(rows) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, im.height - 1], radius=30, fill=(20, 14, 10, 200), outline=GOLD + (255,), width=3)
    for i, (k, v) in enumerate(rows):
        y = 10 + i * rh + rh / 2
        d.text((50, y), k, font=lab_f, fill=GOLD, anchor='lm')
        d.text((50 + lw, y), v, font=val_f, fill=WHITE, anchor='lm')
        if i: d.line([(40, 10 + i * rh), (w - 40, 10 + i * rh)], fill=(255, 255, 255, 50), width=2)
    return im

def bullets(items):
    f = dodum(44); rows = []
    for t in items:
        r = text_el(t, f, WHITE, spacing=12, shadow=False, align='left')
        dot = Image.new('RGBA', (50, 50), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([16, 16, 34, 34], fill=GOLD + (255,))
        row = Image.new('RGBA', (r.width + 40, r.height), (0, 0, 0, 0)); row.alpha_composite(dot, (0, 40)); row.alpha_composite(r, (30, 0))
        rows.append(row)
    w = 920; h = sum(r.height for r in rows) - 50 * (len(rows) - 1) + 60
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=(20, 14, 10, 200), outline=GOLD + (255,), width=3)
    y = 10
    for r in rows: im.alpha_composite(r, (30, y)); y += r.height - 50
    return im

def counter(i, n): return pill(f'{i} / {n}', (0, 0, 0, 150), WHITE, nun(800, 32))

BOX = Image.open('box.jpg').convert('RGB')
N = 6
GOLD = (255, 110, 150)

def cover():
    bg = full_bleed('box.jpg', dark=0.6, blur=30)
    art = BOX.crop((380, 100, 1560, 1860)); art = art.resize((760, int(760 * art.height / art.width)), Image.LANCZOS)
    m = Image.new('L', art.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, art.width - 1, art.height - 1], radius=30, fill=255)
    a = Image.new('RGBA', art.size, (0, 0, 0, 0)); a.paste(art, (0, 0), m)
    ImageDraw.Draw(a).rounded_rectangle([1, 1, art.width - 2, art.height - 2], radius=30, outline=GOLD + (255,), width=5)
    return bg, [
        (pill('머더 미스터리 후기 (스포 없음)', (150, 20, 60, 255), WHITE, jua(44)), 540, 250, -1, 'none'),
        (text_el('더 레드 래프터', jua(116), WHITE), 540, 380, -1, 'none'),
        (a, 540, 1030, 0.15, 'up'),
        (text_el('범인을 찾아도\n끝이 아니다', jua(76), GOLD, spacing=14), 540, 1700, 0.5, 'pop'),
    ]

def story(fn, cx, i, small, big, big_col=WHITE, cy=960, blur=0):
    return full_bleed(fn, cx=cx, dark=0.6, blur=blur), [
        (counter(i, N), 540, 230, 0.0, 'none'),
        (text_el(small, jua(66), CREAM, spacing=20), 540, cy - 140, 0.1, 'up'),
        (text_el(big, jua(118), big_col, spacing=20), 540, cy + 80, 0.45, 'pop'),
    ]

SCENES = [
    (cover(), 3.0),
    (story('sheets.jpg', 0.45, 1, '6명이 모인 밤', '현대\n오컬트 호러', blur=6), 2.6),
    (story('sheets.jpg', 0.55, 2, '과거와 현재를 잇는 시나리오는', '다소\n평범했지만...', blur=6), 2.8),
    (story('box.jpg', 0.5, 3, '마지막에 나온 기믹이', '신선했다', GOLD, blur=4), 2.6),
    (story('box.jpg', 0.5, 4, '처음 해 보는\n엔딩 결정 조건에', '도파민\n터짐', GOLD, blur=4), 3.0),
    (story('sheets.jpg', 0.5, 5, '범인은 생각보다 빨리 찾았는데', '그게 다가\n아닌 게임', blur=6), 3.0),
    ((full_bleed('box.jpg', dark=0.65, blur=24), [
        (counter(6, N), 540, 230, 0.0, 'none'),
        (text_el('해 본 사람만 아는\n그 엔딩', jua(96), WHITE, spacing=20), 540, 820, 0.1, 'up'),
        (text_el('댓글로 스포 금지!', jua(112), GOLD), 540, 1100, 0.6, 'pop'),
        (text_el('#레드래프터 #머더미스터리', jua(52), CREAM), 540, 1300, 1.0, 'up'),
    ]), 3.6),
]

SEC = []; t = 0.0
for (bg, els), hold in SCENES: SEC.append(dict(bg=bg, els=els, t0=t, dur=hold)); t += hold
TOTAL = t
FADE = 0.25

def render_sec(s, idx):
    tmp = f'c{idx}.tmp.mp4'
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    n = int(round(s['dur'] * FPS))
    for k in range(n):
        pr.stdin.write(frame_sec(s, k / FPS, idx).tobytes())
    pr.stdin.close()
    if pr.wait() != 0: sys.exit(1)
    os.replace(tmp, f'c{idx}.mp4')

def frame_sec(s, t, idx):
    z = 1.0 + 0.05 * (t / s['dur'])
    cw, ch = int(W * 1.1 / z), int(H * 1.1 / z)
    x0, y0 = (BW - cw) // 2, (BH - ch) // 2
    f = s['bg'].crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert('RGBA')
    for el, cx, cy, t0, kind in s['els']:
        p = 1.0 if kind == 'none' else ease((t - t0) / 0.45)
        if p <= 0: continue
        im = el
        if kind == 'pop' and p < 1:
            sc = 0.85 + 0.15 * p; im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
        if p < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
        dy = (1 - p) * 40 if kind == 'up' else 0
        f.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))
    f = f.convert('RGB')
    a = min(1.0, t / FADE) if idx > 0 else min(1.0, t / 0.3)
    if idx == len(SEC) - 1: a = min(a, (s['dur'] - t) / 0.6)
    if a < 1: f = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), f, max(0, a))
    return f

if __name__ == '__main__':
    if len(sys.argv) > 1:
        m = Image.new('RGB', (216 * 5, 384 * 2))
        for k, s in enumerate(SEC): m.paste(frame_sec(s, s['dur'] - 0.1, -1).resize((216, 384)), ((k % 5) * 216, (k // 5) * 384))
        m.save('sheet.png'); sys.exit(0)
    for i, s in enumerate(SEC):
        if len(sys.argv) < 2 or True: render_sec(s, i) if (os.environ.get('ONLY') is None or str(i) in os.environ['ONLY'].split(',')) else None
    open('list.txt', 'w').write(''.join(f"file 'c{i}.mp4'\n" for i in range(len(SEC))))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', 'redl_reel.mp4'], check=True)
    frame_sec(SEC[0], SEC[0]['dur'] - 0.1, -1).save('cover_redl.jpg', quality=93)
    print('done', TOTAL)
