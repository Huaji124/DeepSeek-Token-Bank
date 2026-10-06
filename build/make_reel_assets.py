# -*- coding: utf-8 -*-
"""为介绍动画准备素材：整票缩图 + 局部特写。

源：dist/png/*.png（7560×3528，扫描稿质感）与 dist/svg/*.svg。
输出：build/reel/*.jpg（画布动画用）与 *_hi.png（特写用）。

坐标换算：交付 PNG 是 4× 设备像素比截图，所以
    像素 = SVG 用户单位 × 4
"""
import os

from PIL import Image

ROOT = r"E:\Agent项目\鲸元券"
DIST = os.path.join(ROOT, "dist", "png")
OUT = os.path.join(ROOT, "build", "reel")
os.makedirs(OUT, exist_ok=True)

TAGS = ["010000000", "020000000", "050000000",
        "100000000", "200000000", "500000000"]

# 局部特写：(名字, 源文件, 裁切框(像素), 输出宽度)  —— 均取自 1 亿券
CROPS = [
    ("portrait",   "front_100000000.png", (200, 200, 3800, 3320), 1500),
    ("emblem",     "front_100000000.png", (4130, 1930, 5170, 2970), 1040),
    ("ovi",        "front_100000000.png", (3830, 1000, 7330, 1520), 1750),
    ("braille",    "front_100000000.png", (7040, 2960, 7400, 3320), 720),
    ("serial",     "front_100000000.png", (3760, 3220, 5340, 3400), 1500),
    ("regist_f",   "front_100000000.png", (180, 2930, 620, 3370), 880),
    ("lighthouse", "back_100000000.png",  (3080, 1520, 4520, 3160), 1200),
    ("datemark",   "back_100000000.png",  (6080, 2930, 7480, 3320), 1400),
    ("emblem_b",   "back_100000000.png",  (5420, 380, 6620, 1580), 1100),
    ("buoy",       "back_010000000.png",  (3080, 1520, 4520, 3160), 1200),
    ("dipper",     "back_200000000.png",  (2700, 1100, 4900, 3100), 1400),
]


def main():
    print("== 整票缩图 ==")
    for t in TAGS:
        for side in ("front", "back"):
            src = os.path.join(DIST, "%s_%s.png" % (side, t))
            im = Image.open(src).convert("RGB")
            w = 2400
            im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            dst = os.path.join(OUT, "note_%s_%s.jpg" % (side, t))
            im.save(dst, "JPEG", quality=93, optimize=True, subsampling=0)
            print("  %-30s %6d B  %s" % (os.path.basename(dst),
                                         os.path.getsize(dst), im.size))
    print("== 局部特写 ==")
    for name, src, box, w in CROPS:
        im = Image.open(os.path.join(DIST, src)).convert("RGB").crop(box)
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        dst = os.path.join(OUT, "hi_%s.jpg" % name)
        im.save(dst, "JPEG", quality=95, optimize=True, subsampling=0)
        print("  %-30s %6d B  %s" % (os.path.basename(dst),
                                     os.path.getsize(dst), im.size))


if __name__ == "__main__":
    main()
