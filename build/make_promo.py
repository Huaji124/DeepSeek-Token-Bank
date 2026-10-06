# -*- coding: utf-8 -*-
"""完整宣传片：由**正反两条逐层搭建片**拼成一条。

结构（24 fps）：
    片头  6.0 s   标题浮现
    正面 32.17 s  直接复用 `_buildup\f*.png`（不重渲）
    转场  0.8 s   交叠溶解
    反面 32.17 s  直接复用 `_buildup_back\f*.png`
    片尾  9.0 s   六档正票依次浮现 → 落标题 → 淡出
    合计 ≈ 80.1 s

做法上刻意的选择：**正反两段一帧都不重画**，本脚本只生成片头/转场/片尾，
中间两段直接从 `make_buildup.py` 已经产出的帧序列拷过来。这样宣传片与两条
分片永远逐像素同源，改一处不会出现两个版本。

`$env:WY_SCALE = "2"` 时出 4K（读 `_buildup4k` / `_buildup_back4k` 的 JPEG 帧）。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_buildup as MB
import palette as PAL
from PIL import Image, ImageDraw

ROOT = r"E:\Agent项目\鲸元券"
S = MB.S
W, H, FPS = MB.W, MB.H, 24
INK, GOLD, DIM, BG = MB.INK, MB.GOLD, MB.DIM, MB.BG


def crop_note(im):
    """1900×900 展示稿 → 只留票面本体（与 sheet_all.py 同一套换算）。"""
    sc, ox, oy = 0.9386, 63.0, 36.0
    return im.crop((max(0, int(ox + 30 * sc) - 1), max(0, int(oy + 30 * sc) - 1),
                    min(im.width, int(ox + 1860 * sc) + 1),
                    min(im.height, int(oy + 852 * sc) + 1)))

INTRO_F, TRANS_F, OUTRO_F = 144, 19, 216
SRC_FRONT = os.path.join(ROOT, "build", "_buildup" if S == 1 else "_buildup4k")
SRC_BACK = os.path.join(ROOT, "build", "_buildup_back" if S == 1 else "_buildup_back4k")
OUT = os.path.join(ROOT, "build", "_promo" if S == 1 else "_promo4k")
EXT = "png" if S == 1 else "jpg"


def stage():
    return MB.make_bg().copy()


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(t, a, b, soft=0.35):
    """0→1 并在 b 之后**保持 1**（淡入即驻留）。"""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    return ease((t - a) / (b - a))


def die(t, a, b):
    """1→0（淡出），用于片尾收尾与标题交叠。"""
    return 1.0 - seg(t, a, b)


def centre_text(d, y, txt, f, col, alpha, track=0.0):
    if alpha <= 0.01:
        return
    if track:
        w = sum(d.textlength(c, font=f) + track for c in txt) - track
        x = (W - w) / 2
        for c in txt:
            d.text((x, y), c, font=f, fill=col + (int(255 * alpha),))
            x += d.textlength(c, font=f) + track
    else:
        w = d.textlength(txt, font=f)
        d.text((W / 2 - w / 2, y), txt, font=f, fill=col + (int(255 * alpha),))


def mixed_line(d, y, parts, alpha, gap=26):
    """一行里混排中英文：parts = [(文本, 字体, 颜色, 字距, 基线微调), ...]，整体居中。

    **必须分行画、各用各的字体** —— 拉丁字体（Georgia）没有汉字字形，
    把「开源」丢给 `font("en")` 会渲染成两个方框（tofu）。
    """
    if alpha <= 0.01:
        return
    ws = []
    for txt, f, _c, tr, _dy in parts:
        ws.append(sum(d.textlength(ch, font=f) + tr for ch in txt) - tr)
    total = sum(ws) + gap * S * (len(parts) - 1)
    x = (W - total) / 2
    for (txt, f, col, tr, dy), w in zip(parts, ws):
        cx = x
        for ch in txt:
            d.text((cx, y + dy * S), ch, font=f, fill=col + (int(255 * alpha),))
            cx += d.textlength(ch, font=f) + tr
        x += w + gap * S


def render_intro(i):
    """片头：**大字「鲸元券」，小字「开源」**。

    机构名（DeepSeek Token银行）是印在票面上的发行主体，放在片头会让人误以为
    这是官方发行，所以片头只讲名字 + 性质：鲸元券，开源的。
    """
    t = i / FPS
    im = stage()
    d = ImageDraw.Draw(im, "RGBA")
    a1 = seg(t, 0.7, 2.2)
    a2 = seg(t, 1.9, 3.2)
    a3 = seg(t, 3.0, 4.4)
    a4 = seg(t, 3.5, 4.9)
    fade = die(t, 5.2, 6.0)
    centre_text(d, H * 0.345, "鲸元券", MB.font("cnb", 116), INK, a1 * fade, track=24 * S)
    mixed_line(d, H * 0.590,
               [("开源", MB.font("cnb", 32), GOLD, 10 * S, 0),
                ("OPEN SOURCE", MB.font("en", 24), GOLD, 6 * S, 6 * S)],
               a2 * fade, gap=30)
    rw = 300 * S * a3
    d.line([(W / 2 - rw, H * 0.672), (W / 2 + rw, H * 0.672)],
           fill=GOLD + (int(190 * a3 * fade),), width=2 * S)
    centre_text(d, H * 0.712, "完整设计方案 · 2026年", MB.font("cn", 30), DIM, a4 * fade, track=4 * S)
    return im


def render_outro(i):
    t = i / FPS
    im = stage()
    d = ImageDraw.Draw(im, "RGBA")
    names = ["front-%d.png" % k if k != 3 else "mockup-100.png" for k in range(6)]
    cols = [PAL.SERIES[k][2] for k in range(6)]
    nums = [PAL.SERIES[k][0] for k in range(6)]
    if not hasattr(render_outro, "_cache"):
        notes = []
        for n in names:
            p = os.path.join(ROOT, "build", n)
            notes.append(crop_note(Image.open(p).convert("RGB")))
        render_outro._cache = notes
    notes = render_outro._cache
    tw = int(W * 0.80 / 6 * 0.92)
    th = int(tw * notes[0].height / notes[0].width)
    x0 = (W - tw * 6 - 12 * S * 5) / 2
    y0 = H * 0.30
    for k in range(6):
        a = seg(t, 0.55 + k * 0.22, 1.55 + k * 0.22)
        if a <= 0.01:
            continue
        im2 = notes[k].resize((tw, th), Image.LANCZOS)
        px = int(x0 + k * (tw + 12 * S))
        py = int(y0 + 26 * S * (1 - a))
        im.paste(im2, (px, py))
        d.text((px, py + th + 12 * S), nums[k], font=MB.font("en", 15), fill=INK + (int(220 * a),))
        d.text((px, py + th + 33 * S), cols[k], font=MB.font("en", 12), fill=DIM + (int(200 * a),))
    a = seg(t, 2.4, 3.6) * die(t, 6.4, 7.2)
    centre_text(d, H * 0.615, "六档面额 · 正反两面 · 全矢量可缩放", MB.font("cn", 26), INK, a, track=3 * S)
    b = seg(t, 3.6, 4.8)
    centre_text(d, H * 0.700, "DeepSeek Token银行", MB.font("cnb", 44), GOLD, b, track=5 * S)
    c = seg(t, 4.3, 5.4)
    centre_text(d, H * 0.775, "鲸元券 · 全档图稿　2026年", MB.font("cn", 20), DIM, c, track=3 * S)
    k = die(t, 7.4, 8.6)
    if k < 1.0:
        ov = Image.new("RGBA", (W, H), (13, 16, 20, int(255 * (1 - k))))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0

    def put(im):
        nonlocal n
        p = os.path.join(OUT, "f%05d.%s" % (n, EXT))
        if EXT == "png":
            im.save(p)
        else:
            im.save(p, "JPEG", quality=96, subsampling=0)
        n += 1

    for i in range(INTRO_F):
        put(render_intro(i))
    print("intro done", flush=True)
    fr = sorted(os.listdir(SRC_FRONT))
    for f in fr:
        shutil.copyfile(os.path.join(SRC_FRONT, f), os.path.join(OUT, "f%05d.%s" % (n, EXT)))
        n += 1
    print("front done: %d" % len(fr), flush=True)
    # 转场：正面末帧 → 反面首帧 交叠溶解
    last = Image.open(os.path.join(SRC_FRONT, fr[-1])).convert("RGB")
    first = Image.open(os.path.join(SRC_BACK, sorted(os.listdir(SRC_BACK))[0])).convert("RGB")
    for i in range(TRANS_F):
        a = ease(i / (TRANS_F - 1.0))
        put(Image.blend(last, first, a))
    print("transition done", flush=True)
    for f in sorted(os.listdir(SRC_BACK)):
        shutil.copyfile(os.path.join(SRC_BACK, f), os.path.join(OUT, "f%05d.%s" % (n, EXT)))
        n += 1
    print("back done", flush=True)
    for i in range(OUTRO_F):
        put(render_outro(i))
    print("done: %d frames = %.2f s @ %dx%d -> %s" % (n, n / FPS, W, H, OUT))


if __name__ == "__main__":
    main()
