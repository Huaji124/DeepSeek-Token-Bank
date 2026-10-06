# -*- coding: utf-8 -*-
"""鲸元券 · 介绍动画渲染器（PIL 逐帧 → PNG 序列 → ffmpeg H.264）。

设计取向：**高档、克制、慢**。
  · 深石墨底 #0D1014 + 暖白 #F2EFE8 + 细金线 #C9A227
  · 运动一律缓入缓出，无回弹、无弹跳
  · 每个镜头只做一件事：推近 / 平移 / 淡入
  · 大留白，文字字距放宽，章节号用 Georgia

用法：
  & $py build\\make_reel.py            # 渲染全部帧
  & $py build\\make_reel.py --probe 12 # 只出 12 张抽样图用于校对
"""
import base64
import io
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = r"E:\Agent项目\鲸元券"
REEL = os.path.join(ROOT, "build", "reel")
FRAMES = os.path.join(ROOT, "build", "reel_frames")

W, H = 1920, 1080
FPS = 24

BG = (13, 16, 20)
INK = (242, 239, 232)
GOLD = (201, 162, 39)
DIM = (122, 130, 144)
PAPER = (245, 239, 222)

FT = r"C:\Windows\Fonts"
F_CN = os.path.join(FT, "msyh.ttc")
F_CNB = os.path.join(FT, "msyhbd.ttc")
F_EN = os.path.join(FT, "georgia.ttf")
F_ENB = os.path.join(FT, "georgiab.ttf")
F_MONO = os.path.join(FT, "consola.ttf")

_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


# ── 缓动 ────────────────────────────────────────────────────────────
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def seg(t, a, b):
    """把全局时间 t 归一化到 [a, b] 区间内，超出则夹紧。"""
    if b <= a:
        return 1.0
    return max(0.0, min(1.0, (t - a) / (b - a)))


# ── 底 ──────────────────────────────────────────────────────────────
def make_bg():
    """深底 + 极轻的暗角。一次生成，全程复用。"""
    y, x = np.mgrid[0:H, 0:W]
    dx = (x - W / 2) / (W / 2)
    dy = (y - H / 2) / (H / 2)
    r = np.sqrt(dx * dx + dy * dy) / 1.414
    v = 1.0 - 0.34 * (r ** 2.1)
    base = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(BG):
        base[:, :, i] = c * v
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


BGIMG = None


def new_frame():
    global BGIMG
    if BGIMG is None:
        BGIMG = make_bg()
    return BGIMG.copy()


# ── 绘制工具 ────────────────────────────────────────────────────────
def paste_cover(canvas, im, box, alpha=1.0, zoom=1.0, cx=0.5, cy=0.5,
                radius=0, shadow=False):
    """把 im 以 cover 方式铺进 box（可放大 zoom、以 cx/cy 为取景中心）。"""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    s = max(bw / im.width, bh / im.height) * zoom
    nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
    r = im.resize((nw, nh), Image.LANCZOS)
    px = int((nw - bw) * cx)
    py = int((nh - bh) * cy)
    r = r.crop((px, py, px + int(bw), py + int(bh)))
    if radius:
        m = Image.new("L", r.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, r.width - 1, r.height - 1],
                                            radius=radius, fill=255)
        r = r.convert("RGBA")
        r.putalpha(m)
        canvas.paste(r, (int(x0), int(y0)), r)
    elif alpha >= 0.999:
        canvas.paste(r, (int(x0), int(y0)))
    else:
        canvas.paste(Image.blend(canvas.crop((int(x0), int(y0), int(x0) + r.width,
                                              int(y0) + r.height)).convert("RGB"),
                                 r, alpha), (int(x0), int(y0)))


def paste_fit(canvas, im, box, alpha=1.0, zoom=1.0):
    """contain：整张塞进 box，居中，不裁切。宽扁的特写（数字条、冠字号）必须用它，
    用 cover 会把两端切掉 —— 「100,000,000」被切成「00,000,000」就是这么来的。"""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    s = min(bw / im.width, bh / im.height) * zoom
    nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
    r = im.resize((nw, nh), Image.LANCZOS)
    px, py = int(x0 + (bw - nw) / 2), int(y0 + (bh - nh) / 2)
    if alpha >= 0.999:
        canvas.paste(r, (px, py))
    else:
        reg = canvas.crop((px, py, px + nw, py + nh)).convert("RGB")
        canvas.paste(Image.blend(reg, r, alpha), (px, py))
    return (px, py, px + nw, py + nh)


