# -*- coding: utf-8 -*-
"""DeepSeek Token 银行 · 100,000,000 TOKEN 正面稿。

用户 m01275 指示的六项改动（本版全部落地）：
  1. 不改动 DS 标识 —— 鲸徽改为官方矢量原样输出（`whale_mark.whale` 已删除喷气线）；
  2. 票面底色取对应面额文字颜色的相似色 —— 见 `palette.tint()`（HLS 保色相派生）；
  3. 「鲸元储备局」→「DeepSeek Token银行」；
  4. 人物转雕刻线稿 —— PORTRAIT_SRC 指向 `portrait-lineart.png`
     （由 build/lineart_engrave.py 生成：排线疏密由原画明暗驱动）；
  5. 删除「鲸灵 · 灯」「THE WHALE SPIRIT · DENG」与签名「鲸见 灯」「发行总长」；
  6. 人物下方改为浅字 `DeepSeek`，其下 `（2023-）`。
"""
import base64, io, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palette as PAL
from whale_mark import whale as WHALE_MARK
from PIL import Image

ROOT = r"E:\Agent项目\鲸元券"

# ── 扫描模式（`python render_mockup.py --scan`）────────────────────────
# 出「就是货币本体」的高分辨率扫描稿：纸面铺满整幅、无页面底色、无投影，
# 人物墨版的 alpha 通道按 SCAN_UP 倍 Lanczos 放大后再收紧边缘斜坡。
SCAN = "--scan" in sys.argv
SCAN_UP = 4


