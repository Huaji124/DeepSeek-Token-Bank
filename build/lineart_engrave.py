# -*- coding: utf-8 -*-
"""人物主景 → 凹版雕刻线稿（排线由原画明暗驱动）。

原理（这就是真实凹版雕刻的做法）：雕刻人像没有渐变，体积完全靠**平行排线的疏密**表达。
所以不去"抽取线条"，而是：
  1) 从原画取明暗图 D（暗 = 墨多）；
  2) 铺若干**角度不同**的平行线族，每一条线的**线宽**随该处 D 变化
     —— 用「到最近线心的距离」直接算覆盖率，可在 numpy 里向量化，
        等效于逐像素决定这一刀刻多深；
  3) 由浅到深依次启用第二、第三组交叉排线（cross-hatch），形成完整的墨阶；
  4) 再叠一层**轮廓边**（原画梯度），把五官与衣褶的"界"钉死，这是可辨识度的关键；
  5) 全稿染成票面藏青，输出透明底 RGBA。

输出：`assets/portrait/portrait-lineart.png`
校样：`build/lineart-engrave.png`（原画 / 线稿 / 票面尺寸对照 + 缩微）
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = r"E:\Agent项目\鲸元券"
sys.path.insert(0, os.path.join(ROOT, "build"))
import key_portrait as KEYP                                    # noqa: E402

# ── 输入：**一开始的原图**（彩色插画），脚本自己负责去底 ───────────────
SRC = os.path.join(ROOT, "assets", "source", "character-full.jpg")
KEYED = os.path.join(ROOT, "assets", "portrait", "portrait-keyed-half.png")
# 半张票面的横构图：1052×920 → 比例 1.143，与票面左半区（890×782）一致
CROP = (0, 60, 1052, 980)
TARGET_W = 1200

INK = np.array([27, 38, 87], dtype=np.float32)      # #1B2657
OUT_PNG = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.png")
OUT_COVER = os.path.join(ROOT, "assets", "portrait", "portrait-cover.png")
PROOF = os.path.join(ROOT, "build", "lineart-engrave.png")

SPACING = 7.6        # 排线间距（px）
SOFT = 0.95          # 线缘柔度
# 线宽上限 = 0.70 × 间距 —— 最暗处也要留出约 2.2px 的缝，
# 缝是"这是刻出来的线"的唯一证据；一旦并死，读起来就变成印刷网点。
LINE_MAX = SPACING * 0.70
ANG0 = 0.62          # 保留给背景底纹用（人像已改为等值线排线）
KCONTOUR = 26.0      # （保留，当前未启用）
SHADOW_CUT = 0.80    # 亮于该亮度处完全不出线（皮肤/围裙保持干净）
SKIN_CUT = 0.62      # 局部亮度高于此值即判为"皮肤/亮面"，不出排线
FADE_R = 92.0        # 淡入场的模糊半径（px）—— 越大淡入范围越宽
FADE_G = 0.30        # 场高于该值算"人物本体"，保持满墨


def load():
    """原图 → 去底 RGBA → 明暗图。"""
    if not os.path.exists(KEYED):
        KEYP.process(SRC, KEYED, CROP, TARGET_W)
    im = Image.open(KEYED).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3] / 255.0
    # 合成到白底，避免透明区被当成黑
    rgb = rgb * alpha[..., None] + 255.0 * (1 - alpha[..., None])
    lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) / 255.0
    return rgb, alpha, lum


def ink_map(lum, alpha):
    """明暗 → 每一点该刻多深 0..1。

    关键是**抬高白场切断点**：皮肤/脸/围裙在插画里本来就亮，
    只要它们还落在 0..1 的浅端，就会铺出一层极细的假排线 ——
    这正是"皮肤看着很脏"的来源。亮于 WHITE_CUT 的地方一点墨都不出。
    """
    WHITE_CUT, SPAN = 0.845, 0.615      # lum >= 0.845 → 0；lum <= 0.230 → 1
    d = np.clip((WHITE_CUT - lum) / SPAN, 0.0, 1.0)
    return d * np.clip((alpha - 0.35) / 0.45, 0.0, 1.0)


def hatch_cover(h, w, ang, width):
    """某一角度下平行排线的覆盖率。width 为逐像素线宽（px）。

    注意：抗锯齿项 `(half-d)/SOFT + 0.5` 在 width→0 时仍会在**线心**给出 0.5，
    会让整个透明背景浮出一层假排线。故再乘一个「线宽存在度」因子把它压回 0。
    """
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = (-xx * math.sin(ang) + yy * math.cos(ang))
    d = np.abs((v % SPACING) - SPACING * 0.5)          # 到最近线心的距离
    half = np.maximum(width, 0.0) * 0.5
    cover = np.clip((half - d) / SOFT + 0.5, 0.0, 1.0)
    return cover * np.clip(half * 2.0 / SOFT, 0.0, 1.0)


def _blob(h, w, cx, cy, rx, ry, soft=0.42):
    """椭圆保护罩：q<=1 处为 1，到 q>=1+soft 处降为 0。"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    q = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip((1.0 + soft - q) / soft, 0.0, 1.0)


