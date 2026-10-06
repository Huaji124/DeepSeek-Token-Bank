# -*- coding: utf-8 -*-
"""鲸徽定位校准：确认负形眼与喷气线的位置（对比官方原图）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whale_mark as M

ROOT = r"E:\Agent项目\鲸元券"
NAVY, ROOTBLUE = "#1B2657", "#4D6BFE"


def official_raw(cx, cy, size, color):
    """官方原图（保留原有眼部细节），用于对照。"""
    s = size / 24.0
    return (f'<g transform="translate({cx - size / 2} {cy - size / 2}) scale({s})">'
            f'<path d="{M.WHALE_D}" fill="{color}" fill-rule="evenodd"/></g>')


rows = []
y = 200
rows.append(f'<text x="40" y="60" font-family="\'Microsoft YaHei\',sans-serif" font-size="26" '
            f'fill="#2A3A7A">官方原图（保留原眼）</text>')
rows.append(official_raw(240, 200, 300, ROOTBLUE))
rows.append(official_raw(600, 200, 300, NAVY))
rows.append(f'<text x="40" y="400" font-family="\'Microsoft YaHei\',sans-serif" font-size="26" '
            f'fill="#2A3A7A">本模块改编稿：负形眼 + 后喷气（当前标定）</text>')
rows.append(M.whale(240, 540, 300, ROOTBLUE))
rows.append(M.whale(600, 540, 300, NAVY))
rows.append(f'<text x="40" y="740" font-family="\'Microsoft YaHei\',sans-serif" font-size="26" '
            f'fill="#2A3A7A">缩微测试（票面实际印刷尺寸）</text>')
for i, sz in enumerate([96, 64, 44, 30, 20, 14, 10]):
    rows.append(M.whale(140 + i * 190, 850, sz, NAVY))

W, H = 1200, 960
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
       f'height="100%"><rect width="{W}" height="{H}" fill="#F5EFDE"/>{"".join(rows)}</svg>')
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#EEF0F4;overflow:hidden}}
#f{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}}
.n{{width:96vw;height:calc(96vw*{H}/{W});max-height:96vh;max-width:calc(96vh*{W}/{H});}}
</style></head><body><div id="f"><div class="n">{svg}</div></div></body></html>'''
p = os.path.join(ROOT, "build", "whale-cal.html")
open(p, "w", encoding="utf-8").write(html)
print("written:", p)
