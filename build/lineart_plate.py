# -*- coding: utf-8 -*-
"""把**现成的线稿**做成票面用的雕刻底板。

和 lineart_engrave.py 的区别：那一版是拿彩色插画"造"出排线（因为原图没有线），
这一版拿到的是真线稿，所以不需要任何排线生成 —— 直接取墨，只做三件事：

  1. 取景 + 缩放到票面人物框的比例（1200×1049，对应 890×778 的 1.1439）；
  2. 边缘**收细**淡出（把 ink 做侵蚀，而不是降透明度，这样线是"越刻越细"）；
  3. 头与双手保护罩（这两处永远满墨，不受淡出影响）。

输出：
  assets/portrait/portrait-lineart.png  —— 染成票面藏青的 RGBA 墨版
  assets/portrait/portrait-cover.png    —— 人物轮廓（给 render_mockup 生成遮底板用）
  build/lineart-plate.png               —— 校样
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = r"E:\Agent项目\鲸元券"
SRC = os.path.join(ROOT, "assets", "source", "character-lineart.png")
# 彩色原图：和线稿是同一构图（aspect 0.5628 vs 0.5626），按比例对齐后
# 用它的**明暗**来判断哪些区域该出排线（头发/深色裙 = 出线，皮肤/白围裙 = 留白）
SHADE_SRC = os.path.join(ROOT, "assets", "source", "character-full.jpg")
OUT_PNG = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.png")
OUT_COVER = os.path.join(ROOT, "assets", "portrait", "portrait-cover.png")
PROOF = os.path.join(ROOT, "build", "lineart-plate.png")

INK = np.array([27, 38, 87], dtype=np.float32)          # #1B2657

# 取景：线稿内容 bbox 是 x 31~935 / y 30~1667，取上半身，比例严格 1.1439
CROP = (31, 30, 935, 820)                               # 904 × 790
TARGET_W = 1200                                         # → 1200 × 1049

# 墨的提取：线稿是纯黑白，直接按亮度取，只把很浅的纸噪压掉
LO, HI = 0.42, 0.94                                     # lum < LO 全墨，> HI 无墨

# 排线（深色区）：全幅统一方向，靠线宽表达深浅 —— 这是纸币的常规做法
SPACING = 8.2                                           # 排线间距（px）
SOFT = 0.95
LINE_MAX = SPACING * 0.72
ANG0 = 0.62                                             # ≈35°
SH_LO, SH_HI = 0.26, 0.86                               # 明度低于 SH_LO 全出线，高于 SH_HI 不出线

SOFTEN = 0.95                                           # 侵蚀前的柔化半径（做出可侵蚀的线边缘）

# 淡出：底边与左右收得深，**上边完全不收** ——
# 取景上方没有裁到人物（呆毛顶端正好在画幅上缘），上边一羽化就会把呆毛淡掉。
FR_L, FR_R, FR_T, FR_B = 110, 340, 0, 380
FADE_R = 78.0
FADE_G = 0.34

# 保护罩（1200×1049 坐标）：呆毛 / 头 / 抬起的手 / 下方的手 —— 这几处必须满墨
# 坐标是用 build\_handgrid.png（50px 网格叠在墨版上）目测定出来的，勿凭感觉改。
PROTECT = [
    (450.0, 72.0, 120.0, 95.0),        # 头顶呆毛（细长一根，shape_feather 会把它判成孤立细线而收掉）
    (620.0, 230.0, 230.0, 190.0),      # 头·脸·耳鳍
    (960.0, 430.0, 130.0, 120.0),      # 抬起的右手
    (285.0, 850.0, 178.0, 85.0),       # 握住裙摆的左手（含指尖）。
                                       # ry 只取 85：再往下就把 "DeepSeek" 压印那一带
                                       # 也罩成满墨，字会淹在排线里读不出来。
]


def _blob(h, w, cx, cy, rx, ry, soft=0.42):
    """椭圆软边罩：q ≤ 1 处为 1，q ≥ 1+soft 处为 0。"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    q = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip((1.0 + soft - q) / soft, 0.0, 1.0)


def _lum(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) / 255.0


def load():
    """返回 (线稿明度, 彩色原图明度)，两者已对齐到同一尺寸。"""
    im = Image.open(SRC).convert("RGB")
    col = Image.open(SHADE_SRC).convert("RGB")
    # 彩色原图按同比例裁到与线稿同一取景
    sx, sy = col.width / im.width, col.height / im.height
    cbox = (int(round(CROP[0] * sx)), int(round(CROP[1] * sy)),
            int(round(CROP[2] * sx)), int(round(CROP[3] * sy)))
    im = im.crop(CROP)
    col = col.crop(cbox)
    size = (TARGET_W, round(im.height * TARGET_W / im.width))
    im = im.resize(size, Image.LANCZOS)
    col = col.resize(size, Image.LANCZOS)
    return _lum(im), _lum(col)


