"""요즘 먹고 다닌 것들 — reel builder (EP.1 layout, no fade-in at frame 0).

Usage:
  python3 make.py p        # preview contact sheet (sheet.png)
  python3 make.py          # render food_epN_reel.mp4 + food_epN_cover.jpg
Edit EP / CARDS / COVER_SRC below for each episode.
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
W, H, FPS = 1080, 1920, 30

# ---------------- episode data ----------------
EP = 'EP.2'
OUT = 'food_ep' + EP.split('.')[1]   # file names: food_ep2_reel.mp4 / food_ep2_cover.jpg
COVER_SRC = 'photos/01.jpg'
CARDS = [  # (photo, place tag, KR title, EN title, KR comment, EN comment, crop x-center 0..1)
    ('photos/01.jpg', '숯불에 구운 무한 족발', '숯불구이 족발', 'Charcoal-Grilled Jokbal',
     '보드게임 후 뒤풀이는 소중하지!', 'Post-board-game hangouts are precious!', 0.45),
    ('photos/02.jpg', '역할맥', '치즈라볶이 범벅세트', 'Cheese Rabokki & Fried Combo',
     '갑작스런 의리 모임', 'A last-minute hangout with my ride-or-dies.', 0.52),
    ('photos/03.jpg', '역할맥', '석관동 닭떡볶이', 'Seokgwan-dong Chicken Tteokbokki',
     '의외로 맛있어서 흡입한 메뉴', 'Surprisingly good. Totally inhaled it.', 0.5),
    ('photos/04.jpg', '형제애', '탕수육', 'Sweet & Sour Pork',
     '재료가 신선하고 모든 메뉴가 맛있다.', 'Fresh ingredients, and every dish is good.', 0.5),
    ('photos/05.jpg', 'At Home', '에비스 맥주', 'Yebisu Beer',
     '혼술하고 싶던 날', 'One of those nights for drinking solo.', 0.5),
    ('photos/06.jpg', '한강 피크닉', '퀘사디아 · 과일', 'Quesadilla · Fruit',
     '낮부터 저녁까지 먹고 마시고', 'Eating and drinking from noon till evening.', 0.35),
    ('photos/07.jpg', '한강 피크닉', '맥주 · 와인', 'Beer · Wine',
     '주종을 가리지 않고 섞어 마시는데 안 취함', "Mixed every kind of drink and still didn't get drunk.", 0.5),
    ('photos/08.jpg', '한강 피크닉', '초콜릿 맥주', 'Chocolate Beer',
     '귀한 술도 마셔 보고', 'Even got to try a rare bottle.', 0.52),
    ('photos/09.jpg', '한강 피크닉', '꼬마김밥 · 떡볶이 · 순대', 'Mini Gimbap · Tteokbokki · Sundae',
     '빠질 수 없는 K-food 안주', "The K-food snacks you just can't skip.", 0.45),
    ('photos/10.jpg', '성내동', '새우 소금구이', 'Salt-Grilled Shrimp',
     '해장한다고 나갔더니 또 술을 마시네?', 'Went out to cure a hangover... and drank again?', 0.5),
]

# ---------------- style (measured from EP.1) ----------------
NOTO = '/usr/share/fonts/opentype/noto/NotoSansCJK-{}.ttc'
def font(w, s): return ImageFont.truetype(NOTO.format(w), int(s), index=1)  # KR face

GOLD = (246, 221, 161)
WHITE = (250, 248, 245)
GREY = (216, 211, 205)
PILL = (252, 204, 91)
X0 = 86
COVER_DUR, CARD_DUR, XFADE, END_FADE = 2.5, 3.0, 0.5, 0.6


def tracked(draw, xy, text, f, fill, track):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + track
    return x


def tracked_width(text, f, track):
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    return sum(d.textlength(ch, font=f) for ch in text) + track * (len(text) - 1)


def wrap(text, f, maxw):
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    out = []
    for para in text.split('\n'):
        words, line = para.split(' '), ''
        for w_ in words:
            t = (line + ' ' + w_).strip()
            if d.textlength(t, font=f) <= maxw or not line:
                line = t
            else:
                out.append(line); line = w_
        out.append(line)
    return out


def fill_crop(path, cx=0.5, cy=0.5, scale=1.12):
    """Cover-crop photo to a canvas `scale` times the frame (room for slow zoom)."""
    src = Image.open(path).convert('RGB')
    bw, bh = int(W * scale), int(H * scale)
    r = max(bw / src.width, bh / src.height)
    im = src.resize((int(src.width * r + 0.5), int(src.height * r + 0.5)), Image.LANCZOS)
    x = int(min(max(cx * im.width - bw / 2, 0), im.width - bw))
    y = int(min(max(cy * im.height - bh / 2, 0), im.height - bh))
    return im.crop((x, y, x + bw, y + bh))


def zoom_frame(base, z):
    """z in [0,1]: slow push-in, 0 = full base canvas, 1 = 6% tighter."""
    cw, ch = base.width / (1 + 0.06 * z), base.height / (1 + 0.06 * z)
    x0, y0 = (base.width - cw) / 2, (base.height - ch) / 2
    return base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def card_shade():
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H)[:, None] / H
    a += np.clip((ys - 0.40) / 0.32, 0, 1) ** 1.3 * 0.86   # bottom gradient
    a += 0.10                                                # overall dim
    a = np.clip(a, 0, 0.92)
    img = Image.new('RGBA', (W, H), (14, 11, 9, 0))
    img.putalpha(Image.fromarray((a * 255).astype(np.uint8)).resize((W, H)))
    return img


def card_text(i, n, place, kr, en, ckr, cen):
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    lab = font('Bold', 35)
    tracked(d, (X0, 1047), f'{i:02d} / {n:02d}', lab, GOLD, 3.2)
    xw = tracked_width(f'{i:02d} / {n:02d}', lab, 3.2)
    tracked(d, (X0 + xw + 34, 1047), place.upper(), lab, GOLD, 3.2)
    ft = font('Bold', 73)
    d.text((X0 - 2, 1094), kr, font=ft, fill=WHITE)
    d.text((X0, 1178), en, font=font('Regular', 41), fill=GOLD)
    d.rounded_rectangle([X0 - 1, 1245, X0 + 55, 1249], radius=2, fill=(230, 224, 219))
    fk, fe = font('Medium', 44), font('Light', 36)
    y = 1270
    for ln in wrap(ckr, fk, 900):
        d.text((X0, y), ln, font=fk, fill=WHITE); y += 62
    y += 8
    for ln in wrap(cen, fe, 900):
        d.text((X0, y), ln, font=fe, fill=GREY); y += 48
    return t


def cover_layers():
    base = fill_crop(COVER_SRC, 0.5, 0.5, 1.0).filter(ImageFilter.GaussianBlur(26))
    dim = Image.new('RGBA', (W, H), (12, 10, 8, 112))
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    pf = font('Black', 44)
    pw = d.textlength(EP, font=pf) + 86
    d.rounded_rectangle([(W - pw) / 2, 600, (W + pw) / 2, 668], radius=34, fill=PILL)
    d.text((W / 2, 634), EP, font=pf, fill=(60, 40, 10), anchor='mm')
    tf = font('Bold', 122)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    for (txt, y) in (('요즘', 807), ('먹고 다닌 것들', 947)):
        ds.text((W / 2, y + 4), txt, font=tf, fill=(0, 0, 0, 120), anchor='mm')
        d.text((W / 2, y), txt, font=tf, fill=(253, 252, 250), anchor='mm')
    sf, tr = font('Bold', 38), 6.5
    sub = "WHAT I'VE BEEN EATING LATELY"
    sw = tracked_width(sub, sf, tr)
    tracked(d, ((W - sw) / 2, 1040), sub, sf, GOLD, tr)
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    img = base.convert('RGBA'); img.alpha_composite(dim); img.alpha_composite(sh); img.alpha_composite(t)
    return img.convert('RGB')


def ease(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3


def build():
    n = len(CARDS)
    shade = card_shade()
    cover = cover_layers()
    cards = []
    for i, (p, place, kr, en, ckr, cen, cx) in enumerate(CARDS, 1):
        cards.append((fill_crop(p, cx, 0.5, 1.06), card_text(i, n, place, kr, en, ckr, cen)))
    starts = [COVER_DUR + k * CARD_DUR for k in range(n)]
    total = starts[-1] + CARD_DUR + 0.4

    def card_at(k, t):
        base, txt = cards[k]
        lt = t - starts[k]
        f = zoom_frame(base, min(max(lt / (CARD_DUR + XFADE), 0), 1)).convert('RGBA')
        f.alpha_composite(shade)
        p = ease((lt - 0.15) / 0.55)
        if p > 0:
            tl = txt.copy()
            if p < 1:
                tl.putalpha(tl.getchannel('A').point(lambda v: int(v * p)))
            f.alpha_composite(tl, (0, int(28 * (1 - p))))
        return f.convert('RGB')

    def frame(t):
        if t < COVER_DUR:
            img = cover
        else:
            k = min(int((t - COVER_DUR) // CARD_DUR), n - 1)
            img = card_at(k, t)
        # crossfade into next segment
        nxt = None
        for k, s in enumerate(starts):
            if s - XFADE <= t < s:
                nxt = k; break
        if nxt is not None:
            a = (t - (starts[nxt] - XFADE)) / XFADE
            img = Image.blend(img, card_at(nxt, starts[nxt]), a)
        if t > total - END_FADE:
            a = (t - (total - END_FADE)) / END_FADE
            img = Image.blend(img, Image.new('RGB', (W, H)), min(a, 1) * 0.85)
        return img
    return frame, total, starts, cover


if __name__ == '__main__':
    frame, total, starts, cover = build()
    if len(sys.argv) > 1 and sys.argv[1] == 'p':
        ts = [0.0] + [s + 1.5 for s in starts]
        cols = 6; tw, th = 270, 480
        rows = (len(ts) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * tw, rows * th), 'white')
        for j, t in enumerate(ts):
            sheet.paste(frame(t).resize((tw, th)), ((j % cols) * tw, (j // cols) * th))
        sheet.save('sheet.png')
        for j in (1,):
            frame(starts[0] + 1.5).save('card_full.png')
        print('total', round(total, 2))
        sys.exit()
    cover.save(OUT + '_cover.jpg', quality=92)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                          '-map', '0:v', '-map', '1:a', '-shortest',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-movflags', '+faststart', OUT + '_reel.mp4'], stdin=subprocess.PIPE)
    nf = int(total * FPS)
    for fi in range(nf):
        p.stdin.write(frame(fi / FPS).tobytes())
    p.stdin.close(); p.wait()
    print('done', nf / FPS)
