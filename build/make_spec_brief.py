# -*- coding: utf-8 -*-
"""生成「鲸元券 · 尺寸与输出规格简要说明」（.docx 与 .txt 两份）。

数据来源全部实测自交付包本身，不引用任何估计值：
  * 券长取 build/palette.py 的 SERIES
  * 券高 = round(round(券长*12.6) / (150/70)) / 12.6
  * SVG viewBox 实测为 0 0 1890 882（六档一律如此）
  * 要素锚点实测自 dist/svg/front|back_100000000.svg 的 translate()
"""
import os

MM = 12.6
AR = 150.0 / 70.0
UNIT_W, UNIT_H = 1890, 882
OUT_W, OUT_H = 7560, 3528

SERIES = [
    ("10,000,000", 132.0, "#24506B", "深青蓝", "引航"),
    ("20,000,000", 142.0, "#1F5A52", "深海绿", "夜航"),
    ("50,000,000", 148.0, "#4A3A6E", "紫罗兰", "港市"),
    ("100,000,000", 150.0, "#1B2657", "藏青", "守望"),
    ("200,000,000", 158.0, "#8A5A2B", "赭金", "星图"),
    ("500,000,000", 176.0, "#2E2717", "玄金", "远洋"),
]

# 实测锚点（单位：SVG 用户单位，1 亿券下 12.6 单位 = 1 mm）
ANCHORS = [
    ("正面 · 对印标记圆心", 100.0, 786.0, "上半实心扇形，Ø68 单位"),
    ("正面 · 盲文块原点", 1791.0, 765.0, "6 点制单元，块右下角 (1814, 806)"),
    ("正面 · 行徽（鲸鱼）圆心", 1160.0, 612.0, "三同心圆 r=124 / 115 / 92"),
    ("反面 · 对印标记圆心", 1790.0, 786.0, "下半实心扇形，与正面同点同径"),
    ("反面 · 盲文块原点", 76.0, 765.0, "与正面同一物理点（翻面后左右互换）"),
    ("反面 · 主景中轴基点", 948.0, 636.0, "灯塔 / 浮标 / 罗盘等主景由此展开"),
    ("反面 · 年版与厂标", 1705.0, 767.3, "「2026年」+ DeepSeek 标识，贴对印左侧"),
    ("反面 · 面额光变数字", 1444.0, 185.6, "OVI 施加于大号面额数字"),
]


def geom(L):
    cw = int(round(L * MM))
    ch = int(round(cw / AR))
    return cw, ch, ch / MM


def rows():
    out = []
    for denom, L, spot, cname, theme in SERIES:
        cw, ch, hmm = geom(L)
        upp = UNIT_W / L
        dpi = OUT_W / (L / 25.4)
        out.append(dict(denom=denom, L=L, H=hmm, cw=cw, ch=ch,
                        upp=upp, dpi=dpi, spot=spot, cname=cname, theme=theme))
    return out


