import subprocess, sys
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SRC_AUDIO = "/mnt/user-data/uploads/1000018912.mp4"
COVER = "/mnt/user-data/uploads/15795325-image.png"

def font(size):
    return ImageFont.truetype(FONT, size, index=1)  # index 1 = KR

def bg_from(img):
    b = img.resize((H, H)).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    b = b.filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(b).enhance(0.55)

def text_center(draw, y, txt, size, fill, stroke=10):
    f = font(size)
    w = draw.textlength(txt, font=f)
    draw.text(((W - w) / 2, y), txt, font=f, fill=fill,
              stroke_width=stroke, stroke_fill=(30, 20, 20))

def compose(sq, scale, top_lines):
    """sq: square RGB image; scale: zoom factor; top_lines: [(text,size,color)]"""
    canvas = bg_from(sq).copy()
    s = int(W * scale)
    z = sq.resize((s, s), Image.BICUBIC)
    off = (s - W) // 2
    z = z.crop((off, off, off + W, off + W))
    canvas.paste(z, (0, (H - W) // 2))
    d = ImageDraw.Draw(canvas)
    y = 110 if len(top_lines) > 1 else 200
    for txt, size, col in top_lines:
        text_center(d, y, txt, size, col)
        y += int(size * 1.35)
    return canvas

cover = Image.open(COVER).convert("RGB").resize((W, W), Image.LANCZOS)
panels = [Image.open(f"p/p{i}.png").convert("RGB") for i in range(1, 10)]

SERIES = [("15년차 IT기획자의", 64, (255, 255, 255)),
          ("요식업 전생기 EP.1", 64, (255, 214, 102))]
HOOK = [("15년차 IT기획자,", 84, (255, 255, 255)),
        ("샐러드 카페 알바 4시간 만에…", 66, (255, 214, 102))]

# (image, seconds, zoom_from, zoom_to, top text)
shots = [(panels[6], 1.6, 1.0, 1.07, HOOK)]          # hook: 쓰러진 컷
shots.append((cover, 1.8, 1.0, 1.08, []))             # 타이틀
for p in panels[:8]:
    shots.append((p, 2.4, 1.0, 1.05, SERIES))
shots.append((panels[8], 3.2, 1.0, 1.06, SERIES))     # 엔딩

total = sum(s[1] for s in shots)
cmd = ["ffmpeg", "-v", "error", "-y",
       "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", SRC_AUDIO, "-map", "0:v", "-map", "1:a",
       "-af", f"afade=t=out:st={total-1.5:.2f}:d=1.5", "-t", f"{total:.2f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "reel_edit.mp4"]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for img, sec, z0, z1, txt in shots:
    n = int(round(sec * FPS))
    for i in range(n):
        t = i / max(n - 1, 1)
        t = t * t * (3 - 2 * t)
        proc.stdin.write(compose(img, z0 + (z1 - z0) * t, txt).tobytes())
proc.stdin.close(); proc.wait()
print("video", total, "s")

# 9:16 cover
c = compose(cover, 1.0, [])
c.save("cover_9x16.jpg", quality=95)
print("done")
