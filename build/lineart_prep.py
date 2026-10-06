# -*- coding: utf-8 -*-
"""线稿入库：把外部生成的线稿（黑线白底 / 透明底均可）处理成票面可用的单色墨稿。

用法：
    python lineart_prep.py <线稿文件> [输出名]

处理链：
    1. 合成到白底（含 alpha 的图先合白）→ 灰度；
    2. 墨量 = 暗度线性映射（lo 以下视为纸白丢弃，hi 以上视为满墨），可选 gamma 调线重；
    3. 裁掉四周空白（只留墨迹包围盒）；
    4. 等比缩放到票面所需高度 target_h；
    5. 染成指定墨色（默认票面藏青 #1B2657）输出 RGBA PNG。
同时输出一张「叠在纸色上的目视校样」，便于确认缩放后是否可辨。
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = r"E:\Agent项目\鲸元券"
OUTDIR = os.path.join(ROOT, "assets", "portrait")
INK = (27, 38, 87)          # 票面藏青 #1B2657


def prep(src, out_png, ink=INK, lo=0.05, hi=0.50, gamma=1.0,
        target_h=1040, target_w=None, blur=0.0, trim=True):
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")

    L = np.asarray(im.convert("L")).astype(np.float32) / 255.0
    d = np.clip((1.0 - L - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    if gamma != 1.0:
        d = d ** gamma
    if blur > 0:
        di = Image.fromarray((d * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
        d = np.asarray(di).astype(np.float32) / 255.0

    h, w = d.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = ink
    out[..., 3] = (d * 255).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")

    if trim:
        bbox = img.split()[3].point(lambda v: 255 if v > 5 else 0).getbbox()
        if bbox:
            img = img.crop(bbox)

    iw, ih = img.size
    if target_w:
        s = target_w / float(iw)
    else:
        s = target_h / float(ih)
    img = img.resize((max(1, int(round(iw * s))), max(1, int(round(ih * s)))), Image.LANCZOS)

    img.save(out_png)
    print("saved:", out_png, img.size)

    # 目视校样：叠在票面纸色上
    paper = (216, 219, 233)   # 100,000,000 档纸色 #D8DBE9
    cw, ch = img.size
    proof = Image.new("RGB", (cw, ch), paper)
    proof.paste(img, (0, 0), img)
    pp = os.path.splitext(out_png)[0] + "-proof.png"
    proof.save(pp)
    print("proof:", pp)
    return img


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    src = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "portrait-lineart.png"
    prep(src, os.path.join(OUTDIR, name))
