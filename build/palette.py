# -*- coding: utf-8 -*-
"""全项目共用的专色与纸色派生。

设计约束（用户 m01275 指示）：**纸币底色取对应面额文字颜色的相似色**。
派生在 HLS 空间做——保留专色的**色相**，只把明度抬到纸基区间、把饱和度压到纸基区间。
直接与白色做线性混合是不行的：深色专色混白只会得到灰，色相辨识度丢失。
"""
import colorsys

ROOT = r"E:\Agent项目\鲸元券"

PAPER_L = 0.880   # 纸色明度
PAPER_S = 0.55    # 纸色饱和度 = 专色饱和度 × 该系数（下限见 PAPER_S_MIN）
PAPER_S_MIN = 0.20
SHADE_L = 0.660   # 「浅字」明度
SHADE_S = 0.55


def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb2hex(c):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


def _hls_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return _rgb2hex((r * 255, g * 255, b * 255))


def tint(spot, l=None):
    """专色 → 纸色（同色相的浅色版）。l 可覆盖默认明度，用于做纸色渐变。"""
    r, g, b = _hex2rgb(spot)
    h, _l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return _hls_to_hex(h, max(s * PAPER_S, PAPER_S_MIN), PAPER_L if l is None else l)


def paper_ramp(spot):
    """纸色渐变三点（亮 / 基准 / 暗），用于票面纸张的柔和渐变。"""
    return tint(spot, PAPER_L + 0.030), tint(spot), tint(spot, PAPER_L - 0.045)


def shade(spot):
    """专色 → 「浅字」色（票面淡字，如人物下方压印的 DeepSeek）。"""
    r, g, b = _hex2rgb(spot)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return _hls_to_hex(h, max(s * SHADE_S, 0.18), SHADE_L)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(a, b):
    """WCAG 2.1 对比度。"""
    la = 0.2126 * _lin(_hex2rgb(a)[0]) + 0.7152 * _lin(_hex2rgb(a)[1]) + 0.0722 * _lin(_hex2rgb(a)[2])
    lb = 0.2126 * _lin(_hex2rgb(b)[0]) + 0.7152 * _lin(_hex2rgb(b)[1]) + 0.0722 * _lin(_hex2rgb(b)[2])
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# 面额 → (券长 mm, 专色, 专色名, 主题词, 中文大写, 英文)
SERIES = [
    ("10,000,000", 132.0, "#24506B", "深青蓝", "引航", "壹仟萬 TOKEN", "TEN MILLION TOKENS"),
    ("20,000,000", 142.0, "#1F5A52", "深海绿", "夜航", "贰仟萬 TOKEN", "TWENTY MILLION TOKENS"),
    ("50,000,000", 148.0, "#4A3A6E", "紫罗兰", "港市", "伍仟萬 TOKEN", "FIFTY MILLION TOKENS"),
    ("100,000,000", 150.0, "#1B2657", "藏青", "守望", "壹億 TOKEN", "ONE HUNDRED MILLION TOKENS"),
    ("200,000,000", 158.0, "#8A5A2B", "赭金", "星图", "贰億 TOKEN", "TWO HUNDRED MILLION TOKENS"),
    ("500,000,000", 176.0, "#2E2717", "玄金", "远洋", "伍億 TOKEN", "FIVE HUNDRED MILLION TOKENS"),
]

# 盲文数字：布莱叶数字沿用字母 a~j 表示 1~0。
# 点位编号：1=左上 2=左中 3=左下 4=右上 5=右中 6=右下。
_BRAILLE_DIGIT = {1: (1,), 2: (1, 2), 3: (1, 4), 4: (1, 4, 5), 5: (1, 5),
                  6: (1, 2, 4), 7: (1, 2, 4, 5), 8: (1, 2, 5), 9: (2, 4), 0: (2, 4, 5)}
_DOT_POS = {1: (0, 0), 2: (0, 18), 3: (0, 36), 4: (18, 0), 5: (18, 18), 6: (18, 36)}


def braille_dots(tier_index, r=5.0):
    """该档盲文单元的点组。

    **六档不能都印同一个六点块** —— 规范书 6.2 的触觉编码总表要求
    「档位 = 凸点数 = 缺口数」，盲文本来就是给摸的，各档必须能摸出区别。
    这里把档位序号（1~6）编成**布莱叶数字**：档位 n 用数字 n 的点型，
    点为 (dx, dy, r)，原点在盲文单元左上角。
    """
    dots = _BRAILLE_DIGIT.get(tier_index + 1, (1,))
    return [(_DOT_POS[d][0], _DOT_POS[d][1], r) for d in dots]


# 机构与压印（用户 m01275 指示）
BANK_CN = "DeepSeek Token银行"
BANK_EN = "DEEPSEEK TOKEN BANK"
IMPRINT = "DeepSeek"
IMPRINT_YEARS = "（2023-）"
# 单位 TOKEN 的中文名（用户 m01452 指示：不要写「鲸元」，写「词元」）
# 注意：货币名仍是「鲸元券」，冠字号前缀仍是 WY —— 只有「单位的括注」用「词元」。
UNIT_CN = "词元"
MICRO = "DEEPSEEKTOKENBANK"   # 微缩文字带内容

# 固定辅助色
NAVY = "#1B2657"
GOLD = "#B08A3E"
GOLD_L = "#D8BC72"


if __name__ == "__main__":
    print(f"{'面额':>14}  {'专色':8} {'纸色':8} {'浅字色':8} {'对比度':>6}  判定")
    for n, _L, spot, name, theme, cn, en in SERIES:
        p, s = tint(spot), shade(spot)
        c = contrast(spot, p)
        print(f"{n:>14}  {spot:8} {p:8} {s:8} {c:6.2f}  {'OK' if c >= 4.5 else 'LOW'}")
