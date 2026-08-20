#!/usr/bin/env python
"""LaTeX → 可编辑 Word Office Math（OMML）。

技术路线：``latex2mathml`` 转 MathML，再映射为 ``m:oMath`` / ``m:oMathPara``，
供 ``python-docx`` 挂到段落。不依赖本机 TeX / Word COM。

基于LaTeX→OMML嵌入可编辑的公式，复杂宏失败时由调用方回退 PNG/原文。

依赖：``pip install latex2mathml``（另需已有 ``python-docx``）。
"""
from __future__ import annotations

from copy import deepcopy
from xml.etree import ElementTree

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

MATHML_NS = "{http://www.w3.org/1998/Math/MathML}"


def normalize_latex_for_omml(latex: str) -> str:
    """去掉 Word 公式不友好的外壳，保留核心式。"""
    import re

    body = (latex or "").strip()
    if not body:
        return ""
    body = re.sub(r"\\tag\{[^}]*\}", "", body)
    body = body.replace("\n", " ")
    body = re.sub(r"[ \t]{2,}", " ", body).strip()
    # 常见简写
    body = body.replace(r"\le", r"\leq").replace(r"\ge", r"\geq")
    body = body.replace(r"\land", r"\wedge").replace(r"\lor", r"\vee")
    # latex2mathml 对 \left/\right/\big 套 \min/\max 易失败；去掉尺寸命令，保留括号
    body = re.sub(r"\\(big+|Big+|left|right|bigl|bigr|Bigl|Bigr)\b", "", body)
    return body


def _element(name: str):
    return OxmlElement(f"m:{name}")


def _text_run(text: str):
    run = _element("r")
    properties = _element("rPr")
    style = _element("sty")
    style.set(qn("m:val"), "p")
    properties.append(style)
    run.append(properties)
    value = _element("t")
    value.text = text
    run.append(value)
    return run


def _append_children(target, source) -> None:
    if source.text and source.text.strip():
        target.append(_text_run(source.text.strip()))
    for child in source:
        _append_mathml(target, child)
        if child.tail and child.tail.strip():
            target.append(_text_run(child.tail.strip()))


def _script(target, node, kind: str) -> None:
    result = _element(kind)
    expression = _element("e")
    sub = _element("sub")
    sup = _element("sup")
    children = list(node)
    if children:
        _append_mathml(expression, children[0])
    if len(children) > 1:
        _append_mathml(sub, children[1])
    if len(children) > 2:
        _append_mathml(sup, children[2])
    result.append(expression)
    if kind in {"sSub", "sSubSup"}:
        result.append(sub)
    if kind in {"sSup", "sSubSup"}:
        result.append(sup if kind == "sSubSup" else sub)
    target.append(result)


def _append_mathml(target, node) -> None:
    tag = node.tag.removeprefix(MATHML_NS)
    children = list(node)

    if tag in {"math", "mrow", "mstyle", "semantics", "annotation"}:
        _append_children(target, node)
    elif tag in {"mi", "mn", "mo", "mtext"}:
        target.append(_text_run("".join(node.itertext())))
    elif tag == "mfrac":
        fraction = _element("f")
        numerator = _element("num")
        denominator = _element("den")
        if children:
            _append_mathml(numerator, children[0])
        if len(children) > 1:
            _append_mathml(denominator, children[1])
        fraction.extend((numerator, denominator))
        target.append(fraction)
    elif tag == "msub":
        _script(target, node, "sSub")
    elif tag == "msup":
        _script(target, node, "sSup")
    elif tag in {"msubsup", "munderover"}:
        _script(target, node, "sSubSup")
    elif tag == "munder":
        _script(target, node, "sSub")
    elif tag == "mover":
        _script(target, node, "sSup")
    elif tag == "msqrt":
        radical = _element("rad")
        properties = _element("radPr")
        hide_degree = _element("degHide")
        hide_degree.set(qn("m:val"), "1")
        properties.append(hide_degree)
        degree = _element("deg")
        expression = _element("e")
        _append_children(expression, node)
        radical.extend((properties, degree, expression))
        target.append(radical)
    elif tag == "mroot":
        radical = _element("rad")
        degree = _element("deg")
        expression = _element("e")
        if children:
            _append_mathml(expression, children[0])
        if len(children) > 1:
            _append_mathml(degree, children[1])
        radical.extend((degree, expression))
        target.append(radical)
    elif tag == "mfenced":
        delimiter = _element("d")
        properties = _element("dPr")
        begin = _element("begChr")
        begin.set(qn("m:val"), node.attrib.get("open", "("))
        end = _element("endChr")
        end.set(qn("m:val"), node.attrib.get("close", ")"))
        properties.extend((begin, end))
        expression = _element("e")
        _append_children(expression, node)
        delimiter.extend((properties, expression))
        target.append(delimiter)
    elif tag == "mtable":
        matrix = _element("m")
        for row_node in children:
            row = _element("mr")
            for cell_node in list(row_node):
                cell = _element("e")
                _append_children(cell, cell_node)
                row.append(cell)
            matrix.append(row)
        target.append(matrix)
    elif tag in {"mtr", "mtd"}:
        _append_children(target, node)
    elif tag == "mspace":
        target.append(_text_run(" "))
    else:
        _append_children(target, node)


def latex_to_omml(latex: str, *, display: bool = True):
    """返回可挂到 ``paragraph._p`` 的 OMML 元素。

    display=True → ``m:oMathPara``（块级）；False → ``m:oMath``（行内）。
    """
    try:
        from latex2mathml.converter import convert
    except ImportError as error:
        raise RuntimeError(
            "原生公式需要 latex2mathml：pip install latex2mathml"
        ) from error

    body = normalize_latex_for_omml(latex)
    if not body:
        raise ValueError("empty latex")

    mathml = ElementTree.fromstring(convert(body))
    math = _element("oMath")
    _append_mathml(math, mathml)
    if display:
        paragraph = _element("oMathPara")
        paragraph.append(math)
        return paragraph
    return math


def try_latex_to_omml(latex: str, *, display: bool = True):
    """成功返回 OMML 元素，失败返回 None（不抛给调用方）。"""
    try:
        return latex_to_omml(latex, display=display)
    except Exception:
        return None


def clone_omml(element):
    return deepcopy(element)


def omml_available() -> bool:
    try:
        import latex2mathml

        return True
    except ImportError:
        return False
