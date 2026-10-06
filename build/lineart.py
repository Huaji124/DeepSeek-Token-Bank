# -*- coding: utf-8 -*-
"""人物稿 → 线稿转换：黑帽形态学抽取暗线 + alpha 轮廓线。

原理：
  1. 在合成到白底后的灰度图上做「形态学闭运算」——闭运算会填掉比结构元更细的暗线，
     用 (闭 − 原图) 得到「黑帽」，即只保留细暗线，丢弃大面积明暗；
  2. alpha 通道的形态学梯度给出人物剪影轮廓，补进墨线（否则线稿没有外轮廓）；
  3. 两条墨线取 max，软阈值化成 alpha，再染成指定墨色。
"""
import os

import numpy as np
from PIL import Image, ImageFilter

ROOT = r"E:\Agent项目\鲸元券"
SRC = os.path.join(ROOT, "assets", "portrait", "portrait-keyed-3x4.png")
CHIBI = os.path.join(ROOT, "assets", "portrait", "chibi-keyed.png")
OUT = os.path.join(ROOT, "assets", "portrait")


def _lum(src):
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3] / 255.0
    comp = rgb * al[..., None] + 255.0 * (1.0 - al[..., None])
    L = 0.299 * comp[..., 0] + 0.587 * comp[..., 1] + 0.114 * comp[..., 2]
    return L, al


def lineart(src, k=7, t0=0.05, t1=0.18, cw=5.0, ct=0.9, ink=(27, 38, 87)):
    """k=结构元尺寸(须为奇数)；t0/t1=黑帽软阈值区间；cw=轮廓抽取强度；ct=轮廓权重。"""
    L, al = _lum(src)
    Li = Image.fromarray(L.clip(0, 255).astype(np.uint8))
    closed = Li.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    bh = np.asarray(closed).astype(np.float32) - np.asarray(Li).astype(np.float32)
    ink_a = np.clip((bh - t0) / max(t1 - t0, 1e-6), 0.0, 1.0)

    ai = Image.fromarray((al * 255).astype(np.uint8))
    grad = (np.asarray(ai.filter(ImageFilter.MaxFilter(3))).astype(np.float32)
            - np.asarray(ai.filter(ImageFilter.MinFilter(3))).astype(np.float32))
    cont = np.clip(grad / max(cw, 1e-6), 0.0, 1.0) * ct

    a = np.maximum(ink_a, cont)
    a[al < 0.04] = 0.0
    # 轻微模糊做抗锯齿
    aim = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(aim).astype(np.float32) / 255.0

    h, w = a.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = ink
    out[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def lineart_edge(src, blur=1.5, dark=150.0, dark2=95.0, e0=8.0, e1=40.0,
                 ct=0.9, cw=5.0, ink=(27, 38, 87)):
    """边缘 + 暗度门控：只保留「暗侧确实很暗」的边缘，剔掉亮部的明暗分界。"""
    L, al = _lum(src)
    Li = Image.fromarray(L.clip(0, 255).astype(np.uint8))
    Ls = Li.filter(ImageFilter.GaussianBlur(blur))
    E = np.asarray(Ls.filter(ImageFilter.FIND_EDGES)).astype(np.float32)
    Lmin = np.asarray(Li.filter(ImageFilter.MinFilter(5))).astype(np.float32)
    gate = np.clip((dark - Lmin) / max(dark - dark2, 1e-6), 0.0, 1.0)
    ink_a = np.clip((E - e0) / max(e1 - e0, 1e-6), 0.0, 1.0) * gate

    ai = Image.fromarray((al * 255).astype(np.uint8))
    grad = (np.asarray(ai.filter(ImageFilter.MaxFilter(3))).astype(np.float32)
            - np.asarray(ai.filter(ImageFilter.MinFilter(3))).astype(np.float32))
    cont = np.clip(grad / max(cw, 1e-6), 0.0, 1.0) * ct

    a = np.maximum(ink_a, cont)
    a[al < 0.04] = 0.0
    aim = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(aim).astype(np.float32) / 255.0

    h, w = a.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = ink
    out[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


if __name__ == "__main__":
    variants = [
        ("E1", lineart_edge, dict(blur=1.0, dark=150, dark2=95, e0=8, e1=40)),
        ("E2", lineart_edge, dict(blur=1.5, dark=160, dark2=100, e0=6, e1=32)),
        ("E3", lineart_edge, dict(blur=2.0, dark=170, dark2=110, e0=5, e1=28)),
        ("E4", lineart_edge, dict(blur=2.5, dark=180, dark2=120, e0=4, e1=24)),
    ]
    imgs = []
    for name, fn, kw in variants:
        im = fn(SRC, **kw)
        im.save(os.path.join(OUT, f"portrait-lineart-{name}.png"))
        imgs.append((name, im))
        print("saved", name, kw)

    # 接触印相：上行全图，下行头部 3x
    PAPER = (245, 239, 222)
    cw_, ch = 300, 400
    sheet = Image.new("RGB", (cw_ * len(imgs), ch * 2 + 40), (238, 240, 244))
    for i, (name, im) in enumerate(imgs):
        for row, crop in enumerate([(0, 0, 780, 1040), (150, 60, 560, 607)]):
            c = im.crop(crop)
            if row == 0:
                c = c.resize((cw_, ch), Image.LANCZOS)
            else:
                c = c.resize((cw_, ch), Image.LANCZOS)
            bg = Image.new("RGB", (cw_, ch), PAPER)
            bg.paste(c, (0, 0), c)
            sheet.paste(bg, (i * cw_, row * ch + row * 20))
    p = os.path.join(ROOT, "build", "lineart-variants.png")
    sheet.save(p)
    print("sheet:", p)
