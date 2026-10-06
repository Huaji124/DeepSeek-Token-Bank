# -*- coding: utf-8 -*-
"""鲸元券 · 蜡笔涂鸦版（对照网络流传的「鲸亿」手绘梗图）。

Register：手绘蜡笔 / 儿童画 —— 与正式票面（render_mockup.py）刻意相反：
  正式稿 = 凹版雕刻语言（细网线、专色、庄重）
  本稿   = 蜡笔语言（抖动线、色块溢出、纸张颗粒、手写体）
对照图要素（逐项对应）：四角蓝色圆印章「鲸亿」、顶部机构名、题字人、
中央大字券名、红色印章压红色冠字号、底部「数字 token」、人物置左。
输出：build/crayon-100.html / crayon-100.png
"""
import base64
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from whale_mark import whale as WHALE_MARK

ROOT = r"E:\Agent项目\鲸元券"
W, H = 1900, 1000

CRAYON_B = "#2F52C8"      # 蜡笔蓝（主色）
CRAYON_B2 = "#3E6BE0"
CRAYON_B3 = "#8FA6F0"
CRAYON_R = "#D8362E"      # 蜡笔红
CRAYON_Y = "#F0C63C"      # 蜡笔黄
CRAYON_G = "#7CC24A"      # 蜡笔绿
CRAYON_D = "#3A3A3A"      # 蜡笔黑（题字）
PAPER_CR = "#F7F4EA"      # 稍暗的纸色（蜡笔纸）


def b64(p):
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()


CHIBI = b64(os.path.join(ROOT, "assets", "portrait", "chibi-keyed.png"))

rnd = random.Random(20261005)


# ── 蜡笔笔触 ─────────────────────────────────────────────────────────
def wob(points, amp=4.0, seg=9, close=False, jitter_seed=0):
    """把折线细化成带抖动的多点路径，模拟手绘不稳的线。"""
    r = random.Random(jitter_seed)
    out = []
    pts = list(points)
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        for s in range(seg):
            t = s / float(seg)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            out.append((x + r.uniform(-amp, amp), y + r.uniform(-amp, amp)))
    out.append(pts[-1])
    if close:
        out.append(pts[0])
    return out


def stroked(pts, color, width, opacity=1.0, cap="round", extra=1):
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    layers = []
    for k in range(extra):
        off = k * 1.6
        layers.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width:.1f}" '
            f'opacity="{opacity*0.55:.2f}" stroke-linecap="{cap}" stroke-linejoin="round" '
            f'transform="translate({off:.1f} {off*0.8:.1f})"/>')
    layers.append(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width:.1f}" '
        f'opacity="{opacity:.2f}" stroke-linecap="{cap}" stroke-linejoin="round"/>')
    return "".join(layers)


def scribble_fill(cx, cy, r, color, seed, density=26, opacity=0.55, flatten=1.0):
    """用一圈圈潦草线条填一个圆形区域，模拟蜡笔涂色不满不匀。"""
    r0 = random.Random(seed)
    out = []
    for i in range(density):
        rr = r * (0.18 + 0.82 * ((i + 1) / float(density)))
        a0 = r0.uniform(0, math.pi * 2)
        span = r0.uniform(2.2, 5.6)
        pts = []
        steps = 22
        for s in range(steps + 1):
            a = a0 + span * s / float(steps)
            x = cx + math.cos(a) * rr
            y = cy + math.sin(a) * rr * flatten
            pts.append((x + r0.uniform(-2.5, 2.5), y + r0.uniform(-2.5, 2.5)))
        out.append(stroked(pts, color, r0.uniform(3.2, 6.4), opacity * r0.uniform(0.6, 1.0)))
    return "".join(out)


def scribble_ellipse(cx, cy, rx, ry, color, seed, density=18, opacity=0.5):
    r0 = random.Random(seed)
    out = []
    for i in range(density):
        k = 0.2 + 0.8 * ((i + 1) / float(density))
        a0 = r0.uniform(0, math.pi * 2)
        span = r0.uniform(2.4, 5.8)
        pts = []
        for s in range(24):
            a = a0 + span * s / 23.0
            pts.append((cx + math.cos(a) * rx * k + r0.uniform(-3, 3),
                        cy + math.sin(a) * ry * k + r0.uniform(-3, 3)))
        out.append(stroked(pts, color, r0.uniform(3.0, 6.0), opacity * r0.uniform(0.6, 1.0)))
    return "".join(out)


def crayon_seal(cx, cy, r, text, seed, color=CRAYON_B):
    """四角圆形蜡笔印章：潦草蓝圈 + 白色（纸色）手写「鲸亿」。"""
    out = [scribble_fill(cx, cy, r, color, seed, density=30, opacity=0.5)]
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r*0.98:.1f}" fill="none" stroke="{color}" '
               f'stroke-width="3" opacity="0.5"/>')
    out.append(f'<text x="{cx}" y="{cy + r*0.30:.1f}" text-anchor="middle" '
               f'font-family="\'Microsoft YaHei\',\'SimHei\',sans-serif" font-size="{r*0.86:.0f}" '
               f'font-weight="700" fill="{PAPER_CR}" letter-spacing="1" '
               f'transform="rotate({rnd.uniform(-9,9):.1f} {cx} {cy})">{text}</text>')
    return "".join(out)


