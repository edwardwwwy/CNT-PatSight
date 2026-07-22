from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_ROOT = ROOT / "data/interim/extraction/A"
MASTER = ROOT / "data/raw/literature/metadata/literature_master.csv"
CASE_PATH = EXTRACTION_ROOT / "LIT_DB283D1C5235DA93.extraction.json"
OUT = ROOT / "output/pdf/CNT-LitSight_A-Class_Result_Report_WangYang.pdf"

W, H = A4
M = 42

NAVY = HexColor("#0B1F33")
INK = HexColor("#15293D")
SLATE = HexColor("#4B6073")
MUTED = HexColor("#75899B")
LINE = HexColor("#D9E3EA")
PAPER = HexColor("#F4F7F9")
WHITE = white
TEAL = HexColor("#00A6A6")
CYAN = HexColor("#39C6D4")
AMBER = HexColor("#F4B942")
CORAL = HexColor("#F06A5B")
BLUE = HexColor("#3973C9")
GREEN = HexColor("#58A96B")
PURPLE = HexColor("#7A66B7")

FONT = "YaHei"
FONT_BOLD = "YaHeiBold"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT, r"C:\Windows\Fonts\msyh.ttc"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\msyhbd.ttc"))


def tokens(text: str) -> list[str]:
    return re.findall(r"[\u3400-\u9fff]|[A-Za-z0-9_.:/%()+,;#]+|\s+|.", str(text))


def wrap_lines(text: str, font: str, size: float, width: float, max_lines: int | None = None) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in tokens(text):
        if token.isspace() and not current:
            continue
        candidate = current + token
        if current and pdfmetrics.stringWidth(candidate, font, size) > width:
            lines.append(current.rstrip())
            current = token.lstrip()
            if max_lines and len(lines) >= max_lines:
                break
        else:
            current = candidate
    if (not max_lines or len(lines) < max_lines) and current:
        lines.append(current.rstrip())
    if max_lines and len(lines) == max_lines:
        joined = "".join(lines)
        if len(joined) < len(str(text).replace(" ", "")):
            last = lines[-1]
            while last and pdfmetrics.stringWidth(last + "...", font, size) > width:
                last = last[:-1]
            lines[-1] = last.rstrip() + "..."
    return lines


def text_block(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = FONT,
    size: float = 9.2,
    color=INK,
    leading: float | None = None,
    max_lines: int | None = None,
) -> float:
    leading = leading or size * 1.45
    c.setFont(font, size)
    c.setFillColor(color)
    for line in wrap_lines(text, font, size, width, max_lines):
        c.drawString(x, y, line)
        y -= leading
    return y


def pill(c: canvas.Canvas, text: str, x: float, y: float, bg=TEAL, fg=WHITE, size=7.4, pad_x=7) -> float:
    tw = pdfmetrics.stringWidth(text, FONT_BOLD, size)
    w = tw + pad_x * 2
    c.setFillColor(bg)
    c.roundRect(x, y - 9, w, 18, 9, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont(FONT_BOLD, size)
    c.drawString(x + pad_x, y - 2.6, text)
    return w


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float, *, fill=WHITE, stroke=LINE, radius=9) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def page_base(c: canvas.Canvas, page_no: int, title: str, kicker: str) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, H - 7, W, 7, fill=1, stroke=0)
    c.setFont(FONT_BOLD, 7.4)
    c.setFillColor(TEAL)
    c.drawString(M, H - 31, kicker.upper())
    c.setFont(FONT_BOLD, 21)
    c.setFillColor(NAVY)
    c.drawString(M, H - 59, title)
    c.setStrokeColor(LINE)
    c.line(M, H - 72, W - M, H - 72)
    c.setFont(FONT, 6.8)
    c.setFillColor(MUTED)
    c.drawString(M, 22, "CNT-LitSight  当前成果展示  |  数据截止 2026-07-17")
    c.drawRightString(W - M, 22, f"{page_no:02d}")


def finish_page(c: canvas.Canvas) -> None:
    c.showPage()


def kpi(c: canvas.Canvas, x: float, y: float, w: float, h: float, value: str, label: str, note: str, accent=TEAL) -> None:
    card(c, x, y, w, h)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 5, w, 5, 2.5, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 25)
    c.drawString(x + 14, y + h - 37, value)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 8.8)
    c.drawString(x + 14, y + 28, label)
    text_block(c, note, x + 14, y + 14, w - 28, size=6.8, color=MUTED, leading=9, max_lines=1)


def section_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, index: str, title: str, body: str, accent=TEAL) -> None:
    card(c, x, y, w, h)
    c.setFillColor(accent)
    c.circle(x + 20, y + h - 22, 10, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 7.5)
    c.drawCentredString(x + 20, y + h - 25, index)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(x + 38, y + h - 25, title)
    text_block(c, body, x + 14, y + h - 45, w - 28, size=7.5, color=SLATE, leading=11.3, max_lines=5)


def hbar_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float, labels: list[str], values: list[int], colors: list[Color] | None = None) -> None:
    colors = colors or [TEAL] * len(values)
    maxv = max(values) if values else 1
    row_h = h / max(len(values), 1)
    label_w = min(100, w * 0.35)
    for i, (label, val) in enumerate(zip(labels, values)):
        yy = y + h - (i + 0.65) * row_h
        c.setFont(FONT, 7.3)
        c.setFillColor(SLATE)
        c.drawRightString(x + label_w - 8, yy - 2, label)
        bx = x + label_w
        bw = (w - label_w - 28) * val / maxv
        c.setFillColor(HexColor("#E7EEF2"))
        c.roundRect(bx, yy - 6, w - label_w - 28, 10, 5, fill=1, stroke=0)
        c.setFillColor(colors[i % len(colors)])
        c.roundRect(bx, yy - 6, max(bw, 3), 10, 5, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 7.2)
        c.drawRightString(x + w, yy - 2, str(val))


def stacked_bar(c: canvas.Canvas, x: float, y: float, w: float, h: float, items: list[tuple[str, int, Color]]) -> None:
    total = sum(v for _, v, _ in items)
    xx = x
    for label, val, color in items:
        ww = w * val / total
        c.setFillColor(color)
        c.rect(xx, y, ww, h, fill=1, stroke=0)
        if ww > 32:
            c.setFillColor(WHITE if color != AMBER else NAVY)
            c.setFont(FONT_BOLD, 7)
            c.drawCentredString(xx + ww / 2, y + h / 2 - 2.4, str(val))
        xx += ww