def _b64_img(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _upscale_ink(path, n):
    """放大墨版：只放大 alpha 通道、颜色原样取回。

    墨版是**单色墨 + alpha**，所以放大 alpha 就够了 —— 直接对 RGBA 做插值会在
    线条边缘把墨色与透明混出一种脏边（halo）。指数 1.35 把插值出来的软斜坡收紧，
    抵消 Lanczos 造成的软化，线条末端才不会糊成一片。
    """
    im = Image.open(path).convert("RGBA")
    nw, nh = im.width * n, im.height * n
    r, g, b, a = im.split()
    a = a.resize((nw, nh), Image.LANCZOS)
    a = a.point(lambda v: int(255.0 * ((v / 255.0) ** 1.35)))
    # 墨是单色的，RGB 用 NEAREST 放大即可（用 LANCZOS 反而会在透明区把颜色带出来）
    r = r.resize((nw, nh), Image.NEAREST)
    g = g.resize((nw, nh), Image.NEAREST)
    b = b.resize((nw, nh), Image.NEAREST)
    return Image.merge("RGBA", (r, g, b, a))


def b64(p):
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()


# 人物稿：雕刻线稿 + 遮底版（遮底版用于把票面防伪底纹挡在人物轮廓之外）
PORTRAIT_SRC = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.png")
PORTRAIT_SVG_SRC = os.path.join(ROOT, "assets", "portrait", "portrait-lineart.svg")
COVER_SRC = os.path.join(ROOT, "assets", "portrait", "portrait-cover.png")
# 人物现在以矢量 SVG 内嵌（见下方 <svg> 注释）。位图分支保留，便于随时切回。
PORTRAIT = _b64_img(_upscale_ink(PORTRAIT_SRC, SCAN_UP)) if SCAN else b64(PORTRAIT_SRC)
_svg_txt = open(PORTRAIT_SVG_SRC, encoding="utf-8").read()
PSW, PSH = 1200, 1049          # 墨版原始像素尺寸 = 矢量视口
PORTRAIT_SVG = _svg_txt[_svg_txt.index(">") + 1:_svg_txt.rindex("</svg>")]
COVER = b64(COVER_SRC)
# 左半区人物框（按线稿 1200×1049 的 1.1439 比例反算高度）
PX, PY, PW = 50.0, 50.0, 890.0
PH = round(PW / 1.1439, 1)

# 人物用矢量还是位图 —— 两种都留，便于比对：`$env:WY_PLATE="bitmap"` 即切回位图。
PLATE = os.environ.get("WY_PLATE", "svg").strip().lower()
if PLATE == "bitmap":
    PORTRAIT_MARKUP = (
        '<image xlink:href="%s" x="%s" y="%s" width="%s" height="%s" '
        'preserveAspectRatio="none"/>' % (PORTRAIT, PX, PY, PW, PH))
else:
    PORTRAIT_MARKUP = (
        '<svg x="%s" y="%s" width="%s" height="%s" viewBox="0 0 %s %s" '
        'preserveAspectRatio="none">%s</svg>'
        % (PX, PY, PW, PH, PSW, PSH, PORTRAIT_SVG))


def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def paper_patch():
    """生成"人物遮底板"：与票面同一套纸色渐变 + vign，alpha 取人物轮廓（稍胖一圈）。

    直接作为 <image> 叠在防伪底纹之上，把底纹挡在角色图案范围之外。
    用位图而不是 SVG <mask>，是为了绕开遮罩渲染的不确定性，效果可复核。
    """
    W_, H_, M_ = W, H, M
    rw, rh = W_ - 2 * M_, H_ - 2 * M_          # 纸面矩形
    l_, c_, d_ = _hex2rgb(PAPER_L_), _hex2rgb(PAPER_C), _hex2rgb(PAPER_D)
    vg = _hex2rgb("#4A5068")
    vgn = (0.10, 0.01, 0.13)

    def grad(t, stops):
        """stops: [(pos, rgb)] 线性插值。"""
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if t <= p1 or i == len(stops) - 2:
                u = 0.0 if p1 == p0 else min(max((t - p0) / (p1 - p0), 0.0), 1.0)
                return tuple(c0[k] + (c1[k] - c0[k]) * u for k in range(3))
        return stops[-1][1]

    n = 2.0
    vx, vy = 0.9 * rw, rh                        # 渐变向量（objectBoundingBox 0,0 → 0.9,1）
    vlen2 = vx * vx + vy * vy

    im = Image.new("RGB", (int(PW), int(PH)))
    px = im.load()
    for j in range(im.height):
        y = PY + j - M_                          # 纸面矩形内的 y
        for i in range(im.width):
            x = PX + i - M_
            t = (x * vx + y * vy) / vlen2
            t = 0.0 if t < 0 else (1.0 if t > 1 else t)
            base = grad(t, [(0.0, l_), (0.5, c_), (1.0, d_)])
            vy_ = y / rh
            if vy_ < 0.5:
                a = vgn[0] + (vgn[1] - vgn[0]) * (vy_ / 0.5)
            else:
                a = vgn[1] + (vgn[2] - vgn[1]) * ((vy_ - 0.5) / 0.5)
            px[i, j] = tuple(int(round(base[k] * (1 - a) + vg[k] * a)) for k in range(3))

    cov = Image.open(COVER_SRC).convert("RGBA").resize(
        (int(PW), int(PH)), Image.LANCZOS)
    im = im.convert("RGBA")
    im.putalpha(cov.getchannel("A"))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# ── 逐档出稿：`$env:WY_TIER = "0".."5"`（主币六档），默认 3 = 100,000,000 ──
# **版式一行都不动**，只把专色与面额文字换成该档的。纸色、浅字色、底纹色
# 全部由 NAVY 派生（见下一行起），所以换掉 NAVY 整张票的颜色就整体跟着换。
# 验收条件：TIER=3 时必须与既有定稿 `build/mockup-100.png` 逐字节一致。
TIER = int(os.environ.get("WY_TIER", "3"))
DENOM, _L, _SPOT, _CNAME, _THEME, CN_DENOM, EN_DENOM = PAL.SERIES[TIER]
SERIAL = "WY " + DENOM.replace(",", "") + " 8842A"
# 盲文单元：按档位编成布莱叶数字，正反面同一组点。
BRAILLE = "".join('<circle cx="%g" cy="%g" r="%g"/>' % d for d in PAL.braille_dots(TIER))

NAVY, DEEP = _SPOT, "#2A3A7A"
GOLD, GOLD_L = PAL.GOLD, PAL.GOLD_L
PAPER_L_, PAPER_C, PAPER_D = PAL.paper_ramp(NAVY)      # 纸色渐变三点（同色相浅色版）
SHADE = PAL.shade(NAVY)                                 # 「浅字」色
BANK_CN, BANK_EN, UNIT_CN = PAL.BANK_CN, PAL.BANK_EN, PAL.UNIT_CN
# 扫描稿：纸面铺满整幅（M=0），四周不留页面底色
W, H, IN = 1890, 882, 50
M = 0 if SCAN else 30


def ellipses(cx, cy, rx, ry, n, stroke, sw, op, rot=0.0):
    return "\n".join(
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*(i+1)/n:.1f}" ry="{ry*(i+1)/n:.1f}" '
        f'fill="none" stroke="{stroke}" stroke-width="{sw}" opacity="{op:.2f}" '
        f'transform="rotate({rot:g} {cx} {cy})"/>' for i in range(n))