def hand_text(x, y, s, size, color, weight="700", anchor="start", rot=0.0,
              family="'Microsoft YaHei','SimHei',sans-serif", spacing=0, opacity=1.0):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'letter-spacing="{spacing}" opacity="{opacity}" '
            f'transform="rotate({rot} {x} {y})">{s}</text>')


def star(cx, cy, r, color, seed):
    r0 = random.Random(seed)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return stroked(wob(pts, amp=2.2, seg=5, close=True), color, 5.5, 0.85)


def heart(cx, cy, r, color, seed):
    pts = []
    r0 = random.Random(seed)
    for i in range(31):
        t = math.pi * 2 * i / 30.0
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 16.0, cy + y * r / 16.0))
    return stroked(wob(pts, amp=1.5, seg=3, close=True), color, 4.5, 0.8)


def sun(cx, cy, r, seed):
    out = [scribble_fill(cx, cy, r, CRAYON_Y, seed, density=16, opacity=0.5)]
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{CRAYON_Y}" '
               f'stroke-width="4" opacity="0.75"/>')
    for i in range(8):
        a = math.pi * 2 * i / 8.0
        p0 = (cx + math.cos(a) * r * 1.15, cy + math.sin(a) * r * 1.15)
        p1 = (cx + math.cos(a) * r * 1.62, cy + math.sin(a) * r * 1.62)
        out.append(stroked(wob([p0, p1], amp=2.5, seg=5), CRAYON_Y, 5, 0.8))
    # 笑脸
    out.append(f'<circle cx="{cx - r*0.32:.1f}" cy="{cy - r*0.18:.1f}" r="{r*0.09:.1f}" fill="#4A4A4A"/>')
    out.append(f'<circle cx="{cx + r*0.32:.1f}" cy="{cy - r*0.18:.1f}" r="{r*0.09:.1f}" fill="#4A4A4A"/>')
    out.append(stroked([(cx - r * 0.40, cy + r * 0.18), (cx - r * 0.12, cy + r * 0.42),
                        (cx + r * 0.16, cy + r * 0.38), (cx + r * 0.42, cy + r * 0.14)],
                       "#4A4A4A", 4.2, 0.9))
    return "".join(out)


def wave_scribble(x0, x1, y, amp, color, seed, rows=1, gap=26, width=5.5):
    r0 = random.Random(seed)
    out = []
    for rr in range(rows):
        y0 = y + rr * gap
        pts = []
        n = int((x1 - x0) / 26)
        for i in range(n + 1):
            x = x0 + i * (x1 - x0) / float(n)
            pts.append((x, y0 + math.sin(i * 1.1 + rr) * amp + r0.uniform(-2, 2)))
        out.append(stroked(pts, color, width, 0.7))
    return "".join(out)


def frame_rough(inset, color, width, seed, extra_lines=2):
    """手绘外框：多道抖动的近矩形线，模拟反复描边。"""
    x0, y0, x1, y1 = inset, inset * 0.86, W - inset, H - inset * 0.86
    out = []
    for k in range(extra_lines + 1):
        g = k * 5.0
        pts = [(x0 + g, y0 + g), (x1 - g, y0 + g), (x1 - g, y1 - g), (x0 + g, y1 - g)]
        out.append(stroked(wob(pts, amp=6.0, seg=14, close=True, jitter_seed=seed + k),
                           color, width, 0.72 - k * 0.12, extra=1))
    return "".join(out)


body = []

# 纸底 + 颗粒
body.append(f'<rect width="{W}" height="{H}" fill="{PAPER_CR}"/>')
body.append(f'<rect width="{W}" height="{H}" fill="url(#grain)"/>')

# 背景涂色块（蜡笔平涂）
body.append(f'<g opacity="0.42">')
body.append(scribble_ellipse(560, 980, 640, 150, CRAYON_G, 11, density=34, opacity=0.16))
body.append(scribble_ellipse(1500, 420, 560, 330, CRAYON_Y, 12, density=34, opacity=0.13))
body.append(scribble_ellipse(240, 420, 380, 330, CRAYON_B3, 13, density=30, opacity=0.12))
body.append('</g>')

# 手绘外框
body.append(frame_rough(38, CRAYON_B, 7.0, 101, extra_lines=2))

# 四角「鲸亿」印章（内缩到边框内，避免被画布裁切）
SEAL_R = 78
body.append(crayon_seal(158, 152, SEAL_R, "鲸亿", 21))
body.append(crayon_seal(W - 158, 152, SEAL_R, "鲸亿", 22))
body.append(crayon_seal(158, H - 152, SEAL_R, "鲸亿", 23))
body.append(crayon_seal(W - 158, H - 152, SEAL_R, "鲸亿", 24))

