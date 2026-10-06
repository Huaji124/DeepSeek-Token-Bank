# -*- coding: utf-8 -*-
"""鲸元券 · 100 鲸元 背面（票面图稿）。

背面设计原则（与正面分工）：
  正面 = 人物与国族叙事（「守望」）；背面 = 建筑/器物与法偿文本，不放人物。
  背面是「防伪重镇」：微缩文字带、对印圆环、光变墨块、开窗安全线全部在此收口。
输出：build/reverse-100.html / reverse-100.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palette as PAL
from whale_mark import whale as WHALE_MARK, whale_ring as WHALE_RING

ROOT = r"E:\Agent项目\鲸元券"

# 扫描模式（`python render_reverse.py --scan`）：纸面铺满整幅、无页面底色、无投影
SCAN = "--scan" in sys.argv

# ── 逐档出稿：`$env:WY_TIER = "0".."5"`，默认 3 = 100,000,000 ──
# 版式一行不动，只换专色与面额文字。TIER=3 必须与既有定稿逐字节一致。
TIER = int(os.environ.get("WY_TIER", "3"))
NAVY, DEEP = PAL.SERIES[TIER][2], "#2A3A7A"
GOLD, GOLD_L = PAL.GOLD, PAL.GOLD_L
PAPER_L_, PAPER, PAPER_D = PAL.paper_ramp(NAVY)   # 纸色 = 专色同色相浅色版（用户 m01275）
PALE = PAPER_L_
BANK_CN, BANK_EN = PAL.BANK_CN, PAL.BANK_EN
W, H, IN = 1890, 882, 50
M = 0 if SCAN else 30
DENOM = PAL.SERIES[TIER][0]
CN_DENOM = PAL.SERIES[TIER][5].replace(" TOKEN", "")
EN_DENOM = PAL.SERIES[TIER][6]
SERIAL = "WY " + DENOM.replace(",", "") + " 8842A"
# 盲文单元：按档位编成布莱叶数字，正反面同一组点（见 palette.braille_dots）。
BRAILLE = "".join('<circle cx="%g" cy="%g" r="%g"/>' % d for d in PAL.braille_dots(TIER))
MICRO = (PAL.MICRO + DENOM.replace(",", "") + "TOKEN") * 2


def ellipses(cx, cy, rx, ry, n, stroke, sw, op, rot=0.0):
    return "\n".join(
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*(i+1)/n:.1f}" ry="{ry*(i+1)/n:.1f}" '
        f'fill="none" stroke="{stroke}" stroke-width="{sw}" opacity="{op:.2f}" '
        f'transform="rotate({rot:g} {cx} {cy})"/>' for i in range(n))


def rosette(cx, cy, rx, ry, n, stroke, sw, op):
    return ('<g class="ln">' + ellipses(cx, cy, rx, ry, n, stroke, sw, op)
            + ellipses(cx, cy, rx, ry, n, stroke, sw, op, 30)
            + ellipses(cx, cy, rx, ry, n, stroke, sw, op, 60) + '</g>')


def wave(cx, cy, w, amp, period, stroke, sw, op, rows=5, gap=14):
    out = []
    for r in range(rows):
        y0 = cy + r * gap
        d = [f"M {cx-w/2:.0f} {y0:.0f}"]
        n = int(w / (period / 2))
        for s in range(n):
            x = cx - w / 2 + s * (period / 2)
            d.append(f"Q {x-period/8:.0f} {y0+(amp*0.95*(1 if s % 2 else -1)):.0f} {x:.0f} "
                     f"{y0+(amp*(1 if s % 2 else -1)):.0f}")
        out.append(f'<path d="{" ".join(d)}" fill="none" stroke="{stroke}" '
                   f'stroke-width="{sw}" opacity="{op:.2f}"/>')
    return '<g class="ln">' + "".join(out) + '</g>'


# ── 背面主景：鲸元灯塔（几何构成，非照片）────────────────────────────
def back_scene(tier, cx, base_y, hgt, body, band):
    """逐档背面主景。

    **版式一律不动**，只有正中央这一组图元按档位换 —— 与正面"同一版式、只换
    文字与专色"是同一套办法。TIER=3（100,000,000，基准档）仍返回原来那座灯塔，
    输出须与既有定稿逐字节一致。
    """
    if tier == 3:                                   # 守望 · 灯塔（基准，勿改）
        return lighthouse(cx, base_y, hgt, body, band)
    if tier == 0:                                   # 引航 · 灯浮标与航道浪
        return buoy(cx, base_y, hgt * 1.20, body, band)
    if tier == 1:                                   # 夜航 · 罗盘玫瑰（加大）
        return compass(cx, base_y - hgt * 0.46, hgt * 0.40, body, band)
    if tier == 2:                                   # 港市 · 门吊与货箱
        return harbour(cx, base_y, hgt, body, band) + wave(
            cx, base_y + hgt * 0.090, hgt * 1.20, hgt * 0.018, hgt * 0.105,
            body, 1.4, 0.32, 3, hgt * 0.048)
    if tier == 4:                                   # 星图 · 北斗七星（加大）
        return dipper(cx, base_y - hgt * 0.50, hgt * 1.30, body, band)
    return rose32(cx, base_y - hgt * 0.46, hgt * 0.42, body, band)     # 远洋 · 海图罗经


def dipper(cx, cy, w, body, band):
    """北斗七星（大熊座）。

    七颗星的真实相对位置 —— 斗魁四星（天枢/天璇/天玑/天权）成一梯形，
    斗柄三星（玉衡/开阳/摇光）自天权向右上弯出。这里按视星等定半径：
    玉衡、天枢、摇光最亮，天权最暗。**不是随便撒一把星星** ——
    星图这种东西，认得出是北斗才有意义。
    """
    # (x, y) 归一化：x 向右 0~1，y 向下 0~1
    P = [(0.06, 0.44), (0.10, 0.70), (0.34, 0.63), (0.32, 0.34),
         (0.58, 0.29), (0.78, 0.15), (1.00, 0.00)]
    MAG = (1.79, 2.37, 2.44, 3.31, 1.77, 2.23, 1.86)      # 视星等，越小越亮
    EDGE = [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (4, 5), (5, 6)]
    x0, y0 = cx - w / 2, cy - w * 0.30
    o = ['<g fill="none" stroke="%s" stroke-width="%.1f" opacity="0.42">'
         % (body, max(w * 0.010, 1.0))]
    for a, b in EDGE:
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (x0 + w * P[a][0], y0 + w * P[a][1], x0 + w * P[b][0], y0 + w * P[b][1]))
    o.append('</g>')
    for (px, py), m in zip(P, MAG):
        r = w * (0.048 - 0.0075 * (m - 1.7))
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
                 % (x0 + w * px, y0 + w * py, r, body))
    # 天枢→天璇 是"指极星"，延长五倍即北极星；点一颗小的示意
    dx, dy = P[1][0] - P[0][0], P[1][1] - P[0][1]
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="0.55"/>'
             % (x0 + w * (P[0][0] - dx * 1.6), y0 + w * (P[0][1] - dy * 1.6), w * 0.016, band))
    # 背景散星
    o.append('<g fill="%s" opacity="0.35">' % body)
    for i in range(26):
        v = (i * 2654435761 + 12345) % 2147483648
        ax = x0 - w * 0.10 + w * 1.20 * (v % 997) / 997.0
        v = (v * 1103515245 + 12345) % 2147483648
        ay = y0 - w * 0.14 + w * 1.05 * (v % 991) / 991.0
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>'
                 % (ax, ay, 0.9 + (v >> 7) % 3 * 0.55))
    o.append('</g>')
    return "".join(o)


def rose32(cx, cy, r, body, band):
    """三十二向罗经花：八长十六短三十二细 + 恒向线。

    远洋海图的标配。**长针指八方位、短针指十六方位、细针指三十二方位**，
    外圈双环加刻度，四正向配金色。
    """
    import math as _m
    o = ['<g fill="none" stroke="%s" stroke-width="1.5" opacity="0.7">' % body]
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r))
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" opacity="0.55"/>' % (cx, cy, r * 0.94))
    o.append('</g>')
    # 三十二向针：按 11.25° 一档
    for k in range(32):
        ang = _m.radians(k * 11.25)
        if k % 4 == 0:
            ln, wd, op, col = 0.84, 3.4, 0.92, body
        elif k % 2 == 0:
            ln, wd, op, col = 0.58, 2.4, 0.72, body
        else:
            ln, wd, op, col = 0.36, 1.6, 0.50, body
        x2 = cx + _m.sin(ang) * r * ln
        y2 = cy - _m.cos(ang) * r * ln
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="%.1f" opacity="%.2f"/>' % (cx, cy, x2, y2, col, wd, op))
    # 四正向金色针（更长）
    o.append('<g stroke="%s" stroke-width="1.9" opacity="0.85">' % band)
    for k in range(4):
        ang = _m.radians(k * 90)
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cx, cy, cx + _m.sin(ang) * r * 0.99, cy - _m.cos(ang) * r * 0.99))
    o.append('</g>')
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (cx, cy, r * 0.055, band))
    # 恒向线：从罗经花向外辐射的细线
    o.append('<g stroke="%s" stroke-width="1.2" opacity="0.20">' % body)
    for k in range(16):
        ang = _m.radians(k * 22.5)
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cx + _m.sin(ang) * r * 1.02, cy - _m.cos(ang) * r * 1.02,
                    cx + _m.sin(ang) * r * 1.55, cy - _m.cos(ang) * r * 1.55))
    o.append('</g>')
    return "".join(o)


def compass(cx, cy, r, body, band):
    o = ['<g fill="none" stroke="%s" stroke-width="1.6" opacity="0.75">' % body]
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r))
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" opacity="0.5"/>' % (cx, cy, r * 0.82))
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" opacity="0.3"/>' % (cx, cy, r * 0.26))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.85">' % body)
    for k in range(4):
        a = k * 90.0
        o.append('<path transform="rotate(%.1f %.1f %.1f)" d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>'
                 % (a, cx, cy, cx, cy - r * 0.94, cx + r * 0.11, cy, cx, cy - r * 0.10))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.7">' % band)
    for k in range(4):
        o.append('<path transform="rotate(%.1f %.1f %.1f)" d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>'
                 % (k * 90 + 45, cx, cy, cx, cy - r * 0.56, cx + r * 0.075, cy, cx, cy - r * 0.07))
    o.append('</g>')
    return "".join(o)


def harbour(cx, base_y, hgt, body, band):
    o = ['<g fill="none" stroke="%s" stroke-width="2.0" opacity="0.85">' % body]
    for dx in (-0.40, 0.22):
        x = cx + hgt * dx
        o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f"/>'
                 % (x, base_y, x, base_y - hgt * 0.72, x + hgt * 0.30, base_y - hgt * 0.72))
        o.append('<path d="M %.1f %.1f L %.1f %.1f"/>'
                 % (x + hgt * 0.04, base_y - hgt * 0.62, x + hgt * 0.26, base_y - hgt * 0.62))
        o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f"/>'
                 % (x + hgt * 0.15, base_y - hgt * 0.62, x + hgt * 0.15, base_y - hgt * 0.44,
                    x + hgt * 0.15, base_y - hgt * 0.44))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.30" stroke="%s" stroke-width="1.4">' % (band, body))
    for k, (dx, w, h) in enumerate([(-0.30, 0.22, 0.16), (-0.04, 0.18, 0.22),
                                    (0.16, 0.24, 0.13), (0.40, 0.16, 0.19)]):
        x = cx + hgt * dx
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (x, base_y - hgt * h, hgt * w, hgt * h))
    o.append('</g>')
    return "".join(o)


def sky(cx, cy, r, body, band):
    pts = [(-0.86, -0.24), (-0.55, 0.32), (-0.24, -0.46), (0.06, 0.10), (0.34, -0.30),
           (0.62, 0.26), (0.88, -0.12), (-0.44, -0.10), (0.20, 0.48), (0.74, -0.48)]
    o = ['<g fill="none" stroke="%s" stroke-width="1.2" opacity="0.55">' % body]
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (2, 7), (7, 1), (3, 8), (4, 9)):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cx + r * pts[a][0], cy + r * pts[a][1], cx + r * pts[b][0], cy + r * pts[b][1]))
    o.append('</g>')
    for k, (dx, dy) in enumerate(pts):
        rr = r * (0.085 if k % 3 else 0.13)
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="%.2f"/>'
                 % (cx + r * dx, cy + r * dy, rr, band if k % 3 == 0 else body,
                    0.85 if k % 3 == 0 else 0.65))
    return "".join(o)


def seachart(cx, cy, r, body, band):
    o = ['<g fill="none" stroke="%s" stroke-width="1.1" opacity="0.5">' % body]
    for i in range(1, 7):
        rr = r * i / 6.0
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, rr))
    for a in range(0, 180, 30):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" transform="rotate(%d %.1f %.1f)"/>'
                 % (cx - r, cy, cx + r, cy, a, cx, cy))
    o.append('</g>')
    o.append('<g fill="%s" opacity="0.7">' % body)
    for dx, dy, s in ((-0.52, 0.20, 0.10), (0.18, -0.34, 0.13), (0.52, 0.30, 0.09)):
        o.append('<path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f '
                 'C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Z"/>'
                 % (cx + r * dx, cy + r * (dy + s),
                    cx + r * (dx - s), cy + r * dy, cx + r * (dx + s) * 0.4, cy + r * (dy - s),
                    cx + r * dx, cy + r * (dy - s),
                    cx + r * (dx + s), cy + r * dy, cx + r * (dx - s) * 0.4, cy + r * (dy - s),
                    cx + r * dx, cy + r * (dy + s),
                    cx + r * dx, cy + r * (dy + s), cx + r * dx, cy + r * (dy + s),
                    cx + r * dx, cy + r * (dy + s)))
    o.append('</g>')
    return "".join(o)


def buoy(cx, base_y, hgt, body, band):
    """灯浮标：锥形浮体 + 桁架桅 + 顶灯与光弧 + 两道航道浪。

    10,000,000 档原与 100,000,000 档同为灯塔，两档背面撞图；改为浮标后
    一眼可分，也不动版式（仍占原来那组图元的位置与尺度）。
    """
    o = ['<g fill="none" stroke="%s" stroke-width="%.1f">' % (body, hgt * 0.026)]
    w = hgt * 0.20
    # 浮体：上宽下窄的梯形，底面浸在水里
    o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"/>'
             % (cx - w, base_y - hgt * 0.10, cx + w, base_y - hgt * 0.10,
                cx + w * 0.42, base_y + hgt * 0.075, cx - w * 0.42, base_y + hgt * 0.075))
    # 水线
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke-width="%.1f"/>'
             % (cx - w * 1.5, base_y - hgt * 0.005, cx + w * 1.5, base_y - hgt * 0.005, hgt * 0.014))
    o.append('</g>')
    # 桅与横撑
    o.append('<g stroke="%s" stroke-width="%.1f" stroke-linecap="round">' % (body, hgt * 0.020))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
             % (cx, base_y - hgt * 0.10, cx, base_y - hgt * 0.42))
    o.append('</g>')
    o.append('<g fill="none" stroke="%s" stroke-width="%.1f">' % (body, hgt * 0.016))
    for k in (0.20, 0.30):
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cx - w * 0.55, base_y - hgt * k, cx + w * 0.55, base_y - hgt * k))
    o.append('</g>')
    # 顶灯（实心 + 金色灯冠）
    o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
             % (cx, base_y - hgt * 0.455, hgt * 0.030, body))
    o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="%s"/>'
             % (cx - hgt * 0.038, base_y - hgt * 0.455, cx + hgt * 0.038, base_y - hgt * 0.455,
                cx, base_y - hgt * 0.525, band))
    # 光弧
    o.append('<g fill="none" stroke="%s" stroke-width="%.1f" opacity="0.5">'
             % (band, max(hgt * 0.010, 1.2)))
    for k in (0.075, 0.115):
        o.append('<path d="M %.1f %.1f Q %.1f %.1f %.1f %.1f"/>'
                 % (cx - hgt * k, base_y - hgt * 0.49, cx, base_y - hgt * (0.49 + k * 0.55),
                    cx + hgt * k, base_y - hgt * 0.49))
    o.append('</g>')
    # 两道航道浪
    o.append(wave(cx, base_y + hgt * 0.055, hgt * 1.15, hgt * 0.020,
                  hgt * 0.115, body, 1.4, 0.35, 3, hgt * 0.050))
    return "".join(o)


def lighthouse(cx, base_y, hgt, body, band):
    """以灯塔作为背面主景：石砌塔身收分、观景台、灯室、双侧光弧、基座礁石。"""
    top = base_y - hgt
    y_deck = top + hgt * 0.185          # 观景台高度
    y_body = top + hgt * 0.235          # 塔身顶（收分上端）
    hw = hgt * 0.150                    # 塔基半宽
    tw = hgt * 0.088                    # 塔身顶半宽
    p = []
    # 塔身（实心梯形，带描边）
    p.append(f'<path d="M {cx-hw:.1f} {base_y} L {cx-tw:.1f} {y_body:.1f} '
             f'L {cx+tw:.1f} {y_body:.1f} L {cx+hw:.1f} {base_y} Z" '
             f'fill="{PALE}" stroke="{body}" stroke-width="3.4" stroke-linejoin="round"/>')
    # 横向色带：把塔身按高度分 6 段，色带取每段中间
    for k in range(6):
        f_ = (k + 0.5) / 6.0
        yk = y_body + (base_y - y_body) * f_
        wk = tw + (hw - tw) * f_
        p.append(f'<line x1="{cx-wk:.1f}" y1="{yk:.1f}" x2="{cx+wk:.1f}" y2="{yk:.1f}" '
                 f'stroke="{body}" stroke-width="{hgt*0.036:.1f}" opacity="0.85"/>')
    # 观景台（外挑围栏）
    p.append(f'<rect x="{cx-hw*1.26:.1f}" y="{y_deck:.1f}" width="{hw*2.52:.1f}" '
             f'height="{hgt*0.030:.1f}" fill="{body}"/>')
    p.append(f'<line x1="{cx-hw*1.26:.1f}" y1="{y_deck+hgt*0.030:.1f}" x2="{cx+hw*1.26:.1f}" '
             f'y2="{y_deck+hgt*0.030:.1f}" stroke="{body}" stroke-width="2" opacity="0.6"/>')
    # 灯室（梯形玻璃房）
    p.append(f'<path d="M {cx-tw*1.05:.1f} {y_deck:.1f} L {cx-tw*0.88:.1f} {top+hgt*0.080:.1f} '
             f'L {cx+tw*0.88:.1f} {top+hgt*0.080:.1f} L {cx+tw*1.05:.1f} {y_deck:.1f} Z" '
             f'fill="{band}" stroke="{body}" stroke-width="2.8"/>')
    p.append(f'<line x1="{cx:.1f}" y1="{top+hgt*0.080:.1f}" x2="{cx:.1f}" y2="{y_deck:.1f}" '
             f'stroke="{body}" stroke-width="2" opacity="0.75"/>')
    # 穹顶 + 避雷针
    p.append(f'<path d="M {cx-tw*0.88:.1f} {top+hgt*0.080:.1f} '
             f'Q {cx:.1f} {top-hgt*0.030:.1f} {cx+tw*0.88:.1f} {top+hgt*0.080:.1f} Z" '
             f'fill="{body}"/>')
    p.append(f'<line x1="{cx:.1f}" y1="{top-hgt*0.030:.1f}" x2="{cx:.1f}" '
             f'y2="{top-hgt*0.072:.1f}" stroke="{body}" stroke-width="3"/>')
    p.append(f'<circle cx="{cx:.1f}" cy="{top-hgt*0.078:.1f}" r="{hgt*0.011:.1f}" fill="{body}"/>')
    # 双侧光弧
    for d in (1, -1):
        p.append(f'<path d="M {cx+d*tw*1.30:.1f} {top+hgt*0.115:.1f} '
                 f'Q {cx+d*tw*4.4:.1f} {top+hgt*0.040:.1f} {cx+d*tw*8.0:.1f} '
                 f'{top+hgt*0.128:.1f}" fill="none" stroke="{GOLD}" stroke-width="3" '
                 f'opacity="0.60" stroke-linecap="round"/>')
        p.append(f'<path d="M {cx+d*tw*1.30:.1f} {top+hgt*0.140:.1f} '
                 f'Q {cx+d*tw*3.9:.1f} {top+hgt*0.108:.1f} {cx+d*tw*6.9:.1f} '
                 f'{top+hgt*0.196:.1f}" fill="none" stroke="{GOLD}" stroke-width="2" '
                 f'opacity="0.38" stroke-linecap="round"/>')
    # 基座礁石
    p.append(f'<path d="M {cx-hw*1.9:.1f} {base_y:.1f} '
             f'Q {cx-hw*0.95:.1f} {base_y-hgt*0.034:.1f} {cx:.1f} {base_y-hgt*0.024:.1f} '
             f'Q {cx+hw*1.0:.1f} {base_y-hgt*0.036:.1f} {cx+hw*1.9:.1f} {base_y:.1f} Z" '
             f'fill="{body}" opacity="0.92"/>')
    return "".join(p)


svg_body = f'''
  <defs>
    <linearGradient id="paper" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0%" stop-color="{PAPER_L_}"/><stop offset="55%" stop-color="{PAPER}"/>
      <stop offset="100%" stop-color="{PAPER_D}"/>
    </linearGradient>
    <radialGradient id="vign" cx="50%" cy="46%" r="76%">
      <stop offset="55%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#3A4160" stop-opacity="0.13"/>
    </radialGradient>
    <!-- userSpaceOnUse 版纸色渐变，**专供小面积"擦白"**（背面版）。
         角位对印必须落在无底纹区域，否则防伪网线会从圆内穿过。 -->
    <linearGradient id="paperU" gradientUnits="userSpaceOnUse"
                    x1="{M}" y1="{M}" x2="{M+0.35*(W-2*M):.1f}" y2="{H-M}">
      <stop offset="0" stop-color="{PAPER_L_}"/><stop offset="0.55" stop-color="{PAPER}"/>
      <stop offset="1" stop-color="{PAPER_D}"/>
    </linearGradient>
    <!-- 光变油墨（OVI）：与正面同一套色标。背面同样**不设独立色块**，
         只施加在面额数字主块上（规范书 2.4.1 / 5.1 F-04）。 -->
    <linearGradient id="ovi" x1="0.05" y1="0" x2="0.95" y2="1">
      <stop offset="0.00" stop-color="#2F6B4F"/>
      <stop offset="0.20" stop-color="#3E8C7A"/>
      <stop offset="0.40" stop-color="#3D6E9E"/>
      <stop offset="0.60" stop-color="#6B4E9C"/>
      <stop offset="0.80" stop-color="#9C5A6E"/>
      <stop offset="1.00" stop-color="#B08A3E"/>
    </linearGradient>
    <linearGradient id="ovigloss" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0.00" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="0.38" stop-color="#FFFFFF" stop-opacity="0.34"/>
      <stop offset="0.52" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="1.00" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="inner"><rect x="{IN}" y="{IN}" width="{W-2*IN}" height="{H-2*IN}" rx="0"/></clipPath>
    <pattern id="mesh" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="7" stroke="{NAVY}" stroke-width="0.45" opacity="0.30"/>
    </pattern>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="7" stdDeviation="11" flood-color="#141838" flood-opacity="0.28"/>
    </filter>
  </defs>

  <g{'' if SCAN else ' filter="url(#shadow)"'}>
    <rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="0" fill="url(#paper)"/>
    <rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="0" fill="url(#vign)"/>
  </g>

  <g clip-path="url(#inner)">
    <rect x="{IN}" y="{IN}" width="{W-2*IN}" height="{H-2*IN}" fill="url(#mesh)"/>

    {rosette(300, 466, 300, 356, 26, NAVY, 0.8, 0.20)}
    {rosette(1596, 466, 300, 356, 26, NAVY, 0.8, 0.20)}
    <g class="ln">{ellipses(948, 466, 760, 372, 30, DEEP, 0.7, 0.11)}</g>
    {wave(948, 792, 1180, 12, 92, NAVY, 0.95, 0.20, rows=3, gap=16)}
    {wave(948, 92, 1180, 11, 92, NAVY, 0.95, 0.15, rows=2, gap=16)}

    <rect x="{IN}" y="{IN}" width="{W-2*IN}" height="{H-2*IN}" rx="0" fill="none"
          stroke="{NAVY}" stroke-width="3" opacity="0.85"/>
    <rect x="{IN+10}" y="{IN+10}" width="{W-2*(IN+10)}" height="{H-2*(IN+10)}" rx="0" fill="none"
          stroke="{NAVY}" stroke-width="1" opacity="0.5"/>

    <!-- ===== 左区：面额字（大号，识别优先）===== -->
    <text x="112" y="300" font-family="Georgia,'Times New Roman',serif" font-size="86"
          font-weight="700" fill="url(#ovi)">{DENOM}</text>
    <text x="116" y="352" font-family="Georgia,serif" font-size="26" font-weight="700"
          fill="{DEEP}" letter-spacing="4">{EN_DENOM}</text>
    <line x1="116" y1="382" x2="660" y2="382" stroke="{GOLD}" stroke-width="1.6" opacity="0.75"/>
    <text x="116" y="434" font-family="'Microsoft YaHei','SimHei',sans-serif" font-size="40"
          font-weight="700" fill="{DEEP}" letter-spacing="6">{CN_DENOM} TOKEN</text>
    <text x="116" y="470" font-family="'Microsoft YaHei','SimHei',sans-serif" font-size="20"
          fill="{DEEP}" opacity="0.78" letter-spacing="1.6">单位 TOKEN（WYT）· 符号 ₮</text>

    <!-- 潜像：倾斜观察显现面额数字 -->
    <g transform="rotate(-12 340 596)" opacity="0.34">
      <text x="340" y="596" text-anchor="middle" font-family="Georgia,serif" font-size="52"
            font-weight="700" fill="{NAVY}" letter-spacing="1">{DENOM}</text>
    </g>
    <!-- 盲文块：与正面**同一个物理点**、**同一组点**。正面的盲文在券面右下角
         (1791,765)，翻面后左右互换 → 背面在**左下角** (76, 765)：1890 − 1814 = 76。
         点数按档位走布莱叶数字（palette.braille_dots），两面必须一致。 -->
    <g transform="translate(76 765)" fill="{NAVY}" opacity="0.78">
      {BRAILLE}
    </g>

    <!-- 对印标记：**背面只印下半**，与正面 (100, 786) 同点同径（Ø 68 px）。
         翻面后正面左下角（物理点 X=100）落在背面右下角 X = 1890 − 100 = 1790。 -->
    <!-- 年版与厂标：打在**角位对印的左侧**、与对印同一水平带上
         （对印中心 (1790, 786)、半径 34 ⇒ 左缘 1756）。各档同点。 -->
    <text x="1604" y="795" font-family="'Microsoft YaHei','SimHei',sans-serif"
          font-size="22" fill="{DEEP}" opacity="0.78" letter-spacing="1">2026年</text>
    {WHALE_MARK(1724, 786, 38, NAVY)}

    <g transform="translate(1790 786)">
      <!-- 先擦出一块干净纸面：角位对印必须落在**无底纹**的区域，否则防伪网线
           会从圆内穿过去。纸色用 userSpaceOnUse 渐变、再补回网点与四周压暗，
           颜色与该处纸面一致，看不出边界。 -->
      <circle r="35.5" fill="url(#paperU)"/>
      <circle r="34" fill="none" stroke="{NAVY}" stroke-width="2.2" opacity="0.9"/>
      <path d="M -22 0 A 22 22 0 0 0 22 0 Z" fill="{NAVY}" fill-opacity="0.7"/>
    </g>

    <!-- ===== 中区：灯塔主景 ===== -->
    {back_scene(TIER, 948, 668, 372, NAVY, GOLD_L)}
    <g transform="translate(948 636)">
      <path d="M -300 0 Q -150 -26 0 -14 Q 150 -26 300 0" fill="none"
            stroke="{NAVY}" stroke-width="2.6" opacity="0.42"/>
      <path d="M -262 22 Q -131 0 0 10 Q 131 0 262 22" fill="none"
            stroke="{NAVY}" stroke-width="1.8" opacity="0.28"/>
    </g>

    <!-- 对印圆环（旧版，已废止）：旧的独立圆环与正面不同形不同点，
         不满足「正背同点同径」，已由上方 (1790, 786) 的对印标记取代。 -->

    <!-- ===== 右区：鲸徽 + 机构名 ===== -->
    <!-- 行徽：鲸鱼本体施**光变油墨**（与正面同款，`#ovi` + `#ovigloss` 叠印），
         圆环仍用专色。早先这里把鲸鱼填成实心 NAVY，OVI 就丢了 —— 正面有、反面没有，
         同一枚图案在两面表现不一致。`whale_ring` 会把 color 同时用到环上，故此处
         手绘三个环、鲸鱼单独调用。 -->
    <g transform="translate(1560 300)">
      <circle r="176" fill="none" stroke="{GOLD}" stroke-width="1.4" opacity="0.7"/>
      <circle r="173" fill="none" stroke="{NAVY}" stroke-width="2.6" opacity="0.55"/>
      <circle r="136" fill="none" stroke="{NAVY}" stroke-width="1" opacity="0.28"/>
      {WHALE_MARK(0, 0, 232, "url(#ovi)")}
      {WHALE_MARK(0, 0, 232, "url(#ovigloss)")}
    </g>
    <text x="1560" y="530" text-anchor="middle" font-family="'Microsoft YaHei',sans-serif"
          font-size="34" font-weight="700" fill="{NAVY}" letter-spacing="2">{BANK_CN}</text>
    <text x="1560" y="562" text-anchor="middle" font-family="Georgia,serif" font-size="19"
          font-weight="600" fill="{DEEP}" letter-spacing="3.4" opacity="0.85">{BANK_EN}</text>
    <line x1="1348" y1="582" x2="1772" y2="582" stroke="{GOLD}" stroke-width="1.3" opacity="0.8"/>

    <!-- ===== 法偿声明（背面的法定文本区）===== -->
    <text x="1560" y="640" text-anchor="middle" font-family="'Microsoft YaHei',sans-serif"
          font-size="21" fill="{DEEP}" opacity="0.92" letter-spacing="2">本券为法定清偿货币 · 凭券即付 · 不得拒收</text>
    <text x="1560" y="666" text-anchor="middle" font-family="Georgia,serif" font-size="15"
          fill="{DEEP}" opacity="0.66" letter-spacing="1.1">LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE</text>
    <text x="1560" y="700" text-anchor="middle" font-family="'Microsoft YaHei',sans-serif"
          font-size="15" fill="{DEEP}" opacity="0.72" letter-spacing="1.6">{BANK_CN}承诺兑付等值本位资产</text>

    <!-- 光变油墨不设独立色块：原独立墨块已删，改为把主景面额数字整块以 OVI 丝印
         （见上方 fill="url(#ovi)"），与正面同一处理。 -->


    <!-- 微缩文字带：专家的最后一道（仅在右区法偿文本下方一段）-->
    <text x="1020" y="836" font-family="Georgia,serif" font-size="7.5"
          fill="{NAVY}" opacity="0.70" letter-spacing="0.3">{MICRO}</text>

    <!-- ===== 开窗安全线（背面为实线埋入段）===== -->
    <rect x="1236" y="{IN+10}" width="13" height="{H-2*(IN+10)}" fill="{GOLD_L}" opacity="0.22"/>
    <line x1="1242.5" y1="{IN+10}" x2="1242.5" y2="{H-IN-10}" stroke="{NAVY}" stroke-width="1.2"
          opacity="0.35" stroke-dasharray="4 6"/>

    <!-- ===== 下沿：冠字号与版号 ===== -->
    <text x="112" y="828" font-family="Consolas,'Courier New',monospace" font-size="30"
          font-weight="700" fill="{NAVY}" letter-spacing="2">{SERIAL}</text>
    <text x="620" y="828" font-family="Consolas,'Courier New',monospace" font-size="28"
          font-weight="700" fill="{DEEP}" opacity="0.72" letter-spacing="2">{SERIAL}</text>


    <!-- 四角金色 L 形角标已移除：票面改为**锐利直角**后，矩形内框自身就构成了
         直角转折，L 形角标原是配合圆角内框的装饰；且右下角要让位给对印标记。 -->
  </g>

  <rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="0" fill="none"
        stroke="{PAPER_D}" stroke-width="1.5"/>
'''

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'viewBox="0 0 {W} {H}" width="{W if SCAN else "100%"}" '
       f'height="{H if SCAN else "100%"}">{svg_body}</svg>')

if SCAN:
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:transparent;overflow:hidden}}
svg{{display:block}}
</style></head><body>{svg}</body></html>'''
    p = os.path.join(ROOT, "build", "reverse-100-scan.html" if TIER == 3
                     else f"back-{TIER}-scan.html")
else:
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#EEF0F4;overflow:hidden}}
#f{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}}
.n{{width:96vw;height:calc(96vw*{H}/{W});max-height:92vh;max-width:calc(92vh*{W}/{H});}}
</style></head><body><div id="f"><div class="n">{svg}</div></div></body></html>'''
    p = os.path.join(ROOT, "build", "reverse-100.html" if TIER == 3
                     else f"back-{TIER}.html")
open(p, "w", encoding="utf-8").write(html)
print("written:", p, len(html))
