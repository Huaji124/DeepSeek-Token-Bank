# -*- coding: utf-8 -*-
"""鲸徽（正式稿）—— 基于官方 DeepSeek 鲸鱼矢量。

矢量来源：`E:\Agent项目\AI对战游戏\assets\emblems\deepseek.svg`
（viewBox 0 0 24 24，fill-rule="evenodd"，单条 path，1985 字符）
已提取为 `E:\Agent项目\鲸元券\build\deepseek_whale_d.txt`，本模块直接读取。

⚠️ 版权与商标事实（必须让用户知情，并写进规范书）：
  DeepSeek 鲸鱼图形是 **DeepSeek 的商标/品牌标识**，其著作权与商标权均不归本项目所有。
  把它原样印在「鲸元券」票面上，等于本券宣称由 DeepSeek 发行 —— 这在真实货币语境下
  属于冒用商标。用户已明确要求使用该图形（本项目属个人虚拟设定/同人用途），
  故此处照办，但必须在交付物中如实标注来源与风险，不得默不作声地当成本项目原创。

本模块**原样输出官方标识**：不添加、不修改、不覆盖任何笔触。
（早前版本曾在官方图形上追加一条喷气线；用户 m01275 明确指示「不要改动 DS 的标识」，
 该追加笔触已删除，眼部亦保留官方原有负形细节。）
"""
import os

ROOT = r"E:\Agent项目\鲸元券"
_D_PATH = os.path.join(ROOT, "build", "deepseek_whale_d.txt")

with open(_D_PATH, encoding="utf-8") as _f:
    WHALE_D = _f.read().strip()

# 鲸鱼本体的精确包围盒 —— 由无头 Edge 的 path.getBBox() 实测得出，勿手改
#   [x, y, width, height] = [0.00005, 3.00024, 24.00048, 17.66019]（24×24 viewBox 内）
BBOX = (0.00005, 3.00024, 24.00052, 20.66043)   # x0, y0, x1, y1
VIEWBOX = 24.0


def whale(cx, cy, size, color, bg="#F5EFDE", rot=0.0):
    """在 (cx, cy) 处绘制长度约 `size` 的鲸徽（官方矢量原样输出）。

    size = 目标**宽度**（px）。内部按官方 viewBox 的实测包围盒缩放。
    bg   = 纸色（保留参数以便将来需要负形元素时使用）。
    """
    x0, y0, x1, y1 = BBOX
    w = x1 - x0
    h = y1 - y0
    s = size / w
    tx = cx - size / 2.0 - x0 * s
    ty = cy - (h * s) / 2.0 - y0 * s
    g = [f'<g transform="translate({tx:.3f} {ty:.3f}) scale({s:.5f})'
         + (f' rotate({rot:g} {VIEWBOX / 2} {VIEWBOX / 2})' if rot else '') + '">']
    g.append(f'<path d="{WHALE_D}" fill="{color}" fill-rule="evenodd"/>')
    g.append('</g>')
    return "".join(g)


def whale_ring(cx, cy, r_out, size, color, bg="#F5EFDE", ring=True,
               r_in=None, gold=None, label=None):
    """把鲸徽放进圆环，用于票面中区徽章。"""
    out = []
    if gold:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_out}" fill="none" stroke="{gold}" '
                   f'stroke-width="1.4" opacity="0.7"/>')
    if ring:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_out - 3}" fill="none" stroke="{color}" '
                   f'stroke-width="2.6" opacity="0.55"/>')
    if r_in:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r_in}" fill="none" stroke="{color}" '
                   f'stroke-width="1" opacity="0.28"/>')
    out.append(whale(cx, cy, size, color, bg=bg))
    if label:
        out.append(label)
    return "".join(out)


if __name__ == "__main__":
    print("WHALE_D loaded, %d chars" % len(WHALE_D))
    print("BBOX:", BBOX, "aspect w/h = %.3f" % ((BBOX[2] - BBOX[0]) / (BBOX[3] - BBOX[1])))
