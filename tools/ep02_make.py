"""EP.2 reel builder: full-screen panels + big pop-in captions."""
import math, random, subprocess, wave, struct
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
BGM = "/mnt/user-data/uploads/1000018912.mp4"   # EP.1 series BGM
IMG = {k: Image.open(f"/home/claude/ep02/{k}.png").convert("RGB") for k in "ABCDE"}

INK, RED, NOTE = (58, 38, 28), (214, 40, 40), (90, 110, 170)

def font(s): return ImageFont.truetype(FONT, s, index=1)

def fit(draw, lines, max_size, max_w=960):
    s = max_size
    while s > 40 and max(draw.textlength(l, font=font(s)) for l in lines) > max_w:
        s -= 4
    return s

# (panel, seconds, main lines, note, style)
SHOTS = [
    ("E", 2.2, ["최저시급에게", "뭘 그렇게 바래?"], "주 3일 · 2주차 알바가 들은 말 모음", "hook"),
    ("A", 2.2, ["니가 딱 알아서 좀 해"], None, "line"),
    ("B", 2.6, ["보고만 있는거니?"], "(배우는 중인데)", "line"),
    ("A", 2.2, ["니 할일 좀 찾아서 해"], None, "line"),
    ("B", 2.4, ["언제까지", "시키는 일만 할래"], None, "line"),
    ("A", 2.4, ["하나하나", "어떻게 알려줘."], None, "line"),
    ("B", 3.0, ["벌써 2주씩이나 돼서", "아직도 실수를 하면..하~"], None, "line"),
    ("C", 2.6, ["야! 이거나 딲아!", "다 딲아!"], None, "slam"),
    ("E", 2.4, ["지금 너 뭐해야", "될 거 같애?"], None, "line"),
    ("D", 3.4, ["조심히 가세요~"], "(1시간 일한 사장님, 인사 씹고 퇴근)", "line"),
]

def frame(img, t, sec, lines, note, style, idx):
    # slow push-in
    z = 1.0 + 0.04 * (t / sec)
    s = int(W * z), int(H * z)
    im = img.resize(s, Image.BICUBIC)
    ox, oy = (s[0] - W) // 2, (s[1] - H) // 2
    dx = dy = 0
    if style == "slam" and t < 0.45:          # screen shake
        amp = 22 * (1 - t / 0.45)
        dx, dy = int(amp * math.sin(t * 90)), int(amp * math.cos(t * 70))
    im = im.crop((ox - dx, oy - dy, ox - dx + W, oy - dy + H))
    d = ImageDraw.Draw(im)

    # pop-in scale for caption
    pop = 1.0
    dur = 0.12 if style == "slam" else 0.18
    if t < dur:
        start = 1.6 if style == "slam" else 1.25
        pop = start + (1.0 - start) * (t / dur)
    base = 120 if style == "slam" else (104 if style == "hook" else 92)
    size = int(fit(d, lines, base) * pop)
    col = RED if style == "slam" else INK
    y = 250 if style != "hook" else 210
    for ln in lines:
        f = font(size)
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y), ln, font=f, fill=col, stroke_width=12, stroke_fill=(255, 255, 255))
        y += int(size * 1.28)
    if note and t > 0.35:
        f = font(fit(d, [note], 54, 940))
        w = d.textlength(note, font=f)
        d.text(((W - w) / 2, y + 10), note, font=f,
               fill=(NOTE if style != "hook" else (200, 80, 60)),
               stroke_width=8, stroke_fill=(255, 255, 255))
    if style != "hook":   # counter pill
        tag = f"꼽 {idx}/9"
        f = font(44)
        w = d.textlength(tag, font=f)
        d.rounded_rectangle(((W - w) / 2 - 28, 140, (W + w) / 2 + 28, 212), 36, fill=INK)
        d.text(((W - w) / 2, 146), tag, font=f, fill=(255, 255, 255))
    return im

total = sum(s[1] for s in SHOTS)

# thump SFX for the slam line
slam_at = sum(s[1] for s in SHOTS[:7])
sr = 44100
with wave.open("/home/claude/ep02/thump.wav", "w") as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr)
    data = b""
    for i in range(int(sr * 0.5)):
        tt = i / sr
        v = math.exp(-tt * 9) * (0.9 * math.sin(2 * math.pi * (70 - 40 * tt) * tt)
                                  + 0.25 * (random.random() * 2 - 1) * math.exp(-tt * 40))
        data += struct.pack("<h", int(max(-1, min(1, v)) * 30000))
    wv.writeframes(data)

cmd = ["ffmpeg", "-v", "error", "-y",
       "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", BGM, "-i", "/home/claude/ep02/thump.wav",
       "-filter_complex",
       f"[1:a]volume=0.55,afade=t=out:st={total-1.5:.2f}:d=1.5[m];"
       f"[2:a]adelay={int(slam_at*1000)}|{int(slam_at*1000)},volume=1.6[s];"
       f"[m][s]amix=inputs=2:duration=first:normalize=0[a]",
       "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
       "/home/claude/ep02/reel.mp4"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
idx = 0
for key, sec, lines, note, style in SHOTS:
    if style != "hook":
        idx += 1
    n = int(round(sec * FPS))
    for i in range(n):
        p.stdin.write(frame(IMG[key], i / FPS, sec, lines, note, style, idx).tobytes())
p.stdin.close(); p.wait()
print("total", total)