def year_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float, years: list[int]) -> None:
    counts = Counter(years)
    all_years = list(range(min(years), max(years) + 1))
    maxv = max(counts.values())
    plot_h = h - 28
    bw = w / len(all_years)
    for g in range(0, maxv + 1, 3):
        gy = y + 18 + plot_h * g / maxv
        c.setStrokeColor(LINE)
        c.setLineWidth(0.35)
        c.line(x, gy, x + w, gy)
    for i, yr in enumerate(all_years):
        val = counts.get(yr, 0)
        bh = plot_h * val / maxv
        c.setFillColor(TEAL if yr < 2020 else BLUE)
        c.roundRect(x + i * bw + 1, y + 18, max(2, bw - 2), bh, 1.5, fill=1, stroke=0)
        if yr % 4 == 0 or yr == all_years[-1]:
            c.setFont(FONT, 6.2)
            c.setFillColor(MUTED)
            c.drawCentredString(x + (i + 0.5) * bw, y + 5, str(yr))


def line_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float, rows: list[dict]) -> None:
    ymin, ymax = -100.0, 550.0
    px0, py0 = x + 36, y + 30
    pw, ph = w - 50, h - 48
    for value in [-100, 0, 100, 200, 300, 400, 500]:
        yy = py0 + (value - ymin) / (ymax - ymin) * ph
        c.setStrokeColor(LINE)
        c.setLineWidth(0.4)
        c.line(px0, yy, px0 + pw, yy)
        c.setFillColor(MUTED)
        c.setFont(FONT, 6.2)
        c.drawRightString(px0 - 6, yy - 2, str(value))
    method_colors = {"SOBOL": AMBER, "EI": TEAL, "OKG": BLUE}
    for method in ["SOBOL", "EI", "OKG"]:
        pts = []
        for i, row in enumerate(rows):
            if row["method"] == method:
                xx = px0 + i / (len(rows) - 1) * pw
                yy = py0 + (row["yield"] - ymin) / (ymax - ymin) * ph
                pts.append((xx, yy))
        c.setStrokeColor(method_colors[method])
        c.setLineWidth(1.4)
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1])
        for xx, yy in pts:
            c.setFillColor(method_colors[method])
            c.circle(xx, yy, 2.4, fill=1, stroke=0)
    for cut in [12.5, 36.5]:
        xx = px0 + cut / (len(rows) - 1) * pw
        c.setStrokeColor(MUTED)
        c.setDash(2, 2)
        c.line(xx, py0, xx, py0 + ph)
        c.setDash()
    for i, label in enumerate(["Sobol 初始", "EI", "OKG"]):
        start = [0, 13, 37][i]
        end = [12, 36, 60][i]
        xx = px0 + ((start + end) / 2) / 60 * pw
        c.setFont(FONT_BOLD, 7)
        c.setFillColor(list(method_colors.values())[i])
        c.drawCentredString(xx, y + 8, label)
    best_i = max(range(len(rows)), key=lambda i: rows[i]["yield"])
    best = rows[best_i]
    bx = px0 + best_i / (len(rows) - 1) * pw
    by = py0 + (best["yield"] - ymin) / (ymax - ymin) * ph
    c.setStrokeColor(CORAL)
    c.setLineWidth(1)
    c.line(bx, by, min(bx + 45, x + w - 52), min(by + 33, y + h - 12))
    c.setFillColor(CORAL)
    c.setFont(FONT_BOLD, 7.3)
    c.drawString(min(bx + 48, x + w - 70), min(by + 31, y + h - 15), "峰值 499%")
    c.setFillColor(SLATE)
    c.setFont(FONT, 6.5)
    c.drawString(x + 4, y + h - 10, "碳产率 (%)")


def scatter_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float, rows: list[dict]) -> None:
    xmin, xmax = 250, 900
    ymin, ymax = -100, 550
    px0, py0 = x + 38, y + 30
    pw, ph = w - 52, h - 50
    for value in [300, 500, 700, 900]:
        xx = px0 + (value - xmin) / (xmax - xmin) * pw
        c.setStrokeColor(LINE)
        c.line(xx, py0, xx, py0 + ph)
        c.setFont(FONT, 6)
        c.setFillColor(MUTED)
        c.drawCentredString(xx, y + 11, str(value))
    for value in [0, 200, 400]:
        yy = py0 + (value - ymin) / (ymax - ymin) * ph
        c.setStrokeColor(LINE)
        c.line(px0, yy, px0 + pw, yy)
        c.setFont(FONT, 6)
        c.setFillColor(MUTED)
        c.drawRightString(px0 - 5, yy - 2, str(value))
    colors = {"SOBOL": AMBER, "EI": TEAL, "OKG": BLUE}
    for row in rows:
        if not xmin <= row["calc"] <= xmax:
            continue
        xx = px0 + (row["calc"] - xmin) / (xmax - xmin) * pw
        yy = py0 + (row["yield"] - ymin) / (ymax - ymin) * ph
        rr = 2.2 + min(row["total"], 70) / 24
        c.setFillColor(colors[row["method"]])
        c.setStrokeColor(WHITE)
        c.setLineWidth(0.35)
        c.circle(xx, yy, rr, fill=1, stroke=1)
    c.setFillColor(SLATE)
    c.setFont(FONT, 6.5)
    c.drawCentredString(px0 + pw / 2, y + 1, "煅烧温度 (°C)")
    c.saveState()
    c.translate(x + 7, py0 + ph / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "碳产率 (%)")
    c.restoreState()


