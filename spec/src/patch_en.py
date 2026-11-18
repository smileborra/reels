import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
NUN = '/home/claude/onewordc/fonts/'
def nun(s, w=800): return ImageFont.truetype(NUN + f'nunito-latin-{w}-normal.ttf', s)
def hand(s): return ImageFont.truetype('fonts/gaegu.ttf', s)
INK = (40, 30, 30)
im = Image.open('src_fix.png').convert('RGB')
cv = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
m = np.zeros(cv.shape[:2], np.uint8); cv2.rectangle(m, (995, 212), (1140, 275), 255, -1)
im = Image.fromarray(cv2.cvtColor(cv2.inpaint(cv, m, 7, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB))
d = ImageDraw.Draw(im)
def fit(txt, w, h, maker, start):
    s = start
    while s > 12:
        b = d.multiline_textbbox((0, 0), txt, font=maker(s), spacing=int(s * .15), align='center')
        if b[2] - b[0] <= w and b[3] - b[1] <= h: return maker(s)
        s -= 1
    return maker(s)
def bubble(box, txt):
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=(255, 255, 255), outline=INK, width=4)
    f = fit(txt, (x1 - x0) * .74, (y1 - y0) * .7, hand, 40)
    d.multiline_text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), txt, font=f, fill=INK, anchor='mm', align='center', spacing=int(f.size * .15))
def label(box, txt):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=(y1 - y0) // 2, fill=(250, 208, 214), outline=INK, width=4)
    f = fit(txt, (x1 - x0) * .9, (y1 - y0) * .7, nun, 30)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), txt, font=f, fill=INK, anchor='mm')
PARCH = (236, 206, 160); BR = (90, 50, 30)
d.rounded_rectangle((135, 22, 478, 160), radius=14, fill=PARCH); d.rectangle((88, 98, 140, 162), fill=PARCH)
d.multiline_text((306, 92), 'Product Info -\nDivine Registry', font=nun(36), fill=BR, anchor='mm', align='center', spacing=6)
d.rounded_rectangle((42, 172, 490, 352), radius=14, fill=PARCH)
rows = [('Model', '15yr_Restarter'), ('Type', 'Versatile survival explorer'), ('Maker', 'Divine LifeLab'), ('Grade', 'Special Edition ★★★★★')]
for i, (k, v) in enumerate(rows):
    y = 200 + i * 44
    d.text((58, y), k, font=nun(26), fill=BR, anchor='lm')
    fv = nun(24, 700) if '★' not in v else ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 22, index=1)
    d.text((150, y), ': ' + v, font=fv, fill=BR, anchor='lm')
bubble((895, 2, 1190, 210), 'This is...\nmy official\nhuman spec!')
d.text((1068, 242), 'So proud~', font=hand(44), fill=(255, 255, 255), anchor='mm', stroke_width=4, stroke_fill=(30, 22, 22))
label((12, 388, 385, 442), '1. Living life my way'); bubble((330, 420, 520, 565), 'Yes!\nLet\'s do\nthis!')
label((607, 388, 885, 442), '2. Tireless curiosity'); bubble((1020, 392, 1172, 530), 'Curious\nabout\nthis too?')
label((12, 692, 385, 748), '3. Magnetic charm'); bubble((455, 720, 590, 835), "That's\nso you!")
label((607, 692, 895, 748), '4. Crisis survival'); bubble((1035, 698, 1190, 840), 'Just\nhang\non!!')
label((12, 1012, 390, 1068), '5. Obsessed with good food')
im.save('src_en.png')
im.crop((0, 0, 1199, 860)).resize((900, 645)).save('en_chk.png')