# ── 纯文本版 ────────────────────────────────────────────────────────
def write_txt(path):
    R = rows()
    L = []
    a = L.append
    a("鲸元券 · 尺寸与输出规格简要说明")
    a("DeepSeek Token银行 · 结算券「鲸元券」")
    a("=" * 78)
    a("")
    a("一、券幅尺寸")
    a("-" * 78)
    a("%-14s %-8s %8s %8s %9s %14s %9s" %
      ("面额(TOKEN)", "主题", "券长mm", "券高mm", "长宽比", "设计画布px", "等效DPI"))
    for r in R:
        a("%-14s %-8s %8.1f %8.1f %9.4f %7d×%-6d %9.0f" %
          (r["denom"], r["theme"], r["L"], r["H"], r["L"] / r["H"],
           r["cw"], r["ch"], r["dpi"]))
    a("")
    a("说明：")
    a("  · 长宽比六档均为 150 : 70（= 2.1429）。所有面额共用同一套版式，")
    a("    档位之间只差一个等比缩放系数，版式不重排。上表比值的末位小数")
    a("    差异来自券高按 0.1 mm 取整，不是版式不同。")
    a("  · 券长是主参数；券高由基准档（1 亿券 150.0 × 70.0 mm）反算：")
    a("    券高 = round(券长 × 12.6 ÷ (150 ÷ 70)) ÷ 12.6，按 0.1 mm 取整。")
    a("  · 设计画布 = 券长(mm) × 12.6 px/mm，按 1 px 取整。")
    a("")
    a("二、输出文件规格")
    a("-" * 78)
    a("SVG（12 份，svg/ 目录）")
    a("  坐标系      viewBox = 0 0 1890 882（六档一律相同）")
    a("  自包含性    无任何外链、无内嵌位图；人物为嵌套矢量路径")
    a("  可编辑性    可直接在 Illustrator / Inkscape / Figma 打开")
    a("  文件大小    反面约 44 ~ 48 KB；正面约 691 ~ 699 KB")
    a("  单位换算    1 mm = 1890 ÷ 券长(mm) 个用户单位，逐档不同：")
    a("              %-12s %-12s %s" % ("面额", "券长mm", "单位/mm"))
    for r in R:
        a("              %-12s %-12.1f %.3f" % (r["denom"], r["L"], r["upp"]))
    a("")
    a("PNG（12 份，png/ 目录）")
    a("  像素尺寸    %d × %d px（十二张完全一致）" % (OUT_W, OUT_H))
    a("  物理尺寸    按各档券幅计，即票面铺满整幅、无留白、无出血")
    a("  等效精度    1091 ~ 1455 DPI（见上表；小面额券幅小，等效 DPI 更高）")
    a("  渲染方式    无头浏览器 4 倍设备像素比截图，--scan 模式：")
    a("              去掉页面底色与投影，出图即货币本体，非「货币摆在纸上」")
    a("  色彩        8 位 sRGB，无 ICC 嵌入")
    a("")
    a("三、票面要素坐标（以 1 亿券为基准，单位 = SVG 用户单位）")
    a("-" * 78)
    a("%-24s %8s %8s %10s %10s  %s" %
      ("要素", "X单位", "Y单位", "X毫米", "Y毫米", "备注"))
    for name, x, y, note in ANCHORS:
        a("%-24s %8.1f %8.1f %10.2f %10.2f  %s" %
          (name, x, y, x / MM, y / MM, note))
    a("")
    a("说明：以上毫米值仅在 1 亿券（150.0 × 70.0 mm，12.6 单位/mm）成立。")
    a("      其余档位共用同一套用户单位坐标，故相对位置固定、绝对毫米随")
    a("      券幅等比缩放。若需换算某档的毫米值，除以该档的「单位/mm」。")
    a("")
    a("四、版面留白")
    a("-" * 78)
    a("  交付 SVG / PNG 为「票面本体」：票面铺满整幅，四角锐利直角。")
    a("  渲染预览稿（build/mockup-100.png 等）额外带 30 单位的页面留白")
    a("  与投影，仅供展示，不属于交付件。")
    a("  制版时另需外扩出血 3.0 mm，票面四边安全区距裁切线 3.0 mm。")
    a("")
    a("五、字体")
    a("-" * 78)
    a("  中文正字      Microsoft YaHei（微软雅黑）")
    a("  大号面额数字  Georgia Bold")
    a("  英文名称      Georgia")
    a("  冠字号        Consolas")
    a("  字形覆盖注意  货币符号 ₮（U+20AE）在 SimSun（宋体）中**无字形**，")
    a("                排版时须把微软雅黑或 Georgia 排在宋体之前。")
    a("")
    a("六、色彩")
    a("-" * 78)
    a("  纸色          #F5EFDE")
    a("  金色点缀      #B08A3E（深） / #D8BC72（浅）")
    a("  面额专色      逐档不同，见下表；浅色底纹由专色按 HLS 派生")
    for r in R:
        a("                %-14s %s  %s · %s" %
          (r["denom"], r["spot"], r["cname"], r["theme"]))
    a("")
    a("七、版权与合规")
    a("-" * 78)
    a("  票面所用 DeepSeek 鲸鱼标识是 DeepSeek 的商标与品牌资产，")
    a("  著作权与商标权均不属本项目。本包为个人虚拟设定 / 娱乐用途，")
    a("  不得商业发行，不得使他人误认为本券由 DeepSeek 官方发行。")
    a("  详见 docs/spec-book.md 第 8 章。")
    a("")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return len("\n".join(L))


