# -*- coding: utf-8 -*-
"""全系列面额总表：**只排版，不画票**。

票面本身一律由 `render_mockup.py` / `render_reverse.py` 出（见 build/front-*.html、
back-*.html）。这里只做一件事：把已渲染好的正/反面图裁出票面本体，按各档券长
等比缩放，排成总表。

**为什么非要这样**：早先 `render_all_denoms.py` 是"按同一套规则把版式重画一遍"，
结果机构名字号、鲸徽圆心、内外框距离、法偿行距处处与定稿漂移 —— 拿它当总表就是
自相矛盾。总表必须由**同一份成品图**缩出来。

缩放口径：券高按 100,000,000 券的 150 : 70 反算（`Hpx = W / (150/70)`），
各档之间只差一个等比系数，版式不重排。
"""
import base64
import io
import os
import sys

from PIL import Image

ROOT = r"E:\Agent项目\鲸元券"
BUILD = os.path.join(ROOT, "build")
sys.path.insert(0, BUILD)
import palette as PAL

PX_MM = 12.6
AR = 150.0 / 70.0
BG, INK = "#EEF0F4", "#1B2657"
LG, GAP, ROW_GAP = 320, 78, 104
CANVAS_W = 2620


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def crop_note(im):
    """1900×900 展示稿 → 只留票面本体（去掉页底色与投影）。"""
    sc, ox, oy = 0.9386, 63.0, 36.0      # .n 容器在 1900×900 视口下的缩放与居中偏移
    x0 = int(ox + 30 * sc) - 1
    y0 = int(oy + 30 * sc) - 1
    x1 = int(ox + 1860 * sc) + 1
    y1 = int(oy + 852 * sc) + 1
    return im.crop((max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1)))


def main():
    rows = []
    for i, (denom, L, spot, cname, theme, cn, en) in enumerate(PAL.SERIES):
        W = round(L * PX_MM)
        Hpx = round(W / AR)
        # 基准档（TIER=3）的两个渲染器把成品写成 mockup-100.png / reverse-100.png
        # （保留定稿文件名），其余档写 front-{i}.png / back-{i}.png。
        # 这里必须按同一规则取图 —— 否则基准档会静默用到上一次的陈旧文件。
        if i == 3:
            fn, bn = "mockup-100.png", "reverse-100.png"
        else:
            fn, bn = "front-%d.png" % i, "back-%d.png" % i
        f = crop_note(Image.open(os.path.join(BUILD, fn)).convert("RGB"))
        b = crop_note(Image.open(os.path.join(BUILD, bn)).convert("RGB"))
        rows.append((i, denom, L, round(Hpx / PX_MM, 1), spot, cname, theme, cn,
                     f.resize((W, Hpx), Image.LANCZOS), b.resize((W, Hpx), Image.LANCZOS)))

    body, y = [], 118
    body.append('<text x="44" y="52" font-family="Microsoft YaHei" font-size="30" '
                'font-weight="700" fill="%s">鲸元券 · 主币全系列（6 档）</text>' % INK)
    body.append('<text x="44" y="86" font-family="Microsoft YaHei" font-size="15" fill="%s" '
                'opacity="0.82">全档共用同一版式与同一人物构图，只换面额文字与专色；'
                '券长按规范书阶梯，券高按 150 : 70 等比 —— 相邻档只差一个缩放系数</text>' % INK)
    for (i, denom, L, Hmm, spot, cname, theme, cn, f, b) in rows:
        W, Hpx = f.width, f.height
        x = CANVAS_W - 40 - W
        body.append('<text x="44" y="%d" font-family="Microsoft YaHei" font-size="26" '
                    'font-weight="700" fill="%s">%s</text>' % (y + 30, INK, denom))
        body.append('<text x="44" y="%d" font-family="Microsoft YaHei" font-size="16" '
                    'fill="%s" opacity="0.85">%.1f × %.1f mm　%s【%s】</text>'
                    % (y + 56, INK, L, Hmm, spot, cname))
        body.append('<text x="44" y="%d" font-family="Microsoft YaHei" font-size="15" '
                    'fill="%s" opacity="0.75">%s · %s</text>' % (y + 78, INK, cn, theme))
        body.append('<text x="44" y="%d" font-family="Microsoft YaHei" font-size="13" '
                    'fill="%s" opacity="0.58">档位 %d · 凸点 %d · 缺口 %d · 盲文「%s」</text>'
                    % (y + 100, INK, i + 1, i + 1, i + 1, denom.replace(",", "")))
        for tag, im in (("正面 FRONT", f), ("背面 BACK", b)):
            body.append('<text x="%d" y="%d" font-family="Microsoft YaHei" font-size="12" '
                        'fill="%s" opacity="0.5">%s</text>' % (x + 2, y - 8, INK, tag))
            body.append('<image xlink:href="%s" x="%d" y="%d" width="%d" height="%d"/>'
                        % (b64(im), x, y, W, Hpx))
            y += Hpx + GAP
        y += ROW_GAP - GAP
    total_h = y + 20
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
           'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 %d %d" '
           'width="%d" height="%d">%s</svg>'
           % (CANVAS_W, total_h, CANVAS_W, total_h, "".join(body)))
    p = os.path.join(BUILD, "series-all.html")
    open(p, "w", encoding="utf-8").write(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        'html,body{margin:0;padding:0;background:%s}svg{display:block}'
        '</style></head><body>%s</body></html>' % (BG, svg))
    print("written:", p, "canvas", CANVAS_W, total_h)


if __name__ == "__main__":
    main()