def hatch_cover(h, w, ang, width):
    """某一角度下平行排线的覆盖率；width 为逐像素线宽（px）。

    抗锯齿项在 width→0 时仍会在**线心**给出 0.5，会让整片留白浮出假排线，
    故再乘一个"线宽存在度"因子把它压回 0。
    """
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = (-xx * math.sin(ang) + yy * math.cos(ang))
    dist = np.abs((v % SPACING) - SPACING * 0.5)
    half = np.maximum(width, 0.0) * 0.5
    cover = np.clip((half - dist) / SOFT + 0.5, 0.0, 1.0)
    return cover * np.clip(half * 2.0 / SOFT, 0.0, 1.0)


def build():
    lum, lum_c = load()
    h, w = lum.shape

    # ── 第 1 层：线稿本身（轮廓与五官，任何地方都保留）────────────
    ink = np.clip((HI - lum) / (HI - LO), 0.0, 1.0)

    # ── 第 2 层：深色区的排线（用彩色原图的明暗来分区）────────────
    shade = np.clip((SH_HI - lum_c) / (SH_HI - SH_LO), 0.0, 1.0) ** 0.95
    base = np.asarray(Image.fromarray((lum_c * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(2.0))).astype(np.float32) / 255.0
    shade = shade * np.clip((SH_HI - base) / (SH_HI - SH_LO), 0.0, 1.0)

    w1 = LINE_MAX * np.clip(shade / 0.52, 0.0, 1.0)
    cov = hatch_cover(h, w, ANG0, w1)
    # 暗部一律**只用一组同向平行线**。
    # 加第二组垂直细线会把暗部织成网格，放大后读作灰色网点 / 电路板，
    # 而不是雕刻线 —— 用户点出的"手周围那一块发怪"就是这个网。
    ink = np.maximum(ink, cov * 0.94)

    # ── 淡出系数 ─────────────────────────────────────────────────
    a8 = ((1.0 - ink) * 255).astype(np.uint8)           # 纸面 = 255，线条 = 0
    field = np.asarray(Image.fromarray(a8)
                       .filter(ImageFilter.GaussianBlur(FADE_R))).astype(np.float32) / 255.0
    shape_feather = np.clip(field / FADE_G, 0.0, 1.0) ** 0.85

    def _ramp(n, p=1.9):
        return np.linspace(0.0, 1.0, n, dtype=np.float32) ** p

    box = np.ones((h, w), dtype=np.float32)
    box[:, :FR_L] *= _ramp(FR_L, 2.4)[None, :]
    box[:, -FR_R:] *= _ramp(FR_R, 1.45)[::-1][None, :]
    box[:FR_T, :] *= _ramp(FR_T, 2.2)[:, None]
    box[-FR_B:, :] *= _ramp(FR_B, 1.35)[::-1][:, None]

    taper = (shape_feather ** 0.60) * box
    protect = np.zeros((h, w), dtype=np.float32)
    for (cx, cy, rx, ry) in PROTECT:
        protect = np.maximum(protect, _blob(h, w, cx, cy, rx, ry))
    taper = np.maximum(taper, protect)

    # ── 收细：做"侵蚀"而不是降透明度 ─────────────────────────────
    # taper=1 处原样保留；taper 越小，越只有墨最浓的线心能留下，
    # 于是线一根根变细、直至断掉 —— 这才是"线条末端变细"。
    # 但只做侵蚀的话，线心（ink=1）到最边上仍会留一根满墨细线，
    # 所以末段再叠一道很短的透明度收口，让线真正化没。
    ink_full = ink.copy()          # 侵蚀前的完整墨版 —— 求剪影必须用它
    # 先柔化、再侵蚀。纯黑白的线稿直接做侵蚀几乎无效：线心恒为 1，
    # `(ink-(1-taper))/taper` 恒等于 1，线宽根本不变，最后只能靠降透明度
    # 去"变浅" —— 那正是用户不要的效果。柔化之后线条有了可侵蚀的边缘剖面，
    # 阈值一抬，线**真的变细**，直至断掉。
    soft = np.asarray(Image.fromarray((ink * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(SOFTEN))).astype(np.float32) / 255.0
    ink = np.clip((soft - (1.0 - taper)) / np.maximum(taper, 1e-3), 0.0, 1.0)
    # 只在最末尾留一点点透明度收口，主体靠"线变细"消失，不靠"变淡"
    fade_op = np.clip((taper - 0.02) / 0.06, 0.0, 1.0)
    ink = ink * fade_op

    # 极轻柔化，避免缩放后的锯齿
    ink = np.asarray(Image.fromarray((ink * 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(0.45))).astype(np.float32) / 255.0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = INK.astype(np.uint8)
    out[..., 3] = np.clip(ink * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT_PNG)

    # ── 遮底板用的人物轮廓 ───────────────────────────────────────
    # 注意：不能用"墨的浓度"当轮廓 —— 围裙和脸是**留白区**，墨≈0，
    # 于是防伪底纹正好从脸上、围裙上透出来。必须求出**填实的剪影**：
    # 把线条加粗封口 → 从四角洪水填充标出"外面" → 剩下的就是内部。
    #
    # 必须用**侵蚀前**的 ink_full：侵蚀会把淡出区的轮廓线啃断，
    # 一旦轮廓开口，洪水就从缺口灌进裙摆内部 ⇒ 内部被判成"外面"
    # ⇒ 底纹直接横穿下半身（就是之前露馅的地方）。
    b = ((ink_full > 0.30) * 255).astype(np.uint8)
    # 取景是按内容 bbox 紧裁的，四角**本来就压在线稿上**，
    # 于是"从角落洪水填充"根本起不来 ⇒ 外面标不出来 ⇒ 剪影退化成整幅。
    # 先把最外两圈强制清成背景，保证一定有一个可起灌的种子。
    b[:2, :] = 0; b[-2:, :] = 0; b[:, :2] = 0; b[:, -2:] = 0
    bi = Image.fromarray(b).filter(ImageFilter.MaxFilter(9))       # 封住线条缺口

    # 洪水填充"外面"。两个坑：
    # ① Pillow 的 `ImageDraw.floodfill` 在本机版本上对 'L' 图**实测不生效**
    #    （写完像素没变，还不报错），故自己用形态学重建做。
    # ② 不能降到 1/4 分辨率跑 —— 线稿的轮廓线只有 1px 宽，双线性缩到 1/4
    #    会被平均掉，轮廓一断洪水就灌进围裙内部，底纹又穿出来。
    #    直接在原分辨率迭代（每次膨胀 1px，约千次收敛）。
    free = (np.asarray(bi) == 0)                                  # True = 可通行
    # 取景是"上半身"，**底边正好把人物切断** —— 围裙的轮廓在底边是开口的，
    # 洪水会从底边灌进围裙内部，把内部判成"外面"，底纹就从围裙上穿过去。
    # 把最底下几行封成墙即可；外面的背景另有左右两侧可绕通，不受影响。
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
    outside = cur
    print("silhouette: outside = %.1f%%  (character = %.1f%%)"
          % (outside.mean() * 100, 100 - outside.mean() * 100))
    sil = ((~outside) | (np.asarray(bi) > 0)).astype(np.uint8) * 255
    # 分割线就取角色**最外圈边缘**：只往外放 2px（避免底纹贴线），
    # 边缘只软 1.5px。放得太宽 / 糊得太狠，剪影外就会出现一圈"没有底纹"的空带。
    sil = np.asarray(Image.fromarray(sil).filter(ImageFilter.MaxFilter(5))
                     ).astype(np.float32) / 255.0
    cover = np.asarray(Image.fromarray((sil * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255.0
    cover = np.clip(cover * 1.25, 0.0, 1.0)
    # 遮底板跟着人物自己的淡出一起收，但**不能用 taper 本身**：
    # 侵蚀对 ink=1 的线心几乎不衰减（taper 掉到 0.35 时线仍是满墨），
    # 而人物真正消失是在 `clip(taper/0.16)` 那一步 —— 用 taper 直接乘，
    # 遮罩会比人物早退一大截，底纹就从还看得见的围裙上透出来。
    # 这里把收口**直接绑到人物自己的可见度 `fade_op`**。
    # 之前试过用 taper 的各种窗口去近似，都会留下一条"人还看得见、底纹先
    # 回来"的带子（就是围裙下缘与 DeepSeek 压印那一片网格）。绑到 fade_op
    # 就不存在这个窗口：只要人物还有一点墨，遮罩就是满的；人物彻底没了，
    # 遮罩才撤。边界落在人物消失的等值线上，那里墨本来就是 0，看不出来。
    cover = cover * np.clip((taper - 0.06) / 0.08, 0.0, 1.0)
    cv = np.zeros((h, w, 4), dtype=np.uint8)
    cv[..., 3] = np.clip(cover * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(cv, "RGBA").save(OUT_COVER)

    # ── 校样：原线稿 / 墨版 / 票面尺寸（890×778）/ 缩微 ────────────
    paper = (216, 219, 233)
    src_im = Image.open(SRC).convert("RGBA").crop(CROP)
    lin_im = Image.open(OUT_PNG).convert("RGBA")
    tiles = []
    for im, sz in ((src_im, 340), (lin_im, 340), (lin_im, 250), (lin_im, 150)):
        t = im.resize((sz, round(im.height * sz / im.width)), Image.LANCZOS)
        bg = Image.new("RGBA", t.size, paper + (255,))
        bg.alpha_composite(t)
        tiles.append(bg.convert("RGB"))
    HH = max(t.height for t in tiles)
    proof = Image.new("RGB", (sum(t.width for t in tiles) + 12 * (len(tiles) - 1), HH), (238, 240, 244))
    x = 0
    for t in tiles:
        proof.paste(t, (x, 0))
        x += t.width + 12
    proof.save(PROOF)
    print("plate:", OUT_PNG, os.path.getsize(OUT_PNG))
    print("proof:", PROOF, proof.size)


if __name__ == "__main__":
    build()
