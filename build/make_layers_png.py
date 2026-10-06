# -*- coding: utf-8 -*-
"""把分层 SVG 的**每一层单独**渲染成一张透明 PNG，供 PIL 合成逐层搭建动画。

为什么不在浏览器里直接做动画：逐帧改 CSS 再截图，1920×1080 一帧要 1.5 秒；
而这里的做法是**每个图层只渲染一次**，之后所有帧都在 PIL 里拼 —— 快两个数量级，
而且指示线、标签、缓动都能用 Python 精确控制。

输出：build\layers_png\<sheet>\<layer>.png（1920×1080，透明底）
"""
import os
import re
import subprocess
import sys

ROOT = r"E:\Agent项目\鲸元券"
LAYERS = os.path.join(ROOT, "dist", "layers")
OUT = os.path.join(ROOT, "build", "layers_png")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

W, H = 1920, 1080
NOTE_W = 1560
NOTE_H = round(NOTE_W * 882 / 1890)


def layers_of(src):
    return re.findall(r'<g id="(L-[^"]+)" data-layer="([^"]+)"', src)


def build_html(inner, keep):
    """keep = 要显示的 data-layer 名；其余全部 display:none。"""
    css = "\n".join('svg.note g[data-layer="%s"]{display:none}' % n
                    for n in set(l for _, l in layers_of(inner)) if n != keep)
    return ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;padding:0;background:transparent;overflow:hidden}'
            '.st{width:%dpx;height:%dpx;display:flex;align-items:center;justify-content:center}\n'
            '%s\n</style></head><body><div class="st">%s</div></body></html>'
            % (W, H, css, inner))


def main():
    sheets = sys.argv[1:] or ["front_100000000.svg"]
    for name in sheets:
        src = open(os.path.join(LAYERS, name), encoding="utf-8").read()
        body = src[src.index(">", src.index("<svg")) + 1:src.rindex("</svg>")]
        inner = ('<svg class="note" xmlns="http://www.w3.org/2000/svg" '
                 'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1890 882" '
                 'width="%d" height="%d">%s</svg>' % (NOTE_W, NOTE_H, body))
        names, seen = [], set()
        for _, ln in layers_of(src):
            if ln not in seen:
                seen.add(ln)
                names.append(ln)
        d = os.path.join(OUT, name[:-4])
        os.makedirs(d, exist_ok=True)
        html = os.path.join(OUT, "_t.html")
        for ln in names:
            open(html, "w", encoding="utf-8").write(build_html(inner, ln))
            subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--default-background-color=00000000",
                            "--force-device-scale-factor=2",
                            "--window-size=%d,%d" % (W, H),
                            "--virtual-time-budget=12000",
                            "--screenshot=" + os.path.join(d, ln + ".png"),
                            "file:///" + html.replace("\\", "/")], capture_output=True)
            print("  %-22s %s" % (name, ln), flush=True)
        print("%s -> %d layers" % (name, len(names)))


if __name__ == "__main__":
    main()
