# -*- coding: utf-8 -*-
"""人物稿去底：两级 unmix，输出可直接叠在纸色上的透明 PNG。

第 1 级 · 白色底 key
    原图背景是近白（实测 253,253,253），近乎纯白。
    a1 = clamp((|P-255| - T0) / (T1 - T0)) ,  F1 = unmix(P, 255, a1)
    解决：底色不是纸色，直接画上去会露出一个白框。
第 2 级 · 纸色 halo key
    把「边缘残留的近纸色像素」也视为背景，进一步收敛白边。
    a2 = clamp((|F1-K| - S0) / (S1 - S0)) ,  F2 = unmix(F1, K, a2)
    注意乘法合成：a1*F1 + (1-a1)*255 = P，因此中间色不能直接当作背景丢掉。

最终 alpha = a1 * a2，前景 = F2（近背景处会自然压暗，避免泛白）。
"""
import os, sys
from PIL import Image

ROOT = r"E:\Agent项目\鲸元券"
K = (245, 239, 222)          # 纸色
# 阈值是「归一化最大通道差」：d <= B0 判背景，d >= B1 判前景，中间线性过渡
T0, T1 = 0.040, 0.140        # 白底：253/255 -> d=0.008 判背景
# 纸色 halo：贴着纸色(<=0.02)的残留像素再收一次。
# 注意不能设太高：围裙/蕾丝实测 d~0.07，若阈值取 0.05 会把白围裙抠成半透明。
S0, S1 = 0.022, 0.075

def clamp01(v): return 0.0 if v < 0 else (1.0 if v > 1 else v)

def unmix(rgb, key, a):
    return tuple(max(0, min(255, (rgb[i] - (1 - a) * key[i]) / a)) for i in range(3))

def key_pass(rgb, key, b0, b1):
    """b0 = 判背景的边界，b1 = 判前景的边界（b1 > b0）。"""
    d = max(abs(rgb[i] - key[i]) for i in range(3)) / 255.0
    return clamp01((d - b0) / (b1 - b0))

def process(src_path, out_path, crop, target_w):
    im = Image.open(src_path).convert("RGB").crop(crop)
    if im.width != target_w:
        im = im.resize((target_w, round(im.height * target_w / im.width)), Image.LANCZOS)
    px = im.load()
    out = Image.new("RGBA", im.size)
    op = out.load()
    stats = [0, 0, 0]
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            a1 = key_pass(p, (255, 255, 255), T0, T1)
            if a1 <= 0:
                op[x, y] = (0, 0, 0, 0); stats[0] += 1; continue
            f1 = unmix(p, (255, 255, 255), a1)
            a2 = key_pass(f1, K, S0, S1)
            a = a1 * a2
            if a <= 0.004:
                op[x, y] = (0, 0, 0, 0); stats[0] += 1
            elif a >= 0.996:
                op[x, y] = (int(f1[0]), int(f1[1]), int(f1[2]), 255); stats[1] += 1
            else:
                f2 = unmix(f1, K, a2)
                op[x, y] = (int(f2[0]), int(f2[1]), int(f2[2]), round(a * 255)); stats[2] += 1
    out.save(out_path)
    tot = im.width * im.height
    print(f"{os.path.basename(out_path)} {out.size} 透明={stats[0]/tot:.1%} 实心={stats[1]/tot:.1%} 半透明={stats[2]/tot:.1%}")

os.makedirs(os.path.join(ROOT, "assets", "portrait"), exist_ok=True)
process(os.path.join(ROOT, "assets", "source", "character-full.jpg"),
        os.path.join(ROOT, "assets", "portrait", "portrait-keyed-3x4.png"),
        crop=(130, 90, 730, 890), target_w=780)
process(os.path.join(ROOT, "assets", "source", "character-full.jpg"),
        os.path.join(ROOT, "assets", "portrait", "portrait-keyed-head.png"),
        crop=(150, 85, 700, 745), target_w=780)
process(os.path.join(ROOT, "assets", "source", "character-chibi.png"),
        os.path.join(ROOT, "assets", "portrait", "chibi-keyed.png"),
        crop=(140, 90, 1114, 1064), target_w=780)

# 检查图：叠到纸色上
for name in ("portrait-keyed-3x4", "portrait-keyed-head", "chibi-keyed"):
    im = Image.open(os.path.join(ROOT, "assets", "portrait", name + ".png")).convert("RGBA")
    bg = Image.new("RGBA", im.size, K + (255,))
    c = Image.alpha_composite(bg, im).convert("RGB")
    c.thumbnail((520, 720), Image.LANCZOS)
    c.save(os.path.join(ROOT, "build", "keycheck-" + name + ".png"))
print("keycheck images written")
