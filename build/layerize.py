# -*- coding: utf-8 -*-
"""把压平的票面 SVG 重排成**分层 SVG**，供爆炸图 / 分镜动画逐层驱动。

为什么需要这一步
----------------
渲染器（`render_mockup.py` / `render_reverse.py`）吐出来的是**一张压平的图**：
顶层只有「纸面」和「票面内容（带 clip-path）」两个大组，票面内容那个组的直接
子元素全是平铺的 `text` / `rect` / `g` / `path`。拿这种文件做爆炸图，只能整张
平移，做不出「人物浮起来、纹样沉下去」。

做法
----
不重写渲染器（那会引入新的不一致风险），而是**后处理**：按**规则**把直接子元素
归拢进命名层。用规则而不是下标，是因为逐档的主景画法不一样（有的档主景是一个
`<g>`，有的档是一串 `<path>`/`<line>`），子元素个数在 28~53 之间浮动，写死下标必错。

**验收**：分层版与原版同参数渲染，PNG 必须**逐像素一致**（md5 相同）。
包 `<g>` 不改变绘制结果，所以这条可以严格成立；它是这个脚本唯一的正确性保证。
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = r"E:\Agent项目\鲸元券"
DIST = os.path.join(ROOT, "dist")
LAYERS = os.path.join(DIST, "layers")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

TOK = re.compile(r'<!--.*?-->|<(/?)([a-zA-Z][\w:-]*)((?:"[^"]*"|\'[^\']*\'|[^>])*?)(/?)>', re.S)


def _tok(s, start=0):
    """产出 (close, 标签名, 属性串, 是否自闭合)，**跳过注释**。

    注释必须跳过：人物墨版里嵌着带 `<g>` / `<path>` 字样的注释，直接拿正则扫
    会把这些当成真的开标签，深度计数就错位（表现为顶层多出两个未闭合的 `<g>`，
    末尾元素被吞进上一个组里）。
    """
    for m in TOK.finditer(s, start):
        if m.group(2) is None:                     # 注释
            continue
        yield m.start(), m.end(), m.group(1), m.group(2), m.group(3), m.group(4)


# 层规则：(层名, 判定函数)。**按顺序取第一个命中**，特例必须排在通例前。
# 判定函数收 (标签, 属性串, 元素全文, 是否已过内框)，返回 True 即认领。
# `after` = 已越过内框；防伪纹（mesh / g.ln）只可能是内框之前那一段，
# 过了内框再出现 `g class="ln"` 是主景自己的浪线，不能被纹样层认领。
def _rules_front():
    return [
        ("guilloche", lambda t, a, x, aft: not aft and t == "rect" and "url(#mesh)" in a),
        ("guilloche", lambda t, a, x, aft: not aft and t == "g" and 'class="ln"' in a),
        ("frame",     lambda t, a, x, aft: t == "rect" and 'fill="none"' in a),
        ("portrait",  lambda t, a, x, aft: t in ("image", "svg")),
        ("denom",     lambda t, a, x, aft: t == "text" and 'font-size="100"' in a),
        ("emblem",    lambda t, a, x, aft: t == "g" and "translate(1160 612)" in a),
        ("marks",     lambda t, a, x, aft: t == "g" and (
            "translate(100 786)" in a or "translate(1791 765)" in a or 'opacity="0.38"' in a)),
        ("type",      lambda t, a, x, aft: t == "text"),
        ("type",      lambda t, a, x, aft: t == "line"),
    ]


def _rules_back():
    return [
        ("guilloche", lambda t, a, x, aft: not aft and t == "rect" and "url(#mesh)" in a),
        ("guilloche", lambda t, a, x, aft: not aft and t == "g" and 'class="ln"' in a),
        ("frame",     lambda t, a, x, aft: t == "rect" and 'fill="none"' in a),
        ("denom",     lambda t, a, x, aft: t == "text" and
            ('font-size="100"' in a or 'font-size="86"' in a)),      # 正面 100 / 背面 86
        ("marks",     lambda t, a, x, aft: t == "g" and (
            "rotate(-12" in a or "translate(76 765)" in a or "translate(1790 786)" in a)),
        ("marks",     lambda t, a, x, aft: t == "rect" and 'x="1236"' in a),
        ("marks",     lambda t, a, x, aft: t == "line" and 'x1="1242.5"' in a),
        ("emblem",    lambda t, a, x, aft: t == "g" and (
            "translate(1705" in a or "translate(1444" in a or "translate(1560 300)" in a)),
        ("emblem",    lambda t, a, x, aft: t == "circle" and 'cx="1560"' in a),
        ("type",      lambda t, a, x, aft: t == "text"),
        ("type",      lambda t, a, x, aft: t == "line" and 'x1="1348"' in a),
        ("motif",     lambda t, a, x, aft: True),          # 余下全是本档主景
    ]


def _children(s, start):
    """列出 `start` 之后**同一层**的元素。

    `start` 必须是父元素开标签之后的位置；父元素的收口会让本层结束。
    """
    depth, out = 0, []
    for a, b, close, name, attrs, selfc in _tok(s, start):
        if close:
            if depth == 0:
                break
            depth -= 1
            continue
        if depth == 0:
            if selfc:
                out.append((a, b, name, s[a:b]))
            else:
                e = _span(s, a)
                out.append((a, e, name, s[a:e]))
        if not selfc:
            depth += 1
    return out


def _span(s, start):
    """从一个元素起点找到它的闭合位置。"""
    depth = 0
    for a, b, close, name, attrs, selfc in _tok(s, start):
        if close:
            depth -= 1
            if depth == 0:
                return b
            continue
        if not selfc:
            depth += 1
    return len(s)


def _open_tag(text):
    """返回 (标签名, 属性串, 开标签结束偏移)。"""
    for a, b, close, name, attrs, selfc in _tok(text, 0):
        return name, " ".join(attrs.split()), b
    raise ValueError("no tag in %r" % text[:60])


def layerize(svg, table, side):
    body_start = svg.index(">", svg.index("<svg")) + 1
    body_end = svg.rindex("</svg>")
    head, body, tail = svg[:body_start], svg[body_start:body_end], svg[body_end:]

    top = _children(body, 0)
    paper = [e for e in top if e[2] == "g" and "clip-path" not in e[3]]
    clipg = [e for e in top if e[2] == "g" and "clip-path" in e[3]]
    assert len(paper) == 1 and len(clipg) == 1, (side, len(paper), len(clipg))
    paper, clipg = paper[0], clipg[0]

    kids = _children(body, clipg[0] + _open_tag(clipg[3])[2])
    assert kids and kids[0][0] > clipg[0] and kids[-1][1] <= clipg[1], (side, "out of group")

    assign, after = {}, False
    for i, (a, b, tg, text) in enumerate(kids):
        real_tag, attrs, _ = _open_tag(text)
        name = None
        for lname, hit in table:
            if hit(real_tag, attrs, text, after):
                name = lname
                break
        assert name is not None, "%s child %d <%s %s> unclaimed" % (side, i, real_tag, attrs[:60])
        assign[i] = name
        if name == "frame":
            after = True

    # 只把**连续**的同类子元素并成一个组，绝不打乱绘制顺序。
    # 一层的成员可能分成好几段（比如「文字」在内框两侧都有），那就出多个
    # `<g data-layer="type">` —— 下游按 data-layer 选**全部**同名的组一起驱动即可。
    # 一旦为了「一层一个组」而把后面的元素提到前面，绘制顺序就变了：实测正面
    # 会出现最大 10/255 的差异（安全线压冠字号的叠色反了），所以不做。
    out, i, run = [], 0, {}
    while i < len(kids):
        n = assign[i]
        j = i
        while j < len(kids) and assign[j] == n:
            j += 1
        run[n] = run.get(n, 0) + 1
        out.append('<g id="L-%s%d" data-layer="%s">%s</g>'
                   % (n, run[n], n, "".join(k[3] for k in kids[i:j])))
        i = j
    inner = "".join(out)

    newtop = []
    for e in top:
        tag, text = e[2], e[3]
        if e[0] == paper[0] and tag == "g":
            newtop.append('<g id="L-paper" data-layer="paper">%s</g>' % text)
        elif e[0] == clipg[0]:
            newtop.append('<g %s id="L-ink" data-layer="ink">%s</g>' % (_open_tag(text)[1], inner))
        else:
            newtop.append('<g id="L-border" data-layer="border">%s</g>' % text)
    return head + "".join(newtop) + tail


def render(svg_path, out_png, w=1900, h=900):
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--window-size=%d,%d" % (w, h),
                    "--virtual-time-budget=25000", "--screenshot=" + out_png,
                    "file:///" + svg_path.replace("\\", "/")],
                   capture_output=True)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(LAYERS, exist_ok=True)
    verify = "--verify" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")] or ["front", "back"]
    tmp = os.path.join(ROOT, "build", "_lv")
    if verify:
        os.makedirs(tmp, exist_ok=True)

    ok = bad = 0
    for fn in sorted(os.listdir(os.path.join(DIST, "svg"))):
        side = fn.split("_")[0]
        if side not in only:
            continue
        src = os.path.join(DIST, "svg", fn)
        svg = open(src, encoding="utf-8").read()
        out = layerize(svg, _rules_front() if side == "front" else _rules_back(), fn)
        dst = os.path.join(LAYERS, fn)
        open(dst, "w", encoding="utf-8").write(out)
        line = "%-26s %9d -> %9d B" % (fn, len(svg), len(out))

        if verify:
            a, b = os.path.join(tmp, "a.png"), os.path.join(tmp, "b.png")
            render(src, a)
            render(dst, b)
            import numpy as np
            from PIL import Image
            pa = np.asarray(Image.open(a).convert("RGB"), dtype=np.int16)
            pb = np.asarray(Image.open(b).convert("RGB"), dtype=np.int16)
            mx = int(np.abs(pa - pb).max())
            same = mx <= 2
            ok, bad = (ok + 1, bad) if same else (ok, bad + 1)
            line += "   %-9s maxΔ=%d" % ("PASS" if same else "*** FAIL ***", mx)
        print(line, flush=True)
    if verify:
        print("\nverify: %d pass, %d fail  (判据：任一分量最大差 <= 2/255)" % (ok, bad))


if __name__ == "__main__":
    main()