# ── Word 版 ────────────────────────────────────────────────────────
def write_docx(path):
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    R = rows()
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Microsoft YaHei"
    st.font.size = Pt(10.5)

    def H(txt, lvl=1):
        p = doc.add_heading(txt, level=lvl)
        for r in p.runs:
            r.font.name = "Microsoft YaHei"
            r.font.color.rgb = RGBColor(0x1B, 0x26, 0x57)
        return p

    def P(txt, bold=False, size=10.5):
        p = doc.add_paragraph()
        r = p.add_run(txt)
        r.bold = bold
        r.font.size = Pt(size)
        r.font.name = "Microsoft YaHei"
        return p

    def TBL(header, data, widths=None):
        t = doc.add_table(rows=1, cols=len(header))
        t.style = "Light Grid Accent 1"
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            run = c.paragraphs[0].add_run(str(h))
            run.bold = True
            run.font.size = Pt(9.5)
            run.font.name = "Microsoft YaHei"
        for row in data:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                run = cells[i].paragraphs[0].add_run(str(v))
                run.font.size = Pt(9.5)
                run.font.name = "Microsoft YaHei"
        if widths:
            for r in t.rows:
                for i, w in enumerate(widths):
                    r.cells[i].width = Cm(w)
        return t

    ti = doc.add_paragraph()
    ti.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = ti.add_run("鲸元券 · 尺寸与输出规格简要说明")
    run.bold = True
    run.font.size = Pt(19)
    run.font.name = "Microsoft YaHei"
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("DeepSeek Token银行 · 结算券「鲸元券」")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    H("一、券幅尺寸", 1)
    TBL(["面额（TOKEN）", "主题", "券长 mm", "券高 mm", "长宽比",
         "设计画布 px", "等效 DPI"],
        [[r["denom"], r["theme"], "%.1f" % r["L"], "%.1f" % r["H"],
          "%.4f" % (r["L"] / r["H"]), "%d × %d" % (r["cw"], r["ch"]),
          "%.0f" % r["dpi"]] for r in R])
    P("")
    P("说明：", bold=True)
    P("· 长宽比六档恒为 150 : 70 = 2.1429。所有面额共用同一套版式，"
      "档位之间只差一个等比缩放系数，版式不重排。")
    P("· 券长是主参数。券高由基准档（1 亿券 150.0 × 70.0 mm）反算："
      "券高 = round(券长 × 12.6 ÷ (150 ÷ 70)) ÷ 12.6，按 0.1 mm 取整。")
    P("· 设计画布 = 券长(mm) × 12.6 px/mm，按 1 px 取整。")

    H("二、输出文件规格", 1)
    P("SVG —— 12 份（svg/ 目录）", bold=True)
    P("· 坐标系：viewBox = 0 0 1890 882，六档一律相同。")
    P("· 自包含：无任何外链、无内嵌位图；人物为嵌套矢量路径。")
    P("· 可编辑：可直接在 Illustrator / Inkscape / Figma 中打开编辑。")
    P("· 文件大小：反面约 44 ~ 48 KB，正面约 691 ~ 699 KB。")
    P("· 单位换算：1 mm = 1890 ÷ 券长(mm) 个用户单位，逐档不同 ——")
    TBL(["面额（TOKEN）", "券长 mm", "单位 / mm"],
        [[r["denom"], "%.1f" % r["L"], "%.3f" % r["upp"]] for r in R])
    P("")
    P("PNG —— 12 份（png/ 目录）", bold=True)
    P("· 像素尺寸：%d × %d px，十二张完全一致。" % (OUT_W, OUT_H))
    P("· 物理尺寸：按各档券幅计，即票面铺满整幅，无留白、无出血。")
    P("· 等效精度：1091 ~ 1455 DPI。小面额券幅小，等效 DPI 更高。")
    P("· 渲染方式：无头浏览器 4 倍设备像素比截图，--scan 模式去掉页面底色"
      "与投影，出图即货币本体，而非「货币摆在纸上」。")
    P("· 色彩：8 位 sRGB，无 ICC 嵌入。")

    H("三、票面要素坐标", 1)
    P("以 1 亿券为基准；单位 = SVG 用户单位。", bold=True)
    TBL(["要素", "X 单位", "Y 单位", "X 毫米", "Y 毫米", "备注"],
        [[n, "%.1f" % x, "%.1f" % y, "%.2f" % (x / MM), "%.2f" % (y / MM), note]
         for n, x, y, note in ANCHORS])
    P("")
    P("说明：以上毫米值仅在 1 亿券（150.0 × 70.0 mm，12.6 单位/mm）成立。"
      "其余档位共用同一套用户单位坐标，故相对位置固定、绝对毫米随券幅等比"
      "缩放。若需换算某档的毫米值，除以该档的「单位/mm」。")

    H("四、版面留白与出血", 1)
    P("· 交付的 SVG / PNG 是「票面本体」：票面铺满整幅，四角锐利直角。")
    P("· 渲染预览稿（build/mockup-100.png 等）额外带 30 单位页面留白与投影，"
      "仅供展示，不属于交付件。")
    P("· 制版另需外扩出血 3.0 mm；安全区距裁切线 3.0 mm。")

    H("五、字体", 1)
    TBL(["用途", "字体"],
        [["中文正字", "Microsoft YaHei（微软雅黑）"],
         ["大号面额数字", "Georgia Bold"],
         ["英文名称", "Georgia"],
         ["冠字号", "Consolas"]])
    P("")
    P("字形覆盖注意：货币符号 ₮（U+20AE）在 SimSun（宋体）中无字形，"
      "排版时须把微软雅黑或 Georgia 排在宋体之前，否则出豆腐块。", bold=True)

    H("六、色彩", 1)
    P("纸色 #F5EFDE　金色点缀 #B08A3E（深）/ #D8BC72（浅）")
    P("面额专色逐档不同；浅色底纹由专色按 HLS 派生。")
    TBL(["面额（TOKEN）", "专色", "色名", "主题"],
        [[r["denom"], r["spot"], r["cname"], r["theme"]] for r in R])

    H("七、版权与合规", 1)
    P("票面所用 DeepSeek 鲸鱼标识是 DeepSeek 的商标与品牌资产，"
      "著作权与商标权均不属本项目。本包为个人虚拟设定 / 娱乐用途，"
      "不得商业发行，不得使他人误认为本券由 DeepSeek 官方发行。")
    P("详见 docs/spec-book.md 第 8 章「商标与合规警示」。")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    return os.path.getsize(path)


if __name__ == "__main__":
    D = r"E:\Agent项目\鲸元券\dist"
    n = write_txt(os.path.join(D, "鲸元券-尺寸说明.txt"))
    print("txt  %d chars" % n)
    b = write_docx(os.path.join(D, "鲸元券-尺寸说明.docx"))
    print("docx %d bytes" % b)
