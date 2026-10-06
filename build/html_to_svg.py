# -*- coding: utf-8 -*-
"""从渲染器产出的自包含 HTML 里抽出票面 SVG，写成独立可用的 .svg 文件。

渲染器（render_mockup.py / render_reverse.py）把整张票面组装成一段 <svg>
再塞进 HTML 预览页。默认走 WY_PLATE=svg，人物是**嵌套 <svg>**（矢量），
所以外层 <svg> 取出来就是一份自包含的纯矢量文件，不含任何外链。

用法：& $py build\html_to_svg.py <in.html> <out.svg>
"""
import os
import sys


def extract(html_path, svg_path):
    t = open(html_path, encoding="utf-8").read()
    i = t.index("<svg")
    j = t.rindex("</svg>") + len("</svg>")
    s = t[i:j]
    if "xmlns=" not in s[:300]:
        s = s.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    s = '<?xml version="1.0" encoding="UTF-8"?>\n' + s + "\n"
    os.makedirs(os.path.dirname(svg_path), exist_ok=True)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(s)
    # 自包含性自检：不允许出现外链
    bad = [k for k in ("http://", "https://", "file://") if k in s]
    return len(s), [b for b in bad if b != "http://www.w3.org/2000/svg"]


if __name__ == "__main__":
    n, bad = extract(sys.argv[1], sys.argv[2])
    print("%s -> %s  %d chars  ext-link:%s" %
          (os.path.basename(sys.argv[1]), os.path.basename(sys.argv[2]),
           n, ",".join(bad) if bad else "none"))
