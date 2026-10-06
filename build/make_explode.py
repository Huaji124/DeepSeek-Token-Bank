# -*- coding: utf-8 -*-
"""路径 A 试验片：用**分层 SVG** 做 6 秒爆炸图。

做法：把分层 SVG 内嵌进一张 HTML，用 CSS 按 `data-layer` 给每层加 `transform`，
**逐帧改写 `<style>` 再截图**（不用 SMIL / CSS animation —— 无头截图的时序不可靠，
把变换直接烘进每一帧才是确定的）。

坐标系：`transform-box: view-box` + `transform-origin: 945px 441px`，
这样 CSS 里的 px 就等于 SVG 用户单位，旋转绕票面中心。

输出：build\_explode\f%03d.png（1920×1080）
"""
import os
import re
import subprocess
import sys

ROOT = r"E:\Agent项目\鲸元券"
LAYERS = os.path.join(ROOT, "dist", "layers")
OUT = os.path.join(ROOT, "build", "_explode")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

W, H, FPS, DUR = 1920, 1080, 24, 6.0
NOTE_W = 1560                       # 票面在舞台上的宽度
NOTE_H = round(NOTE_W * 882 / 1890)

# 每层：爆炸位移 (dx, dy)、旋转角、透明度、延迟。顺序即炸开次序。
PLAN = {
    "frame":     (0, 0, 0.0, 1.00, 0.00),
    "paper":     (0, 0, 0.0, 1.00, 0.05),
    "guilloche": (0, 132, -3.5, 0.30, 0.16),
    "type":      (0, -52, 0.0, 0.42, 0.26),
    "marks":     (0, 104, 2.0, 1.00, 0.34),
    "portrait":  (-64, -132, -6.0, 1.00, 0.44),
    "motif":     (0, -168, 4.5, 1.00, 0.44),
    "denom":     (34, -206, 0.0, 1.00, 0.56),
    "emblem":    (96, -248, 8.0, 1.00, 0.66),
}
ORDER = ["frame", "paper", "guilloche", "type", "marks", "portrait", "motif", "denom", "emblem"]


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def phase(t):
    """返回 0~1 的「炸开程度」。0 = 合拢，1 = 张开。"""
    if t < 2.4:
        return ease_io(t / 2.4)
    if t < 3.6:
        return 1.0
    if t < 5.4:
        u = (t - 3.6) / 1.8
        # 收拢时轻微过冲：0.6% 缩放回弹，全片唯一弹性
        return 1.0 - ease_io(u) * 1.0 + (0.006 if u > 0.92 else 0.0)
    return 0.0


def style_for(t):
    k = phase(t)
    rows = ['.st{background:#0D1014}',
            'svg.note{display:block}',
            'svg.note g[data-layer]{transform-box:view-box;transform-origin:945px 441px}']
    for name in ORDER:
        dx, dy, rot, op, delay = PLAN[name]
        d = 0.0 if k <= 0 else max(0.0, min(1.0, (k - delay) / max(0.01, 1 - delay)))
        d = ease_io(d)
        rows.append('svg.note g[data-layer="%s"]{transform:translate(%.2fpx,%.2fpx) '
                    'rotate(%.3fdeg);opacity:%.4f}'
                    % (name, dx * d, dy * d, rot * d, 1 - (1 - op) * d))
    return "\n".join(rows)


def build_html(svg_inner, t):
    # 整片缓慢推近：0.985 → 1.000，六秒走完，克制到几乎察觉不到
    z = 0.985 + 0.015 * ease_io(t / DUR)
    return ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;padding:0;background:#0D1014;overflow:hidden}'
            '.st{width:%dpx;height:%dpx;display:flex;align-items:center;justify-content:center}'
            '.st>svg{transform:scale(%.5f)}\n'
            '%s\n</style></head><body><div class="st">%s</div></body></html>'
            % (W, H, z, style_for(t), svg_inner))


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "front_100000000.svg"
    src = open(os.path.join(LAYERS, name), encoding="utf-8").read()
    inner = src[src.index(">", src.index("<svg")) + 1:src.rindex("</svg>")]
    inner = ('<svg class="note" xmlns="http://www.w3.org/2000/svg" '
             'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1890 882" '
             'width="%d" height="%d">%s</svg>' % (NOTE_W, NOTE_H, inner))
    os.makedirs(OUT, exist_ok=True)
    N = int(DUR * FPS)
    html = os.path.join(OUT, "f.html")
    png = os.path.join(OUT, "f%03d.png")
    for i in range(N):
        t = i / FPS
        open(html, "w", encoding="utf-8").write(build_html(inner, t))
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H),
                        "--virtual-time-budget=12000", "--screenshot=" + png % i,
                        "file:///" + html.replace("\\", "/")], capture_output=True)
        if i % 24 == 0:
            print("frame %d / %d" % (i, N), flush=True)
    print("done: %d frames -> %s" % (N, OUT))


if __name__ == "__main__":
    main()
