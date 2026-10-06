# -*- coding: utf-8 -*-
"""对照片：官方 DeepSeek 鲸鱼矢量 vs 本票自绘鲸徽。

官方矢量取自 `E:\Agent项目\AI对战游戏\assets\emblems\deepseek.svg`
（viewBox 0 0 24 24，fill-rule evenodd，单条 path，1985 字符）。

重要版权提示（必须写进规范书）：
  DeepSeek 鲸鱼是 **DeepSeek 的商标/品牌标识**。把它原样印在「鲸元券」票面上，
  意味着本券声明自己由 DeepSeek 发行 —— 这是**冒用商标**，现实货币绝不可为。
  正确做法（本稿路线）：
    只借鉴其**设计语言**（整体鲸形、单色实心、负形做眼、圆头短尾），
    鲸徽本身自绘，保留可识别的差异（本稿为侧游 + 后喷气 + 单眼负形）。
  若确实要致敬，只能放在**纪念钞的次要位置**并注明出处，不能充当发行机构徽志。
"""
import os
import re

ROOT = r"E:\Agent项目\鲸元券"
NAVY = "#1B2657"
BLUE = "#4D6BFE"

_d = open(os.path.join(ROOT, "build", "deepseek_whale_d.txt"), encoding="utf-8").read().strip()
OFFICIAL_D = _d

# 本票自绘鲸徽（whale_lab.py 定稿形状）
OWN_D = ("M 1.00 -0.10 "
         "C 0.99 -0.34 0.86 -0.52 0.62 -0.56 "
         "C 0.40 -0.60 0.18 -0.54 0.02 -0.42 "
         "C -0.14 -0.31 -0.28 -0.20 -0.44 -0.16 "
         "C -0.54 -0.13 -0.62 -0.16 -0.68 -0.26 "
         "C -0.76 -0.40 -0.88 -0.50 -0.96 -0.44 "
         "C -1.02 -0.39 -1.00 -0.26 -0.92 -0.14 "
         "C -1.00 -0.02 -1.04 0.12 -0.96 0.20 "
         "C -0.88 0.28 -0.78 0.16 -0.70 0.04 "
         "C -0.62 -0.06 -0.54 -0.06 -0.46 0.00 "
         "C -0.30 0.12 -0.12 0.32 0.10 0.46 "
         "C 0.34 0.60 0.66 0.56 0.84 0.38 "
         "C 0.96 0.24 1.00 0.06 1.00 -0.10 Z")


def official(cx, cy, size, color, bg="#F5EFDE"):
    s = size / 24.0
    return (f'<g transform="translate({cx - size / 2} {cy - size / 2}) scale({s})">'
            f'<path d="{OFFICIAL_D}" fill="{color}" fill-rule="evenodd"/></g>')


def own(cx, cy, size, color, bg="#F5EFDE", spout=True, eye=True):
    """size = 全长（约 2 个归一化单位）对应的像素宽。"""
    s = size / 2.0
    out = [f'<g transform="translate({cx} {cy}) scale({s})">',
           f'<path d="{OWN_D}" fill="{color}"/>']
    if eye:
        out.append(f'<circle cx="0.62" cy="-0.26" r="0.050" fill="{bg}"/>')
    if spout:
        out.append(f'<path d="M 0.52 -0.56 C 0.50 -0.70 0.42 -0.78 0.32 -0.82" fill="none" '
                   f'stroke="{color}" stroke-width="0.048" stroke-linecap="round"/>')
    out.append("</g>")
    return "".join(out)


rows = [
    ("官方 DeepSeek 鲸（品牌蓝 #4D6BFE）", official, BLUE),
    ("官方 DeepSeek 鲸（票面藏青 #1B2657）", official, NAVY),
    ("本票自绘鲸徽（藏青，带后喷气）", own, NAVY),
]

W, H = 1300, 1180
parts = [f'<rect width="{W}" height="{H}" fill="#F5EFDE"/>']
y = 40
for title, fn, col in rows:
    parts.append(f'<text x="30" y="{y + 20}" font-family="\'Microsoft YaHei\',sans-serif" '
                 f'font-size="21" fill="#2A3A7A">{title}</text>')
    y += 48
    # 大图
    parts.append(fn(150, y + 90, 230, col) if fn is official else fn(150, y + 90, 230, col))
    # 缩微测试：货币上实际的印刷尺寸
    for j, sz in enumerate([64, 40, 28, 18, 12]):
        xx = 380 + j * 150
        parts.append(fn(xx, y + 95, sz, col) if fn is official else fn(xx, y + 95, sz, col))
        parts.append(f'<text x="{xx}" y="{y + 165}" font-family="monospace" font-size="14" '
                     f'fill="#8A8060" text-anchor="middle">{sz}px</text>')
    y += 290
    parts.append(f'<line x1="30" y1="{y - 40}" x2="{W - 30}" y2="{y - 40}" stroke="#D9CFB4"/>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
       f'height="100%">{"".join(parts)}</svg>')
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#EEF0F4;overflow:hidden}}
#f{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}}
.n{{width:96vw;height:calc(96vw*{H}/{W});max-height:96vh;max-width:calc(96vh*{W}/{H});}}
</style></head><body><div id="f"><div class="n">{svg}</div></div></body></html>'''
p = os.path.join(ROOT, "build", "whale-compare.html")
open(p, "w", encoding="utf-8").write(html)
print("written:", p)