# 装饰：爱心 / 星星 / 太阳
body.append(heart(212, 312, 34, CRAYON_R, 31))
body.append(heart(214, 398, 30, CRAYON_R, 32))
body.append(heart(258, 464, 26, CRAYON_R, 33))
body.append(star(316, 226, 46, CRAYON_Y, 41))
body.append(star(392, 180, 26, CRAYON_Y, 42))
body.append(sun(W - 240, 250, 56, 51))

# ── 左区：Q 版人物 ────────────────────────────────────────────────
body.append(f'<image x="212" y="196" width="600" height="600" xlink:href="{CHIBI}" '
            f'preserveAspectRatio="xMidYMid meet" transform="rotate(-2.5 512 496)"/>')

# ── 顶部：机构名与题字 ────────────────────────────────────────────
body.append(hand_text(620, 168, "Deepseek token 银行", 54, CRAYON_B, rot=-1.6, spacing=1.5))
body.append(hand_text(620, 236, "Deepseek", 46, CRAYON_B, rot=-0.8, spacing=1))
body.append(hand_text(842, 240, "梁文峰", 46, CRAYON_B, rot=0.9, spacing=2))

# ── 中央：券名（黑蜡笔大字）──────────────────────────────────────
body.append(f'<g transform="rotate(-3.4 1330 560)">')
for k in range(3):
    body.append(hand_text(1330 + (k - 1) * 3.2, 590 + (k - 1) * 2.4, "鲸 元 券",
                          132, CRAYON_D, anchor="middle", spacing=10, opacity=0.35))
body.append(hand_text(1330, 590, "鲸 元 券", 132, CRAYON_D, anchor="middle", spacing=10))
body.append('</g>')

# ── 红色冠字号 271989 + 压印红章（章压数字右端，如梗图）────────────
body.append(hand_text(1250, 690, "271989", 84, CRAYON_R, anchor="middle",
                      family="Georgia,'Times New Roman',serif", spacing=8, rot=-1.2))
# 红色印章（2×2 篆体感方块）：压在数字右端，避开画布边缘与下沿
sx, sy, ss = 1436, 646, 96
body.append(f'<g transform="rotate(-6 {sx + ss/2} {sy + ss/2})">')
body.append(f'<rect x="{sx}" y="{sy}" width="{ss}" height="{ss}" fill="none" '
            f'stroke="{CRAYON_R}" stroke-width="9" opacity="0.88" rx="4"/>')
for i in range(2):
    for j in range(2):
        cx = sx + ss * (0.28 + 0.44 * j)
        cy = sy + ss * (0.28 + 0.44 * i)
        body.append(scribble_ellipse(cx, cy, ss * 0.19, ss * 0.19, CRAYON_R,
                                     60 + i * 2 + j, density=10, opacity=0.75))
body.append('</g>')

# ── 海面与跃鲸（中右侧空档，与红章错开）──────────────────────────
body.append(wave_scribble(1000, 1660, 726, 6, CRAYON_B2, 71, rows=2, gap=24, width=5))
body.append(WHALE_MARK(1630, 660, 96, CRAYON_B2, bg=PAPER_CR))
body.append(scribble_ellipse(1666, 614, 11, 7, CRAYON_B2, 81, density=6, opacity=0.55))

# ── 下沿：数字 token（两个右对齐锚点，末端让开右下角印章）─────────
body.append(hand_text(1400, 886, "100000000", 78, CRAYON_B, anchor="end",
                      family="Georgia,'Times New Roman',serif", spacing=4, rot=-1.0))
body.append(hand_text(1630, 886, "token", 58, CRAYON_B, anchor="end",
                      family="Georgia,'Times New Roman',serif", spacing=2, rot=-1.0))

# ── 左下蜡笔涂鸦小注（右移，避开左下角印章与人物裙摆）────────────
body.append(hand_text(300, 840, "DeepSeek Token银行 · 虚拟设定", 24, CRAYON_B, rot=-1.4, opacity=0.85))
body.append(hand_text(300, 878, "非真实货币 · 仅供玩赏", 22, CRAYON_R, rot=0.8, opacity=0.8))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="100%" height="100%">
  <defs>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" seed="7" result="n"/>
      <feColorMatrix in="n" type="saturate" values="0" result="g"/>
      <feComponentTransfer in="g">
        <feFuncA type="linear" slope="0.16" intercept="0"/>
      </feComponentTransfer>
    </filter>
    <filter id="rough">
      <feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="2" seed="19" result="t"/>
      <feDisplacementMap in="SourceGraphic" in2="t" scale="5" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
  </defs>
  <g filter="url(#rough)">{''.join(body)}</g>
</svg>'''

html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#E9E9EA;overflow:hidden}}
#f{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}}
.n{{width:97vw;height:calc(97vw*{H}/{W});max-height:95vh;max-width:calc(95vh*{W}/{H});
   filter:drop-shadow(0 10px 22px rgba(0,0,0,.28));}}
</style></head><body><div id="f"><div class="n">{svg}</div></div></body></html>'''

p = os.path.join(ROOT, "build", "crayon-100.html")
open(p, "w", encoding="utf-8").write(html)
print("written:", p, len(html))
