# -*- coding: utf-8 -*-
"""鲸元券 · 人物主景「雕刻线稿」——纯 SVG 手绘（凹版雕刻语言）。

凹版雕刻人像靠**排线的疏密与走向**塑造体积：没有渐变、没有平涂色块、没有环境光。
本稿只做三件事：
  1) 等宽/微变宽的线描出轮廓与结构；
  2) 「发缕（lock）」为单位造型 —— 每缕是一条脊线加一个宽度剖面，
     内部排线直接由**偏移曲线族**生成（因此永远贴合发缕形状、尖端自然收拢）；
  3) 交叉排线压暗颈下、刘海下、衣褶。

关键实现：**背景发用 mask 遮挡，不用纸色填充** —— 票面纸色随面额变化，
硬编码纸色会破坏其它档；mask 保持透明底，纸色由票面自己透出来。

输出：`build/line-portrait.svg`（透明底，藏青墨色）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = r"E:\Agent项目\鲸元券"
INK = "#1B2657"
W, H = 600, 800


# ────────────────────────── 基础工具 ──────────────────────────
def resample(pts, n):
    seg = [0.0]
    for i in range(1, len(pts)):
        seg.append(seg[-1] + math.dist(pts[i - 1], pts[i]))
    total = seg[-1] or 1.0
    out, j = [], 0
    for i in range(n + 1):
        target = total * i / n
        while j < len(seg) - 2 and seg[j + 1] < target:
            j += 1
        span = seg[j + 1] - seg[j]
        t = 0.0 if span == 0 else (target - seg[j]) / span
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


def cubic(p0, c1, c2, p1, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u**2 * t * c1[0] + 3 * u * t**2 * c2[0] + t**3 * p1[0],
                    u**3 * p0[1] + 3 * u**2 * t * c1[1] + 3 * u * t**2 * c2[1] + t**3 * p1[1]))
    return out


def quad(p0, c1, p1, n=18):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * p0[0] + 2 * u * t * c1[0] + t * t * p1[0],
                    u * u * p0[1] + 2 * u * t * c1[1] + t * t * p1[1]))
    return out


def d_of(pts, close=False):
    s = "M %.2f %.2f " % pts[0] + " ".join("L %.2f %.2f" % p for p in pts[1:])
    return s + (" Z" if close else "")


def stroke(pts, w=1.2, op=1.0, close=False):
    return (f'<path d="{d_of(pts, close)}" fill="none" stroke="{INK}" '
            f'stroke-width="{w:.2f}" stroke-opacity="{op:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def offset_curve(pts, ws):
    """沿法向偏移：正负号决定左右。"""
    n = len(pts)
    out = []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        out.append((x - dy / L * ws[i], y + dx / L * ws[i]))
    return out


def lock(spine, wmax, n=30, tip=1.6, root=0.85):
    """一条发缕：闭合轮廓点列（脊线两侧按宽度剖面偏移后合拢）。"""
    pts = resample(spine, n)
    ws = [wmax * ((1 - (i / n) ** tip) ** 0.75) * (root + (1 - root) * min(1.0, i / n * 6))
          for i in range(n + 1)]
    left = offset_curve(pts, ws)
    right = offset_curve(pts, [-w for w in ws])
    return pts, ws, left, right


def lock_lines(spine, wmax, count, n=30, tip=1.6, root=0.85, ops=None):
    """发缕的排线：边界 + 内部偏移曲线族。"""
    pts = resample(spine, n)
    ws = [wmax * ((1 - (i / n) ** tip) ** 0.75) * (root + (1 - root) * min(1.0, i / n * 6))
          for i in range(n + 1)]
    left = offset_curve(pts, ws)
    right = offset_curve(pts, [-w for w in ws])
    out = [stroke(left, 2.4), stroke(right, 2.4)]
    for k in range(1, count + 1):
        for sgn in (1, -1):
            f = sgn * k / (count + 1)
            op = (ops or 0.85) * (1.0 - 0.35 * abs(f))
            out.append(stroke(offset_curve(pts, [w * f for w in ws]), 1.1, op))
    # 尖端合拢线
    out.append(stroke([left[-1], right[-1]], 1.6, 0.9))
    return out, (left + right[::-1])


# ────────────────────────── 造型 ──────────────────────────
FACE = None
def face_shape():
    """脸廓（闭合）：额 → 左颧 → 左颊 → 下巴 → 右颊 → 右颧 → 额。"""
    p = cubic((300, 176), (240, 182), (228, 220), (226, 258), 18)
    p += cubic((226, 258), (225, 292), (244, 322), (268, 336), 14)[1:]
    p += cubic((268, 336), (282, 344), (318, 344), (332, 336), 10)[1:]
    p += cubic((332, 336), (356, 322), (375, 292), (374, 258), 14)[1:]
    p += cubic((374, 258), (372, 220), (360, 182), (300, 176), 18)[1:]
    return p


def bang_locks():
    """刘海：五缕，尖端垂到眉上方。"""
    return [
        (((160, 250), (168, 176), (214, 128), (270, 118)), 34),
        (((236, 130), (268, 148), (286, 178), (292, 214)), 26),
        (((300, 112), (330, 132), (352, 170), (354, 210)), 30),
        (((348, 128), (382, 156), (404, 196), (410, 244)), 32),
        (((196, 150), (216, 186), (228, 216), (232, 250)), 20),
    ]


def side_locks():
    """两侧垂发：贴脸下行，末端外翻。"""
    return [
        (((214, 196), (186, 262), (182, 356), (198, 442)), 26),
        (((382, 196), (414, 262), (420, 356), (404, 448)), 26),
        (((240, 210), (212, 274), (210, 368), (226, 448)), 18),
        (((360, 210), (390, 276), (392, 370), (376, 452)), 18),
    ]


def back_locks():
    """背景长发：左右各三缕，最外两缕带波浪。"""
    return [
        (((196, 178), (140, 268), (128, 430), (162, 600)), 52),
        (((404, 178), (462, 268), (476, 430), (442, 600)), 52),
        (((246, 168), (196, 282), (188, 460), (222, 664)), 44),
        (((354, 168), (406, 282), (414, 460), (380, 664)), 44),
        (((300, 160), (262, 300), (258, 500), (292, 700)), 48),
        (((300, 160), (340, 300), (344, 500), (310, 700)), 48),
    ]


def ear_fins():
    """鲸鱼耳鳍：贴在头两侧、露出发际之外。"""
    return [
        (((238, 244), (188, 252), (150, 284), (132, 322)), 22),
        (((362, 244), (412, 252), (450, 284), (468, 320)), 22),
    ]


def neck_body():
    """颈 + 肩 + 胸衣（一个闭合体，用于遮挡背景发）。"""
    p = cubic((272, 320), (268, 352), (262, 366), (250, 378), 12)
    p += cubic((250, 378), (206, 402), (166, 452), (150, 540), 18)[1:]
    p += [(150, 800), (450, 800)]
    p += cubic((450, 540), (434, 452), (394, 402), (350, 378), 18)[1:]
    p += cubic((350, 378), (338, 366), (332, 352), (328, 320), 12)[1:]
    return p


def apron_shape():
    p = quad((252, 452), (300, 476), (348, 452), 16)
    p += cubic((348, 452), (372, 552), (378, 660), (366, 800), 20)[1:]
    p += [(234, 800)]
    p += cubic((234, 800), (222, 660), (228, 552), (252, 452), 20)[1:]
    return p


def headband_shape():
    top = quad((180, 220), (300, 76), (420, 220), 36)
    bot = quad((196, 244), (300, 118), (404, 244), 36)
    return top + bot[::-1]


def build():
    P = []
    # ── 遮挡用的「前景轮廓」（放进 mask，不描边）
    occluders = []
    occluders.append(face_shape())
    occluders.append(neck_body())
    occluders.append(apron_shape())
    occluders.append(headband_shape())
    bang_closed, side_closed = [], []
    for sp, wm in bang_locks():
        _, _, l, r = lock(sp, wm)
        bang_closed.append(l + r[::-1])
    for sp, wm in side_locks():
        _, _, l, r = lock(sp, wm)
        side_closed.append(l + r[::-1])
    occluders += bang_closed + side_closed

    mask_body = '<rect x="0" y="0" width="%d" height="%d" fill="#FFFFFF"/>' % (W, H)
    for o in occluders:
        mask_body += f'<path d="{d_of(o, True)}" fill="#000000"/>'
    P.append(f'<defs><mask id="mBack">{mask_body}</mask></defs>')

    # ── 1. 背景长发（被 mask 遮挡）
    bg = []
    for sp, wm in back_locks():
        ls, _ = lock_lines(sp, wm, 7, ops=0.8)
        bg += ls
    P.append('<g mask="url(#mBack)">' + "".join(bg) + '</g>')

    # ── 2. 耳鳍（在背景发之上、脸之后）
    for sp, wm in ear_fins():
        ls, _ = lock_lines(sp, wm, 6, ops=0.8)
        P += ls

    # ── 3. 脸
    P.append(stroke(face_shape(), 2.6, close=True))

    # ── 4. 侧发（在脸之上）
    for sp, wm in side_locks():
        ls, _ = lock_lines(sp, wm, 4, ops=0.85)
        P += ls

    # ── 5. 刘海（在脸之上）
    for sp, wm in bang_locks():
        ls, _ = lock_lines(sp, wm, 5, ops=0.85)
        P += ls

    # ── 6. 发箍
    top = quad((180, 220), (300, 76), (420, 220), 36)
    bot = quad((196, 244), (300, 118), (404, 244), 36)
    P.append(stroke(top, 2.6))
    P.append(stroke(bot, 2.0))
    for i in range(1, len(top) - 1, 3):
        x, y = top[i]
        P.append(stroke(quad((x - 10, y), (x, y - 15), (x + 10, y), 12), 1.7))
    n = min(len(top), len(bot))
    for k in range(1, 5):
        t = k / 5
        P.append(stroke([(top[i][0] + (bot[i][0] - top[i][0]) * t,
                          top[i][1] + (bot[i][1] - top[i][1]) * t) for i in range(n)], 1.0, 0.65))

    # ── 7. 蝴蝶结（头饰右侧）
    P += bow(418, 168, 0.78)

    # ── 8. 眉 / 眼 / 鼻 / 嘴
    P += brow(262, 226, 1)
    P += brow(338, 224, -1)
    P += eye(262, 254, 1)
    P += eye(338, 252, -1)
    P.append(stroke([(300, 272), (295, 286), (303, 288)], 1.7))
    P.append(stroke(quad((285, 306), (300, 322), (317, 304), 16), 2.2))
    P.append(stroke(quad((291, 309), (300, 316), (311, 308), 14), 1.4, 0.7))
    # 腮红（点刻短线）
    for side in (1, -1):
        cx = 300 - side * 56
        for k in range(3):
            for r in range(3):
                x = cx + side * (k * 5 + r * 2)
                y = 292 + r * 6
                P.append(stroke([(x, y), (x + side * 6, y - 2)], 1.0, 0.4))

    # ── 9. 颈影交叉排线
    for k in range(4):
        y = 386 + k * 6
        P.append(stroke([(256 + k * 3, y), (344 - k * 3, y - 3)], 1.0, 0.4))
    for k in range(4):
        P.append(stroke([(268 + k * 8, 380), (262 + k * 8, 406)], 1.0, 0.35))

    # ── 10. 荷叶领 + 领结
    for sgn, cx0 in ((1, 262), (-1, 338)):
        for k in range(4):
            x = cx0 + sgn * k * 13
            y = 402 + abs(k - 1.5) * 4
            P.append(stroke(quad((x - 9, y), (x, y + 17), (x + 9, y), 12), 1.8))
    P.append(stroke(cubic((238, 404), (260, 424), (340, 424), (362, 404), 20), 2.2))
    P += bow(300, 442, 0.72)

    # ── 11. 围裙（含腰褶与小鲸刺绣）
    P.append(stroke(quad((252, 452), (300, 476), (348, 452), 16), 2.0))
    P.append(stroke(cubic((252, 452), (244, 428), (248, 414), (258, 404), 12), 1.8))
    P.append(stroke(cubic((348, 452), (356, 428), (352, 414), (342, 404), 12), 1.8))
    ap_l = cubic((240, 468), (222, 560), (220, 668), (236, 790), 22)
    ap_r = cubic((360, 468), (378, 560), (380, 668), (364, 790), 22)
    P.append(stroke(ap_l, 2.2))
    P.append(stroke(ap_r, 2.2))
    n = min(len(ap_l), len(ap_r))
    for k in range(1, 7):
        t = k / 7
        P.append(stroke([(ap_l[i][0] + (ap_r[i][0] - ap_l[i][0]) * t,
                          ap_l[i][1] + (ap_r[i][1] - ap_l[i][1]) * t) for i in range(n)], 1.0, 0.5))
    for k in range(3):
        y = 560 + k * 60
        P.append(stroke(quad((228, y), (300, y + 16), (372, y), 20), 1.3, 0.65))
    # 小鲸刺绣
    P.append(stroke(quad((288, 690), (302, 672), (322, 684), 16), 1.8))
    P.append(stroke(quad((288, 690), (298, 706), (322, 684), 16), 1.8))
    P.append(f'<circle cx="304" cy="684" r="2.0" fill="{INK}"/>')
    P.append(stroke([(290, 674), (285, 664)], 1.3))
    return "\n".join(P)


def bow(cx, cy, s=1.0):
    g = []
    lw, lh = 36 * s, 25 * s
    g.append(stroke(quad((cx, cy), (cx - lw * 1.2, cy - lh), (cx - lw * 1.55, cy + lh * 0.45), 16), 2.2))
    g.append(stroke(quad((cx - lw * 1.55, cy + lh * 0.45), (cx - lw * 0.9, cy + lh * 1.1), (cx, cy), 16), 2.2))
    g.append(stroke(quad((cx, cy), (cx + lw * 1.2, cy - lh), (cx + lw * 1.55, cy + lh * 0.45), 16), 2.2))
    g.append(stroke(quad((cx + lw * 1.55, cy + lh * 0.45), (cx + lw * 0.9, cy + lh * 1.1), (cx, cy), 16), 2.2))
    g.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{7*s:.1f}" ry="{8*s:.1f}" '
             f'fill="none" stroke="{INK}" stroke-width="2.0"/>')
    for sgn in (1, -1):
        for k in range(3):
            t = 0.30 + k * 0.20
            g.append(stroke([(cx + sgn * lw * 1.30 * (1 - t), cy - lh * 0.55 * (1 - t) + k * 3),
                             (cx + sgn * 5, cy + k * 3)], 0.9, 0.5))
    g.append(stroke(cubic((cx - 4 * s, cy + 7 * s), (cx - 15 * s, cy + 30 * s),
                          (cx - 9 * s, cy + 44 * s), (cx - 20 * s, cy + 56 * s), 16), 1.8))
    g.append(stroke(cubic((cx + 4 * s, cy + 7 * s), (cx + 15 * s, cy + 30 * s),
                          (cx + 9 * s, cy + 44 * s), (cx + 20 * s, cy + 56 * s), 16), 1.8))
    return g


def eye(cx, cy, flip=1):
    g = []
    ex, ey = 31, 19
    g.append(stroke(cubic((cx - ex * flip, cy + 2), (cx - ex * 0.5 * flip, cy - ey * 1.45),
                          (cx + ex * 0.5 * flip, cy - ey * 1.45), (cx + ex * flip, cy - 1)), 3.0))
    g.append(stroke(cubic((cx - ex * flip, cy + 3), (cx - ex * 0.5 * flip, cy + ey * 1.2),
                          (cx + ex * 0.5 * flip, cy + ey * 1.2), (cx + ex * flip, cy + 1)), 1.4))
    ir = 14.0
    iris = [(cx + ir * math.cos(2 * math.pi * i / 44), cy + 1 + ir * 1.05 * math.sin(2 * math.pi * i / 44))
            for i in range(45)]
    g.append(stroke(iris, 2.0, close=True))
    pup = [(cx + 6.2 * math.cos(2 * math.pi * i / 28), cy + 1 + 6.6 * math.sin(2 * math.pi * i / 28))
           for i in range(29)]
    g.append(f'<path d="{d_of(pup, True)}" fill="{INK}"/>')
    g.append(f'<circle cx="{cx - 4.8:.1f}" cy="{cy - 4.6:.1f}" r="3.2" fill="#FFFFFF"/>')
    g.append(stroke(quad((cx - 8, cy + 9), (cx, cy + 13), (cx + 8, cy + 9), 12), 1.8))
    for k in range(3):
        x0 = cx + ex * flip
        g.append(stroke([(x0 - k * 1.2 * flip, cy - 2 - k * 1.5),
                         (x0 + (6 - k * 1.4) * flip, cy - 11 - k * 2.5)], 2.4))
    return g


def brow(cx, cy, flip=1):
    return [stroke(cubic((cx - 25 * flip, cy + 3), (cx - 8 * flip, cy - 8),
                         (cx + 10 * flip, cy - 8), (cx + 25 * flip, cy - 1), 16), 2.6)]


def main():
    body = build()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}">\n{body}\n</svg>')
    open(os.path.join(ROOT, "build", "line-portrait.svg"), "w", encoding="utf-8").write(svg)
    small = svg.replace('width="600" height="800"', 'width="240" height="320"')
    tiny = svg.replace('width="600" height="800"', 'width="120" height="160"')
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#EEF0F4;overflow:hidden}}
#w{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center;gap:40px}}
.b{{background:#D8DBE9;box-shadow:0 2px 18px rgba(20,30,60,.18)}}
</style></head><body><div id="w">
<div class="b" style="width:600px;height:800px">{svg}</div>
<div class="b" style="width:240px;height:320px">{small}</div>
<div class="b" style="width:120px;height:160px">{tiny}</div>
</div></body></html>'''
    open(os.path.join(ROOT, "build", "line-portrait.html"), "w", encoding="utf-8").write(html)
    print("ok, bytes:", len(svg))


if __name__ == "__main__":
    main()