def rosette(cx, cy, rx, ry, n, stroke, sw, op):
    return ('<g class="ln">' + ellipses(cx, cy, rx, ry, n, stroke, sw, op)
            + ellipses(cx, cy, rx, ry, n, stroke, sw, op, 30)
            + ellipses(cx, cy, rx, ry, n, stroke, sw, op, 60) + '</g>')


def wave(cx, cy, w, amp, period, stroke, sw, op, rows=5, gap=14):
    out = []
    for r in range(rows):
        y0 = cy + r * gap
        d = [f"M {cx-w/2:.0f} {y0:.0f}"]
        for s in range(1, int(w / (period / 4)) + 1):
            x = cx - w/2 + s * (period / 4)
            d.append(f"Q {x-period/8:.0f} {y0+(amp*0.95*(1 if s%2 else -1)):.0f} {x:.0f} "
                     f"{y0+(amp*(1 if s%2 else -1)):.0f}")
        out.append(f'<path d="{" ".join(d)}" fill="none" stroke="{stroke}" stroke-width="{sw}" opacity="{op:.2f}"/>')
    return '<g class="ln">' + "".join(out) + '</g>'


MICRO = (PAL.MICRO * 4)[:68]
PATCH = paper_patch()

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W if SCAN else '100%'}" height="{H if SCAN else '100%'}">
  <defs>
    <linearGradient id="paper" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0" stop-color="{PAPER_L_}"/><stop offset="0.5" stop-color="{PAPER_C}"/>
      <stop offset="1" stop-color="{PAPER_D}"/>
    </linearGradient>
    <linearGradient id="vign" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#4A5068" stop-opacity="0.10"/>
      <stop offset="0.5" stop-color="#4A5068" stop-opacity="0.01"/>
      <stop offset="1" stop-color="#4A5068" stop-opacity="0.13"/>
    </linearGradient>
    <!-- userSpaceOnUse 版纸色渐变，**专供小面积"擦白"**。
         角位对印等处需要在票面上擦出一小块干净纸面（挡住底纹与主景线条）；
         而 #paper 是 objectBoundingBox 渐变，填在小圆上会以自己的包围盒
         重新铺一遍渐变，颜色与周围对不上，故另置这一份。坐标与票面外框一致，
         所以小圆采样到的就是该处真实的纸色。 -->
    <linearGradient id="paperU" gradientUnits="userSpaceOnUse"
                    x1="{M}" y1="{M}" x2="{M+0.9*(W-2*M):.1f}" y2="{H-M}">
      <stop offset="0" stop-color="{PAPER_L_}"/><stop offset="0.5" stop-color="{PAPER_C}"/>
      <stop offset="1" stop-color="{PAPER_D}"/>
    </linearGradient>
    <linearGradient id="vignU" gradientUnits="userSpaceOnUse" x1="0" y1="{M}" x2="0" y2="{H-M}">
      <stop offset="0" stop-color="#4A5068" stop-opacity="0.10"/>
      <stop offset="0.5" stop-color="#4A5068" stop-opacity="0.01"/>
      <stop offset="1" stop-color="#4A5068" stop-opacity="0.13"/>
    </linearGradient>
    <clipPath id="inner"><rect x="{IN}" y="{IN}" width="{W-2*IN}" height="{H-2*IN}" rx="0"/></clipPath>
    <!-- 光变油墨（OVI）：静态稿无法表现"随视角变色"，只能把一段视角内的
         连续色相变化一次画出来 —— 绿 → 蓝绿 → 紫 → 古铜，正是 OVI 油墨
         在倾斜过程中的典型走向。角度与纸面渐变错开，避免读成普通渐变。 -->
    <linearGradient id="ovi" x1="0.05" y1="0" x2="0.95" y2="1">
      <stop offset="0.00" stop-color="#2F6B4F"/>
      <stop offset="0.20" stop-color="#3E8C7A"/>
      <stop offset="0.40" stop-color="#3D6E9E"/>
      <stop offset="0.60" stop-color="#6B4E9C"/>
      <stop offset="0.80" stop-color="#9C5A6E"/>
      <stop offset="1.00" stop-color="#B08A3E"/>
    </linearGradient>
    <!-- 高光带：模拟油墨在某个倾角下"翻亮"的一条窄带 -->
    <linearGradient id="ovigloss" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0.00" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="0.38" stop-color="#FFFFFF" stop-opacity="0.34"/>
      <stop offset="0.52" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="1.00" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <mask id="pmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <image xlink:href="{COVER}" x="{PX}" y="{PY}" width="{PW}" height="{PH}"
             preserveAspectRatio="none"/>
    </mask>
    <pattern id="mesh" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="7" stroke="{NAVY}" stroke-width="0.45" opacity="0.20"/>
    </pattern>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="7" stdDeviation="11" flood-color="#141838" flood-opacity="0.28"/>
    </filter>
  </defs>

  <g{'' if SCAN else ' filter="url(#shadow)"'}>
    <rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="0" fill="url(#paper)"/>
    <rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="0" fill="url(#vign)"/>
  </g>

  <g clip-path="url(#inner)">
    <rect x="{IN}" y="{IN}" width="{W-2*IN}" height="{H-2*IN}" fill="url(#mesh)"/>

    {rosette(268, 420, 286, 344, 24, NAVY, 0.85, 0.18)}
    {rosette(1470, 430, 250, 330, 22, NAVY, 0.85, 0.15)}
    <g class="ln">{ellipses(960, 441, 800, 392, 30, NAVY, 0.7, 0.11)}</g>
    {wave(1520, 786, 620, 12, 88, NAVY, 0.95, 0.18, rows=4, gap=16)}
    {wave(1520, 104, 620, 11, 88, NAVY, 0.95, 0.14, rows=3, gap=16)}

    <rect x="{IN}" y="{IN}" width="{W-2*IN}" height="{H-2*IN}" rx="0" fill="none"
          stroke="{NAVY}" stroke-width="3" opacity="0.85"/>
    <rect x="{IN+10}" y="{IN+10}" width="{W-2*(IN+10)}" height="{H-2*(IN+10)}" rx="0" fill="none"
          stroke="{NAVY}" stroke-width="1" opacity="0.5"/>

    <!-- ===== 左半区：人物（遮底板 → 线稿）===== -->
    <!-- 遮底板仍是位图（它本身不是画面内容，只是一层纸色补丁） -->
    <image xlink:href="{PATCH}" x="{PX}" y="{PY}" width="{PW}" height="{PH}"
           preserveAspectRatio="none"/>
    <!-- 人物墨版：矢量内嵌 <svg>（默认）或位图 <image>，由 WY_PLATE 环境变量切换。
         矢量版由 `build/plate_svg.py` 程序生成（轮廓两层贝塞尔 + 恒定细线宽排线）。 -->
    {PORTRAIT_MARKUP}
    <!-- ===== 压印铭文：移到角色右侧，细、小 ===== -->
    <text x="806" y="752" text-anchor="middle" font-family="Georgia,'Times New Roman',serif"
          font-size="24" font-weight="400" fill="{SHADE}" opacity="0.85" letter-spacing="3">DeepSeek</text>
    <text x="806" y="774" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="13" font-weight="400" fill="{SHADE}" opacity="0.7" letter-spacing="2">（2023-）</text>

    <!-- ===== 右半区：机构名（顶部横题）===== -->
    <text x="1390" y="140" text-anchor="middle" font-family="'Microsoft YaHei','SimHei',sans-serif"
          font-size="36" font-weight="700" fill="{NAVY}" letter-spacing="2">{BANK_CN}</text>
    <text x="1390" y="172" text-anchor="middle" font-family="Georgia,serif" font-size="17"
          font-weight="600" fill="{DEEP}" letter-spacing="4" opacity="0.85">{BANK_EN}</text>
    <line x1="1150" y1="190" x2="1630" y2="190" stroke="{GOLD}" stroke-width="1.3" opacity="0.75"/>

    <!-- ===== 右半区：面额（光变油墨）===== -->
    <text x="985" y="312" font-family="Georgia,'Times New Roman',serif" font-size="100"
          font-weight="700" fill="url(#ovi)">{DENOM}</text>
    <text x="989" y="356" font-family="Georgia,'Times New Roman',serif" font-size="24"
          font-weight="700" fill="{DEEP}" letter-spacing="3">{EN_DENOM}</text>
    <text x="989" y="390" font-family="'Microsoft YaHei','SimHei',sans-serif" font-size="21"
          fill="{DEEP}" opacity="0.8" letter-spacing="2">{CN_DENOM}（{UNIT_CN}）</text>
    <text x="989" y="422" font-family="Georgia,serif" font-size="18"
          fill="{DEEP}" opacity="0.72" letter-spacing="2">₮{DENOM} · WYT</text>

    <!-- ===== 右半区：鲸徽（官方标识原样，改为光变油墨）===== -->
    <g transform="translate(1160 612)">
      <circle r="124" fill="none" stroke="{NAVY}" stroke-width="2.4" opacity="0.5"/>
      <circle r="115" fill="none" stroke="{GOLD}" stroke-width="1.3" opacity="0.65"/>
      <circle r="92" fill="none" stroke="{NAVY}" stroke-width="1" opacity="0.26"/>
      {WHALE_MARK(0, 4, 152, "url(#ovi)")}
      {WHALE_MARK(0, 4, 152, "url(#ovigloss)")}
      <text y="-80" text-anchor="middle" font-family="Georgia,serif" font-size="21"
            font-weight="700" fill="{NAVY}" letter-spacing="5" opacity="0.9">TOKEN</text>
    </g>

    <!-- ===== 右半区：法偿声明 ===== -->
    <text x="1560" y="580" text-anchor="middle" font-family="'Microsoft YaHei',sans-serif"
          font-size="20" fill="{DEEP}" opacity="0.92" letter-spacing="1.5">
      本券为法定清偿货币 · 凭券即付 · 不得拒收</text>
    <text x="1560" y="604" text-anchor="middle" font-family="Georgia,serif" font-size="14"
          fill="{DEEP}" opacity="0.68" letter-spacing="1">LEGAL TENDER FOR ALL DEBTS, PUBLIC AND PRIVATE</text>
    <text x="1560" y="622" text-anchor="middle" font-family="Georgia,serif" font-size="7.5"
          fill="{NAVY}" opacity="0.72" letter-spacing="0.3">{MICRO}</text>

    <!-- 对印标记：**正面只印上半**，下半由背面拼合（正背同点同径，透光下合成
         一个实心圆）。位置在**券面左下角**，距上、左内框各留 12 px 安全距；
         背面同一个物理点落在**右下角** (1790, 786) —— 翻面后左右互换。
         锚点：中心 (7.94, 62.38) mm，半圆 Ø 6.0 mm。 -->
    <g transform="translate(100 786)">
      <!-- 先擦出一块干净纸面：角位对印必须落在**无底纹、无主景线条**的区域，
           否则防伪网线与人物线稿会从圆内穿过去，读成"圆里还有画"。
           用 userSpaceOnUse 的纸色渐变铺，颜色与该处纸面完全一致，看不出边界。 -->
      <circle r="35.5" fill="url(#paperU)"/>
      <circle r="35.5" fill="url(#vignU)"/>
      <circle r="34" fill="none" stroke="{NAVY}" stroke-width="2.2" opacity="0.9"/>
      <path d="M -22 0 A 22 22 0 0 1 22 0 Z" fill="{NAVY}" fill-opacity="0.7"/>
    </g>
    <!-- 盲文块：规范书 6.1.1「右下角，距裁切线右下各 6.0 mm」。
         内容按档位走布莱叶数字（见 palette.braille_dots）—— 六档都印同一个
         六点块是错的，摸上去分不出面额。正面与背面必须**完全同点**。 -->
    <g transform="translate(1791 765)" fill="{NAVY}" opacity="0.78">
      {BRAILLE}
    </g>
    <!-- 光变徽记（(1560, 378) 的 OVI 螺旋圆环）已按用户指示删除。
         规范书 2.4.2 里「正面光变徽记」那一项随之作废，OVI 载体只剩
         面额数字与鲸徽两处；docs/ 需同步（见 task-19）。 -->
    <g opacity="0.38">
      <rect x="946" y="{IN+12}" width="14" height="{H-2*(IN+12)}" fill="{GOLD_L}" opacity="0.20"/>
      <rect x="946" y="{IN+12}" width="14" height="{H-2*(IN+12)}" fill="none" stroke="{GOLD}"
            stroke-width="1.1" stroke-dasharray="30 20"/>
    </g>

    <!-- ===== 下沿 ===== -->
    <text x="960" y="826" font-family="Consolas,'Courier New',monospace" font-size="28"
          font-weight="700" fill="{NAVY}" letter-spacing="2">{SERIAL}</text>
    <text x="1745" y="826" text-anchor="end" font-family="Consolas,'Courier New',monospace"
          font-size="28" font-weight="700" fill="{NAVY}" opacity="0.58" letter-spacing="2">{SERIAL}</text>

    <!-- 四角金色 L 形角标已移除：票面改为**锐利直角**后，矩形内框自身就构成了
         直角转折，L 形角标原是配合圆角内框的装饰；且左下角要让位给对印标记。 -->
  </g>

  <rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="0" fill="none"
        stroke="{PAPER_D}" stroke-width="1.5"/>
</svg>'''

if SCAN:
    # 扫描稿：整幅就是货币本体，无页面底色、无缩放、无投影
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:transparent;overflow:hidden}}
svg{{display:block}}
</style></head><body>{svg}</body></html>'''
    p = os.path.join(ROOT, "build", "mockup-100-scan.html" if TIER == 3
                     else f"front-{TIER}-scan.html")
else:
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#EEF0F4;overflow:hidden}}
#f{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}}
.n{{width:96vw;height:calc(96vw*{H}/{W});max-height:92vh;max-width:calc(92vh*{W}/{H});}}
</style></head><body><div id="f"><div class="n">{svg}</div></div></body></html>'''
    p = os.path.join(ROOT, "build", "mockup-100.html" if TIER == 3
                     else f"front-{TIER}.html")
open(p, "w", encoding="utf-8").write(html)
print("written:", p, len(html))
