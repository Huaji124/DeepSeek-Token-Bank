# -*- coding: utf-8 -*-
"""鲸元券 · 面额序列总览（主币 6 档，按真实相对尺寸排列）。

用途：验收「可识别性」第一原则 —— 三米外一眼分清面额。
尺寸取自 docs/spec-book.md 3.2 表（权威值）：
  10→132.0×70.0 / 20→142.0×70.0 / 50→148.0×70.0
  100→150.0×70.0 / 200→158.0×70.0 / 500→176.0×70.0（mm，券高统一 70.0）
输出：build/series.html / series.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palette as PAL
from whale_mark import whale as WHALE_MARK

ROOT = r"E:\Agent项目\鲸元券"
GOLD, GOLD_L = PAL.GOLD, PAL.GOLD_L
BANK_CN, BANK_EN = PAL.BANK_CN, PAL.BANK_EN

# 面额 → (编号, 券长 mm, 专色, 专色名, 主题, 中文大写, 英文)
# 纸色不再固定，由各档专色按同色相浅色版派生（用户 m01275 指示）
SERIES = PAL.SERIES
H_MM = 70.0
PX_MM = 12.6


def ellipses(cx, cy, rx, ry, n, stroke, sw, op, rot=0.0):
    return "\n".join(
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*(i+1)/n:.1f}" ry="{ry*(i+1)/n:.1f}" '
        f'fill="none" stroke="{stroke}" stroke-width="{sw}" opacity="{op:.2f}" '
        f'transform="rotate({rot:g} {cx} {cy})"/>' for i in range(n))


def rosette(cx, cy, rx, ry, n, stroke, sw, op):
    return "<g>" + ellipses(cx, cy, rx, ry, n, stroke, sw, op) \
        + ellipses(cx, cy, rx, ry, n, stroke, sw, op, 30) \
        + ellipses(cx, cy, rx, ry, n, stroke, sw, op, 60) + "</g>"


def note_x0_y0(n, w_mm, color, name, theme, cn, en, dpi_scale):
    """单张券的 SVG 片段：w = 券长(px)，h = 70.0mm(px)。"""
    W = w_mm * PX_MM * dpi_scale
    H = H_MM * PX_MM * dpi_scale
    IN = 50 * dpi_scale
    paper = PAL.tint(color)                       # 纸色 = 本档专色同色相浅色版
    out = []
    out.append(f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" rx="0" fill="{paper}"/>')
    out.append(f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" rx="0" fill="none" '
               f'stroke="{PAL.tint(color, PAL.PAPER_L - 0.070)}" stroke-width="1.4"/>')
    # 底纹：双花球 + 同心椭圆
    out.append(rosette(W * 0.155, H * 0.52, W * 0.135, H * 0.40, 22, color, 0.7 * dpi_scale, 0.17))
    out.append(rosette(W * 0.845, H * 0.52, W * 0.135, H * 0.40, 22, color, 0.7 * dpi_scale, 0.17))
    out.append(ellipses(W * 0.5, H * 0.52, W * 0.42, H * 0.42, 24, color, 0.6 * dpi_scale, 0.10))
    # 内框
    out.append(f'<rect x="{IN:.1f}" y="{IN:.1f}" width="{W-2*IN:.1f}" height="{H-2*IN:.1f}" '
               f'rx="0" fill="none" stroke="{color}" stroke-width="{3*dpi_scale:.1f}" opacity="0.85"/>')
    # 左区：面额数字（第一识别要素）
    # 数字串变为 9 位 + 2 个千位分隔符（形如 100,000,000），横向占用大幅增加。
    # Georgia 粗体字宽实测：数字 ≈ 0.70 em/位，逗号 ≈ 0.25 em —— 按此反算字号，
    # 上限取「到鲸徽圆环左缘」与「到右区机构英文名左缘」两者中更紧的一个。
    w_em = 0.70 * sum(c.isdigit() for c in n) + 0.25 * n.count(",")
    w_org = 0.62 * len(BANK_EN) * (H * 0.034) + (len(BANK_EN) - 1) * (1.2 * dpi_scale)   # DEEPSEEK TOKEN BANK
    right_lim = min(W * 0.575 - H * 0.215, (W - IN - 18) - w_org)
    fs = min(H * 0.17, (right_lim - (IN + 18) - 24) / w_em)
    cn_y = H * 0.540
    ln_y = H * 0.585
    en_y = H * 0.645
    out.append(f'<text x="{IN+18:.1f}" y="{H*0.38:.1f}" font-family="Georgia,serif" '
               f'font-size="{fs:.1f}" font-weight="700" fill="{color}">{n}</text>')
    out.append(f'<text x="{IN+22:.1f}" y="{cn_y:.1f}" font-family="\'Microsoft YaHei\',sans-serif" '
               f'font-size="{H*0.088:.1f}" font-weight="700" fill="{color}" opacity="0.92" '
               f'letter-spacing="{3*dpi_scale:.1f}">{cn}</text>')
    out.append(f'<line x1="{IN+22:.1f}" y1="{ln_y:.1f}" x2="{IN+22+H*0.92:.1f}" y2="{ln_y:.1f}" '
               f'stroke="{GOLD}" stroke-width="{1.4*dpi_scale:.1f}" opacity="0.8"/>')
    out.append(f'<text x="{IN+22:.1f}" y="{en_y:.1f}" font-family="Georgia,serif" '
               f'font-size="{H*0.052:.1f}" fill="{color}" opacity="0.72" '
               f'letter-spacing="{1.6*dpi_scale:.1f}">{en}</text>')
    # 中区：鲸徽 + 主题词（圆环右移并略缩，把左区让给长数字串）
    cxm = W * 0.575
    out.append(f'<circle cx="{cxm:.1f}" cy="{H*0.50:.1f}" r="{H*0.215:.1f}" fill="none" '
               f'stroke="{color}" stroke-width="{2.2*dpi_scale:.1f}" opacity="0.5"/>')
    out.append(f'<circle cx="{cxm:.1f}" cy="{H*0.50:.1f}" r="{H*0.195:.1f}" fill="none" '
               f'stroke="{GOLD}" stroke-width="{1.2*dpi_scale:.1f}" opacity="0.62"/>')
    out.append(WHALE_MARK(cxm, H * 0.495, H * 0.27, color))
    out.append(f'<text x="{cxm:.1f}" y="{H*0.80:.1f}" text-anchor="middle" '
               f'font-family="\'Microsoft YaHei\',sans-serif" font-size="{H*0.072:.1f}" '
               f'font-weight="700" fill="{color}" letter-spacing="{4*dpi_scale:.1f}" '
               f'opacity="0.9">{theme}</text>')
    # 右区：机构名 + 竖排重复面额（机构名上移，让开鲸徽圆环的垂直范围）
    xr = W - IN - 18
    out.append(f'<text x="{xr:.1f}" y="{H*0.185:.1f}" text-anchor="end" '
               f'font-family="\'Microsoft YaHei\',sans-serif" font-size="{H*0.058:.1f}" '
               f'font-weight="700" fill="{color}" letter-spacing="{1.6*dpi_scale:.1f}">{BANK_CN}</text>')
    out.append(f'<text x="{xr:.1f}" y="{H*0.245:.1f}" text-anchor="end" font-family="Georgia,serif" '
               f'font-size="{H*0.034:.1f}" fill="{color}" opacity="0.72" '
               f'letter-spacing="{1.2*dpi_scale:.1f}">{BANK_EN}</text>')
    for k, op in enumerate((0.55, 0.38, 0.24)):
        out.append(f'<text x="{xr:.1f}" y="{H*(0.48+k*0.135):.1f}" text-anchor="end" '
                   f'font-family="Georgia,serif" font-size="{H*0.062:.1f}" font-weight="700" '
                   f'fill="{color}" opacity="{op}">{n}</text>')
    # 开窗安全线（仅主币）
    sx = W * 0.70
    out.append(f'<rect x="{sx:.1f}" y="{IN:.1f}" width="{9*dpi_scale:.1f}" '
               f'height="{H-2*IN:.1f}" fill="{GOLD_L}" opacity="0.20"/>')
    out.append(f'<rect x="{sx:.1f}" y="{IN:.1f}" width="{9*dpi_scale:.1f}" '
               f'height="{H-2*IN:.1f}" fill="none" stroke="{GOLD}" '
               f'stroke-width="{1*dpi_scale:.1f}" stroke-dasharray="{22*dpi_scale:.1f} {14*dpi_scale:.1f}"/>')
    # 下沿冠字号（面额码为完整数字串，不含千位分隔符）
    nc = n.replace(",", "")
    out.append(f'<text x="{IN+18:.1f}" y="{H*0.925:.1f}" '
               f'font-family="Consolas,\'Courier New\',monospace" font-size="{H*0.068:.1f}" '
               f'font-weight="700" fill="{color}" letter-spacing="{2.4*dpi_scale:.1f}">'
               f'WY {nc} 8842A</text>')
    return "".join(out)


DPI = 1.0
LEFT_GUTTER = 236        # 左侧留给规格标注
rows = []
y = 120.0
ROW_GAP = 34.0
LABEL_H = 44.0
total_w = 176.0 * PX_MM
for n, w_mm, color, cname, theme, cn, en in SERIES:
    wpx = w_mm * PX_MM
    hpx = H_MM * PX_MM
    x = LEFT_GUTTER + (total_w - wpx)      # 右对齐，便于目视比较长度差
    rows.append(f'<g transform="translate({x:.1f} {y:.1f})">'
                f'{note_x0_y0(n, w_mm, color, cname, theme, cn, en, DPI)}'
                f'</g>')
    rows.append(f'<text x="22" y="{y+hpx*0.44:.1f}" font-family="\'Microsoft YaHei\',sans-serif" '
                f'font-size="27" font-weight="700" fill="#1B2657">{cn}</text>')
    rows.append(f'<text x="22" y="{y+hpx*0.44+32:.1f}" font-family="Consolas,monospace" '
                f'font-size="20" fill="#2A3A7A">{w_mm:.1f} × {H_MM:.1f} mm</text>')
    rows.append(f'<text x="22" y="{y+hpx*0.44+58:.1f}" font-family="\'Microsoft YaHei\',sans-serif" '
                f'font-size="19" fill="{color}">{cname} {color}</text>')
    rows.append(f'<text x="22" y="{y+hpx*0.44+82:.1f}" font-family="\'Microsoft YaHei\',sans-serif" '
                f'font-size="19" fill="#4A4A55">主题「{theme}」</text>')
    y += hpx + ROW_GAP + LABEL_H

Y_END = y + 90
CANVAS_W = LEFT_GUTTER + total_w + 60
header = (
    f'<text x="22" y="58" font-family="\'Microsoft YaHei\',sans-serif" font-size="34" '
    f'font-weight="700" fill="#1B2657">鲸元券 · 主币面额序列（按真实相对尺寸）</text>'
    f'<text x="22" y="92" font-family="\'Microsoft YaHei\',sans-serif" font-size="20" '
    f'fill="#4A4A55">尺寸与专色取自 docs/spec-book.md 3.2 表；券高统一 70.0 mm；'
    f'右对齐以便目视比对各档券长差（10→500 依次 132.0 / 142.0 / 148.0 / 150.0 / 158.0 / 176.0 mm）</text>'
)
footer = (
    f'<text x="22" y="{Y_END-40:.1f}" font-family="\'Microsoft YaHei\',sans-serif" font-size="19" '
    f'fill="#4A4A55">三维同时分级：每档在「尺寸 / 色调（色相角）/ 主题」三个维度上同时与前后面额不同；'
    f'相邻色相差 ≥ 18°，不足者靠明度差 ΔL* ≥ 25 分离（见规范书 3.3）。</text>'
)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'viewBox="0 0 {CANVAS_W:.0f} {Y_END:.0f}" width="100%" height="100%">'
       f'<rect width="{CANVAS_W:.0f}" height="{Y_END:.0f}" fill="#EEF0F4"/>'
       f'{header}{"".join(rows)}{footer}</svg>')

html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#EEF0F4}}
body{{display:flex;justify-content:center}}
.n{{width:{CANVAS_W:.0f}px}}
</style></head><body><div class="n">{svg}</div></body></html>'''

p = os.path.join(ROOT, "build", "series.html")
open(p, "w", encoding="utf-8").write(html)
print("written:", p, len(html), "canvas", CANVAS_W, Y_END)
