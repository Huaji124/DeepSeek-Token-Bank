# -*- coding: utf-8 -*-
"""把线稿矢量化成 SVG —— 自己做 **标量场** marching squares + Douglas-Peucker。

为什么要自己写：本机没有 skimage / scipy / opencv / potrace / vtracer
（实测全部 import 失败），所以轮廓提取与简化都手写，只依赖 numpy。

**为什么必须在灰度场上取 0.5 等值线，而不是先二值化再描边**：
线稿是抗锯齿的，笔画只有 2~4 px 宽。先 `g < 128` 二值化再沿像素格走轮廓，
轮廓只能落在「黑格与白格的中点」上，等于每条笔画左右各缩掉半个像素 ——
实测整幅墨量 3.29% → 2.56%，IoU 只有 **0.49**，线条肉眼可见地变细。
改成在**灰度覆盖率场**上做线性插值的 0.5 等值线，轮廓就能落在亚像素位置，
与抗锯齿边缘一致。

边的键（保证相邻两格算出的交点完全同一个）：
  - 横边（上下）：`H(y,x) = (y*W+x)*2`      连接像素 (x,y) 与 (x+1,y)，沿 x 参数化
  - 竖边（左右）：`V(y,x) = (y*W+x)*2+1`    连接像素 (x,y) 与 (x,y+1)，沿 y 参数化
格子 (x,y) 的四条边即 T=H(y,x)、B=H(y+1,x)、L=V(y,x)、R=V(y,x+1)。

用法：
    python trace_ink.py                 # eps=0.5
    python trace_ink.py 0.35 out.svg
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = r"E:\Agent项目\鲸元券"
PLATE_MODE = "--plate" in sys.argv
# ── 超采样倍数（仅墨版模式）──────────────────────────────────────────
# **矢量化栅格图不会自动变平滑**：轮廓是沿像素格边界走出来的折线，
# 放大 N 倍看就是 N 级台阶。所以墨版先 Lanczos 上采样再做等值线，
# 等值线落点是插值场的亚像素交点，折线逼近的是平滑曲线而不是像素阶梯；
# 最后把坐标除以 SUP 回到原视口。这是"矢量在放大后反而比位图难看"的解药。
SUP = 4
SMOOTH = 0.35      # 仅墨版模式：轻度各向同性预平滑（原图尺度）
ALONG = 3.0        # 仅墨版模式：沿排线方向的平均半径（原图尺度）
ANG = 0.62         # 排线方向（与 lineart_plate.py 的 ANG0 一致）
if PLATE_MODE:
    # 直接矢量化**票面用的墨版**（`lineart_plate.py` 的产物）：
    # 墨在 alpha 通道里，RGB 是单色墨色。这样矢量化出来的就是票面上那幅画本身。
    SRC = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.png")
    OUT = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.svg")
else:
    SRC = os.path.join(ROOT, "assets", "source", "character-lineart.png")
    OUT = os.path.join(ROOT, "assets", "portrait", "character-lineart.svg")
    SUP = 1

EPS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
if len(sys.argv) > 2:
    OUT = sys.argv[2]
# ── 为什么要「多层等值线叠加」，而不是一条 0.5 等值线 ──────────────────
# 线稿是抗锯齿的，笔画**边缘是软的**（一条线的剖面大致是 0 → 1 → 0 的坡）。
# 单一等值线只能把这条坡切在一个位置，结果必然是「一整条硬边、内部纯色」——
# 线要么偏细、要么把细笔画整根丢掉（细笔画峰值覆盖率可能还不到 0.5）。
# 改成在若干档各出一条轮廓、逐层叠加、每层半透明：最深处叠加到接近全墨，
# 边缘只有最外一层 —— 软边就被还原出来了。
LEVELS = (0.18, 0.34, 0.52, 0.72)
# 每层的填充不透明度 —— **外层要低、内层要高**，这样从线边到线心才是
# 「浅 → 中 → 深 → 近全墨」的四级坡。四层都用同一个值会让整条线发灰。
LAYER_OPACITY = (0.40, 0.42, 0.52, 0.80)   # 累积 0.40 / 0.65 / 0.83 / 0.97

INK = "#1B2657"
MIN_AREA = 0.20         # 小于这个面积（px²）的碎点才丢；调大＝丢细节，别乱调

# 每个格子状态下轮廓穿过的两条边。位：TL=8 TR=4 BR=2 BL=1（1 = 墨）。
# 值里的字母是格子四条边：T 上、R 右、B 下、L 左。
SEGS = {
    1: ["LB"], 2: ["BR"], 3: ["LR"], 4: ["TR"],
    5: ["LT", "BR"], 6: ["TB"], 7: ["LT"],
    8: ["TL"], 9: ["TB"], 10: ["TR", "LB"], 11: ["TR"],
    12: ["LR"], 13: ["BR"], 14: ["LB"],
}


def edge_params(f, level):
    """算出每条边上的等值线交点参数 t（0~1），无交点处为 NaN。"""
    h, w = f.shape
    th = np.full((h, w - 1), np.nan, np.float32)      # 横边 H(y,x)：左边到右边
    tv = np.full((h - 1, w), np.nan, np.float32)      # 竖边 V(y,x)：上边到下边
    a = f[:, :-1]
    b = f[:, 1:]
    sel = (a - level) * (b - level) < 0
    th[sel] = ((level - a[sel]) / (b[sel] - a[sel]))
    a = f[:-1, :]
    b = f[1:, :]
    sel = (a - level) * (b - level) < 0
    tv[sel] = ((level - a[sel]) / (b[sel] - a[sel]))
    return th, tv


def build_segments(f, level):
    """返回线段端点键（两个 int64 数组）。"""
    h, w = f.shape
    inside = (f > level).astype(np.uint8)
    tl, tr = inside[:-1, :-1], inside[:-1, 1:]
    bl, br = inside[1:, :-1], inside[1:, 1:]
    state = (tl << 3) | (tr << 2) | (br << 1) | bl

    # 用「横边编号」与「竖边编号」两套键，两者加偏移区分
    NC = h * w
    K = {}

    def hkey(y, x):
        return y * (w - 1) + x

    def vkey(y, x):
        return NC + y * w + x

    ys, xs = np.nonzero(state)
    st = state[ys, xs]
    K["T"] = hkey(ys, xs)
    K["B"] = hkey(ys + 1, xs)
    K["L"] = vkey(ys, xs)
    K["R"] = vkey(ys, xs + 1)

    a_parts, b_parts = [], []
    for code, pairs in SEGS.items():
        sel = st == code
        if not sel.any():
            continue
        for pair in pairs:
            a_parts.append(K[pair[0]][sel])
            b_parts.append(K[pair[1]][sel])
    return np.concatenate(a_parts), np.concatenate(b_parts)


def link_loops(a_arr, b_arr):
    """把散线段接成闭合环。每个顶点度数恰好为 2。"""
    adj = {}
    for a, b in zip(a_arr.tolist(), b_arr.tolist()):
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    loops = []
    while adj:
        start = next(iter(adj))
        loop = [start]
        cur = start
        while True:
            nbrs = adj.get(cur)
            if not nbrs:
                break
            nxt = nbrs.pop()
            if not nbrs:
                del adj[cur]
            other = adj.get(nxt)
            if other is not None:
                try:
                    other.remove(cur)
                except ValueError:
                    pass
                if not other:
                    del adj[nxt]
            loop.append(nxt)
            if nxt == start:
                break
            cur = nxt
        if len(loop) > 3:
            loops.append(loop)
    return loops


def keys_to_xy(keys, th, tv, h, w):
    """键 → 亚像素坐标（已减掉补边）。"""
    NC = h * w
    keys = np.asarray(keys, dtype=np.int64)
    horiz = keys < NC
    out = np.zeros((len(keys), 2), np.float64)
    # 横边
    k = keys[horiz]
    y, x = np.divmod(k, w - 1)
    out[horiz, 0] = x + np.nan_to_num(th[y, x], nan=0.5)
    out[horiz, 1] = y
    # 竖边
    k = keys[~horiz] - NC
    y, x = np.divmod(k, w)
    out[~horiz, 0] = x
    out[~horiz, 1] = y + np.nan_to_num(tv[y, x], nan=0.5)
    out -= 1.0          # 减掉补边
    return out


def _dp(p, eps):
    n = len(p)
    if n < 3:
        return p
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = p[i], p[j]
        v = b - a
        L = float(np.hypot(*v))
        seg = p[i + 1:j]
        if L < 1e-9:
            dist = np.hypot(*(seg - a).T)
        else:
            dist = np.abs(v[0] * (seg[:, 1] - a[1]) - v[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(dist))
        if dist[k] > eps:
            m = i + 1 + k
            keep[m] = True
            stack.append((i, m))
            stack.append((m, j))
    return p[keep]


def simplify(pts, eps):
    """闭合环先在距起点最远点处切成两段，避免首尾重合导致 DP 退化。"""
    n = len(pts)
    if n < 4:
        return pts
    d = np.hypot(*(pts - pts[0]).T)
    far = int(np.argmax(d))
    if far == 0:
        return pts
    r1 = _dp(pts[:far + 1], eps)
    r2 = _dp(np.vstack([pts[far:], pts[:1]]), eps)
    return np.vstack([r1[:-1], r2[:-1]])


def _along_blur(f, ang, k):
    """只沿排线方向做平均（各向异性平滑）。

    各向同性模糊会把排线本身糊成一团（试过 1.20 px，排线变成斑块）。
    但锯齿的来源是**对角线在像素格上的台阶**——它同时沿着线和横跨线，
    只在"沿线的方向"平均就足以把台阶抹成一条平滑的边，而横跨线的
    陡峭剖面（这才是线看起来"锐"的原因）原样保留。
    """
    if k <= 0:
        return f
    dx, dy = math.cos(ang), math.sin(ang)
    pad = k + 1
    g = np.pad(f, pad, mode="edge")
    acc = np.zeros_like(g)
    n = 0
    for i in range(-k, k + 1):
        sx, sy = int(round(i * dx)), int(round(i * dy))
        acc += np.roll(np.roll(g, sy, axis=0), sx, axis=1)
        n += 1
    return acc[pad:pad + f.shape[0], pad:pad + f.shape[1]] / n


def main():
    global INK
    if PLATE_MODE:
        rgba = Image.open(SRC).convert("RGBA")
        if SUP > 1:
            rgba = rgba.resize((rgba.width * SUP, rgba.height * SUP), Image.LANCZOS)
        arr = np.asarray(rgba)
        f = arr[..., 3].astype(np.float32) / 255.0      # 墨量在 alpha 里
        # 超采样解决不了台阶：真正的噪声源是墨版自身在**像素尺度上就有的抖动**
        # （排线网点 + alpha 门控）。沿排线方向做各向异性平滑把它抹平，
        # 横跨线的陡峭剖面（线为什么看起来"锐"）原样保留。
        if SUP > 1:
            if SMOOTH > 0:
                f = np.asarray(Image.fromarray((f * 255).astype(np.uint8))
                               .filter(ImageFilter.GaussianBlur(SMOOTH))).astype(np.float32) / 255.0
            if ALONG > 0:
                f = _along_blur(f, ANG, int(round(ALONG * SUP)))
        # 取墨色要看**全不透明**的像素，阈值低了会被半透明的抗锯齿边拉偏
        full = arr[..., 3] > 250
        INK = "#%02X%02X%02X" % tuple(arr[..., :3][full].mean(axis=0).round().astype(int))
        size = (rgba.width // SUP, rgba.height // SUP)
    else:
        im = Image.open(SRC).convert("L")
        f = 1.0 - np.asarray(im).astype(np.float32) / 255.0
        size = im.size
    print("source %s %s  mean ink %.2f%%  ink color %s"
          % (size, "plate" if PLATE_MODE else "raw", 100.0 * f.mean(), INK))

    f = np.pad(f, 1, constant_values=0.0)
    h, w = f.shape
    w0, h0 = size

    layers = []
    for level in LEVELS:
        th, tv = edge_params(f, level)
        a_arr, b_arr = build_segments(f, level)
        loops = link_loops(a_arr, b_arr)

        paths, npts = [], 0
        for lp in loops:
            pts = keys_to_xy(lp[:-1], th, tv, h, w)
            if len(pts) < 3:
                continue
            area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], -1))
                             - np.dot(pts[:, 1], np.roll(pts[:, 0], -1)))
            if area < MIN_AREA:
                continue
            s = simplify(pts, EPS)
            if len(s) < 3:
                continue
            npts += len(s)
            s = (s - 1.0) / SUP          # 去掉补边，再回到原视口尺度
            paths.append("M" + " ".join("%.2f %.2f" % (px, py) for px, py in s) + "Z")
        layers.append("".join(paths))
        print("  level %.2f  segments %6d  contours %5d  kept %5d  points %6d"
              % (level, len(a_arr), len(loops), len(paths), npts))

    # 每层一个独立 <path>：同一 path 内 evenodd 会互相抵消，分层才能叠加
    body = "".join('<path fill="%s" fill-opacity="%.2f" fill-rule="evenodd" d="%s"/>'
                   % (INK, LAYER_OPACITY[i], d) for i, d in enumerate(layers))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">%s</svg>'
           % (w0, h0, body))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("written: %s  %d chars" % (OUT, len(svg)))


if __name__ == "__main__":
    main()
