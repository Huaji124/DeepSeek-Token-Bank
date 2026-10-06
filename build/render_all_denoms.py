# -*- coding: utf-8 -*-
"""按设计语言渲染**全部 9 档面额**（3 辅币 + 6 主币）。

设计语言（与 100,000,000 券同构，逐档只换三个维度）：
  · 尺寸：券长按 3.2 / 3.1.3 的阶梯，券高主币 70.0、辅币 52/54/56
  · 色调：专色由本档决定，纸色 = 专色同色相的浅色版（palette.tint）
  · 主题：主景场景逐档不同（引航 / 夜航 / 港市 / 守望 / 星图 / 远洋 + 辅币三式）

共用的固定要素（锚点与 100M 券一致，按券高比例缩放）：
  鲸徽、机构名（中/英）、面额数字（OVI 丝印）、中文大写、单位行、
  法偿声明、冠字号 ×2、微缩文字带、盲文块（右下 6 点）、
  凸点组（左缘，点数 = 档位）、右缘缺口（数 = 档位）、内框直角双线。
主币另加：开窗安全线、对印（左下）、潜像、压印铭文。
辅币按 3.1.4 不设人物、安全线、对印、潜像、微缩带。

输出：build/series-all.html / series-all.png（一张总表，9 档按真实相对尺寸排列）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palette as PAL
from whale_mark import whale as WHALE_MARK

ROOT = PAL.ROOT
PX_MM = 12.6
H_MAIN = 882                      # 70.0 mm
GOLD, GOLD_L, NAVY = PAL.GOLD, PAL.GOLD_L, PAL.NAVY

# 主币：(面额, 券长mm, 专色, 专色名, 主题, 中文大写, 英文, 人物取景框)
# 取景框 = 矢量墨版 viewBox 0 0 1200 1049 内的 (x, y, w, h)，逐档换构图（3.3.2 姿态须可区分）
# 人物：**全系列共用同一张、同一取景**（用户 m03984：「人物不要有区别啊」）。
# 每档只换卷长 / 色调 / 背景场景，人物构图一个像素都不动。
VB_STD = (0, 0, 1200, 1049)          # 与 100,000,000 券完全一致的取景

MAIN = [
    ("10,000,000", 132.0, "#24506B", "深青蓝", "引航", "壹仟萬 TOKEN", "TEN MILLION TOKENS",
     VB_STD),
    ("20,000,000", 142.0, "#1F5A52", "深海绿", "夜航", "贰仟萬 TOKEN", "TWENTY MILLION TOKENS",
     VB_STD),
    ("50,000,000", 148.0, "#4A3A6E", "紫罗兰", "港市", "伍仟萬 TOKEN", "FIFTY MILLION TOKENS",
     VB_STD),
    ("100,000,000", 150.0, "#1B2657", "藏青", "守望", "壹億 TOKEN", "ONE HUNDRED MILLION TOKENS",
     VB_STD),
    ("200,000,000", 158.0, "#8A5A2B", "赭金", "星图", "贰億 TOKEN", "TWO HUNDRED MILLION TOKENS",
     VB_STD),
    ("500,000,000", 176.0, "#2E2717", "玄金", "远洋", "伍億 TOKEN", "FIVE HUNDRED MILLION TOKENS",
     VB_STD),
]

# 辅币：(面额, 券长mm, 券高mm, 专色, 专色名, 主题, 中文大写, 英文, 面额码)
SUB = [
    ("100,000", 100.0, 52.0, "#9FB7AE", "浅雾青", "单尾破浪", "壹拾萬 分", "ONE HUNDRED THOUSAND FEN", "100000"),
    ("200,000", 108.0, 54.0, "#8FA3C4", "浅灰蓝", "双尾交浪", "贰拾萬 分", "TWO HUNDRED THOUSAND FEN", "200000"),
    ("500,000", 116.0, 56.0, "#C2A46B", "浅赭金", "环浪饰框", "伍拾萬 分", "FIVE HUNDRED THOUSAND FEN", "500000"),
]

PORTRAIT_SVG = open(os.path.join(ROOT, "assets", "portrait", "portrait-lineart.svg"),
                    encoding="utf-8").read()
PSW, PSH = 1200, 1049


def portrait_markup(x, y, w, h, vb):
    vx, vy, vw, vh = vb
    return ('<svg x="%.1f" y="%.1f" width="%.1f" height="%.1f" viewBox="%d %d %d %d" '
            'preserveAspectRatio="none">%s</svg>'
            % (x, y, w, h, vx, vy, vw, vh, PORTRAIT_SVG))


def ovi_def():
    return ('<linearGradient id="ovi" x1="0.05" y1="0" x2="0.95" y2="1">'
            '<stop offset="0" stop-color="#2F6B4F"/><stop offset=".2" stop-color="#3E8C7A"/>'
            '<stop offset=".4" stop-color="#3D6E9E"/><stop offset=".6" stop-color="#6B4E9C"/>'
            '<stop offset=".8" stop-color="#9C5A6E"/><stop offset="1" stop-color="#B08A3E"/>'
            '</linearGradient>')


# ────────────────────────── 底纹（防伪花球） ──────────────────────────
def rosette(cx, cy, r, n, color, op, sw):
    out = ['<g fill="none" stroke="%s" stroke-width="%.2f" opacity="%.2f">' % (color, sw, op)]
    for i in range(n):
        rr = r * (i + 1) / n
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, rr))
    out.append('</g>')
    return "".join(out)


def ellipses(cx, cy, rx, ry, n, rot, color, op, sw):
    out = ['<g fill="none" stroke="%s" stroke-width="%.2f" opacity="%.2f" '
           'transform="rotate(%.1f %.1f %.1f)">' % (color, sw, op, rot, cx, cy)]
    for i in range(n):
        k = (i + 1) / n
        out.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f"/>'
                   % (cx, cy, rx * k, ry * k))
    out.append('</g>')
    return "".join(out)


def waves(y, x0, x1, amp, period, color, op, sw, rows=3):
    out = ['<g fill="none" stroke="%s" stroke-width="%.2f" opacity="%.2f">' % (color, sw, op)]
    for r in range(rows):
        yy = y + r * amp * 2.1
        d = ["M %.1f %.1f" % (x0, yy)]
        x = x0
        step = period / 2.0
        up = True
        while x < x1:
            d.append("q %.1f %.1f %.1f 0" % (step / 2.0, (-amp if up else amp), step))
            x += step
            up = not up
        out.append('<path d="%s"/>' % " ".join(d))
    out.append('</g>')
    return "".join(out)


# ────────────────────────── 主景场景（逐档不同） ──────────────────────────
def scene(theme, W, H, IN, spot, deep, gold):
    """每档一个独立场景，画在券面左半区。全部程序生成，无位图。"""
    o = []
    x0, x1 = IN * 0.6, W * 0.56
    mid = (x0 + x1) / 2.0
    if theme == "引航":                      # 提灯 + 浪脊 + 幼鲸尾
        o.append('<g opacity="0.55">')
        for i, (cx, cy, r, op) in enumerate([(mid, H * 0.32, H * 0.20, 0.055),
                                             (mid, H * 0.32, H * 0.135, 0.075),
                                             (mid, H * 0.32, H * 0.075, 0.10)]):
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="%.3f"/>'
                     % (cx, cy, r, gold, op))
        o.append('</g>')
        o.append(waves(H * 0.80, x0, x1, H * 0.022, H * 0.09, deep, 0.45, 0.9, 3))
        o.append(fluke(mid - H * 0.28, H * 0.70, H * 0.10, deep, 0.85, -14))
    elif theme == "夜航":                     # 星群 + 罗盘 + 浮标
        o.append(starfield(x0, IN, x1, H * 0.62, 26, deep, 0.55, seedn=7))
        o.append(compass(mid, H * 0.42, H * 0.19, deep, gold))
        o.append(waves(H * 0.84, x0, x1, H * 0.018, H * 0.075, deep, 0.40, 0.9, 2))
        o.append(buoy(x1 - H * 0.10, H * 0.78, H * 0.055, deep, gold))
    elif theme == "港市":                     # 码头吊机 + 货箱成排
        o.append(cranes(x0, H * 0.30, x1, H * 0.62, 3, deep, 0.85))
        o.append(crates(x0, H * 0.62, x1, H * 0.80, deep, gold, 0.75))
        o.append(waves(H * 0.86, x0, x1, H * 0.016, H * 0.07, deep, 0.35, 0.9, 2))
    elif theme == "守望":                     # 满月 + 鲸群剪影
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="0.13"/>'
                 % (mid, H * 0.30, H * 0.22, gold))
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" '
                 'stroke-width="1.4" opacity="0.35"/>' % (mid, H * 0.30, H * 0.22, gold))
        for i, (dx, dy, s) in enumerate([(-0.20, 0.60, 0.085), (0.02, 0.66, 0.105),
                                         (0.24, 0.59, 0.075)]):
            o.append(whale_sil(mid + W * 0.0 + (x1 - x0) * dx, H * dy, H * s, deep, 0.55))
        o.append(waves(H * 0.86, x0, x1, H * 0.018, H * 0.08, deep, 0.35, 0.9, 2))
    elif theme == "星图":                     # 穹顶 + 星座网
        o.append('<path d="M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f" fill="none" '
                 'stroke="%s" stroke-width="1.6" opacity="0.5"/>'
                 % (x0, H * 0.66, (x1 - x0) / 2, H * 0.46, x1, H * 0.66, deep))
        o.append(starfield(x0, IN, x1, H * 0.60, 30, deep, 0.60, seedn=13))
        o.append(constellation(x0, IN, x1, H * 0.58, deep, 0.55))
    elif theme == "远洋":                     # 三桅帆 + 跃鲸
        o.append(ship(mid, H * 0.30, H * 0.44, deep, gold))
        o.append(fluke(mid + H * 0.34, H * 0.72, H * 0.13, deep, 0.85, 16))
        o.append(waves(H * 0.84, x0, x1, H * 0.024, H * 0.095, deep, 0.45, 0.9, 3))
    # ── 辅币三式（3.1.3 表：无人物，鲸徽 + 尾鳍 / 浪饰）────────────────
    elif theme == "单尾破浪":
        o.append(waves(H * 0.72, x0, x1, H * 0.030, H * 0.10, deep, 0.45, 1.0, 4))
        o.append(fluke(mid, H * 0.44, H * 0.24, deep, 0.88, -8))
        o.append(spray(mid, H * 0.60, H * 0.30, deep, 14))
    elif theme == "双尾交浪":
        o.append(waves(H * 0.74, x0, x1, H * 0.028, H * 0.095, deep, 0.42, 1.0, 4))
        o.append(fluke(mid - H * 0.13, H * 0.46, H * 0.20, deep, 0.85, -22))
        o.append(fluke(mid + H * 0.15, H * 0.44, H * 0.18, deep, 0.70, 26))
        o.append(spray(mid, H * 0.62, H * 0.34, deep, 20))
    elif theme == "环浪饰框":
        o.append('<g fill="none" stroke="%s" stroke-width="1.1" opacity="0.5">' % deep)
        for i in range(9):
            r = H * (0.10 + 0.045 * i)
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (mid, H * 0.52, r))
        o.append('</g>')
        o.append(fluke(mid, H * 0.52, H * 0.17, deep, 0.85, 0))
        o.append(waves(H * 0.80, x0, x1, H * 0.022, H * 0.085, deep, 0.40, 1.0, 3))
    return "".join(o)


def spray(cx, cy, w, color, n):
    """浪花：一圈深浅不一的小点。"""
    out = ['<g fill="%s" opacity="0.45">' % color]
    v = 11
    for i in range(n):
        v = (v * 1103515245 + 12345) % 2147483648
        px = cx - w / 2 + w * (v % 1000) / 1000.0
        v = (v * 1103515245 + 12345) % 2147483648
        py = cy - w * 0.16 + w * 0.32 * (v % 1000) / 1000.0
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (px, py, 0.9 + (v >> 6) % 3 * 0.6))
    out.append('</g>')
    return "".join(out)


def fluke(cx, cy, s, color, op, rot):
    """鲸尾：两叶展开、中缝略低、下方收成尾柄。"""
    a = cx, cy + s
    c1 = (cx - s * 0.08, cy + s * 0.55), (cx - s * 0.60, cy + s * 0.10), (cx - s * 1.20, cy - s * 0.30)
    c2 = (cx - s * 0.85, cy - s * 0.45), (cx - s * 0.35, cy - s * 0.30), (cx, cy - s * 0.16)
    c3 = (cx + s * 0.35, cy - s * 0.30), (cx + s * 0.85, cy - s * 0.45), (cx + s * 1.20, cy - s * 0.30)
    c4 = (cx + s * 0.60, cy + s * 0.10), (cx + s * 0.08, cy + s * 0.55), (cx, cy + s)
    seg = lambda pts: " ".join("%.1f %.1f" % p for p in pts)
    d = "M %.1f %.1f C %s C %s C %s C %s Z" % (a[0], a[1], seg(c1), seg(c2), seg(c3), seg(c4))
    return ('<path d="%s" fill="%s" opacity="%.2f" transform="rotate(%d %.1f %.1f)"/>'
            % (d, color, op, rot, cx, cy))


def whale_sil(cx, cy, s, color, op):
    return ('<g transform="translate(%.1f %.1f) scale(%.4f)" opacity="%.2f">%s</g>'
            % (cx, cy, s / 24.0, op, WHALE_MARK(0, 0, 24.0, color)))


def starfield(x0, y0, x1, y1, n, color, op, seedn=5):
    out = ['<g fill="%s" opacity="%.2f">' % (color, op)]
    v = seedn
    for i in range(n):
        v = (v * 1103515245 + 12345) % 2147483648
        px = x0 + (x1 - x0) * (v % 1000) / 1000.0
        v = (v * 1103515245 + 12345) % 2147483648
        py = y0 + (y1 - y0) * (v % 1000) / 1000.0
        r = 0.9 + ((v >> 7) % 3) * 0.55
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (px, py, r))
    out.append('</g>')
    return "".join(out)


def constellation(x0, y0, x1, y1, color, op):
    pts = [(0.14, 0.30), (0.32, 0.18), (0.46, 0.34), (0.62, 0.22), (0.80, 0.36), (0.68, 0.52)]
    xs = [x0 + (x1 - x0) * a for a, _ in pts]
    ys = [y0 + (y1 - y0) * b for _, b in pts]
    d = "M " + " L ".join("%.1f %.1f" % (a, b) for a, b in zip(xs, ys))
    out = ['<path d="%s" fill="none" stroke="%s" stroke-width="1.1" opacity="%.2f"/>'
           % (d, color, op)]
    for a, b in zip(xs, ys):
        out.append('<circle cx="%.1f" cy="%.1f" r="3.0" fill="%s" opacity="0.8"/>' % (a, b, color))
    return "".join(out)


def compass(cx, cy, r, color, gold):
    out = ['<g fill="none" stroke="%s" stroke-width="1.8" opacity="0.75">' % color,
           '<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r),
           '<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r * 0.78)]
    for i in range(8):
        a = math.radians(i * 45)
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                   % (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78,
                      cx + math.cos(a) * r * 1.16, cy + math.sin(a) * r * 1.16))
    out.append('</g>')
    out.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="%s" opacity="0.8"/>'
               % (cx, cy - r * 0.52, cx + r * 0.17, cy, cx, cy + r * 0.52, cx - r * 0.17, cy, gold))
    return "".join(out)


def buoy(cx, cy, r, color, gold):
    return ('<g opacity="0.85"><path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="%s"/>'
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="0.8"/>'
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6"/></g>'
            % (cx - r * 0.5, cy, cx + r * 0.5, cy, cx, cy - r * 1.35, gold,
               cx - r * 0.5, cy - r * 0.62, r, r * 0.62, color,
               cx, cy - r * 1.35, cx, cy - r * 2.05, color))


def cranes(x0, ytop, x1, ybase, n, color, op):
    out = ['<g fill="none" stroke="%s" stroke-width="2.0" opacity="%.2f">' % (color, op)]
    span = (x1 - x0) / n
    for i in range(n):
        cx = x0 + span * (i + 0.5)
        h = (ybase - ytop) * (0.72 + 0.28 * ((i * 7) % 3) / 2.0)
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx, ybase, cx, ytop + (ybase - ytop) - h))
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                   % (cx - span * 0.30, ytop + (ybase - ytop) - h, cx + span * 0.36, ytop + (ybase - ytop) - h))
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                   % (cx + span * 0.20, ytop + (ybase - ytop) - h, cx + span * 0.20, ytop + (ybase - ytop) - h * 0.62))
    out.append('</g>')
    return "".join(out)


def crates(x0, ytop, x1, ybase, color, gold, op):
    out = ['<g opacity="%.2f">' % op]
    span = (x1 - x0)
    w = span / 7.0
    for i in range(7):
        h = (ybase - ytop) * (0.45 + 0.55 * ((i * 5) % 3) / 2.0)
        cx = x0 + w * i
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" '
                   'stroke="%s" stroke-width="1.5"/>' % (cx, ybase - h, w * 0.86, h, color))
        if i % 3 == 0:
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                       'stroke-width="1.4"/>' % (cx, ybase - h, cx + w * 0.86, ybase, gold))
    out.append('</g>')
    return "".join(out)


def ship(cx, ybase, h, color, gold):
    o = ['<g fill="none" stroke="%s" stroke-width="2.0">' % color]
    o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>'
             % (cx - h * 0.62, ybase, cx + h * 0.62, ybase, cx, ybase + h * 0.24))
    for i, (dx, hh) in enumerate([(-0.36, 0.62), (0.0, 0.82), (0.34, 0.56)]):
        m = cx + h * dx
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (m, ybase, m, ybase - h * hh))
        o.append('<path d="M %.1f %.1f Q %.1f %.1f %.1f %.1f L %.1f %.1f Z" fill="%s" opacity="0.20"/>'
                 % (m, ybase - h * hh * 0.92, m + h * 0.22, ybase - h * hh * 0.55,
                    m, ybase - h * hh * 0.12, m, ybase - h * hh * 0.92, gold))
    o.append('</g>')
    return "".join(o)


# ────────────────────────── 一张券 ──────────────────────────
def note(W, H, spot, theme, denom, cn, en, code, tier, portrait=None, is_sub=False,
         side="front"):
    IN = max(10.0, round(H * 0.0567, 1))
    M = max(4.0, round(H * 0.034, 1))
    paper, paper_l, paper_d = PAL.tint(spot), PAL.tint(spot, 0.910), PAL.tint(spot, 0.835)
    deep = spot
    shade = PAL.shade(spot)
    k = H / 882.0
    o = []

    o.append('<defs>%s'
             '<linearGradient id="pp" x1="0" y1="0" x2="0.9" y2="1">'
             '<stop offset="0" stop-color="%s"/><stop offset="0.55" stop-color="%s"/>'
             '<stop offset="1" stop-color="%s"/></linearGradient>'
             '<radialGradient id="vg" cx="50%%" cy="46%%" r="76%%">'
             '<stop offset="55%%" stop-color="#000" stop-opacity="0"/>'
             '<stop offset="100%%" stop-color="#3A4160" stop-opacity="0.13"/></radialGradient>'
             '<clipPath id="cl"><rect x="%d" y="%d" width="%d" height="%d"/></clipPath>'
             '</defs>' % (ovi_def(), paper_l, paper, paper_d, IN, IN, W - 2 * IN, H - 2 * IN))

    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="url(#pp)"/>' % (M, M, W - 2 * M, H - 2 * M))
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="url(#vg)"/>' % (M, M, W - 2 * M, H - 2 * M))
    o.append('<g clip-path="url(#cl)">')
    o.append(rosette(W * 0.30, H * 0.46, H * 0.55, 16, deep, 0.13, 0.9))
    o.append(rosette(W * 0.78, H * 0.34, H * 0.42, 14, deep, 0.11, 0.9))
    o.append(ellipses(W * 0.5, H * 0.5, W * 0.62, H * 0.86, 12, -8, deep, 0.10, 0.9))
    o.append(waves(H * 0.90, 0, W, H * 0.02, H * 0.11, deep, 0.16, 0.8, 4))
    o.append(back_scene(theme, W * 0.375, H * 0.700, H * 0.255, deep, GOLD_L,
                        W * 0.215, W * 0.560) if side == "back" else
             scene(theme, W, H, IN, spot, deep, GOLD_L))
    o.append('</g>')

    # 人物（仅主币正面）
    if portrait is not None and side == "front":
        bx, by = IN * 0.50, IN * 0.42
        bw, bh = W * 0.435, H * 0.885
        o.append(portrait_markup(bx, by, bw, bh, portrait))

    # 框
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s" '
             'stroke-width="%s"/>' % (M, M, W - 2 * M, H - 2 * M, paper_d, max(1.0, 2.0 * k)))
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s" '
             'stroke-width="%s"/>' % (IN, IN, W - 2 * IN, H - 2 * IN, deep, max(1.6, 3.2 * k)))

    # 主币专属：安全线 / 对印 / 潜像 / 压印（仅正面）
    if not is_sub and side == "front":
        tx = W * 0.504 - 7 * k
        o.append('<g opacity="0.38"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="%s" opacity="0.20"/><rect x="%.1f" y="%.1f" width="%.1f" '
                 'height="%.1f" fill="none" stroke="%s" stroke-width="1.1" '
                 'stroke-dasharray="30 20"/></g>'
                 % (tx, IN + 12, 14 * k, H - 2 * (IN + 12), GOLD_L,
                    tx, IN + 12, 14 * k, H - 2 * (IN + 12), GOLD))
        o.append('<g transform="translate(%.1f %.1f)" opacity="0.9">'
                 '<circle r="%.1f" fill="none" stroke="%s" stroke-width="%.2f"/>'
                 '<path d="M %.1f 0 A %.1f %.1f 0 0 1 %.1f 0 Z" fill="%s" fill-opacity="0.7"/>'
                 '</g>' % (100 * k, 786 * k, 34 * k, deep, 2.2 * k,
                           -22 * k, 22 * k, 22 * k, 22 * k, deep))
        o.append('<text x="%.1f" y="%.1f" font-family="Georgia,serif" font-size="%.1f" '
                 'opacity="0.26" fill="%s" text-anchor="middle" transform="rotate(-12 %.1f %.1f)">%s</text>'
                 % (W * 0.19, H * 0.68, 52 * k, deep, W * 0.19, H * 0.68, denom))

    # 面额数字（OVI）
    o.append('<text x="%.1f" y="%.1f" font-family="Georgia,\'Times New Roman\',serif" '
             'font-size="%.1f" font-weight="700" fill="url(#ovi)" letter-spacing="%.1f">%s</text>'
             % (W * 0.522, H * 0.354, 100 * k, -1.0 * k, denom))
    o.append('<text x="%.1f" y="%.1f" font-family="Georgia,serif" font-size="%.1f" '
             'font-weight="700" fill="%s" letter-spacing="%.1f">%s</text>'
             % (W * 0.524, H * 0.404, 24 * k, deep, 3.0 * k, en))
    o.append('<text x="%.1f" y="%.1f" font-family="\'Microsoft YaHei\',sans-serif" '
             'font-size="%.1f" fill="%s" letter-spacing="%.1f">%s（%s）</text>'
             % (W * 0.524, H * 0.442, 21 * k, deep, 1.5 * k, cn, PAL.UNIT_CN))
    o.append('<text x="%.1f" y="%.1f" font-family="Georgia,serif" font-size="%.1f" '
             'fill="%s" opacity="0.9">₮%s · WYT</text>'
             % (W * 0.524, H * 0.478, 17 * k, deep, denom.replace(",", ",")))

    # 机构名
    o.append('<text x="%.1f" y="%.1f" text-anchor="end" font-family="\'Microsoft YaHei\',sans-serif" '
             'font-size="%.1f" font-weight="700" fill="%s" letter-spacing="%.1f">%s</text>'
             % (W - IN * 1.2, H * 0.159, 40 * k, deep, 8.0 * k, PAL.BANK_CN))
    o.append('<text x="%.1f" y="%.1f" text-anchor="end" font-family="Georgia,serif" '
             'font-size="%.1f" fill="%s" letter-spacing="%.1f" opacity="0.85">%s</text>'
             % (W - IN * 1.2, H * 0.204, 17 * k, deep, 4.0 * k, PAL.BANK_EN))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" '
             'opacity="0.75"/>' % (W * 0.575, H * 0.222, W - IN * 1.2, H * 0.222, GOLD, 1.5 * k))

    # 鲸徽
    ex, ey, er = W * 0.6136, H * 0.694, 124 * k
    o.append('<g transform="translate(%.1f %.1f)">' % (ex, ey))
    o.append('<circle r="%.1f" fill="none" stroke="%s" stroke-width="%.2f" opacity="0.75"/>'
             % (er, deep, 2.0 * k))
    o.append('<circle r="%.1f" fill="none" stroke="%s" stroke-width="%.2f" opacity="0.9"/>'
             % (er * 0.927, GOLD, 2.0 * k))
    o.append('<circle r="%.1f" fill="none" stroke="%s" stroke-width="%.2f" opacity="0.5"/>'
             % (er * 0.742, deep, 1.4 * k))
    o.append('<text y="%.1f" text-anchor="middle" font-family="Georgia,serif" font-size="%.1f" '
             'fill="%s" letter-spacing="%.1f">TOKEN</text>' % (-er * 0.645, 21 * k, deep, 2.0 * k))
    o.append(WHALE_MARK(0, er * 0.032, er * 1.226, "url(#ovi)"))
    o.append('</g>')

    # 法偿
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="\'Microsoft YaHei\',sans-serif" '
             'font-size="%.1f" fill="%s" opacity="0.92" letter-spacing="1.5">本券为法定清偿货币 · 凭券即付 · 不得拒收</text>'
             % (W * 0.825, H * 0.658, 20 * k, deep))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Georgia,serif" '
             'font-size="%.1f" fill="%s" opacity="0.68" letter-spacing="1">LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE</text>'
             % (W * 0.825, H * 0.685, 14 * k, deep))
    if not is_sub:
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Georgia,serif" '
                 'font-size="%.1f" fill="%s" opacity="0.72" letter-spacing="0.3">%s</text>'
                 % (W * 0.825, H * 0.705, 7.5 * k, NAVY, PAL.MICRO))

    # 冠字号
    o.append('<text x="%.1f" y="%.1f" font-family="Consolas,monospace" font-size="%.1f" '
             'font-weight="700" fill="%s" letter-spacing="%.1f">WY %s 8842A</text>'
             % (IN * 1.6, H * 0.9366, 28 * k, NAVY, 2.0 * k, code))
    o.append('<text x="%.1f" y="%.1f" text-anchor="end" font-family="Consolas,monospace" '
             'font-size="%.1f" font-weight="700" fill="%s" opacity="0.58" letter-spacing="%.1f">WY %s 8842A</text>'
             % (W - IN * 2.9, H * 0.9366, 28 * k, NAVY, 2.0 * k, code))

    # 盲文块（右下 6 点）
    o.append('<g transform="translate(%.1f %.1f)" fill="%s" opacity="0.78">'
             % (W - IN * 1.9, H * 0.8566, NAVY))
    for bx, by in [(0, 0), (0, 18), (0, 36), (18, 0), (18, 18), (18, 36)]:
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (bx * k, by * k, 5 * k))
    o.append('</g>')

    # 凸点组（左缘，点数 = 档位）与右缘缺口
    nd = min(tier, 9)
    o.append('<g fill="%s" opacity="0.85">' % deep)
    for i in range(nd):
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>'
                 % (IN * 0.42, H * 0.5 + (i - (nd - 1) / 2.0) * 26 * k, 5.0 * k))
    o.append('</g>')

    # 压印（仅主币）
    if not is_sub:
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Georgia,serif" '
                 'font-size="%.1f" fill="%s" opacity="0.85" letter-spacing="%.1f">%s</text>'
                 % (W * 0.4265, H * 0.8526, 24 * k, shade, 3.0 * k, PAL.IMPRINT))
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="\'Segoe UI\',sans-serif" '
                 'font-size="%.1f" fill="%s" opacity="0.7" letter-spacing="%.1f">%s</text>'
                 % (W * 0.4265, H * 0.8776, 13 * k, shade, 2.0 * k, PAL.IMPRINT_YEARS))

    return ('<g transform="translate(0 0)"><svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 %d %d" width="%d" '
            'height="%d">%s</svg></g>' % (W, H, W, H, "".join(o)))


def beacon(cx, ybase, h, color, gold):
    """灯塔（背面主景）。"""
    o = ['<g stroke="%s" fill="none" stroke-width="2.0">' % color]
    o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>'
             % (cx - h * 0.16, ybase, cx - h * 0.09, ybase - h * 0.72,
                cx + h * 0.09, ybase - h * 0.72, cx + h * 0.16, ybase))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.85">' % color)
    for k in range(5):
        yy = ybase - h * (0.10 + 0.125 * k)
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (cx - h * 0.155 + h * 0.004 * k, yy, h * 0.31 - h * 0.008 * k, h * 0.045))
    o.append('</g>')
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
             % (cx - h * 0.11, ybase - h * 0.80, h * 0.22, h * 0.085, gold))
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="2.0"/>'
             % (cx, ybase - h * 0.88, h * 0.075, color))
    o.append('<g stroke="%s" stroke-width="1.6" opacity="0.5" fill="none">' % gold)
    for d in (-1, 1):
        o.append('<path d="M %.1f %.1f Q %.1f %.1f %.1f %.1f"/>'
                 % (cx + d * h * 0.12, ybase - h * 0.86, cx + d * h * 0.42, ybase - h * 1.00,
                    cx + d * h * 0.62, ybase - h * 0.90))
    o.append('</g>')
    return "".join(o)


def compass(cx, cy, r, color, gold):
    """罗盘玫瑰（背面主景）。"""
    o = ['<g fill="none" stroke="%s" stroke-width="1.6">' % color]
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r))
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" stroke="%s" opacity="0.7"/>' % (cx, cy, r * 0.78, gold))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.85">' % color)
    for k in range(8):
        a = math.pi * 2 * k / 8 - math.pi / 2
        L = r * (0.86 if k % 2 == 0 else 0.5)
        w = r * (0.085 if k % 2 == 0 else 0.05)
        o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>'
                 % (cx + math.cos(a) * L, cy + math.sin(a) * L,
                    cx + math.cos(a + 1.5708) * w, cy + math.sin(a + 1.5708) * w,
                    cx + math.cos(a - 1.5708) * w, cy + math.sin(a - 1.5708) * w))
    o.append('</g>')
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (cx, cy, r * 0.075, gold))
    return "".join(o)


def dome(cx, cy, r, color, gold):
    """星穹：半圆穹顶 + 经纬网格 + 星点。"""
    o = ['<g fill="none" stroke="%s" stroke-width="1.4" opacity="0.8">' % color]
    o.append('<path d="M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f"/>' % (cx - r, cy, r, r, cx + r, cy))
    for k in range(1, 5):
        rr = r * k / 5.0
        o.append('<path d="M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f" opacity="0.55"/>'
                 % (cx - rr, cy, rr, rr, cx + rr, cy))
    for k in range(1, 8):
        a = math.pi * k / 8.0
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" opacity="0.5"/>'
                 % (cx, cy, cx + math.cos(a) * r, cy - math.sin(a) * r))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.75">' % gold)
    for k in range(16):
        a = math.pi * (0.08 + 0.84 * k / 15.0)
        rr = r * (0.35 + 0.6 * ((k * 37) % 11) / 10.0)
        o.append('<circle cx="%.1f" cy="%.1f" r="1.7"/>' % (cx + math.cos(a) * rr, cy - math.sin(a) * rr))
    o.append('</g>')
    return "".join(o)


def chart(cx, cy, w, h, color, gold):
    """海图：经纬网 + 航迹 + 鲸尾。"""
    o = ['<g stroke="%s" stroke-width="0.9" opacity="0.45" fill="none">' % color]
    for k in range(1, 7):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cx - w / 2 + w * k / 7.0, cy - h / 2, cx - w / 2 + w * k / 7.0, cy + h / 2))
    for k in range(1, 5):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cx - w / 2, cy - h / 2 + h * k / 5.0, cx + w / 2, cy - h / 2 + h * k / 5.0))
    o.append('</g>')
    o.append('<path d="M %.1f %.1f Q %.1f %.1f %.1f %.1f T %.1f %.1f" fill="none" stroke="%s" '
             'stroke-width="1.8" stroke-dasharray="9 6"/>'
             % (cx - w * 0.42, cy + h * 0.30, cx - w * 0.12, cy - h * 0.10,
                cx + w * 0.10, cy + h * 0.10, cx + w * 0.44, cy - h * 0.26, gold))
    o.append(fluke(cx + w * 0.30, cy - h * 0.30, h * 0.16, color, 0.85, 14))
    return "".join(o)


def backside(W, H, spot, theme, denom, cn, en, code, tier, is_sub=False):
    """卡片背面：与 100,000,000 券同构，主景按本档主题另画一景。"""
    IN = H * ROBUST_IN
    k = H / 882.0
    paper = PAL.tint(spot)
    deep = PAL.shade(spot)
    o = ['<rect x="0" y="0" width="%.1f" height="%.1f" rx="0" fill="%s"/>' % (W, H, paper)]
    o.append(guilloche(W, H, spot))
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="0" fill="none" stroke="%s" '
             'stroke-width="%.1f"/>' % (IN, IN, W - 2 * IN, H - 2 * IN, deep, 3.0 * k))
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="0" fill="none" stroke="%s" '
             'stroke-width="%.1f" opacity="0.5"/>'
             % (IN + 10 * k, IN + 10 * k, W - 2 * IN - 20 * k, H - 2 * IN - 20 * k, deep, 1.3 * k))
    # 左区：大号面额数字（OVI）+ 中英全称 + 金线 + 中文大写
    o.append('<text x="%.1f" y="%.1f" font-family="Georgia,serif" font-size="%.1f" font-weight="700" '
             'fill="url(#ovi)">%s</text>' % (W * 0.075, H * 0.335, H * 0.115, denom))
    o.append('<text x="%.1f" y="%.1f" font-family="Georgia,serif" font-size="%.1f" font-weight="700" '
             'fill="%s" letter-spacing="%.1f">%s</text>'
             % (W * 0.078, H * 0.395, H * 0.030, PAL.DEEP, 3.0 * k, en))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" '
             'opacity="0.75"/>' % (W * 0.078, H * 0.432, W * 0.44, H * 0.432, GOLD, 1.6 * k))
    o.append('<text x="%.1f" y="%.1f" font-family="\'Microsoft YaHei\',sans-serif" font-size="%.1f" '
             'font-weight="700" fill="%s" letter-spacing="%.1f">%s</text>'
             % (W * 0.078, H * 0.492, H * 0.046, PAL.DEEP, 5.0 * k, cn))
    o.append('<text x="%.1f" y="%.1f" font-family="\'Microsoft YaHei\',sans-serif" font-size="%.1f" '
             'fill="%s" opacity="0.85">单位 TOKEN（%s）· 符号 ₮</text>'
             % (W * 0.078, H * 0.533, H * 0.023, PAL.DEEP, PAL.CODE))
    # 中区：本档主景
    mid = W * 0.545
    o.append(back_scene(theme, mid, H * 0.56, H * 0.40, deep, GOLD,
                        W * 0.30, W * 0.72))
    # 右区：鲸徽 + 机构名 + 法偿
    rx = W * 0.845
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%.1f" '
             'opacity="0.8"/>' % (rx, H * 0.315, H * 0.215, GOLD, 1.8 * k))
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%.1f"/>'
             % (rx, H * 0.315, H * 0.196, deep, 1.6 * k))
    o.append(WHALE_MARK(rx, H * 0.325, H * 0.27, deep))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="\'Microsoft YaHei\','
             'sans-serif" font-size="%.1f" font-weight="700" fill="%s" letter-spacing="%.1f">%s</text>'
             % (rx, H * 0.665, H * 0.040, deep, 2.0 * k, PAL.BANK_CN))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Georgia,serif" '
             'font-size="%.1f" fill="%s" letter-spacing="%.1f">%s</text>'
             % (rx, H * 0.705, H * 0.021, PAL.DEEP, 3.0 * k, PAL.BANK_EN))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" '
             'opacity="0.7"/>' % (rx - W * 0.088, H * 0.728, rx + W * 0.088, H * 0.728, GOLD, 1.3 * k))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="\'Microsoft YaHei\','
             'sans-serif" font-size="%.1f" fill="%s" opacity="0.92">本券为法定清偿货币 · 凭券即付 · '
             '不得拒收</text>' % (rx, H * 0.785, H * 0.023, deep))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Georgia,serif" '
             'font-size="%.1f" fill="%s" opacity="0.68">LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE'
             '</text>' % (rx, H * 0.815, H * 0.016, deep))
    o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Georgia,serif" '
             'font-size="%.1f" fill="%s" opacity="0.72">%s</text>'
             % (rx, H * 0.838, H * 0.0086, PAL.NAVY, PAL.MICRO))
    # 无障碍：盲文块（右下）+ 凸点组（左缘）+ 缺口（右缘）
    o.append(braille(W - IN - 6.0 * PX_MM * k, H - IN - 9.0 * PX_MM * k, k))
    o.append(tactile(W, H, IN, tier, deep))
    # 下沿：冠字号 ×2
    o.append('<text x="%.1f" y="%.1f" font-family="Consolas,\'Courier New\',monospace" '
             'font-size="%.1f" font-weight="700" fill="%s" letter-spacing="%.1f">WY %s 8842A</text>'
             % (IN + 6.0 * PX_MM * k, H - IN * 0.30, H * 0.032, PAL.NAVY, 2.0 * k, code))
    o.append('<text x="%.1f" y="%.1f" text-anchor="end" font-family="Consolas,\'Courier New\','
             'monospace" font-size="%.1f" font-weight="700" fill="%s" opacity="0.58" '
             'letter-spacing="%.1f">WY %s 8842A</text>'
             % (W - IN - 6.0 * PX_MM * k, H - IN * 0.30, H * 0.032, PAL.NAVY, 2.0 * k, code))
    return "".join(o)


def back_scene(theme, cx, cy, h, deep, gold, x0, x1):
    """背面主景：**与正面的主景是不同的一景**。"""
    o = []
    if theme == "引航":
        o.append(beacon(cx, cy + h * 0.46, h * 1.05, deep, gold))
        o.append(waves(cy + h * 0.48, x0, x1, h * 0.05, h * 0.18, deep, 0.45, 0.9, 3))
    elif theme == "夜航":
        o.append(compass(cx, cy - h * 0.05, h * 0.48, deep, gold))
        o.append(spray(cx, cy + h * 0.52, h * 1.1, deep, 18))
        o.append(waves(cy + h * 0.50, x0, x1, h * 0.04, h * 0.16, deep, 0.38, 0.9, 2))
    elif theme == "港市":
        o.append(cranes(x0, cy - h * 0.46, x1, cy + h * 0.42, 2, deep, 0.85))
        o.append(crates(x0 + h * 0.10, cy + h * 0.02, x1 - h * 0.10, cy + h * 0.42, deep, gold, 0.8))
        o.append(waves(cy + h * 0.46, x0, x1, h * 0.045, h * 0.17, deep, 0.42, 0.9, 3))
    elif theme == "守望":
        o.append(beacon(cx, cy + h * 0.44, h * 1.10, deep, gold))
        o.append(waves(cy + h * 0.48, x0, x1, h * 0.045, h * 0.17, deep, 0.42, 0.9, 3))
    elif theme == "星图":
        o.append(dome(cx, cy + h * 0.34, h * 0.72, deep, gold))
        o.append(waves(cy + h * 0.46, x0, x1, h * 0.035, h * 0.14, deep, 0.35, 0.9, 2))
    elif theme == "远洋":
        o.append(chart(cx, cy, h * 1.55, h * 0.82, deep, gold))
        o.append(waves(cy + h * 0.46, x0, x1, h * 0.035, h * 0.14, deep, 0.35, 0.9, 2))
    elif theme == "单尾破浪":
        o.append(waves(cy + h * 0.34, x0, x1, h * 0.055, h * 0.19, deep, 0.45, 1.0, 4))
        o.append(fluke(cx, cy - h * 0.02, h * 0.36, deep, 0.85, -6))
    elif theme == "双尾交浪":
        o.append(waves(cy + h * 0.36, x0, x1, h * 0.05, h * 0.17, deep, 0.42, 1.0, 4))
        o.append(fluke(cx - h * 0.20, cy - h * 0.04, h * 0.30, deep, 0.85, -24))
        o.append(fluke(cx + h * 0.22, cy - h * 0.08, h * 0.26, deep, 0.7, 28))
    elif theme == "环浪饰框":
        o.append('<g fill="none" stroke="%s" stroke-width="1.2" opacity="0.55">' % deep)
        for i in range(10):
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, h * (0.14 + 0.062 * i)))
        o.append('</g>')
        o.append(fluke(cx, cy, h * 0.26, deep, 0.85, 0))
    return "".join(o)


def baseline_img(name, w, h):
    """把已定稿的 1280 DPI 扫描稿缩到本行尺寸、以 data URI 内嵌。

    扫描稿（`--scan` 模式）就是"货币本体"，没有页面底色也没有投影，
    正好可以直接摆进总表；用 1× 那张会把底色和阴影一起带进来。
    """
    import base64
    import io
    from PIL import Image
    p = os.path.join(ROOT, "build", name)
    im = Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return ('<image xlink:href="data:image/png;base64,%s" x="0" y="0" width="%d" height="%d"/>'
            % (base64.b64encode(buf.getvalue()).decode("ascii"), w, h))


def main():
    # **同比例放大 / 缩小**：券长保持 3.2 / 3.1.3 的阶梯不变，券高按 100,000,000 券的
    # 150.0 × 70.0 的比例（150/70 = 2.1429）反算 —— 各档之间只差一个等比缩放系数，
    # 版式一个像素都不重排。
    AR = 150.0 / 70.0

    rows = []
    for i, (denom, L, spot, cname, theme, cn, en, vb) in enumerate(MAIN):
        W = round(L * PX_MM)
        Hpx = round(W / AR)
        if L == 150.0:
            # **100,000,000 是基准稿，必须用已定稿的那两张图**，不能由本脚本重画
            # ——本脚本是"按同一套规则另画一遍"，与 render_mockup.py 的实现必然
            # 有出入，摆在一起就会自相矛盾。这里直接嵌定稿的 1280 DPI 扫描稿
            # （扫描稿是"就是货币本体"，无底色无投影，正好合表）。
            front = baseline_img("mockup-100-scan.png", W, Hpx)
            back = baseline_img("reverse-100-scan.png", W, Hpx)
        else:
            front = note(W, Hpx, spot, theme, denom, cn, en, denom.replace(",", ""),
                         i + 4, portrait=vb, is_sub=False)
            back = note(W, Hpx, spot, theme, denom, cn, en, denom.replace(",", ""),
                        i + 4, portrait=None, is_sub=False, side="back")
        rows.append((i + 4, denom, L, round(Hpx / PX_MM, 1), spot, cname, theme, cn, front, back))
    for i, (denom, L, _Hm, spot, cname, theme, cn, en, code) in enumerate(SUB):
        W = round(L * PX_MM)
        Hpx = round(W / AR)
        front = note(W, Hpx, spot, theme, denom, cn, en, code, i + 1, is_sub=True)
        back = note(W, Hpx, spot, theme, denom, cn, en, code, i + 1, is_sub=True, side="back")
        rows.append((i + 1, denom + " 分", L, round(Hpx / PX_MM, 1), spot, cname, theme, cn,
                     front, back))

    total_w = max(round(r[2] * PX_MM) for r in rows)
    LG, GAP = 300, 46
    CW = LG + total_w + 90
    y = 120
    body = []
    body.append('<text x="34" y="58" font-family="Georgia,serif" font-size="34" font-weight="700" '
                'fill="#1B2657">鲸元券 · 全系列面额（3 辅币 + 6 主币）</text>')
    body.append('<text x="34" y="90" font-family="Georgia,serif" font-size="17" fill="#1B2657" '
                'opacity="0.7">WHALE-YUAN NOTE — FULL DENOMINATION SERIES · 真实相对尺寸 · '
                '尺寸 / 色调 / 主题三维同时分级</text>')
    for tier, denom, L, Hm, spot, cname, theme, cn, svg, svgb in rows:
        W = round(L * PX_MM)
        Hpx = round(Hm * PX_MM)
        x = LG + (total_w - W)
        body.append('<text x="34" y="%d" font-family="Georgia,serif" font-size="26" '
                    'font-weight="700" fill="#1B2657">%s</text>' % (y + 34, denom))
        body.append('<text x="34" y="%d" font-family="\'Microsoft YaHei\',sans-serif" font-size="17" '
                    'fill="#1B2657" opacity="0.85">%s　%s　「%s」</text>'
                    % (y + 60, L, cname, theme))
        body.append('<text x="34" y="%d" font-family="Georgia,serif" font-size="14" '
                    'fill="#1B2657" opacity="0.6">%s × %s mm　%s</text>'
                    % (y + 82, L, Hm, spot))
        body.append('<text x="34" y="%d" font-family="\'Microsoft YaHei\',sans-serif" font-size="13" '
                    'fill="#1B2657" opacity="0.55">档位 %d　触觉点 %d ／ 缺口 %d</text>'
                    % (y + 102, tier, min(tier, 9), min(tier, 9)))
        body.append('<g transform="translate(%d %d)">%s</g>' % (x, y, svg))
        body.append('<text x="%d" y="%d" font-family="Georgia,serif" font-size="13" '
                    'fill="#1B2657" opacity="0.5">正面 FRONT</text>' % (x, y - 8))
        body.append('<g transform="translate(%d %d)">%s</g>' % (x, y + Hpx + 14, svgb))
        body.append('<text x="%d" y="%d" font-family="Georgia,serif" font-size="13" '
                    'fill="#1B2657" opacity="0.5">背面 BACK</text>' % (x, y + Hpx + 6))
        y += Hpx * 2 + 56 + GAP

    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;background:#EEF0F4}svg{display:block}</style></head><body>'
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 %d %d" width="%d" height="%d" style="background:#EEF0F4">%s</svg>'
            '</body></html>' % (CW, y + 40, CW, y + 40, "".join(body)))
    out_html = os.path.join(ROOT, "build", "series-all.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print("written: %s  canvas %d x %d" % (out_html, CW, y + 40))


if __name__ == "__main__":
    main()