def text(canvas, x, y, s, f, color=INK, alpha=1.0, track=0.0, anchor="la",
         align_center=False):
    """带字距的文字。track 单位 px。"""
    if alpha <= 0.01 or not s:
        return 0
    d = ImageDraw.Draw(canvas)
    col = tuple(int(c * alpha + b * (1 - alpha)) for c, b in zip(color, BG))
    if abs(track) < 0.01 and not align_center:
        d.text((x, y), s, font=f, fill=col, anchor=anchor)
        return d.textlength(s, font=f)
    widths = [d.textlength(ch, font=f) for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    cx = x - total / 2 if align_center else x
    for ch, cw in zip(s, widths):
        d.text((cx, y), ch, font=f, fill=col, anchor=anchor)
        cx += cw + track
    return total


def rule(canvas, x0, x1, y, alpha=1.0, color=GOLD, width=1):
    if alpha <= 0.01:
        return
    d = ImageDraw.Draw(canvas)
    col = tuple(int(c * alpha + b * (1 - alpha)) for c, b in zip(color, BG))
    d.rectangle([x0, y, x1, y + width - 1], fill=col)


def label(canvas, x, y, cn, en, f_cn, f_en, alpha=1.0, gap=14):
    text(canvas, x, y, cn, f_cn, INK, alpha)
    text(canvas, x, y + f_cn.size + gap, en, f_en, GOLD, alpha * 0.85, track=2.2)


def caption(canvas, x, y, s, f, alpha=1.0, maxw=None):
    text(canvas, x, y, s, f, DIM, alpha)


def chapter(canvas, no, cn, en, a):
    """章节片头：细金线 + 编号 + 标题。"""
    f_no = font(F_EN, 68)
    f_cn = font(F_CN, 46)
    f_en = font(F_EN, 19)
    hx = W * 0.16
    rule(canvas, hx, hx + 96, H * 0.44, a, GOLD, 2)
    text(canvas, hx + 128, H * 0.44 - 46, no, f_no, GOLD, a)
    text(canvas, hx + 128, H * 0.44 + 44, cn, f_cn, INK, a, track=6)
    text(canvas, hx + 130, H * 0.44 + 44 + 62, en, f_en, DIM, a, track=3.4)


# ── 素材 ────────────────────────────────────────────────────────────
def load(name):
    return Image.open(os.path.join(REEL, name)).convert("RGB")


A = {}


def assets():
    if A:
        return A
    for f in os.listdir(REEL):
        A[f.rsplit(".", 1)[0]] = load(f)
    return A


TAGS = ["010000000", "020000000", "050000000",
        "100000000", "200000000", "500000000"]
SIZES = [("10,000,000", "132.0 × 61.6", "引航"),
         ("20,000,000", "142.0 × 66.3", "夜航"),
         ("50,000,000", "148.0 × 69.1", "港市"),
         ("100,000,000", "150.0 × 70.0", "守望"),
         ("200,000,000", "158.0 × 73.7", "星图"),
         ("500,000,000", "176.0 × 82.1", "远洋")]

# ── 镜头 ────────────────────────────────────────────────────────────
NOTE_BOX = (250, 235, 1670, 1050)


def sc_title(p):
    c = new_frame()
    a = ease(p * 1.5)
    w = int(W * 0.34 * ease_out(p * 1.6))
    rule(c, W / 2 - w / 2, W / 2 + w / 2, H * 0.40, a, GOLD, 2)
    text(c, W / 2, H * 0.44, "DeepSeek Token银行", font(F_CN, 62), INK,
         ease(seg(p, .18, .62)), track=10, align_center=True)
    text(c, W / 2, H * 0.55, "DEEPSEEK TOKEN BANK", font(F_EN, 21), GOLD,
         ease(seg(p, .30, .74)), track=7.0, align_center=True)
    text(c, W / 2, H * 0.66, "鲸 元 券 · 设 计 方 案", font(F_CN, 30), DIM,
         ease(seg(p, .42, .88)), track=4, align_center=True)
    return c


def sc_front(p):
    c = new_frame()
    im = assets()["note_front_100000000"]
    # 从虚到实，同时极缓推近
    z = 1.06 - 0.06 * ease_io(p)
    box = NOTE_BOX
    paste_cover(c, im, box, 1.0, z)
    # 顶部说明
    a = ease(seg(p, .05, .35))
    text(c, 250, 92, "正面 · OBVERSE", font(F_EN, 20), GOLD, a, track=5)
    text(c, 250, 126, "100,000,000 TOKEN　基准档", font(F_CN, 27), INK, a, track=3)
    text(c, 250, 168, "", font(F_CN, 20), DIM, 0)
    rule(c, 250, 250 + 560 * ease(seg(p, .2, .8)), 214, a, GOLD, 1)
    return c


def sc_portrait(p):
    c = new_frame()
    im = assets()["hi_portrait"]
    box = (860, 200, 1720, 1000)
    paste_cover(c, im, box, 1.0, 1.02 + 0.05 * ease_io(p), 0.5 - 0.10 * ease_io(p), 0.45)
    a = ease(seg(p, .04, .30))
    label(c, 190, 400, "主景人物", "PORTRAIT", font(F_CNB, 40), font(F_EN, 18), a)
    rule(c, 190, 190 + 70, 500, a, GOLD, 2)
    caption(c, 190, 536, "鲸灵 · 灯", font(F_CN, 26), ease(seg(p, .2, .5)))
    caption(c, 190, 578, "THE WHALE SPIRIT · DENG", font(F_EN, 15),
            ease(seg(p, .24, .54)))
    rule(c, 190, 420, 630, ease(seg(p, .3, .6)), DIM, 1)
    for i, (t1, t2) in enumerate([("雕刻线稿 · 820 条变宽排线", .42),
                                  ("明暗由原画亮度驱动", .52),
                                  ("矢量输出 · 无损缩放", .62)]):
        caption(c, 190, 668 + i * 42, t1, font(F_CN, 19), ease(seg(p, t2, t2 + .26)))
    return c


def sc_ovi(p):
    c = new_frame()
    im = assets()["hi_ovi"]
    box = (200, 340, 1720, 620)
    paste_fit(c, im, box, 1.0, 1.0 + 0.03 * ease_io(p))
    a = ease(seg(p, .04, .30))
    label(c, 200, 160, "光变油墨", "OPTICALLY VARIABLE INK", font(F_CNB, 40),
          font(F_EN, 18), a)
    rule(c, 200, 270, 262, a, GOLD, 2)
    # 视角模拟：一条扫过的高光带
    sx = 200 + (1720 - 200 + 300) * ease_io(p)
    band = Image.new("L", (int(box[2] - box[0]), int(box[3] - box[1])), 0)
    ImageDraw.Draw(band).polygon(
        [(sx - 260, 0), (sx - 60, 0), (sx - 200, band.height), (sx - 400, band.height)],
        fill=110)
    band = band.filter(ImageFilter.GaussianBlur(48))
    reg = c.crop((int(box[0]), int(box[1]), int(box[2]), int(box[3]))).convert("RGB")
    reg = Image.composite(Image.new("RGB", reg.size, (255, 255, 255)), reg,
                          band.point(lambda v: int(v * 0.42)))
    c.paste(reg, (int(box[0]), int(box[1])))
    caption(c, 200, 700, "色相随观察角度连续变化", font(F_CN, 21),
            ease(seg(p, .28, .58)))
    caption(c, 200, 742, "绿 → 蓝绿 → 靛蓝 → 紫 → 古铜", font(F_CN, 21),
            ease(seg(p, .40, .70)))
    return c


def sc_emblem(p):
    c = new_frame()
    im = assets()["hi_emblem"]
    box = (1010, 230, 1740, 960)
    paste_cover(c, im, box, 1.0, 1.10 - 0.07 * ease_io(p))
    a = ease(seg(p, .04, .30))
    label(c, 190, 340, "行徽", "BANK EMBLEM", font(F_CNB, 40), font(F_EN, 18), a)
    rule(c, 190, 260, 442, a, GOLD, 2)
    caption(c, 190, 486, "官方 DeepSeek 鲸鱼矢量", font(F_CN, 23),
            ease(seg(p, .2, .5)))
    caption(c, 190, 528, "原样输出 · 未作任何改动", font(F_CN, 23),
            ease(seg(p, .32, .62)))
    caption(c, 190, 596, "外环 Ø248 · 金环 Ø230 · 内环 Ø184", font(F_EN, 17),
            ease(seg(p, .44, .74)), )
    return c


def sc_marks(p):
    """对印 / 盲文 / 冠字号 三联。三张特写长宽比差很大（1:1、1:1、8.8:1），
    所以一律 contain 摆放，绝不裁切。"""
    c = new_frame()
    a0 = ease(seg(p, .02, .28))
    text(c, 200, 160, "对印 · 盲文 · 冠字号", font(F_CNB, 40), INK, a0, track=4)
    rule(c, 200, 270, 232, a0, GOLD, 2)
    # 左：对印（1:1）　中：盲文（1:1）　右：冠字号（宽扁，跨两列宽）
    items = [("hi_regist_f", (200, 300, 600, 700), "对印标记", "REGISTRATION"),
             ("hi_braille", (660, 300, 1060, 700), "盲文单元", "BRAILLE"),
             ("hi_serial", (1120, 400, 1760, 520), "冠字号", "SERIAL NUMBER")]
    for i, (key, box, cn, en) in enumerate(items):
        a = ease(seg(p, .05 + i * .10, .32 + i * .10))
        paste_fit(c, assets()[key], box, a)
        ux = box[0] if i < 2 else 1120
        uy = 760 if i < 2 else 620
        rule(c, ux, ux + 62, uy, a, GOLD, 2)
        text(c, ux, uy + 28, cn, font(F_CNB, 30), INK, a, track=3)
        text(c, ux, uy + 74, en, font(F_EN, 15), GOLD, a * .85, track=2.6)
    caption(c, 200, 960, "三项均按档位编码：对印上下半分、盲文布莱叶数字、冠字号 WY{面额}8842A",
            font(F_CN, 19), ease(seg(p, .5, .8)))
    return c


def sc_back(p):
    c = new_frame()
    im = assets()["note_back_100000000"]
    paste_cover(c, im, NOTE_BOX, 1.0, 1.06 - 0.06 * ease_io(p))
    a = ease(seg(p, .05, .35))
    text(c, 250, 92, "反面 · REVERSE", font(F_EN, 20), GOLD, a, track=5)
    text(c, 250, 126, "100,000,000 TOKEN　基准档", font(F_CN, 27), INK, a, track=3)
    rule(c, 250, 250 + 560 * ease(seg(p, .2, .8)), 214, a, GOLD, 1)
    return c


def sc_lighthouse(p):
    c = new_frame()
    im = assets()["hi_lighthouse"]
    box = (900, 150, 1740, 1010)
    paste_cover(c, im, box, 1.0, 1.06 + 0.06 * ease_io(p))
    a = ease(seg(p, .04, .30))
    label(c, 190, 380, "反向主景", "REVERSE MOTIF", font(F_CNB, 40), font(F_EN, 18), a)
    rule(c, 190, 260, 482, a, GOLD, 2)
    caption(c, 190, 526, "六档背面主景各不相同", font(F_CN, 23), ease(seg(p, .2, .5)))
    for i, s in enumerate(["10,000,000　灯浮标", "20,000,000　罗盘玫瑰",
                           "50,000,000　门吊货箱", "100,000,000　灯塔",
                           "200,000,000　北斗七星", "500,000,000　罗经花"]):
        caption(c, 190, 596 + i * 40, s, font(F_CN, 19),
                ease(seg(p, .3 + i * .05, .56 + i * .05)))
    return c


def sc_datemark(p):
    c = new_frame()
    im = assets()["hi_datemark"]
    box = (200, 400, 1720, 700)
    paste_fit(c, im, box, 1.0, 1.0 + 0.02 * ease_io(p))
    a = ease(seg(p, .04, .30))
    label(c, 200, 210, "年版与厂标", "YEAR & MARK", font(F_CNB, 40), font(F_EN, 18), a)
    rule(c, 200, 270, 312, a, GOLD, 2)
    caption(c, 200, 780, "反面右下角，贴在角位对印左侧、同一水平带上",
            font(F_CN, 22), ease(seg(p, .24, .56)))
    caption(c, 200, 826, "六档同点，不随面额漂移", font(F_CN, 22),
            ease(seg(p, .38, .70)))
    return c


def sc_series(p):
    c = new_frame()
    a0 = ease(seg(p, .02, .24))
    text(c, 150, 84, "全 系 列", font(F_CNB, 40), INK, a0, track=8)
    rule(c, 150, 240, 156, a0, GOLD, 2)
    text(c, 150, 176, "FULL DENOMINATION SERIES", font(F_EN, 16), GOLD, a0 * .85, track=4)
    # 六档等高，按真实相对长度并排
    base_h = 128
    total = sum(1 for _ in TAGS)
    ws = []
    for i, (denom, sz, th) in enumerate(SIZES):
        L = float(sz.split(" × ")[0])
        ws.append(base_h * (L / 70.0))
    gap = 26
    tw = sum(ws) + gap * 5
    x = (W - tw) / 2
    for i, (denom, sz, th) in enumerate(SIZES):
        t0 = .06 + i * .075
        a = ease(seg(p, t0, t0 + .22))
        dy = 40 * (1 - a)
        im = assets()["note_front_" + TAGS[i]]
        box = (x, 300 + dy, x + ws[i], 300 + dy + base_h)
        paste_cover(c, im, box, a)
        text(c, x, 300 + base_h + 34, denom, font(F_EN, 15), INK, a, track=1.2)
        text(c, x, 300 + base_h + 58, th, font(F_CN, 15), DIM, a)
        x += ws[i] + gap
    a1 = ease(seg(p, .62, .84))
    rule(c, (W - tw) / 2, (W + tw) / 2, 560, a1, GOLD, 1)
    text(c, W / 2, 600, "六档共用同一版式与同一人物构图", font(F_CN, 24), INK,
         a1, track=3, align_center=True)
    text(c, W / 2, 648, "只换面额文字与专色；券长按阶梯，券高按 150 : 70 等比",
         font(F_CN, 20), DIM, a1, track=1.5, align_center=True)
    return c


def sc_spec(p):
    c = new_frame()
    a0 = ease(seg(p, .02, .24))
    text(c, 150, 84, "规 格", font(F_CNB, 40), INK, a0, track=8)
    rule(c, 150, 240, 156, a0, GOLD, 2)
    text(c, 150, 176, "SPECIFICATIONS", font(F_EN, 16), GOLD, a0 * .85, track=4)
    hdr = [("面额 TOKEN", 150), ("券幅 mm", 640), ("主题", 980), ("专色", 1240)]
    for i, (s, x) in enumerate(hdr):
        text(c, x, 250, s, font(F_CN, 18), GOLD, ease(seg(p, .06, .26)), track=2)
    rule(c, 150, 1770, 288, ease(seg(p, .08, .3)), DIM, 1)
    for i, ((denom, sz, th), col) in enumerate(zip(SIZES, [
            "#24506B 深青蓝", "#1F5A52 深海绿", "#4A3A6E 紫罗兰",
            "#1B2657 藏青", "#8A5A2B 赭金", "#2E2717 玄金"])):
        t0 = .14 + i * .07
        a = ease(seg(p, t0, t0 + .2))
        y = 320 + i * 68
        text(c, 150, y, denom, font(F_EN, 22), INK, a, track=1.5)
        text(c, 640, y, sz, font(F_EN, 22), DIM, a, track=1.2)
        text(c, 980, y, th, font(F_CN, 22), INK, a, track=2)
        text(c, 1240, y, col, font(F_EN, 17), DIM, a, track=1.2)
        rule(c, 150, 1770, y + 40, a * .22, DIM, 1)
    a1 = ease(seg(p, .60, .84))
    text(c, 150, 800, "SVG 12 份 · 纯矢量自包含", font(F_CN, 24), INK, a1, track=2)
    text(c, 150, 848, "PNG 12 份 · 7560 × 3528 px · 1091 ~ 1455 DPI", font(F_EN, 20),
         DIM, a1, track=1.2)
    text(c, 150, 900, "长宽比六档均为 150 : 70", font(F_CN, 20), DIM, a1, track=2)
    return c


def sc_outro(p):
    c = new_frame()
    a = ease(seg(p, .05, .40))
    w = int(W * 0.30 * ease_out(p * 1.5))
    rule(c, W / 2 - w / 2, W / 2 + w / 2, H * 0.40, a, GOLD, 2)
    text(c, W / 2, H * 0.44, "DeepSeek Token银行", font(F_CN, 54), INK,
         ease(seg(p, .12, .50)), track=9, align_center=True)
    text(c, W / 2, H * 0.545, "DEEPSEEK TOKEN BANK", font(F_EN, 19), GOLD,
         ease(seg(p, .24, .60)), track=6.4, align_center=True)
    text(c, W / 2, H * 0.64, "鲸元券 · 全档图稿", font(F_CN, 26), DIM,
         ease(seg(p, .38, .78)), track=5, align_center=True)
    text(c, W / 2, H * 0.80, "本券为个人虚拟设定 · 娱乐用途 · 不构成发行或兑付承诺",
         font(F_CN, 17), (90, 96, 108), ease(seg(p, .56, .92)), track=1.5,
         align_center=True)
    text(c, W / 2, H * 0.845, "DeepSeek 标识为 DeepSeek 商标，本项目与 DeepSeek 官方无关联",
         font(F_CN, 17), (90, 96, 108), ease(seg(p, .66, .98)), track=1.5,
         align_center=True)
    return c


# (时长秒, 渲染函数)
SCENES = [
    (7.0, sc_title),
    (12.0, sc_front),
    (13.0, sc_portrait),
    (10.0, sc_ovi),
    (9.0, sc_emblem),
    (10.0, sc_marks),
    (11.0, sc_back),
    (12.0, sc_lighthouse),
    (9.0, sc_datemark),
    (12.0, sc_series),
    (12.0, sc_spec),
    (8.0, sc_outro),
]
XFADE = 0.7
TOTAL = sum(d for d, _ in SCENES)


def time_table():
    out, t = [], 0.0
    for d, fn in SCENES:
        out.append((t, t + d, fn))
        t += d
    return out


TT = time_table()


def render(t):
    for i, (t0, t1, fn) in enumerate(TT):
        if t0 <= t < t1 or (i == len(TT) - 1 and t >= t1):
            base = fn((t - t0) / (t1 - t0))
            if t1 - t < XFADE and i + 1 < len(TT):
                nxt = TT[i + 1][2](0.0)
                return Image.blend(nxt, base, ease((t1 - t) / XFADE))
            if t - t0 < XFADE and i > 0:
                prv = TT[i - 1][2](1.0)
                return Image.blend(prv, base, ease((t - t0) / XFADE))
            return base
    return new_frame()


def main():
    assets()
    if "--probe" in sys.argv:
        n = int(sys.argv[sys.argv.index("--probe") + 1])
        d = os.path.join(ROOT, "build", "reel_probe")
        os.makedirs(d, exist_ok=True)
        idx = [int(round(i * (TOTAL - 0.05) / (n - 1))) for i in range(n)]
        for j, s in enumerate(idx):
            render(float(s)).save(os.path.join(d, "p%02d_%05.1fs.jpg" % (j, s)),
                                  "JPEG", quality=90)
        print("probe %d frames, total %.1f s @ %d fps = %d frames"
              % (n, TOTAL, FPS, int(TOTAL * FPS)))
        return
    os.makedirs(FRAMES, exist_ok=True)
    N = int(TOTAL * FPS)
    for i in range(N):
        # 存 JPEG 而不是 PNG：3000 帧 1080p 的 PNG 要 4.5 GB，JPEG q=96 只要 ~0.9 GB，
        # 而这条片子最终要再走一遍 H.264 编码，源帧再无损也没有意义。
        render(i / FPS).save(os.path.join(FRAMES, "f%05d.jpg" % i),
                             "JPEG", quality=96, subsampling=0)
        if i % 200 == 0:
            print("frame %d / %d" % (i, N), flush=True)
    print("done: %d frames -> %s" % (N, FRAMES))


if __name__ == "__main__":
    main()
