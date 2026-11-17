import os, subprocess
from PIL import Image, ImageDraw
ns = {'__name__': 'x', '__file__': '/home/claude/onewordc/claude_ep.py'}
exec(compile(open('/home/claude/onewordc/claude_ep.py').read().replace("if __name__ == '__main__':", "if False:"), 'c', 'exec'), ns)
os.chdir('/home/claude/onewordc')
g = ns['g']; W, H, BW, BH = ns['W'], ns['H'], ns['BW'], ns['BH']
jua, nunito, text_el, ease = g['jua'], g['nunito'], g['text_el'], g['ease']
base = ns['bg_files']()
ox, oy = (BW - W) // 2, (BH - H) // 2
_win = base.crop((ox, oy, ox + W, oy + H)).crop((70, 990, 1010, 1810))
BG = g['to_img'](g['vgrad']([(0, (24, 30, 62)), (1, (52, 40, 90))])).crop((ox, oy, ox + W, oy + H))
_m = Image.new('L', _win.size, 0); ImageDraw.Draw(_m).rounded_rectangle([10, 10, _win.width - 11, _win.height - 11], radius=34, fill=255)
BG.paste(_win, (70, 990), _m)
INK, BLUE, TOM = (30, 40, 80), (40, 70, 160), (226, 72, 52)
q = text_el('내가 문서 파일이라면?', jua(96), (255, 255, 255))
by = text_el('by Claude', nunito(800, 66, True), (255, 140, 110))
def file_row(name, big=False):
    f = jua(66 if big else 46)
    d0 = ImageDraw.Draw(Image.new('L', (1, 1))); tw = d0.textlength(name, font=f)
    w, h = int(tw + 200), 140 if big else 104
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if big: d.rounded_rectangle([0, 0, w - 1, h - 1], radius=22, fill=(214, 228, 255, 255), outline=BLUE, width=4)
    x, y = 30, (h - 96) // 2
    d.polygon([(x, y), (x + 58, y), (x + 80, y + 22), (x + 80, y + 96), (x, y + 96)], fill=(232, 110, 60))
    d.text((x + 40, y + 60), 'P', font=nunito(800, 38), fill=(255, 255, 255), anchor='mm')
    d.text((x + 115, h / 2), name, font=f, fill=INK if big else (110, 116, 130), anchor='lm')
    return im
rows = [file_row('기획서_최종.pptx'), file_row('기획서_진짜최종.pptx'), file_row('최종_진짜최종_ver.3', True)]
DUR = 2.6
def draw(t):
    f = BG.copy().convert('RGBA')
    def put(im, cx, cy, t0, kind='up'):
        p = ease((t - t0) / 0.35)
        if p <= 0: return
        el = im
        if kind == 'pop' and p < 1:
            s = 1.25 - 0.25 * p; el = el.resize((int(el.width * s), int(el.height * s)))
        if p < 1: el = el.copy(); el.putalpha(el.getchannel('A').point(lambda v: int(v * p)))
        f.alpha_composite(el, (int(cx - el.width / 2), int(cy - el.height / 2 + (0 if kind == 'pop' else (1 - p) * 30))))
    put(q, 540, 420, -1)
    put(rows[0], 540, 1140, 0.05); put(rows[1], 540, 1260, 0.2)
    put(rows[2], 540, 1420, 0.4, 'pop')
    put(by, 540, 600, 0.6)
    out = f.convert('RGB')
    return out
draw(0).resize((360, 640)).save('hook0.png'); draw(2.4).resize((360, 640)).save('hookprev.png')
g['render']('c_hook', DUR, draw)
open('list_hook.txt', 'w').write("file 'c_hook.mp4'\n" + ''.join(f"file 'c{i:02d}.mp4'\n" for i in range(12)))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list_hook.txt', '-c', 'copy', 'silent_hook.mp4'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'silent_hook.mp4', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                '-c:v', 'copy', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', 'me_in_one_word_by_claude_spinoff_hook.mp4'], check=True)
print('ok')
