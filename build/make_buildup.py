# -*- coding: utf-8 -*-
"""逐层搭建动画：**从空白界面开始，一件一件加上票面要素，每加一件用指示线标出它是什么。**

素材来自 `build\layers_png\<sheet>\<layer>.png`（每个图层一张全舞台透明 PNG，
由 `make_layers_png.py` 渲染）。所有帧都在 PIL 里合成 —— 指示线、标签、缓动全可控。

输出：build\_buildup\f%04d.png（1920×1080）
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = r"E:\Agent项目\鲸元券"
# 用哪一面：`$env:WY_SHEET = "back_100000000.svg"` 出反面
SHEET = os.environ.get("WY_SHEET", "front_100000000")
SRC = os.path.join(ROOT, "build", "layers_png", SHEET.replace(".svg", ""))

# 输出倍率：`$env:WY_SCALE = "2"` 出 4K（3840×2160）。
# 图层 PNG 本来就是 DSF=2 渲染的 3840×2160，出 4K 时是**原尺寸直接用**，没有放大损失。
S = int(os.environ.get("WY_SCALE", "1"))
_tag = ("" if SHEET.startswith("front") else "_back") + ("" if S == 1 else "4k")
OUT = os.path.join(ROOT, "build", "_buildup" + _tag)

W, H = 1920 * S, 1080 * S
FPS = 24
BG = (13, 16, 20)
INK = (242, 239, 232)
GOLD = (201, 162, 39)
DIM = (122, 130, 144)

# 票面在舞台上占的矩形（1× 基准：(180,176) 起、1560×728）
NOTE_X, NOTE_Y, NOTE_W, NOTE_H = 180 * S, 176 * S, 1560 * S, 728 * S

# 步骤：(显示名, [图层], 带引线的小标题, 副标题, 引线锚点(相对票面 0~1), 标签锚点(舞台 px), 对齐)
STEPS_FRONT = [
    ("paper",     ["paper"],            "纸基", "专色派生的浅色渐变 · 满版", (0.07, 0.07), (58, 74), "lt"),
    ("guilloche", ["guilloche"],        "防伪底纹", "同心花球 · 波浪线 · 斜线网", (0.20, 0.34), (58, 530), "lt"),
    ("frame",     ["frame", "border"],  "内框与外框", "直角双线 · 无圆角", (0.50, 0.012), (960, 74), "ct"),
    ("portrait",  ["portrait"],         "主景人物 · DeepSeek拟人", "雕刻线稿 · 单一姿态全档共用", (0.16, 0.46), (58, 1002), "lt"),
    ("denom",     ["denom"],            "面额数字", "光变油墨 OVI", (0.80, 0.30), (1862, 74), "rt"),
    ("type",      ["type"],             "券面文字", "机构名 · 中英全称 · 法偿声明 · 冠字号", (0.90, 0.90), (1862, 1002), "rt"),
    ("emblem",    ["emblem"],           "官方鲸徽", "DeepSeek 标识原样 · 光变油墨", (0.65, 0.62), (1862, 530), "rt"),
    ("marks",     ["marks"],            "安全与无障碍要素", "对印 · 盲文 · 开窗安全线 · 潜像", (0.045, 0.86), (960, 1002), "ct"),
]

# 反面：没有人物、没有开窗安全线与潜像，主景改为灯塔，并多出「年版与厂标」。
# 锚点由各图层的实测包围盒反算（`make_layers_png.py` 出图后量 1× 中心）。
STEPS_BACK = [
    ("paper",     ["paper"],            "纸基", "专色派生的浅色渐变 · 满版", (0.07, 0.07), (58, 74), "lt"),
    ("guilloche", ["guilloche"],        "防伪底纹", "同心花球 · 波浪线 · 斜线网", (0.20, 0.34), (58, 530), "lt"),
    ("frame",     ["frame", "border"],  "内框与外框", "直角双线 · 无圆角", (0.50, 0.012), (960, 74), "ct"),
    ("motif",     ["motif"],            "背面主景", "灯塔 · 六档各绘一景", (0.50, 0.63), (960, 1002), "ct"),
    ("denom",     ["denom"],            "面额数字", "光变油墨 OVI", (0.213, 0.323), (58, 1002), "lt"),
    ("type",      ["type"],             "券面文字", "机构名 · 中英全称 · 法偿声明 · 冠字号 · 年版厂标", (0.85, 0.46), (1862, 74), "rt"),
    ("emblem",    ["emblem"],           "官方鲸徽", "DeepSeek 标识原样 · 光变油墨", (0.83, 0.40), (1862, 530), "rt"),
    ("marks",     ["marks"],            "安全与无障碍要素", "对印 · 盲文块 · 开窗安全线", (0.93, 0.87), (1862, 1002), "rt"),
]

STEPS = STEPS_BACK if SHEET.startswith("back") else STEPS_FRONT
STEP_DUR = 3.6          # 每步秒数
FADE = 0.55             # 图层淡入时长
LINE_DRAW = 0.40        # 指示线画出的时长
CALLOUT_OUT = 0.50      # 指示线淡出时长
TAIL = 3.4              # 全部加完之后停留


def font(name, size):
    p = {"cn": r"C:\Windows\Fonts\msyh.ttc", "cnb": r"C:\Windows\Fonts\msyhbd.ttc",
         "en": r"C:\Windows\Fonts\georgia.ttf", "enb": r"C:\Windows\Fonts\georgiab.ttf"}[name]
    return ImageFont.truetype(p, size * S)


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


_cache = {}


def layer_img(name):
    if name not in _cache:
        im = Image.open(os.path.join(SRC, name + ".png")).convert("RGBA")
        _cache[name] = im.resize((W, H), Image.LANCZOS)
    return _cache[name]


def make_bg():
    if "bg" in _cache:
        return _cache["bg"]
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(0, 260 * S, 2 * S):
        a = int(30 * (1 - i / (260.0 * S)))
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(28, 33, 42, a))
    _cache["bg"] = im
    return im


def note_xy(rel):
    """相对票面坐标(0~1) → 舞台像素。"""
    return (NOTE_X + rel[0] * NOTE_W, NOTE_Y + rel[1] * NOTE_H)


def render(t):
    bg = make_bg().copy()
    total = len(STEPS) * STEP_DUR
    t = min(t, total + TAIL)
    # 1) 按时间叠加图层
    for i, (key, lns, _t1, _t2, _a, _l, _al) in enumerate(STEPS):
        start = i * STEP_DUR
        if t < start:
            break
        a = ease_out((t - start) / FADE)
        # 轻微上浮进场
        dy = int(14 * S * (1 - a))
        for ln in lns:
            src = layer_img(ln)
            if a < 0.995:
                src = src.copy()
                src.putalpha(src.split()[3].point(lambda v, a=a: int(v * a)))
            bg.paste(src, (0, dy), src)
    # 2) 当前步的指示线
    i = int(min(t, total - 0.001) // STEP_DUR)
    if t < total:
        key, lns, t1, t2, anchor, lab, al = STEPS[i]
        s = i * STEP_DUR
        u = t - s
        a_in = ease_out(u / LINE_DRAW) if u < LINE_DRAW else 1.0
        a_out = 1.0 - ease_io((u - (STEP_DUR - CALLOUT_OUT)) / CALLOUT_OUT) \
            if u > STEP_DUR - CALLOUT_OUT else 1.0
        a = max(0.0, min(1.0, min(a_in, a_out)))
        if a > 0.01:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            f1, f2 = font("cnb", 26), font("cn", 15)
            # 文字块先量宽高，引线**从文字块边缘**出发 —— 早先引线起点写死成
            # 距标签 250px 的定值，短标签就会从空白处拉出来，看着「对不齐」。
            w1, w2 = d.textlength(t1, font=f1), d.textlength(t2, font=f2)
            tw = max(w1, w2)
            LEAD = 38 * S                  # 标题基线与副标题基线的行距
            BH = LEAD + 18 * S             # 文字块高（含副标题降部）
            lx, ly = lab[0] * S, lab[1] * S
            if al == "lt":
                tx = lx
                ex0, ey0 = lx + tw + 16 * S, ly + 18 * S
            elif al == "rt":
                tx = lx - tw
                ex0, ey0 = lx - tw - 16 * S, ly + 18 * S
            else:
                tx = lx - tw / 2
                ex0 = lx
                ey0 = ly + BH + 12 * S if ly < H / 2 else ly - 12 * S
            px, py = note_xy(anchor)
            # 折线：文字块边缘 → 先走一段短头 → 斜向锚点
            if al == "ct":
                midy = ey0 + ((26 if ly < H / 2 else -26) * S)
                ex = ex0 + (px - ex0) * a
                ey = ey0 + (py - ey0) * a
                pts = [(ex0, ey0), (ex0, midy), (ex, ey)]
            else:
                sgn = 1 if al == "lt" else -1
                midx = ex0 + sgn * 26 * S
                ex = ex0 + (px - ex0) * a
                ey = ey0 + (py - ey0) * a
                pts = [(ex0, ey0), (midx, ey0), (ex, ey)]
            d.line(pts, fill=(201, 162, 39, int(210 * a)), width=2 * S, joint="curve")
            if a > 0.85:
                rr = (4.0 + 2.0 * (1 - (a - 0.85) / 0.15)) * S
                d.ellipse([px - rr, py - rr, px + rr, py + rr],
                          outline=(201, 162, 39, int(230 * a)), width=2 * S)
                d.ellipse([px - 2 * S, py - 2 * S, px + 2 * S, py + 2 * S],
                          fill=(201, 162, 39, int(230 * a)))
            d.text((tx, ly), t1, font=f1, fill=(242, 239, 232, int(255 * a)))
            d.text((tx, ly + LEAD), t2, font=f2, fill=(150, 158, 172, int(255 * a)))
            # 文字块外缘的竖标线，让标签块与引线在视觉上咬住
            if al != "ct":
                bx = tx - 10 * S if al == "lt" else tx + tw + 10 * S
                d.line([(bx, ly - 4 * S), (bx, ly + BH - 8 * S)],
                       fill=(201, 162, 39, int(150 * a)), width=2 * S)
            bg.paste(ov, (0, 0), ov)
    # 3) 进度刻度
    d = ImageDraw.Draw(bg, "RGBA")
    n = len(STEPS)
    for k in range(n):
        x = NOTE_X + k * (NOTE_W / (n - 1))
        on = t >= k * STEP_DUR
        r = (3.0 if on else 2.4) * S
        col = (201, 162, 39, 230) if on else (70, 78, 90, 160)
        d.ellipse([x - r, 946 * S - r, x + r, 946 * S + r], fill=col)
    return bg


def main():
    os.makedirs(OUT, exist_ok=True)
    N = int((len(STEPS) * STEP_DUR + TAIL) * FPS)
    # 4K 存 JPEG：772 帧 3840×2160 的 PNG 要 8 GB 以上，JPEG q=96 只要 1 GB 出头，
    # 而这条片子最后还要走一遍 H.264，源帧再无损也没有意义。1080p 仍存 PNG。
    jpg = S > 1
    for i in range(N):
        im = render(i / FPS)
        if jpg:
            im.save(os.path.join(OUT, "f%04d.jpg" % i), "JPEG", quality=96, subsampling=0)
        else:
            im.save(os.path.join(OUT, "f%04d.png" % i))
        if i % 24 == 0:
            print("frame %d / %d" % (i, N), flush=True)
    print("done: %d frames = %.1f s @ %dx%d -> %s" % (N, N / FPS, W, H, OUT))


if __name__ == "__main__":
    main()