def engrave(rgb, alpha, lum):
    h, w = lum.shape
    d = ink_map(lum, alpha)
    # 平滑墨量，避免原画噪点变成斑纹
    d = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.1))).astype(np.float32) / 255.0

    # ── 淡出方式：**收细线条**，不是降低不透明度 ────────────────────
    # 用户要求「线条在末端变细的那种淡化」。做法是把淡出系数乘到**明暗图 d** 上，
    # 而不是乘到最终的 ink 上：d 决定每一刀的线宽与启用几组排线，
    # d 变小 ⇒ 线越刻越细、交叉组数递减 ⇒ 笔画自然"收尖"消失，
    # 而已经刻出来的线始终是满墨的实线（不会变成灰雾）。
    def _ramp(n, p=1.9):
        return np.linspace(0.0, 1.0, n, dtype=np.float32) ** p

    a8b = (alpha * 255).astype(np.uint8)
    field = np.asarray(Image.fromarray(a8b)
                       .filter(ImageFilter.GaussianBlur(FADE_R))).astype(np.float32) / 255.0
    shape_feather = np.clip(field / FADE_G, 0.0, 1.0) ** 0.85

    FR_L, FR_R, FR_T, FR_B = 46, 380, 64, 330
    box_feather = np.ones((h, w), dtype=np.float32)
    box_feather[:, :FR_L] *= _ramp(FR_L, 2.4)[None, :]
    box_feather[:, -FR_R:] *= _ramp(FR_R, 1.30)[::-1][None, :]
    box_feather[:FR_T, :] *= _ramp(FR_T, 2.2)[:, None]
    box_feather[-FR_B:, :] *= _ramp(FR_B, 1.25)[::-1][:, None]

    taper = (shape_feather ** 0.55) * box_feather

    # 头/脸/耳鳍与双手必须保持清晰 —— 在这些位置把淡出直接顶回 1
    protect = np.zeros((h, w), dtype=np.float32)
    for cx, cy, rx, ry in ((615, 285, 250, 185),      # 头 · 脸 · 耳鳍
                           (992, 488, 132, 126),      # 抬起的手
                           (292, 788, 102, 96)):      # 下方的手
        protect = np.maximum(protect, _blob(h, w, cx, cy, rx, ry))
    taper = np.maximum(taper, protect)
    taper = np.asarray(Image.fromarray((taper * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0

    d = d * taper

    # 排线逼近脸部时**逐渐变细**（而不是被遮罩一刀切断）——
    # 直接乘 cov 会把发丝拦腰截断，留下一圈放射状的"划痕"。
    # 乘到 d 上则线条自然收细、收没，和前面那套"末端变细"的淡出同一套语言。
    face = _blob(h, w, 600.0, 272.0, 104.0, 76.0, soft=0.95)
    d = d * (1.0 - 0.97 * face)

    w1 = LINE_MAX * np.clip(d / 0.58, 0.0, 1.0)
    cov = hatch_cover(h, w, ANG0, w1)

    w2 = (LINE_MAX * 0.42) * np.clip((d - 0.80) / 0.20, 0.0, 1.0)
    c2 = hatch_cover(h, w, ANG0 + math.pi / 2.0, w2)
    cov = 1.0 - (1.0 - cov) * (1.0 - c2)

    # 皮肤按亮度软门控（皮肤亮 ⇒ 门为 0；头发/裙子暗 ⇒ 门为 1）。
    # 边界落在明暗交界处，本来就是有形体的地方，看不见任何几何形状。
    base = np.asarray(Image.fromarray((lum * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(3.0))).astype(np.float32) / 255.0
    cov = cov * np.clip((SKIN_CUT - base) / 0.18, 0.0, 1.0)

    # 排线从脸上撤掉后脸会"空" —— 五官得靠原画自己画好的线补回来。
    feat = np.clip((0.86 - lum) / 0.16, 0.0, 1.0)
    feat = feat * np.clip(face * 1.7, 0.0, 1.0)
    # 必须再乘一道"这里是皮肤"的亮度门 —— 否则脸周围那一圈深色头发
    # 会被 feat 一起抓成实心，脸上就多出一个黑椭圆。
    feat = feat * np.clip((base - 0.52) / 0.22, 0.0, 1.0)
    feat = np.asarray(Image.fromarray((feat * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255.0
    cov = np.maximum(cov, feat * 0.92)

    # 轮廓线：把五官与衣褶的"界"钉死（可辨识度的关键）。
    # 门限必须高 —— 低门限会把 JPEG 噪点、网纹边缘全当成线，皮肤就是这样变脏的。
    g = np.asarray(Image.fromarray((lum * 255).astype(np.uint8))
                   .filter(ImageFilter.MedianFilter(3))
                   .filter(ImageFilter.GaussianBlur(1.1))).astype(np.float32)
    gy, gx = np.gradient(g)
    mag = np.hypot(gx, gy)
    edge = np.clip((mag - 22.0) / 44.0, 0.0, 1.0)
    # 门控放开一点：原先要求"暗"才留边，结果脸上连自己画好的五官轮廓都被滤掉，
    # 亮面（脸、手）显得空。现在只要在人物实心区内、不是平坦噪声就留。
    edge = edge * np.clip((d + 0.02) / 0.34, 0.0, 1.0)
    edge = edge * np.clip((alpha - 0.60) / 0.25, 0.0, 1.0) * taper

    # 剪影外缘（柔和过渡：先取梯度再模糊，避免 1px 硬描边）
    a8 = (alpha * 255).astype(np.uint8)
    sil = np.asarray(Image.fromarray(a8).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255.0
    sy, sx = np.gradient(sil)
    sil_edge = np.clip(np.hypot(sx, sy) * 3.2, 0.0, 1.0) * taper
    sil_edge = np.asarray(Image.fromarray((sil_edge * 255).astype(np.uint8))
                          .filter(ImageFilter.GaussianBlur(1.4))).astype(np.float32) / 255.0

    ink = np.clip(cov * 0.97, 0.0, 1.0) * np.clip((alpha - 0.30) / 0.35, 0.0, 1.0)
    ink = np.maximum(ink, edge * 0.95)
    ink = ink + (1.0 - ink) * sil_edge * 0.92

    # 整体极轻微柔化，让排线边缘不生硬
    ink = np.asarray(Image.fromarray((np.clip(ink, 0, 1) * 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255.0

    # ── 遮底（cover）：把票面防伪底纹挡在人物轮廓之外 ──────────────
    cfield = np.asarray(Image.fromarray((np.clip(alpha * 2.6, 0, 1) * 255).astype(np.uint8))
                        .filter(ImageFilter.GaussianBlur(FADE_R * 0.30))).astype(np.float32) / 255.0
    cover = np.clip(cfield / 0.45, 0.0, 1.0) ** 0.7
    cover = cover * np.clip(np.maximum(box_feather, protect) * 1.25, 0.0, 1.0)
    cover = np.asarray(Image.fromarray((cover * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32) / 255.0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = INK.astype(np.uint8)
    out[..., 3] = np.clip(ink * 255.0, 0, 255).astype(np.uint8)

    cov_out = np.zeros((h, w, 4), dtype=np.uint8)
    cov_out[..., 0:3] = 255
    cov_out[..., 3] = np.clip(cover * 255.0, 0, 255).astype(np.uint8)
    return out, cov_out


def main():
    rgb, alpha, lum = load()
    out, cov_out = engrave(rgb, alpha, lum)
    Image.fromarray(out, "RGBA").save(OUT_PNG)
    Image.fromarray(cov_out, "RGBA").save(OUT_COVER)

    # ── 校样：原画 / 线稿 / 票面尺寸 / 缩微
    paper = (216, 219, 233)
    src_im = Image.open(KEYED).convert("RGBA")
    lin_im = Image.open(OUT_PNG).convert("RGBA")

    def on_paper(img, w=None):
        if w:
            img = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS)
        bg = Image.new("RGB", img.size, paper)
        bg.paste(img, (0, 0), img)
        return bg

    panels = [
        on_paper(src_im, 300),
        on_paper(lin_im, 300),
        on_paper(lin_im, 150),
        on_paper(lin_im, 76),
    ]
    gap = 24
    Wt = sum(p.width for p in panels) + gap * (len(panels) + 1)
    Ht = max(p.height for p in panels) + gap * 2
    sheet = Image.new("RGB", (Wt, Ht), (238, 240, 244))
    x = gap
    for p in panels:
        sheet.paste(p, (x, gap))
        x += p.width + gap
    sheet.save(PROOF)
    print("lineart:", OUT_PNG, os.path.getsize(OUT_PNG))
    print("proof  :", PROOF, sheet.size)


if __name__ == "__main__":
    main()