def parse_case() -> list[dict]:
    payload = json.loads(CASE_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(payload["tables"]["yield_quality"])
    rows: list[dict] = []
    pattern = re.compile(
        r"(SOBOL|EI|OKG) experimental point (\d+): total metal ([-\d.]+) wt%, Co ([-\d.]+) wt%, "
        r"Mo ([-\d.]+) wt%, drying ([-\d.]+) C, calcination ([-\d.]+) C; carbon yield ([-\d.]+)"
    )
    for text in df["secondary_result_summary"]:
        m = pattern.search(text)
        if not m:
            continue
        rows.append(
            {
                "method": m.group(1),
                "point": int(m.group(2)),
                "total": float(m.group(3)),
                "co": float(m.group(4)),
                "mo": float(m.group(5)),
                "dry": float(m.group(6)),
                "calc": float(m.group(7)),
                "yield": float(m.group(8)),
            }
        )
    if len(rows) != 61:
        raise RuntimeError(f"Expected 61 Bayesian optimization rows, got {len(rows)}")
    return rows


def source_sets(sm: pd.DataFrame, sr: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    return df.merge(sr[["run_id", "source_id"]], on="run_id", how="left")


def build() -> Path:
    register_fonts()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    packages = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(EXTRACTION_ROOT.glob("*.extraction.json"))]
    frame = lambda table: pd.DataFrame([row for package in packages for row in package["tables"][table]])
    sm = frame("source_master")
    sr = frame("source_run")
    cat = source_sets(sm, sr, frame("catalyst_system"))
    rpg = source_sets(sm, sr, frame("reactor_process_gas"))
    yq = source_sets(sm, sr, frame("yield_quality"))
    ev = frame("evidence_index")
    literature = pd.read_csv(MASTER, low_memory=False)
    case_rows = parse_case()

    years = pd.to_numeric(sm["publication_year"], errors="coerce").dropna().astype(int).tolist()
    run_counts = sr.groupby("source_id").size()
    evidence_counts = ev.groupby("source_id").size()
    metals = ["Fe", "Ni", "Co", "Mo", "Cu", "Au", "La", "Ru"]
    metal_counts: dict[str, int] = {}
    for metal in metals:
        mask = cat["active_metals"].str.contains(rf"(?<![A-Za-z]){metal}(?![a-z])", regex=True, na=False)
        metal_counts[metal] = int(cat.loc[mask, "source_id"].nunique())

    carbon_rules = [
        ("甲烷 / 沼气", ["methane", "ch4", "biogas", "natural gas"]),
        ("乙炔", ["acetylene", "c2h2"]),
        ("其他烃类", ["benzene", "toluene", "xylene", "propane", "butane", "lpg", "hexane", "ethylbenzene", "camphor"]),
        ("乙烯", ["ethylene", "c2h4"]),
        ("聚合物 / 生物质", ["plastic", "polyethylene", "polypropylene", "biomass", "waste", "wood", "corn", "bagasse", "tire", "tyre", "pet", "hdpe"]),
        ("醇类", ["ethanol", "methanol", "alcohol"]),
        ("CO / CO2", ["carbon monoxide", "carbon dioxide", "co2"]),
    ]
    carbon_counts: dict[str, int] = {}
    for label, needles in carbon_rules:
        mask = rpg["carbon_source"].str.lower().map(lambda s: any(n in s for n in needles))
        carbon_counts[label] = int(rpg.loc[mask, "source_id"].nunique())

    char_counts = {}
    for term in ["SEM", "TEM", "Raman", "XRD", "TGA", "BET"]:
        char_counts[term] = int(
            yq.groupby("source_id")["characterization_methods"].apply(lambda s: s.str.contains(term, case=False, regex=False).any()).sum()
        )

    c = canvas.Canvas(str(OUT), pagesize=A4, pageCompression=1)
    c.setTitle("CNT-LitSight 当前成果展示与 A 类文献数据分析")
    c.setAuthor("王扬")
    c.setCreator("GPT 5.6 Sol")
    c.setSubject("CNT 文献结构化提取、A 类66篇总结分析与项目资源说明")

    # 01 Cover
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 11, W, 11, fill=1, stroke=0)
    c.setStrokeColor(Color(1, 1, 1, alpha=0.12))
    for i in range(8):
        c.circle(W - 72, H - 125, 18 + i * 14, fill=0, stroke=1)
    c.setFillColor(CYAN)
    c.circle(W - 72, H - 125, 13, fill=1, stroke=0)
    pill(c, "CURRENT RESULTS / 2026", M, H - 95, bg=TEAL)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 31)
    c.drawString(M, H - 170, "CNT-LitSight")
    c.setFont(FONT_BOLD, 25)
    c.drawString(M, H - 210, "当前成果展示与 A 类文献数据分析")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 12)
    c.drawString(M, H - 242, "证据驱动的碳纳米管文献结构化提取")
    c.setStrokeColor(Color(0, 0.65, 0.65, alpha=0.7))
    c.setLineWidth(2)
    c.line(M, H - 274, W - M, H - 274)
    cover_items = [("66", "A 类成果集"), ("870", "实验运行"), ("6,037", "证据索引"), ("1,487", "全库元数据")]
    x0 = M
    for i, (value, label) in enumerate(cover_items):
        x = x0 + i * 128
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 19)
        c.drawString(x, H - 326, value)
        c.setFillColor(HexColor("#9EB5C5"))
        c.setFont(FONT, 7.4)
        c.drawString(x, H - 345, label)
    card(c, M, 92, W - 2 * M, 118, fill=HexColor("#102B43"), stroke=HexColor("#29475F"), radius=12)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 7.5)
    c.drawString(M + 18, 184, "REPORT CREDITS")
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 11)
    c.drawString(M + 18, 157, "制作人  王扬")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 9)
    c.drawString(M + 18, 133, "数据提取与报告辅助模型  GPT 5.6 Sol")
    c.drawString(M + 18, 111, "数据截止  2026年7月17日")
    c.setFillColor(HexColor("#6D879A"))
    c.setFont(FONT, 6.6)
    c.drawRightString(W - M, 40, "CNT-LITSIGHT / RESULT REPORT")
    finish_page(c)

    # 02 Executive summary
    page_base(c, 2, "一页看懂目前成果", "Executive snapshot")
    kpi(c, M, 674, 119, 96, "66", "A 类结构化论文", "统一合并后的八表成果集", TEAL)
    kpi(c, M + 129, 674, 119, 96, "870", "实验运行", "平均 13.2 条 / 篇", BLUE)
    kpi(c, M + 258, 674, 119, 96, "6,037", "证据索引", "93.5% 为高置信证据", GREEN)
    kpi(c, M + 387, 674, 119, 96, "1,686", "工艺阶段", "平均 1.94 阶段 / 运行", AMBER)
    card(c, M, 492, W - 2 * M, 158)
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(NAVY)
    c.drawString(M + 18, 622, "当前达到的结果")
    bullets = [
        "将 66 篇 A 类论文统一为来源、运行、催化剂、反应过程、产率质量、成本规模、证据与问题八张关联表。",
        "保留 870 条实验运行和 6,037 条字段级证据，语义审计未发现重复运行号、错误或警告。",
        "最佳展示案例完整覆盖 61 个贝叶斯优化实验点，可直接比较 Sobol、EI 与 OKG 三阶段结果。",
        "全库已积累 1,487 篇元数据，但全文权利、解析成本与独立证据复核决定了可扩展上限。",
    ]
    yy = 594
    for body in bullets:
        c.setFillColor(TEAL)
        c.circle(M + 23, yy + 2, 2.7, fill=1, stroke=0)
        yy = text_block(c, body, M + 34, yy + 6, W - 2 * M - 52, size=8.2, color=SLATE, leading=13, max_lines=2) - 5
    section_card(c, M, 330, 246, 138, "A", "成果边界", "66 篇是当前统一合并、可按同一八表结构分析的成果集。它不等于 208 篇候选全部可获得全文，也不等于所有数值都可跨论文直接比较。", TEAL)
    section_card(c, M + 263, 330, 246, 138, "B", "质量状态", "结构审计已通过；324 条审阅问题被显式保留，全部仍标记为待独立证据复核。这比把不确定信息隐藏为“完成”更可复核。", AMBER)
    card(c, M, 112, W - 2 * M, 194, fill=NAVY, stroke=NAVY)
    pill(c, "CORE MESSAGE", M + 18, 278, bg=TEAL)
    c.setFont(FONT_BOLD, 16)
    c.setFillColor(WHITE)
    c.drawString(M + 18, 242, "在无新增专项经费条件下，已完成一套可追溯、可扩展的高质量样板。")
    text_block(c, "下一阶段的瓶颈已从“能否抽取”转为“能否合法获得更多全文、承担大模型与计算消耗，并安排领域专家复核”。", M + 18, 211, W - 2 * M - 36, size=10, color=HexColor("#C4D4DE"), leading=16, max_lines=3)
    finish_page(c)

    # 03 Objective
    page_base(c, 3, "项目目标：把论文变成可计算资产", "Goal and value")
    card(c, M, 650, W - 2 * M, 118, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 18, 738, "核心问题")
    text_block(c, "CNT 文献中的催化剂配方、反应条件、产率和表征结果分散在正文、表格、图像与补充材料中，难以直接检索、比较或用于模型训练。", M + 18, 711, W - 2 * M - 36, size=11, font=FONT_BOLD, color=WHITE, leading=18, max_lines=3)
    cols = [
        ("01", "统一对象", "给每篇论文、每次实验运行和每条证据分配稳定标识，避免只做段落摘要。", TEAL),
        ("02", "还原实验", "拆分配方、载体、预处理、温度、气体、停留时间、产率与质量表征。", BLUE),
        ("03", "证据可追溯", "每个关键字段指回页码、表格、图像或正文片段，保留置信度和问题。", GREEN),
        ("04", "支持决策", "形成可过滤、可统计、可复核的数据资产，为路线筛选和后续建模提供输入。", AMBER),
    ]
    for i, item in enumerate(cols):
        section_card(c, M + (i % 2) * 263, 474 - (i // 2) * 154, 246, 132, *item)
    card(c, M, 174, W - 2 * M, 122)
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(M + 18, 268, "项目最终不是“论文收藏夹”，而是一条数据生产线")
    steps = ["文献", "全文", "实验运行", "八表数据", "证据链", "统计与模型"]
    sx = M + 22
    yy = 218
    for i, step in enumerate(steps):
        bw = 68
        c.setFillColor(TEAL if i in [0, 3, 5] else HexColor("#DCE6EC"))
        c.roundRect(sx, yy, bw, 30, 7, fill=1, stroke=0)
        c.setFillColor(WHITE if i in [0, 3, 5] else INK)
        c.setFont(FONT_BOLD, 7.4)
        c.drawCentredString(sx + bw / 2, yy + 10, step)
        if i < len(steps) - 1:
            c.setStrokeColor(MUTED)
            c.line(sx + bw + 4, yy + 15, sx + bw + 16, yy + 15)
            c.line(sx + bw + 12, yy + 18, sx + bw + 16, yy + 15)
            c.line(sx + bw + 12, yy + 12, sx + bw + 16, yy + 15)
        sx += 84
    finish_page(c)

    # 04 Workflow
    page_base(c, 4, "实现流程：从检索到证据闭环", "End-to-end workflow")
    workflow = [
        ("01", "元数据收集", "Crossref、开放索引与项目既有清单", TEAL),
        ("02", "筛选分级", "相关性、可提取性、优先级 A/B/C", BLUE),
        ("03", "合法全文获取", "开放获取、机构申请、已有本地来源", GREEN),
        ("04", "解析与对象识别", "正文、表格、图注、补充材料", AMBER),
        ("05", "运行级抽取", "一行实验对应一个 run_id", CORAL),
        ("06", "八表标准化", "保留原值，同时谨慎标准化", PURPLE),
        ("07", "证据与审计", "字段证据、问题日志、语义审计", TEAL),
    ]
    y = 682
    for idx, title, body, color in workflow:
        card(c, M + 32, y, W - 2 * M - 64, 66)
        c.setFillColor(color)
        c.circle(M + 58, y + 33, 16, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 8)
        c.drawCentredString(M + 58, y + 30, idx)
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 10)
        c.drawString(M + 88, y + 40, title)
        c.setFillColor(SLATE)
        c.setFont(FONT, 7.8)
        c.drawString(M + 88, y + 20, body)
        if idx != "07":
            c.setStrokeColor(LINE)
            c.setLineWidth(2)
            c.line(M + 58, y, M + 58, y - 13)
        y -= 78
    card(c, M, 104, W - 2 * M, 66, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 16, 147, "三条贯穿式质量规则")
    text_block(c, "不把推测写成报告值  |  不跨论文强行统一不同产率定义  |  不绕过付费墙或来源授权", M + 16, 125, W - 2 * M - 32, size=8.4, font=FONT_BOLD, color=INK, max_lines=1)
    finish_page(c)

    # 05 Eight-table model
    page_base(c, 5, "八表数据模型与质量门控", "Data architecture")
    tables = [
        ("01", "source_master", "论文来源、作者、年份、DOI、获取状态", "66 行", TEAL),
        ("02", "source_run", "实验运行边界、标签、摘要与置信度", "870 行", BLUE),
        ("03", "catalyst_system", "活性金属、载体、制备、物相与失活", "870 行", GREEN),
        ("04", "reactor_process_gas", "反应器、温度、时间、气体与流程阶段", "1,686 行", AMBER),
        ("05", "yield_quality", "原始产率定义、产品类型、形貌与表征", "870 行", CORAL),
        ("06", "cost_scale_review", "规模、连续运行、成本、安全与产业判断", "870 行", PURPLE),
        ("07", "evidence_index", "字段级来源定位、证据文本、置信度", "6,037 行", TEAL),
        ("08", "review_issue_log", "定义冲突、缺失项、图值近似与待复核问题", "324 行", AMBER),
    ]
    for i, (idx, name, desc, count, color) in enumerate(tables):
        col, row = i % 2, i // 2
        x, y = M + col * 263, 645 - row * 123
        card(c, x, y, 246, 102)
        c.setFillColor(color)
        c.roundRect(x + 12, y + 65, 28, 24, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 7)
        c.drawCentredString(x + 26, y + 73, idx)
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 9.4)
        c.drawString(x + 48, y + 76, name)
        c.setFillColor(color)
        c.setFont(FONT_BOLD, 8)
        c.drawRightString(x + 232, y + 76, count)
        text_block(c, desc, x + 14, y + 49, 218, size=7.5, color=SLATE, leading=11, max_lines=3)
    card(c, M, 113, W - 2 * M, 82, fill=NAVY, stroke=NAVY)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 10)
    c.drawString(M + 18, 164, "质量门控结果")
    c.setFillColor(HexColor("#BFD0DA"))
    c.setFont(FONT, 8.2)
    c.drawString(M + 18, 138, "61 个手工包语义审计：840 条运行，重复 run_id = 0，errors = 0，warnings = 0")
    finish_page(c)

    # 06 A-class landscape
    page_base(c, 6, "A 类任务全景：208 篇候选怎样落地", "Coverage and access")
    card(c, M, 566, W - 2 * M, 186)
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 724, "处理去向（互斥口径，合计 208）")
    labels = ["进入统一成果集", "已解析但不适合实验矩阵", "全文或解析不可用", "旧版异名包待统一"]
    values = [66, 28, 109, 5]
    hbar_chart(c, M + 14, 585, W - 2 * M - 28, 118, labels, values, [TEAL, AMBER, CORAL, PURPLE])
    c.setFont(FONT, 6.8)
    c.setFillColor(MUTED)
    c.drawString(M + 16, 576, "注：旧版异名包存在于批次命名空间外，未计入当前66篇统一合并集。")
    card(c, M, 354, W - 2 * M, 188)
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 514, "获取状态（候选全集）")
    access = [("验证可用", 94, TEAL), ("本地既有", 5, GREEN), ("付费墙", 100, CORAL), ("站点阻断", 8, AMBER), ("最终失败", 1, PURPLE)]
    stacked_bar(c, M + 16, 466, W - 2 * M - 32, 28, access)
    lx, ly = M + 16, 438
    for label, val, color in access:
        c.setFillColor(color)
        c.circle(lx + 4, ly + 3, 3.5, fill=1, stroke=0)
        c.setFont(FONT, 7)
        c.setFillColor(SLATE)
        c.drawString(lx + 12, ly, f"{label} {val}")
        lx += 96
    text_block(c, "100 篇候选明确处于付费墙后；8 篇受到站点访问阻断；1 篇在合法重试后仍失败。不可获得全文是当前覆盖率最大的结构性限制。", M + 16, 406, W - 2 * M - 32, size=8.3, color=SLATE, leading=13, max_lines=3)
    card(c, M, 118, W - 2 * M, 210, fill=HexColor("#E9F3F6"), stroke=HexColor("#C9DDE5"))
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 12)
    c.drawString(M + 18, 296, "为什么“66篇”比“抓到更多PDF”更有价值")
    reasons = [
        ("可比较", "共同字段和运行级边界"),
        ("可追溯", "每条关键数据有证据定位"),
        ("可复核", "问题和不确定性没有被隐藏"),
        ("可扩展", "新论文可沿同一八表规范进入"),
    ]
    for i, (head, body) in enumerate(reasons):
        x = M + 18 + i * 123
        c.setFillColor(TEAL if i % 2 == 0 else BLUE)
        c.roundRect(x, 188, 105, 74, 8, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawString(x + 10, 237, head)
        text_block(c, body, x + 10, 218, 84, size=6.8, color=WHITE, leading=10, max_lines=3)
    finish_page(c)

    # 07 Case introduction
    page_base(c, 7, "最佳展示案例：61点贝叶斯优化实验", "Best data showcase")
    card(c, M, 630, W - 2 * M, 123, fill=NAVY, stroke=NAVY)
    pill(c, "NANOMATERIALS 2023", M + 18, 724, bg=TEAL)
    text_block(c, "Bayesian Optimization of Wet-Impregnated Co-Mo/Al2O3 Catalyst for Maximizing the Yield of Carbon Nanotube Synthesis", M + 18, 694, W - 2 * M - 36, size=11.3, font=FONT_BOLD, color=WHITE, leading=16, max_lines=3)
    c.setFont(FONT, 7.3)
    c.setFillColor(HexColor("#AFC3D1"))
    c.drawString(M + 18, 646, "DOI 10.3390/nano14010075  |  数据对象 LIT_DB283D1C5235DA93")
    kpi(c, M, 507, 158, 98, "61", "完整实验点", "每点保留配方、热处理与产率", TEAL)
    kpi(c, M + 176, 507, 158, 98, "3", "设计阶段", "Sobol 13 / EI 24 / OKG 24", BLUE)
    kpi(c, M + 352, 507, 157, 98, "305", "证据条目", "每个实验点平均 5 条", GREEN)
    card(c, M, 313, W - 2 * M, 168)
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(M + 18, 453, "为什么选它作为展示案例")
    reasons = [
        "运行矩阵完整：61 个物理实验点全部进入结构化数据。",
        "变量清晰：总金属、Co、Mo、干燥温度、煅烧温度与碳产率可直接联动。",
        "阶段可比较：从初始空间探索到两种贝叶斯优化策略，变化趋势直观。",
        "证据密度高：表格与正文证据覆盖每个点，适合展示“论文到数据资产”的效果。",
    ]
    yy = 424
    for i, body in enumerate(reasons, 1):
        c.setFillColor(TEAL)
        c.setFont(FONT_BOLD, 7)
        c.drawString(M + 18, yy, f"0{i}")
        yy = text_block(c, body, M + 44, yy + 1, W - 2 * M - 62, size=8.2, color=SLATE, leading=12, max_lines=2) - 5
    card(c, M, 113, W - 2 * M, 174, fill=HexColor("#EAF2F5"), stroke=HexColor("#C9DDE5"))
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(M + 18, 260, "共同合成条件")
    conditions = [("反应器", "5.5 cm 内径、1.3 m 水平石英管"), ("温度", "690°C"), ("保持时间", "10 min"), ("气体", "C2H4 30 / H2 30 / N2 150 sccm")]
    for i, (a, b) in enumerate(conditions):
        x = M + 18 + i * 123
        c.setFillColor(WHITE)
        c.roundRect(x, 153, 108, 80, 8, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.setFont(FONT_BOLD, 7.3)
        c.drawString(x + 10, 211, a)
        text_block(c, b, x + 10, 190, 88, size=7.2, font=FONT_BOLD, color=INK, leading=10.5, max_lines=4)
    finish_page(c)

    # 08 Case line result
    page_base(c, 8, "61点结果：优化阶段显著抬升高产区间", "Optimization trajectory")
    card(c, M, 376, W - 2 * M, 376)
    line_chart(c, M + 14, 398, W - 2 * M - 28, 322, case_rows)
    card(c, M, 237, 246, 115, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 16, 326, "最高结果")
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 25)
    c.drawString(M + 16, 286, "499%")
    c.setFont(FONT, 7.6)
    c.setFillColor(HexColor("#BFD0DA"))
    c.drawString(M + 16, 258, "EI 第11点：46 wt% Co，0 wt% Mo")
    card(c, M + 263, 237, 246, 115)
    c.setFillColor(BLUE)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 279, 326, "相对初始阶段最好点")
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 25)
    c.drawString(M + 279, 286, "+104.5%")
    c.setFont(FONT, 7.6)
    c.setFillColor(SLATE)
    c.drawString(M + 279, 258, "Sobol 峰值 244% -> EI 峰值 499%")
    card(c, M, 112, W - 2 * M, 101, fill=HexColor("#FFF5E0"), stroke=HexColor("#F3D59B"))
    c.setFillColor(AMBER)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 16, 186, "解释边界")
    text_block(c, "图中百分数沿用原论文的碳产率定义；负值和超过100%的结果均按原表保留。该比较展示的是同一论文内部的优化轨迹，不应与采用其他产率分母的论文直接横向排序。", M + 16, 163, W - 2 * M - 32, size=8.1, color=SLATE, leading=12.3, max_lines=3)
    finish_page(c)

    # 09 Case scatter
    page_base(c, 9, "配方与热处理：高产点集中在可辨识窗口", "Design-space reading")
    card(c, M, 402, 334, 350)
    scatter_chart(c, M + 10, 420, 314, 304, case_rows)
    c.setFont(FONT, 6.7)
    legend_x = M + 24
    for label, color in [("Sobol", AMBER), ("EI", TEAL), ("OKG", BLUE)]:
        c.setFillColor(color)
        c.circle(legend_x, 735, 3.2, fill=1, stroke=0)
        c.setFillColor(SLATE)
        c.drawString(legend_x + 8, 732, label)
        legend_x += 63
    card(c, M + 350, 402, 159, 350, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 366, 724, "峰值条件")
    facts = [("总金属", "46 wt%"), ("Co", "46 wt%"), ("Mo", "0 wt%"), ("干燥", "139°C"), ("煅烧", "766°C"), ("碳产率", "499%")]
    yy = 688
    for label, value in facts:
        c.setFillColor(HexColor("#AFC3D1"))
        c.setFont(FONT, 7.3)
        c.drawString(M + 366, yy, label)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 10)
        c.drawRightString(W - M - 16, yy, value)
        c.setStrokeColor(HexColor("#29475F"))
        c.line(M + 366, yy - 12, W - M - 16, yy - 12)
        yy -= 44
    c.setFillColor(HexColor("#6F8797"))
    c.setFont(FONT, 6.5)
    c.drawString(M + 366, 425, "点大小近似表示总金属负载")
    insights = [
        ("01", "高产点主要出现在约 40-47 wt% 总金属、以 Co 为主的窗口。"),
        ("02", "EI 与 OKG 都找到接近 500% 的结果，说明高产区域具有一定重复可发现性。"),
        ("03", "变量相关性不等于机理因果；最优配方仍需独立复现实验与误差分析。"),
    ]
    for i, (idx, body) in enumerate(insights):
        section_card(c, M + i * 176, 205, 158, 164, idx, "数据解读", body, [TEAL, BLUE, AMBER][i])
    card(c, M, 112, W - 2 * M, 69, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    text_block(c, "这页体现结构化数据的核心价值：同一实验点的配方、热处理和产率不再散落在表格中，而可以联动筛选、可视化和建模。", M + 16, 153, W - 2 * M - 32, size=8.4, font=FONT_BOLD, color=INK, leading=13, max_lines=2)
    finish_page(c)

    # 10 Aggregate profile I
    page_base(c, 10, "66篇总体画像 I：时间与实验密度", "Portfolio profile")
    card(c, M, 461, W - 2 * M, 291)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 725, "发表年份分布")
    year_chart(c, M + 18, 485, W - 2 * M - 36, 212, years)
    c.setFont(FONT, 6.8)
    c.setFillColor(MUTED)
    c.drawString(M + 18, 473, "蓝色为 2020 年及以后；28/66 篇发表于 2020 年后。")
    kpi(c, M, 326, 158, 108, "2004-2026", "年份跨度", "中位发表年份 2019", TEAL)
    kpi(c, M + 176, 326, 158, 108, "13.2", "平均运行 / 篇", "中位数 7，范围 1-126", BLUE)
    kpi(c, M + 352, 326, 157, 108, "42", "运行数少于10的论文", "16篇为1-3条，26篇为4-9条", AMBER)
    card(c, M, 113, W - 2 * M, 188)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 274, "每篇论文的实验运行密度")
    bins = ["1-3 条", "4-9 条", "10-24 条", "25 条以上"]
    vals = [int((run_counts <= 3).sum()), int(((run_counts >= 4) & (run_counts <= 9)).sum()), int(((run_counts >= 10) & (run_counts <= 24)).sum()), int((run_counts >= 25).sum())]
    hbar_chart(c, M + 16, 137, W - 2 * M - 32, 116, bins, vals, [AMBER, TEAL, BLUE, PURPLE])
    c.setFont(FONT, 6.8)
    c.setFillColor(MUTED)
    c.drawString(M + 16, 125, "实验密度差异反映研究设计不同，不应把“运行多”直接解释为“论文质量高”。")
    finish_page(c)

    # 11 Aggregate profile II
    page_base(c, 11, "66篇总体画像 II：催化剂、碳源与工艺", "Catalyst and process")
    card(c, M, 451, 246, 301)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 724, "活性金属覆盖（论文数）")
    mlabels = [m for m in metals if metal_counts[m] > 0]
    hbar_chart(c, M + 12, 479, 220, 216, mlabels, [metal_counts[m] for m in mlabels], [TEAL, BLUE, CORAL, PURPLE, AMBER, GREEN, CYAN, NAVY])
    card(c, M + 263, 451, 246, 301)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 279, 724, "碳源覆盖（论文数，非互斥）")
    clabels = list(carbon_counts)
    hbar_chart(c, M + 269, 479, 226, 216, clabels, [carbon_counts[k] for k in clabels], [TEAL, BLUE, AMBER, PURPLE, GREEN, CORAL, NAVY])
    card(c, M, 287, W - 2 * M, 138, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 18, 397, "合成温度口径")
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 22)
    c.drawString(M + 18, 354, "775°C")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 7.4)
    c.drawString(M + 18, 331, "生长 / 反应型阶段温度中位数")
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 10)
    c.drawString(M + 173, 359, "四分位区间 650-850°C")
    text_block(c, "61 篇论文至少有一个可数值化温度设定；不同路线、反应器和阶段定义并不完全等价。", M + 173, 334, 318, size=7.4, color=HexColor("#BFD0DA"), leading=11, max_lines=3)
    card(c, M, 112, W - 2 * M, 149)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 233, "总体结论")
    text_block(c, "Fe 覆盖 43 篇，是样本中最常见活性金属；Ni 27 篇、Co 18 篇、Mo 12 篇。碳源路线更分散，甲烷/沼气覆盖 21 篇、乙炔 18 篇、其他烃类 14 篇、乙烯 12 篇。多种碳源可出现在同一论文，因此碳源计数不相加为66。", M + 16, 207, W - 2 * M - 32, size=8.4, color=SLATE, leading=13.2, max_lines=5)
    finish_page(c)

    # 12 Aggregate profile III
    page_base(c, 12, "66篇总体画像 III：结果覆盖与证据质量", "Evidence and readiness")
    kpi(c, M, 646, 158, 108, "47 / 66", "含数值型原始结果", "611 条运行含明确数字", TEAL)
    kpi(c, M + 176, 646, 158, 108, "35 / 66", "含标准化结果", "430 条运行有标准化数值", BLUE)
    kpi(c, M + 352, 646, 157, 108, "93.5%", "高置信证据", "5,642 条 high / 395 条 medium", GREEN)
    card(c, M, 425, 246, 193)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 16, 590, "常见表征覆盖（论文数）")
    labels = ["TEM", "SEM", "Raman", "XRD", "TGA", "BET"]
    hbar_chart(c, M + 12, 448, 220, 123, labels, [char_counts[x] for x in labels], [TEAL, BLUE, PURPLE, AMBER, CORAL, GREEN])
    card(c, M + 263, 425, 246, 193)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(M + 279, 590, "证据分布")
    c.setFillColor(TEAL)
    c.circle(M + 338, 510, 50, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.circle(M + 338, 510, 29, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 14)
    c.drawCentredString(M + 338, 506, "6,037")
    c.setFillColor(SLATE)
    c.setFont(FONT, 7.2)
    c.drawString(M + 405, 536, "平均 91.5 条 / 篇")
    c.drawString(M + 405, 512, "中位 51 条 / 篇")
    c.drawString(M + 405, 488, "范围 5-759 条")
    card(c, M, 235, W - 2 * M, 164, fill=HexColor("#FFF5E0"), stroke=HexColor("#F3D59B"))
    c.setFillColor(AMBER)
    c.setFont(FONT_BOLD, 9)
    c.drawString(M + 16, 370, "为什么仍有 324 条待复核问题")
    text_block(c, "高严重度 210 条、中等 113 条、低 1 条。问题主要来自关键数据缺失、产率定义歧义、图值读取、运行边界和来源自身限制。问题日志不是失败记录，而是对“哪些结论还需要领域专家判断”的显式清单。", M + 16, 343, W - 2 * M - 32, size=8.4, color=SLATE, leading=13.2, max_lines=5)
    card(c, M, 112, W - 2 * M, 99, fill=NAVY, stroke=NAVY)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 10)
    c.drawString(M + 16, 182, "读数原则")
    text_block(c, "原论文采用质量产率、催化剂归一化产率、碳转化率、森林高度、增长速率等不同指标。本报告优先保留原定义；只有口径明确时才标准化。", M + 16, 157, W - 2 * M - 32, size=8.2, color=HexColor("#BFD0DA"), leading=12.5, max_lines=3)
    finish_page(c)

    # 13-14 all 66 papers
    sm_list = sm.copy()
    sm_list["source_title"] = sm_list["source_title"].str.replace(r"<[^>]+>", "", regex=True)
    sm_list["run_count"] = sm_list["source_id"].map(run_counts).fillna(0).astype(int)
    sm_list["evidence_count"] = sm_list["source_id"].map(evidence_counts).fillna(0).astype(int)
    sm_list = sm_list.sort_values(["publication_year", "source_title"], ascending=[False, True]).reset_index(drop=True)
    for appendix_page, start in [(13, 0), (14, 33)]:
        page_base(c, appendix_page, f"A 类66篇分析对象清单 {1 if start == 0 else 2}/2", "Complete A-class corpus")
        subset = sm_list.iloc[start : start + 33]
        per_col = 17
        row_h = 35.2
        for local_i, (_, row) in enumerate(subset.iterrows()):
            col = local_i // per_col
            rr = local_i % per_col
            x = M + col * 263
            y = 724 - rr * row_h
            if rr % 2 == 0:
                c.setFillColor(WHITE)
                c.roundRect(x, y - 25, 246, 31, 4, fill=1, stroke=0)
            number = start + local_i + 1
            c.setFillColor(TEAL)
            c.setFont(FONT_BOLD, 6.9)
            c.drawString(x + 7, y - 1, f"{number:02d}  {int(row.publication_year)}")
            c.setFillColor(MUTED)
            c.setFont(FONT, 6.3)
            c.drawRightString(x + 239, y - 1, f"R{row.run_count} / E{row.evidence_count}")
            text_block(c, row.source_title, x + 7, y - 12, 232, size=6.3, color=INK, leading=8, max_lines=2)
        card(c, M, 75, W - 2 * M, 45, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
        c.setFont(FONT, 6.8)
        c.setFillColor(SLATE)
        c.drawString(M + 12, 93, "R = 实验运行数，E = 证据索引数。清单覆盖当前统一合并成果集的全部66篇论文。")
        finish_page(c)

    # 15 UCL and paywall
    page_base(c, 15, "UCL机构申请、开放获取与付费墙现实", "Access contribution")
    card(c, M, 603, W - 2 * M, 149, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 18, 724, "机构身份的实际贡献")
    text_block(c, "使用王扬的 UCL 机构身份与申请渠道，帮助核验合法全文路径、识别开放获取版本，并为需要作者或机构确认的开放论文申请提供可信学术背景。", M + 18, 694, W - 2 * M - 36, size=11, font=FONT_BOLD, color=WHITE, leading=18, max_lines=4)
    section_card(c, M, 425, 158, 148, "01", "合法路径核验", "优先检查 DOI、出版社开放页面、机构仓储、作者存档和项目已有本地全文。", TEAL)
    section_card(c, M + 176, 425, 158, 148, "02", "开放论文申请", "机构身份提升申请说明的可验证性，但不保证出版社全文自动开放。", BLUE)
    section_card(c, M + 352, 425, 157, 148, "03", "证据可信度", "保留来源链接与本地路径，报告只使用合法获得和可追溯的内容。", GREEN)
    card(c, M, 236, W - 2 * M, 163, fill=HexColor("#FFF0ED"), stroke=HexColor("#F2C7BF"))
    c.setFillColor(CORAL)
    c.setFont(FONT_BOLD, 10)
    c.drawString(M + 18, 370, "付费墙仍是最大限制")
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 30)
    c.drawString(M + 18, 320, "100 篇")
    c.setFillColor(SLATE)
    c.setFont(FONT, 8)
    c.drawString(M + 18, 293, "A 类候选被明确标记为 paywalled")
    text_block(c, "此外有 8 篇受站点阻断、1 篇合法重试后仍失败。UCL 机构申请和开放获取检索能扩大合法来源，但不能代替出版社订阅、文献许可或单篇购买。", M + 170, 337, 321, size=8.6, color=SLATE, leading=13.5, max_lines=5)
    card(c, M, 112, W - 2 * M, 100, fill=HexColor("#EAF2F5"), stroke=HexColor("#C9DDE5"))
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 9)
    c.drawString(M + 16, 184, "合规边界")
    text_block(c, "本项目没有绕过付费墙、验证码或站点限制。无法合法获取的全文被明确记录为不可用，而不是用摘要推断实验数据。", M + 16, 158, W - 2 * M - 32, size=8.4, color=SLATE, leading=13, max_lines=3)
    finish_page(c)

    # 16 Funding and conclusion
    page_base(c, 16, "从66到1,487：下一阶段为什么需要经费", "Scale-up requirements")
    card(c, M, 620, W - 2 * M, 132, fill=NAVY, stroke=NAVY)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 20)
    c.drawString(M + 18, 708, "66 篇统一成果集")
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 11)
    c.drawString(M + 224, 708, "->")
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 20)
    c.drawString(M + 264, 708, f"{len(literature):,} 篇全库元数据")
    text_block(c, "扩大覆盖面不仅是“多跑一次脚本”，而是全文权利、模型调用、解析计算与独立证据复核同时增长。", M + 18, 670, W - 2 * M - 36, size=9, color=HexColor("#BFD0DA"), leading=14, max_lines=2)
    needs = [
        ("01", "全文与许可", "出版社订阅、文献购买、馆际互借、合法开放版本发现。", CORAL),
        ("02", "大模型调用", "1,000+ 篇全文需要按长度、表格数和迭代轮次持续消耗 token / API 额度。", TEAL),
        ("03", "OCR与计算", "扫描PDF、复杂表格、图像读数、存储、批处理与失败重试。", BLUE),
        ("04", "专家复核", "产率定义、实验边界、催化剂化学与图值近似需要领域判断。", AMBER),
    ]
    for i, item in enumerate(needs):
        section_card(c, M + (i % 2) * 263, 449 - (i // 2) * 159, 246, 138, *item)
    card(c, M, 149, W - 2 * M, 118, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 18, 239, "当前阶段结论")
    text_block(c, "在无新增专项经费的情况下，项目已把合法可得来源、规则抽取、独立证据复核、证据链和语义审计组合到当前可达到的最好水平。进一步增加论文来源、突破付费全文覆盖，并开展超大规模结构化提取，需要持续经费与授权支持。", M + 18, 212, W - 2 * M - 36, size=9.1, font=FONT_BOLD, color=INK, leading=14.5, max_lines=5)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(M, 116, "制作人  王扬")
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.5)
    c.drawRightString(W - M, 116, "数据提取与报告辅助模型  GPT 5.6 Sol")
    c.save()
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
