# -*- coding: utf-8 -*-
"""把人物墨版**直接生成成矢量**（不是描摹栅格稿）。

为什么要有这个脚本
------------------
`trace_ink.py` 能描摹位图墨版，但**描摹栅格图不会变平滑**：墨版是排线网点的
栅格图，边缘天生是硬的（alpha 门控只给约 1 px 过渡），逐像素描出的轮廓在 4 倍
扫描稿上就是 4 级台阶，比带抗锯齿的位图更糙。试过各向同性模糊、各向异性沿排线
模糊、4 倍超采样，都压不掉。

所以换个做法：**别描摹，直接画**。

  · 排线 —— 本来就是程序生成的（`lineart_plate.py` 里 `hatch_cover()` 是解析式），
    可以直接吐成 SVG 描边。排线的宽度由明暗场决定，把它量化成 5 档线宽，
    沿每条排线采样、把同档的连续区段合成**一条直线段**（排线本身是直线，
    只有"档位切换点"在变，所以每段就是一根线段），`stroke-width` 取该档宽度。
  · 轮廓与五官 —— 线稿本身是抗锯齿的，场是光滑的，描摹它出来就是光滑曲线。
    淡出照旧用"侵蚀"：对线稿墨场做 `(blur(ink) - (1-taper)) / taper`，
    线心随 taper 下降而变细直到断掉，然后照常取多层等值线，
    于是"线条末端变细"这件事在矢量里也成立（不是靠蒙版变淡）。
  · 剪影 —— 沿用 `lineart_plate.py` 的洪水填充（遮底板仍由那个脚本产出位图，
    它只是一层纸色补丁，不是画面内容）。

输出 `E:\\Agent项目\\鲸元券\\assets\\portrait\\portrait-lineart.svg`，
由 `render_mockup.py` 以内嵌 `<svg>` 的形式放进票面。
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lineart_plate as LP
import trace_ink as TI

ROOT = r"E:\Agent项目\鲸元券"
OUT = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.svg")

# 排线：**大量很细的等宽线**，靠"线的疏密"而不是"线的粗细"表现明暗。
# 这是真实票面雕刻的做法（线宽恒定约 0.1 mm，靠间距变化出调子）。
# 之前的做法是"固定间距 + 变线宽"，结果：线宽收到 0 时两端变成尖刺，
# 线宽变化处又出现台阶 —— 用户看到的就是那些"毛刺"和"不顺滑的过渡"。
SPACING = 3.6            # 最密时的线距（px，板坐标）
LW = 0.95                # 线宽下限（亮处的线宽，px）
# 暗部把线加宽。不这么做，恒定细线的墨量上限只有 LW/SPACING ≈ 26%，
# 暗处永远压不黑、整幅发灰发飘；真实凹版也是这个道理——亮处细线，
# 暗处线变粗、相邻两根几乎并拢，才出得来厚实的黑。
LW_GROW = 1.90           # 暗部额外加宽量（px）
GOLDEN = 0.6180339887    # 低差异序列：让"该亮哪几根"均匀铺开，不会扎堆
# 短于此长度的线一律不画。**这是唯一保留的"修毛刺"手段**：手上、围裙上那些
# 极淡的明暗会零星点亮几根孤立的短线，看着就是一圈莫名其妙的毛刺；把过短的
# 段丢掉即可，不必去动调子场（动调子场会把中间调一起擦掉）。
MIN_RUN = 12.0

# 轮廓：**两层就够**。四层低不透明度叠出来是一条又软又糊的灰带 ——
# 用户说的"边缘毛躁"有一半来自它。要的是干净的一条线：
# 外层略宽、压一点透明度当过渡，内层直接满墨。
LEVELS = (0.28, 0.60)
LAYER_OPACITY = (0.85, 1.0)
EPS = 0.45
MIN_AREA = 0.20
STEP = 1.0               # 沿排线的采样步长（px，板坐标）

INK = "#1B2657"


def silhouette(ink_full):
    """填实剪影：加粗封口 → 四角洪水填充标出"外面" → 取反。

    与 `lineart_plate.py` 里那段完全同构（那边产出位图遮底板，这边用来把排线
    关在人物内部）。注意两个坑：本机 Pillow 的 `ImageDraw.floodfill` 对 'L' 图
    静默失效，所以自己用形态学重建做；取景底边把人物切断，最底几行要封成墙。
    """
    b = ((ink_full > 0.30) * 255).astype(np.uint8)
    b[:2, :] = 0; b[-2:, :] = 0; b[:, :2] = 0; b[:, -2:] = 0
    bi = Image.fromarray(b).filter(ImageFilter.MaxFilter(9))
    free = (np.asarray(bi) == 0)
    free[-3:, :] = False
    cur = np.zeros_like(free)
    cur[0, :] |= free[0, :]; cur[-1, :] |= free[-1, :]
    cur[:, 0] |= free[:, 0]; cur[:, -1] |= free[:, -1]
    for _ in range(6000):
        nxt = cur.copy()
        nxt[1:, :] |= cur[:-1, :]; nxt[:-1, :] |= cur[1:, :]
        nxt[:, 1:] |= cur[:, :-1]; nxt[:, :-1] |= cur[:, 1:]
        nxt &= free
        if np.array_equal(nxt, cur):
            break
        cur = nxt
    sil = ((~cur) | (np.asarray(bi) > 0)).astype(np.float32)
    print("silhouette: character = %.1f%%" % (sil.mean() * 100))
    return sil


def taper_field(ink_lines, h, w):
    """淡出/收细系数，与 `lineart_plate.build()` 同式。"""
    a8 = ((1.0 - ink_lines) * 255).astype(np.uint8)
    field = np.asarray(Image.fromarray(a8).filter(
        ImageFilter.GaussianBlur(LP.FADE_R))).astype(np.float32) / 255.0
    shape_feather = np.clip(field / LP.FADE_G, 0.0, 1.0) ** 0.85

    def _ramp(n, p):
        return np.linspace(0.0, 1.0, n, dtype=np.float32) ** p

    box = np.ones((h, w), dtype=np.float32)
    box[:, :LP.FR_L] *= _ramp(LP.FR_L, 2.4)[None, :]
    box[:, -LP.FR_R:] *= _ramp(LP.FR_R, 1.45)[::-1][None, :]
    box[:LP.FR_T, :] *= _ramp(LP.FR_T, 2.2)[:, None]
    box[-LP.FR_B:, :] *= _ramp(LP.FR_B, 1.35)[::-1][:, None]

    taper = (shape_feather ** 0.60) * box
    protect = np.zeros((h, w), dtype=np.float32)
    for (cx, cy, rx, ry) in LP.PROTECT:
        protect = np.maximum(protect, LP._blob(h, w, cx, cy, rx, ry))
    return np.maximum(taper, protect)


def hatch_paths(shade, sil, taper, ink_lines, h, w):
    """**大量很细的等宽线**，靠疏密表现明暗。

    早先的做法是"固定间距 + 变线宽"，两个毛病都出在变线宽上：
      · 线宽收到 0 时，包络多边形的两端变成**尖刺**（用户圈出来的那些毛刺）；
      · 线宽在相邻采样点上来回跳，边缘就出现台阶，过渡不顺滑。
    改成等宽之后，每根线就是一根干净的细条，两端方正，没有尖角。

    明暗怎么表达？给每根线一个阈值 `t_k`（用黄金比低差异序列铺开，保证
    "该亮哪几根"在空间上均匀分布、不会扎堆），`shade > t_k` 的地方就画。
    于是暗处线多、亮处线少，过渡是**一根一根地增减**，天然平滑。
    """
    dx, dy = math.cos(LP.ANG0), math.sin(LP.ANG0)      # 沿线方向
    nx, ny = -math.sin(LP.ANG0), math.cos(LP.ANG0)     # 法向

    # 细线版的调子场：**不加门槛、不腐蚀、不减线稿、不抬低频**。
    # 原画明暗直接驱动"哪几根线点亮"：暗处线密、亮处线疏，过渡就是一根一根地
    # 增减。后面那些加减法都是为了压轮廓边的毛刺而加的，代价是把中间调也一并
    # 擦掉（用户：「擦的东西太多了」），已全部撤掉；毛刺改用 MIN_RUN 处理。
    # **只画深色区**：明暗值低于 0.25 的地方一根线都不出。手背、袖口、围裙这些
    # 亮面上那点极淡的明暗本不该出线，逐点阈值一判就零星点亮几根斜短线，看着
    # 就是一圈莫名其妙的毛刺。这条坎正好对上"深色区和浅色区的区分"。
    d = np.clip((shade - 0.45) / 0.55, 0.0, 1.0)
    d = d * np.clip(taper * 1.35, 0.0, 1.0)            # 淡出处线一根根变少，直至没有
    # 沿排线方向抹平：阈值判定是逐点的，场一旦有细微起伏就会把线切成碎段
    d = TI._along_blur(np.clip(d, 0.0, 1.0), LP.ANG0, 6)

    corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], dtype=np.float32)
    vv = -corners[:, 0] * math.sin(LP.ANG0) + corners[:, 1] * math.cos(LP.ANG0)
    k0 = int(math.floor(vv.min() / SPACING)) - 1
    k1 = int(math.ceil(vv.max() / SPACING)) + 1
    t = np.arange(-math.hypot(w, h) * 0.15, math.hypot(w, h) * 1.15,
                  STEP, dtype=np.float32)

    # 线宽在暗部**加宽**。不这么做，恒定细线的墨量上限只有 LW/SPACING ≈ 26%，
    # 暗处永远压不黑，整幅发灰发飘 —— 真实凹版也是这个道理：亮处是细线，
    # 暗处线条变粗、相邻两根几乎并拢，才出得来厚实的黑。
    # 关键是**给线宽留一个下限**（不到 0）：线宽一旦能收到 0，包络两端就会收出尖刺。
    paths, nseg = [], 0
    for k in range(k0, k1 + 1):
        thr = (k * GOLDEN) % 1.0
        v = k * SPACING + SPACING * 0.5
        px = v * nx + t * dx
        py = v * ny + t * dy
        ix = np.rint(px).astype(np.int32)
        iy = np.rint(py).astype(np.int32)
        ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
        if not ok.any():
            continue
        dd = np.zeros(len(t), dtype=np.float32)
        dd[ok] = d[iy[ok], ix[ok]]
        live = (dd > thr) & ok
        if not live.any():
            continue
        HW = (LW + LW_GROW * np.clip((dd - 0.55) / 0.35, 0.0, 1.0)) * 0.5
        chg = np.flatnonzero(np.diff(live.astype(np.int8)) != 0) + 1
        starts = np.concatenate(([0], chg))
        ends = np.concatenate((chg, [len(live)]))
        for s, e in zip(starts, ends):
            if not live[s] or (e - s) * STEP < MIN_RUN:
                continue
            cx, cy, hh = px[s:e], py[s:e], HW[s:e]
            up = np.stack([cx + nx * hh, cy + ny * hh], axis=1)
            dn = np.stack([cx - nx * hh, cy - ny * hh], axis=1)[::-1]
            poly = TI.simplify(np.vstack([up, dn, up[:1]]), 0.18)[:-1]
            if len(poly) < 3:
                continue
            paths.append("M" + " ".join("%.2f %.2f" % (a2, b2) for a2, b2 in poly) + "Z")
            nseg += 1
    return paths, nseg


def smooth_d(pts):
    """闭合折线 → 二次贝塞尔平滑路径。

    直接输出折线的话，等值线在像素尺度上的微小抖动会变成一圈小锯齿，
    放大就看得很明显。把原顶点当控制点、相邻顶点的中点当曲线上的点，
    得到的就是一条过中点的平滑闭合曲线 —— 曲线本身与分辨率无关。
    """
    n = len(pts)
    p = np.vstack([pts, pts[:1]])
    mid = (p[:-1] + p[1:]) * 0.5
    d = ["M%.2f %.2f" % (mid[-1][0], mid[-1][1])]
    for i in range(n):
        d.append("Q%.2f %.2f %.2f %.2f" % (p[i][0], p[i][1], mid[i][0], mid[i][1]))
    d.append("Z")
    return "".join(d)


def trace_field(f, view_w, view_h, levels=None, min_area=None, blur=0.35, eps=None):
    """对覆盖率场取等值线，返回每层的 d 字符串（与 trace_ink 同法）。"""
    levels = LEVELS if levels is None else levels
    min_area = MIN_AREA if min_area is None else min_area
    eps = EPS if eps is None else eps
    # 追踪前轻微抹平：抗锯齿线稿的场本身是光滑的，但像素级的离散仍会让
    # 等值线带上细小抖动；0.35 px 的模糊足以把它压掉，又不动真实细节。
    f = np.asarray(Image.fromarray((f * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255.0
    f = np.pad(f, 1, constant_values=0.0)
    h, w = f.shape
    layers = []
    for lv in levels:
        th, tv = TI.edge_params(f, lv)
        a_arr, b_arr = TI.build_segments(f, lv)
        loops = TI.link_loops(a_arr, b_arr)
        paths = []
        for lp in loops:
            pts = TI.keys_to_xy(lp[:-1], th, tv, h, w)
            if len(pts) < 3:
                continue
            area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], -1))
                             - np.dot(pts[:, 1], np.roll(pts[:, 0], -1)))
            if area < min_area:
                continue
            s = TI.simplify(pts, eps)
            if len(s) < 3:
                continue
            paths.append(smooth_d(s - 1.0))               # 去掉补边
        layers.append("".join(paths))
        print("  %s level %.2f  contours %d" % ("outline", lv, len(paths)))
    return layers


def main():
    lum, lum_c = LP.load()
    h, w = lum.shape
    print("plate %dx%d" % (w, h))

    ink_lines = np.clip((LP.HI - lum) / (LP.HI - LP.LO), 0.0, 1.0)

    shade = np.clip((LP.SH_HI - lum_c) / (LP.SH_HI - LP.SH_LO), 0.0, 1.0) ** 0.95
    base = np.asarray(Image.fromarray((lum_c * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(2.0))).astype(np.float32) / 255.0
    shade = shade * np.clip((LP.SH_HI - base) / (LP.SH_HI - LP.SH_LO), 0.0, 1.0)

    taper = taper_field(ink_lines, h, w)
    sil = silhouette(ink_lines)

    # ── 剪影：排线必须被裁在人物轮廓之内 ─────────────────────────
    # 不裁的话，每条排线都在自己的明暗阈值处各自断开，断口在轮廓边上一根根
    # 参差排列，连起来就是一圈锯齿状的「梳子」—— 用户看到的「边缘全是毛刺」。
    # 剪影场先重度抹平再取 0.5 等值线，裁切线才是光滑的。
    # 剪影本身比"画出来的轮廓"要胖一圈：线稿里发梢那几笔很淡，剪影把它们跟
    # 周围半透明的一并算进"里面"，于是排线会有一圈**探出描边之外**的毛边。
    # 先把剪影腐蚀一圈再取等值线，排线就停在描边以里，边界由描边自己交代。
    sil_e = np.asarray(Image.fromarray(((sil > 0.5) * 255).astype(np.uint8))
                       .filter(ImageFilter.MinFilter(7))).astype(np.float32) / 255.0
    clipd = trace_field(sil_e, w, h, levels=(0.5,), min_area=8.0,
                        blur=1.2, eps=0.9)[0]
    print("  clip contours ok  %d chars" % len(clipd))

    # ── 排线（矢量描边，裁在剪影内）──────────────────────────────
    segs, nseg = hatch_paths(shade, sil, taper, ink_lines, h, w)
    print("hatch polygons %d" % nseg)
    hatch = '<path d="%s"/>' % "".join(segs)

    # ── 轮廓（侵蚀后取多层等值线，线随 taper 变细直至断掉）─────────
    soft = np.asarray(Image.fromarray((ink_lines * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(LP.SOFTEN))).astype(np.float32) / 255.0
    ero = np.clip((soft - (1.0 - taper)) / np.maximum(taper, 1e-3), 0.0, 1.0)
    layers = trace_field(ero, w, h)
    outline = "".join(
        '<path fill-opacity="%.2f" d="%s"/>' % (LAYER_OPACITY[i], d)
        for i, d in enumerate(layers) if d)

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">'
           '<defs><clipPath id="sil" clip-rule="evenodd"><path d="%s"/></clipPath></defs>'
           '<g fill="%s" fill-rule="nonzero" clip-path="url(#sil)">%s</g>'
           '<g fill="%s" fill-rule="nonzero">%s</g></svg>'
           % (w, h, clipd, INK, hatch, INK, outline))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("written: %s  %d chars" % (OUT, len(svg)))


if __name__ == "__main__":
    main()
