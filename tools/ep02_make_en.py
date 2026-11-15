"""EP.2 English version: cover the Korean captions with a caption card and redraw them in English."""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SRC = '/home/claude/reels/ep02/reel.mp4'
FD = '/home/claude/onewordc/fonts/'
def nun(w, s, it=False): return ImageFont.truetype(FD + f"nunito-latin-{w}-{'italic' if it else 'normal'}.ttf", int(s))

INK, RED, NOTE = (58, 38, 28), (214, 40, 40), (90, 110, 170)
PAPER = (252, 244, 230)

SHOTS = [
    (2.2, ["What more do you want", "from minimum wage?"], "Things I heard in week 2 of my part-time job", "hook"),
    (2.2, ["Just figure it out yourself."], None, "line"),
    (2.6, ["Are you just gonna", "stand there and watch?"], "(I'm literally still learning...)", "line"),
    (2.2, ["Go find something to do."], None, "line"),
    (2.4, ["Are you only ever gonna", "do what you're told?"], None, "line"),
    (2.4, ["Do I have to explain", "every single thing?"], None, "line"),
    (3.0, ["Two whole weeks and you're", "still making mistakes... sigh"], None, "line"),
    (2.6, ["HEY! WIPE THIS!", "WIPE IT ALL!"], None, "slam"),
    (2.4, ["So what do you think", "you should be doing now?"], None, "line"),
    (3.4, ["Have a good evening~"], "(Boss worked 1 hour, ignored me, left)", "line"),
]

CARD = (40, 110, 1040, 640)
mask = Image.new('L', (W, H), 0)
ImageDraw.Draw(mask).rounded_rectangle(CARD, radius=48, fill=255)
shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle((CARD[0], CARD[1] + 12, CARD[2], CARD[3] + 12), radius=48, fill=(90, 60, 40, 70))
shadow = shadow.filter(ImageFilter.GaussianBlur(14))

def fit(d, lines, size, maxw=900, w='800', it=False):
    while size > 30 and max(d.textlength(l, font=nun(w, size, it)) for l in lines) > maxw: size -= 3
    return size

def draw(im, t, sec, lines, note, style, idx):
    im = im.convert('RGBA'); im.alpha_composite(shadow); im = im.convert('RGB')
    im.paste(Image.new('RGB', (W, H), PAPER), (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(CARD, radius=48, outline=(230, 214, 190), width=4)
    dur = 0.12 if style == 'slam' else 0.18
    pop = 1.0
    if t < dur:
        st = 1.35 if style == 'slam' else 1.2
        pop = st + (1 - st) * (t / dur)
    base = 104 if style == 'slam' else (86 if style == 'hook' else 78)
    size = fit(d, lines, base)
    size_p = int(size * pop)
    col = RED if style == 'slam' else INK
    n = len(lines) + (1 if note else 0)
    block = len(lines) * size * 1.22 + (60 if note else 0)
    y = (CARD[1] + 70 + CARD[3]) / 2 - block / 2 + (20 if style != 'hook' else 0)
    for ln in lines:
        f = nun('800', size_p)
        d.text((W / 2, y + size / 2), ln, font=f, fill=col, anchor='mm')
        y += size * 1.22
    if note and t > 0.35:
        fs = fit(d, [note], 44, 900, '700', True)
        d.text((W / 2, y + 30), note, font=nun('700', fs, True), fill=(200, 80, 60) if style == 'hook' else NOTE, anchor='mm')
    if style != 'hook':
        tag = f'DIG #{idx}/9'
        f = nun('800', 40); w = d.textlength(tag, font=f)
        d.rounded_rectangle(((W - w) / 2 - 28, CARD[1] + 30, (W + w) / 2 + 28, CARD[1] + 92), 31, fill=INK)
        d.text((W / 2, CARD[1] + 61), tag, font=f, fill=(255, 255, 255), anchor='mm')
    return im

if __name__ == '__main__':
    preview = len(sys.argv) > 1
    total = sum(s[0] for s in SHOTS)
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    out = None if preview else subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-i', SRC, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
         '-c:a', 'copy', '-movflags', '+faststart', '-shortest', 'reel_en.tmp.mp4'], stdin=subprocess.PIPE)
    starts, acc = [], 0
    for s in SHOTS: starts.append(acc); acc += s[0]
    k = 0; shots_prev = []
    while True:
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        T = k / FPS
        i = max(j for j in range(len(SHOTS)) if starts[j] <= T + 1e-6)
        sec, lines, note, style = SHOTS[i]
        idx = sum(1 for s in SHOTS[:i + 1] if s[3] != 'hook')
        fr = draw(Image.frombytes('RGB', (W, H), raw), T - starts[i], sec, lines, note, style, idx)
        if preview:
            if abs(T - (starts[i] + sec - 0.3)) < 0.5 / FPS: shots_prev.append(fr.resize((216, 384)))
        else:
            out.stdin.write(fr.tobytes())
        k += 1
    if preview:
        m = Image.new('RGB', (216 * 5, 384 * 2))
        for j, p in enumerate(shots_prev): m.paste(p, ((j % 5) * 216, (j // 5) * 384))
        m.save('prev.png')
    else:
        out.stdin.close(); out.wait()
        import os; os.replace('reel_en.tmp.mp4', 'reel_en.mp4')
    print('frames', k)
