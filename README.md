# 鲸元券 · WHALE-YUAN TOKEN

一个**虚构货币**的完整视觉设计方案 —— 六档面额、正反两面、**纯矢量票面**，
附货币规范书、视觉系统图与全套生成脚本。

本项目是**同人性质的视觉设计练习**，不是真实货币。

- **货币单位** TOKEN（中文名「词元」，国际代码 `WYT`，符号 `₮`）
- **发行机构** DeepSeek Token银行 / DEEPSEEK TOKEN BANK
- **主币面额** 10,000,000 / 20,000,000 / 50,000,000 / 100,000,000 / 200,000,000 / 500,000,000 TOKEN
- **基准券 K100** 150.0 × 70.0 mm（1890 × 882 px @ 12.6 px/mm）
- **主景人物** DeepSeek拟人形象
- **券幅阶梯** 132.0 → 142.0 → 148.0 → 150.0 → 158.0 → 176.0 mm（长宽比恒为 150 : 70）

> ⚠️ **虚构性**：本券为虚拟设定物，非真实货币，不具任何法定清偿效力，
> 票面上的「法定清偿货币」「凭券即付」等字样是虚构世界观内的设定文本。
>
> ⚠️ **商标**：票面所用的 DeepSeek 鲸鱼标识是 **DeepSeek 的商标与品牌资产**，
> 著作权与商标权**均不属于本项目**，不在本仓库任何许可的授权范围内。
> 本项目与 DeepSeek 官方**没有任何隶属、合作、赞助或背书关系**。
> 详见 [NOTICE.md](NOTICE.md) 与规范书 §8。

---

## 一、交付物

| 交付物 | 路径 | 规格 |
|---|---|---|
| **票面矢量图稿**（6 档 × 正反 = 12 份） | [`dist/svg/`](dist/svg) | **纯矢量、完全自包含**；每份 44 ~ 699 KB，可无损缩放 |
| **超高清位图**（6 档 × 正反 = 12 份） | [`dist/png/`](dist/png) | 7560 × 3528 px，等效 1091 ~ 1455 DPI，扫描件质感 |
| **全系列总表** | [dist/series-all.png](dist/series-all.png) | 2620 × 11950 px，六档正反面按真实相对尺寸排列 |
| **尺寸与输出规格说明** | [dist/鲸元券-尺寸说明.docx](dist/鲸元券-尺寸说明.docx) · [.txt](dist/鲸元券-尺寸说明.txt) | 券幅表 / 输出规格 / 要素坐标 / 字体 / 色彩 |
| **货币规范书** | [docs/spec-book.md](docs/spec-book.md) | 八章 + 附录；票面规格、面额体系、视觉系统、防伪分层、无障碍、印制工艺、商标合规 |
| **视觉系统图** | [docs/visual-system.html](docs/visual-system.html) · [.png](docs/visual-system.png) | 色板 / 基准网格与版式定位 / 字体层级表 / 纹饰母题库 / 徽志规范 / 面额色彩分级条 |
| **交付包** | [dist/README.txt](dist/README.txt) | 全档图稿打包说明与重生成命令 |

※ `dist/png/` 单张 15 ~ 17 MB、十二张合计 183 MB，走 **Git LFS**（见 [`.gitattributes`](.gitattributes)）。
直接 `git clone` 会**自动取回实体文件**；若只想要指针，用
`GIT_LFS_SKIP_SMUDGE=1 git clone`，再按需 `git lfs pull`。

### 面额一览

| 面额（TOKEN） | 主题 | 券长 mm | 券高 mm | 专色 | 反面主景 |
|---|---|---|---|---|---|
| 10,000,000 | 引航 | 132.0 | 61.6 | `#24506B` 深青蓝 | 灯浮标 |
| 20,000,000 | 夜航 | 142.0 | 66.3 | `#1F5A52` 深海绿 | 罗盘玫瑰 |
| 50,000,000 | 港市 | 148.0 | 69.0 | `#4A3A6E` 紫罗兰 | 门吊与货箱 |
| 100,000,000 | 守望 | 150.0 | 70.0 | `#1B2657` 藏青 | 灯塔（基准档） |
| 200,000,000 | 星图 | 158.0 | 73.7 | `#8A5A2B` 赭金 | 北斗七星 |
| 500,000,000 | 远洋 | 176.0 | 82.1 | `#2E2717` 玄金 | 三十二向罗经花 |

---

## 二、授权

本仓库**分两部分授权**，另附第三方声明：

| 范围 | 许可 | 文件 |
|---|---|---|
| 源代码（`build/**`） | **MIT** | [LICENSE](LICENSE) |
| 图稿与文档（`dist/**`、`assets/**`、`docs/**`） | **CC BY-NC 4.0** | [LICENSE-ARTWORK](LICENSE-ARTWORK) |
| DeepSeek 鲸鱼标识 | **不属于本项目**，不在任何许可内 | [NOTICE.md](NOTICE.md) §1 |
| `assets/source/` 人物原图 | 作者提供，**需自行确认权属** | [NOTICE.md](NOTICE.md) §3 |

图稿设为**非商业**，是因为票面使用了第三方商标 —— 若允许商业使用，
等于允许他人从事可能构成商标侵权的行为。

---

## 三、目录结构

```
鲸元券/
├─ LICENSE / LICENSE-ARTWORK / NOTICE.md    授权与第三方声明
├─ dist/                    交付物
│  ├─ svg/                      12 份纯矢量票面（6 档 × 正反）
│  ├─ png/                      12 份超高清位图（Git LFS，7560 × 3528）
│  ├─ docs/                     规范书与视觉系统图副本
│  ├─ README.txt / 尺寸说明.docx / 尺寸说明.txt
│  └─ series-all.png            全系列总表
├─ docs/                    规范性文档
│  ├─ spec-book.md              货币规范书（唯一权威文本）
│  └─ visual-system.html/.png   视觉系统图
├─ build/                   渲染脚本
│  ├─ palette.py                ★ 色彩与面额序列的唯一来源
│  ├─ whale_mark.py             ★ 全项目唯一鲸徽来源
│  ├─ plate_svg.py              人物墨版生成器（逐条排线 → 变宽包络多边形）
│  ├─ render_mockup.py          正面渲染器（WY_TIER 选档，--scan 出扫描稿）
│  ├─ render_reverse.py         反面渲染器（同上，含逐档 back_scene）
│  ├─ html_to_svg.py            从自包含 HTML 中抽出独立 SVG
│  ├─ sheet_all.py              全系列总表排版
│  └─ make_spec_brief.py        生成尺寸说明（docx + txt）
└─ assets/
   ├─ source/                 原始人物稿
   └─ portrait/               去底后人物稿与墨版
```

---

## 四、重新渲染

本机工具链（Windows / PowerShell）：

```powershell
$py   = "C:\Users\29938\AppData\Local\Programs\Python\Python310\python.exe"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

渲染脚本生成**自包含 HTML**（嵌套 SVG），再用 Edge 无头模式截图：

```powershell
# 单档渲染：WY_TIER = 0..5，3 为基准档（1 亿）
$env:WY_TIER = "3"
& $py "$PWD\build\render_mockup.py"  --scan     # 正面
& $py "$PWD\build\render_reverse.py" --scan     # 反面

# 抽独立 SVG
& $py "$PWD\build\html_to_svg.py" "$PWD\build\mockup-100-scan.html" "$PWD\out.svg"

# 出超高清 PNG（4 倍设备像素比 → 7560 × 3528）
& $edge --headless=new --disable-gpu --hide-scrollbars `
        --force-device-scale-factor=4 --window-size=1890,882 `
        --virtual-time-budget=60000 `
        --screenshot="$PWD\out.png" "file:///$($PWD.Path.Replace('\','/'))/build/mockup-100-scan.html"
```

`--scan` 模式去掉页面底色与投影，让票面铺满整幅 —— 出图即「货币本体」，
而不是「货币摆在纸上」。

> **注意**：渲染器的输出文件名有两条规则 —— 基准档（`WY_TIER=3`）保留定稿名
> `mockup-100*.html` / `reverse-100*.html`，其余档为 `front-{i}*.html` / `back-{i}*.html`。
> 取图时若用错规则，会静默读到上一次的陈旧文件。

Edge 会向 stderr 输出 `QQBrowser user data path not found` 一类报错，**可忽略**；
控制台里含中文的路径显示为乱码亦不影响落盘。

长图截图（总表、视觉系统图）的**窗口高度必须 ≥ 画布高度**，否则会被**静默截断**。

---

## 五、设计要点

完整条文见 [docs/spec-book.md](docs/spec-book.md)。骨架如下：

1. **可识别性第一** —— 面额由**尺寸 + 主色调 + 图案主题**三维同时分级：
   券长 132.0 → 176.0 mm 阶梯、相邻档色相角差 ≥ 18°（不足者以 ΔL\* ≥ 25 分离）、
   六档专属主题词。全档共用同一人物构图与同一套版式，档位之间**只差一个等比
   缩放系数**，不重排。
2. **形制规范** —— 全档共享同一坐标系（基准网格、安全线位、水印位），
   预留 3.0 mm 出血与套印公差；关键防伪元素避开 6.0 mm 折线保护带。
3. **防伪三层** —— 公众级（水印、开窗安全线、凹版手感、光变油墨、对印）／
   机读级（磁编码、紫外荧光、红外吸收对）／专家级（微缩文字、接线印刷、
   无色荧光纤维）。每层 ≥ 2 项且**原理两两互斥**。
4. **无障碍** —— 触觉编码三码一致（凸点数 = 边缘缺口数 = 档位序号）；
   盲文块按档位编码点型；色觉障碍下不得以红绿差异作为唯一区分手段。
5. **工艺可行** —— 设计即对凹印 + 胶印 + 丝印 + 号码印四道工序下指令；
   渐变以线条粗细／密度实现，不用网点。
6. **人物为矢量** —— 主景不是位图贴图，而是 `plate_svg.py` 逐条生成的
   **变宽包络多边形**（约 820 条），因此 12 份 SVG 全部自包含、无任何外链。

---

## 六、已知事项

- 规范书记录了**一处版面结构性限制**（9 位全值面额串与两条 6.0 mm 纵向折线
  保护带之间的容量冲突），已给出裁决方向，标记为**未定案 · 制版前必须消解**。
- **六档 SVG 的 `viewBox` 一律为 `0 0 1890 882`**，并未按券幅缩放 ⇒
  「1 mm = 多少用户单位」**逐档不同**（10,000,000 券为 14.318，500,000,000 券为
  10.739）。要素坐标的毫米值只在 1 亿券成立，其余档位按比例缩放。
  换算表见 [dist/鲸元券-尺寸说明.txt](dist/鲸元券-尺寸说明.txt)。
- 辅币（100,000 / 200,000 / 500,000 分）在规范书中有设定条文，**尚无对应图稿**。
- `build/` 下的 `*.html` 与位图成品均为**可重新生成的中间产物**，未纳入版本管理。
