from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from build_a_class_result_pdf import (
    AMBER,
    BASE,
    BLUE,
    CASE_BASE,
    CORAL,
    FONT,
    FONT_BOLD,
    GREEN,
    H,
    INK,
    M,
    MUTED,
    NAVY,
    PURPLE,
    SLATE,
    TEAL,
    W,
    card,
    finish_page,
    kpi,
    page_base,
    pill,
    register_fonts,
    section_card,
    text_block,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pdf/CNT-PatSight_A-Class_Result_Report_WangYang.pdf"
RUN_ID = "LIT_DB283D1C5235DA93_EI_11"


def clean(value) -> str:
    text = str(value).strip()
    text = re.sub(r"<[^>]+>", "", text)
    return text


def kv_panel(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    rows: list[tuple[str, str]],
    *,
    accent=TEAL,
    label_w: float = 92,
) -> None:
    card(c, x, y, w, h)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 5, w, 5, 2.5, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(x + 14, y + h - 28, title)
    available = h - 48
    row_h = available / max(len(rows), 1)
    for i, (label, value) in enumerate(rows):
        top = y + h - 47 - i * row_h
        if i:
            c.setStrokeColor(HexColor("#E4EBEF"))
            c.setLineWidth(0.4)
            c.line(x + 14, top + 9, x + w - 14, top + 9)
        c.setFillColor(MUTED)
        c.setFont(FONT_BOLD, 6.8)
        c.drawString(x + 14, top, label)
        text_block(c, clean(value), x + label_w, top + 1, w - label_w - 14, size=6.9, color=INK, leading=9.2, max_lines=2)


def narrative_panel(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    paragraphs: list[str],
    *,
    accent=TEAL,
    fill=white,
) -> None:
    card(c, x, y, w, h, fill=fill)
    c.setFillColor(accent)
    c.setFont(FONT_BOLD, 8)
    c.drawString(x + 16, y + h - 27, title)
    yy = y + h - 52
    for para in paragraphs:
        c.setFillColor(accent)
        c.circle(x + 20, yy + 3, 2.5, fill=1, stroke=0)
        yy = text_block(c, para, x + 31, yy + 7, w - 47, size=8.2, color=SLATE, leading=13.2, max_lines=4) - 8


def grid_table(
    c: canvas.Canvas,
    x: float,
    y: float,
    widths: list[float],
    row_h: float,
    headers: list[str],
    rows: list[list[str]],
    *,
    font_size: float = 6.9,
    header_fill=NAVY,
    max_lines: int = 2,
) -> None:
    total_w = sum(widths)
    total_h = row_h * (len(rows) + 1)
    card(c, x, y, total_w, total_h, radius=6)
    c.setFillColor(header_fill)
    c.roundRect(x, y + total_h - row_h, total_w, row_h, 6, fill=1, stroke=0)
    xx = x
    for j, head in enumerate(headers):
        c.setFillColor(white)
        c.setFont(FONT_BOLD, font_size)
        c.drawString(xx + 7, y + total_h - row_h + row_h / 2 - 2.5, head)
        xx += widths[j]
    for i, row in enumerate(rows):
        yy = y + total_h - row_h * (i + 2)
        c.setFillColor(white if i % 2 == 0 else HexColor("#F7F9FA"))
        c.rect(x, yy, total_w, row_h, fill=1, stroke=0)
        xx = x
        for j, val in enumerate(row):
            if j:
                c.setStrokeColor(HexColor("#E4EBEF"))
                c.setLineWidth(0.35)
                c.line(xx, yy, xx, yy + row_h)
            text_block(c, clean(val), xx + 7, yy + row_h - 12, widths[j] - 14, size=font_size, color=INK, leading=9.2, max_lines=max_lines)
            xx += widths[j]


def source_list_pages(c: canvas.Canvas, sm: pd.DataFrame, sr: pd.DataFrame, ev: pd.DataFrame) -> None:
    run_counts = sr.groupby("source_id").size()
    evidence_counts = ev.groupby("source_id").size()
    rows = sm.copy()
    rows["source_title"] = rows["source_title"].map(clean)
    rows["run_count"] = rows["source_id"].map(run_counts).fillna(0).astype(int)
    rows["evidence_count"] = rows["source_id"].map(evidence_counts).fillna(0).astype(int)
    rows = rows.sort_values(["publication_year", "source_title"], ascending=[False, True]).reset_index(drop=True)
    for page_no, start in [(14, 0), (15, 33)]:
        page_base(c, page_no, f"A 类66篇分析对象清单 {1 if start == 0 else 2}/2", "Complete A-class corpus")
        subset = rows.iloc[start : start + 33]
        per_col = 17
        row_h = 35.2
        for local_i, (_, row) in enumerate(subset.iterrows()):
            col = local_i // per_col
            rr = local_i % per_col
            x = M + col * 263
            yy = 724 - rr * row_h
            if rr % 2 == 0:
                c.setFillColor(white)
                c.roundRect(x, yy - 25, 246, 31, 4, fill=1, stroke=0)
            number = start + local_i + 1
            c.setFillColor(TEAL)
            c.setFont(FONT_BOLD, 6.9)
            c.drawString(x + 7, yy - 1, f"{number:02d}  {int(row.publication_year)}")
            c.setFillColor(MUTED)
            c.setFont(FONT, 6.3)
            c.drawRightString(x + 239, yy - 1, f"R{row.run_count} / E{row.evidence_count}")
            text_block(c, row.source_title, x + 7, yy - 12, 232, size=6.3, color=INK, leading=8, max_lines=2)
        card(c, M, 75, W - 2 * M, 45, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
        c.setFont(FONT, 6.8)
        c.setFillColor(SLATE)
        c.drawString(M + 12, 93, "R = 实验运行数，E = 证据索引数。清单覆盖当前统一合并成果集的全部66篇论文。")
        finish_page(c)


def build() -> Path:
    register_fonts()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    sm = pd.read_csv(BASE / "source_master.csv", keep_default_na=False)
    sr = pd.read_csv(BASE / "source_run.csv", keep_default_na=False)
    ev = pd.read_csv(BASE / "evidence_index.csv", keep_default_na=False)

    case = {name: pd.read_csv(CASE_BASE / f"{name}.csv", keep_default_na=False) for name in [
        "source_master", "source_run", "catalyst_system", "reactor_process_gas",
        "yield_quality", "cost_scale_review", "evidence_index", "review_issue_log"
    ]}
    case_source = case["source_master"].iloc[0]
    case_run = case["source_run"].query("run_id == @RUN_ID").iloc[0]
    case_cat = case["catalyst_system"].query("run_id == @RUN_ID").iloc[0]
    case_proc = case["reactor_process_gas"].query("run_id == @RUN_ID").iloc[0]
    case_yield = case["yield_quality"].query("run_id == @RUN_ID").iloc[0]
    case_cost = case["cost_scale_review"].query("run_id == @RUN_ID").iloc[0]
    case_ev = case["evidence_index"].query("run_id == @RUN_ID")
    c = canvas.Canvas(str(OUT), pagesize=A4, pageCompression=1)
    c.setTitle("CNT-PatSight 当前成果展示与 A 类文献数据说明")
    c.setAuthor("王扬")
    c.setCreator("GPT 5.6 Sol")
    c.setSubject("CNT 文献结构化提取、A 类66篇总结与八表示例")

    # 01 Cover
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 11, W, 11, fill=1, stroke=0)
    pill(c, "CURRENT RESULTS / 2026", M, H - 95, bg=TEAL)
    c.setFillColor(white)
    c.setFont(FONT_BOLD, 31)
    c.drawString(M, H - 170, "CNT-PatSight")
    c.setFont(FONT_BOLD, 25)
    c.drawString(M, H - 210, "当前成果展示与 A 类文献数据说明")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 11)
    c.drawString(M, H - 244, "从合法文献来源到运行级八表数据与证据链")
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.line(M, H - 278, W - M, H - 278)
    text_block(c, "本报告说明项目目标、合法文献来源、结构化实现流程和当前 A 类66篇成果，并使用一篇完整论文展示八张关联表如何保存来源、实验条件、结果与证据。", M, H - 322, W - 2 * M, size=10.2, color=HexColor("#C5D4DE"), leading=17, max_lines=6)
    values = [("1,487", "全库元数据"), ("208", "A 类候选"), ("66", "统一八表论文"), ("870", "实验运行")]
    for i, (value, label) in enumerate(values):
        x = M + i * 128
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 19)
        c.drawString(x, 370, value)
        c.setFillColor(HexColor("#9EB5C5"))
        c.setFont(FONT, 7.4)
        c.drawString(x, 351, label)
    card(c, M, 92, W - 2 * M, 118, fill=HexColor("#102B43"), stroke=HexColor("#29475F"), radius=12)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 7.5)
    c.drawString(M + 18, 184, "REPORT CREDITS")
    c.setFillColor(white)
    c.setFont(FONT_BOLD, 11)
    c.drawString(M + 18, 157, "制作人  王扬")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 9)
    c.drawString(M + 18, 133, "数据提取与报告辅助模型  GPT 5.6 Sol")
    c.drawString(M + 18, 111, "数据截止  2026年7月17日")
    finish_page(c)

    # 02 Status
    page_base(c, 2, "当前成果与报告范围", "Current status")
    kpi(c, M, 674, 119, 96, "1,487", "文献元数据", "当前全库主表的唯一来源数", TEAL)
    kpi(c, M + 129, 674, 119, 96, "208", "A 类候选", "优先处理的高相关候选", BLUE)
    kpi(c, M + 258, 674, 119, 96, "66", "八表成果集", "同一结构下可统一分析", GREEN)
    kpi(c, M + 387, 674, 119, 96, "870", "实验运行", "每条运行具有稳定 run_id", AMBER)
    narrative_panel(c, M, 450, W - 2 * M, 194, "本报告展示什么", [
        "项目的目标不是简单保存 PDF 或生成论文摘要，而是把可复现实验条件拆分成运行级记录，并把每个关键字段连接回原文证据。",
        "当前统一成果集包含 66 篇 A 类论文、870 条实验运行、1,686 条反应过程阶段和 6,037 条证据记录。",
        "报告使用一篇包含 61 个物理实验点的完整论文包，展示实际字段、八表关系和证据连接方式。",
    ], accent=TEAL)
    narrative_panel(c, M, 238, W - 2 * M, 186, "当前成果形成的能力", [
        "66 篇论文已经进入统一八表目录，可按照同一数据结构读取来源、实验运行、催化剂、过程、结果与证据。",
        "870 条实验运行均具有稳定 run_id，可进一步连接 1,686 条过程阶段和 6,037 条字段级证据。",
        "数据可以按照活性金属、载体、碳源、温度、反应器、产品类型和表征方法进行组合筛选。",
    ], accent=BLUE)
    card(c, M, 112, W - 2 * M, 100, fill=NAVY, stroke=NAVY)
    text_block(c, "报告通过过程说明、字段展示和论文清单，完整呈现数据从文献来源到运行级记录与字段证据的形成过程。", M + 18, 176, W - 2 * M - 36, size=10, font=FONT_BOLD, color=white, leading=16, max_lines=3)
    finish_page(c)

    # 03 Goals
    page_base(c, 3, "项目目标与实际用途", "Goal and use")
    narrative_panel(c, M, 563, W - 2 * M, 189, "项目背景与目标", [
        "CNT 合成研究包含催化剂制备、反应器配置、气体条件、产率、形貌和表征等多层信息，项目将这些内容转化为可以计算和检索的结构化记录。",
        "每篇论文进一步拆分为配方、温度、时间点和对照条件对应的实验运行，使每组条件和结果保持清晰关联。",
        "source_id、run_id、catalyst_id、process_stage_id、product_id 和 evidence_id 共同构成稳定的数据关系。",
    ], accent=TEAL)
    left = [
        ("01", "形成可检索数据", "可按金属、载体、碳源、温度、反应器、产率定义和表征方法筛选。", TEAL),
        ("02", "保留实验上下文", "不只保存一个产率数字，同时保留制备、气体、时间、产品和原始定义。", BLUE),
    ]
    right = [
        ("03", "支持证据核验", "每个关键记录都有来源定位和置信度，便于快速回到原文核验。", GREEN),
        ("04", "为后续建模准备", "结构统一后可以开展统计、相似实验检索并构建模型输入。", AMBER),
    ]
    for i, item in enumerate(left):
        section_card(c, M, 386 - i * 151, 246, 132, *item)
    for i, item in enumerate(right):
        section_card(c, M + 263, 386 - i * 151, 246, 132, *item)
    card(c, M, 112, W - 2 * M, 96, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    text_block(c, "最终交付物不是一组孤立结论，而是一套能够继续补充、纠错、筛选和复核的文献数据基础设施。", M + 18, 171, W - 2 * M - 36, size=9.5, font=FONT_BOLD, color=INK, leading=15, max_lines=3)
    finish_page(c)

    # 04 Sources
    page_base(c, 4, "合法文献来源是怎样获得的", "Literature acquisition")
    narrative_panel(c, M, 566, W - 2 * M, 186, "来源顺序", [
        "首先通过 DOI、出版社页面和开放元数据索引确认论文身份、题名、作者、年份与正式链接。",
        "全文优先使用出版社明确开放的 HTML/PDF、机构知识库、作者合法存档版本，以及项目已有且来源可说明的本地文件。",
        "在公开版本和机构申请路径核验中，也使用王扬的 UCL 机构身份进行合法来源申请或确认。",
    ], accent=TEAL)
    steps = [
        ("01", "身份核验", "核对 DOI、题名、年份、期刊和来源链接，避免同名或版本混淆。", TEAL),
        ("02", "开放版本发现", "检查出版社开放页面、机构仓储、作者版本和补充材料。", BLUE),
        ("03", "文件验证", "确认下载内容为真实 PDF/HTML，并完成格式签名、正文内容和来源一致性验证。", GREEN),
        ("04", "本地登记", "记录文件路径、获取状态、来源对象和解析状态，后续不覆盖原始文件。", AMBER),
    ]
    for i, item in enumerate(steps):
        section_card(c, M + (i % 2) * 263, 394 - (i // 2) * 150, 246, 130, *item)
    card(c, M, 112, W - 2 * M, 100, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 16, 184, "来源管理结果")
    text_block(c, "文献身份、正式链接、全文路径、文件状态和解析记录被统一登记，原始 PDF/HTML 与文本衍生文件分层保存，便于后续检索和证据回溯。", M + 16, 159, W - 2 * M - 32, size=8.5, color=SLATE, leading=13.3, max_lines=3)
    finish_page(c)

    # 05 Workflow
    page_base(c, 5, "从文献到八表数据的实现流程", "Implementation workflow")
    workflow = [
        ("01", "元数据收集与去重", "把不同数据库返回的 DOI、题名和作者记录归并为唯一 source_id，保留版本来源与归并记录。"),
        ("02", "相关性筛选与 A/B/C 分级", "根据 CNT 生产相关性、实验信息可能性和全文需求确定优先级，A 类优先进入正式抽取。"),
        ("03", "全文获取、验证与解析", "验证 PDF/HTML 文件类型，提取正文、表格、图注和补充材料，并记录解析质量。"),
        ("04", "实验运行拆分", "识别论文中的配方、条件、对照、时间点和样品编号，为每个实验对象建立 run_id。"),
        ("05", "八表字段填充", "分别保存来源、运行、催化剂、过程、产品、规模成本、证据和质量复核；原始表述与标准化字段并存。"),
        ("06", "证据链接与审计", "关键字段连接到页码、表号、图号或正文片段，随后检查主外键、标识唯一性和语义一致性。"),
    ]
    y = 661
    colors = [TEAL, BLUE, GREEN, AMBER, CORAL, PURPLE]
    for i, (idx, title, body) in enumerate(workflow):
        card(c, M, y, W - 2 * M, 82)
        c.setFillColor(colors[i])
        c.circle(M + 27, y + 41, 14, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 7.5)
        c.drawCentredString(M + 27, y + 38, idx)
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 9.6)
        c.drawString(M + 52, y + 54, title)
        text_block(c, body, M + 52, y + 34, W - 2 * M - 68, size=7.6, color=SLATE, leading=11.2, max_lines=3)
        y -= 93
    card(c, M, 105, W - 2 * M, 70, fill=NAVY, stroke=NAVY)
    text_block(c, "贯穿全流程的原则：原始表述优先、字段口径清晰、运行标识稳定、表间关系一致、关键数据均可定位到来源证据。", M + 16, 147, W - 2 * M - 32, size=8.3, font=FONT_BOLD, color=white, leading=13, max_lines=3)
    finish_page(c)

    # 06 Eight tables
    page_base(c, 6, "八表结构与每张表的职责", "Eight-table model")
    rows = [
        ["01", "source_master", "论文级", "题名、作者、期刊、DOI、全文路径、筛选与审核状态", "66"],
        ["02", "source_run", "运行级", "实验边界、运行标签、数据类型、摘要、置信度", "870"],
        ["03", "catalyst_system", "运行级", "活性金属、载体、前驱体、制备、干燥、煅烧、还原", "870"],
        ["04", "reactor_process_gas", "阶段级", "反应器、规模、温度、时间、压力、碳源与各气体流量", "1,686"],
        ["05", "yield_quality", "运行级", "原始产率、标准化说明、CNT 类型、形貌、尺寸、纯度与表征", "870"],
        ["06", "cost_scale_review", "运行级", "规模、连续运行、成本信息、安全、排放、复现与产业评述", "870"],
        ["07", "evidence_index", "证据级", "目标表与字段、来源位置、证据文本、值状态、置信度", "6,037"],
        ["08", "review_issue_log", "复核级", "字段复核、证据补充、审核流转、处理结果与版本记录", "-"],
    ]
    grid_table(c, M, 337, [30, 105, 52, 269, 55], 43, ["序号", "表名", "粒度", "主要内容", "行数"], rows, font_size=6.8, max_lines=3)
    narrative_panel(c, M, 154, W - 2 * M, 150, "为什么需要拆成八张表", [
        "一个实验运行可以有多个过程阶段和多条证据，直接放在单张宽表中会重复论文信息，也难以表达一对多关系。",
        "表间通过稳定标识连接。来源信息只保存一次，运行级条件可以扩展，证据和质量复核记录也能独立增加而不改写原始数据。",
    ], accent=TEAL)
    finish_page(c)

    # 07 QA
    page_base(c, 7, "质量控制与证据体系", "Quality assurance")
    kpi(c, M, 665, 158, 100, "61", "语义审计包", "手工结构化包全部完成审计", TEAL)
    kpi(c, M + 176, 665, 158, 100, "840", "已审计运行", "运行标识与表间关联一致", GREEN)
    kpi(c, M + 352, 665, 157, 100, "6,037", "证据索引", "关键字段连接来源定位", BLUE)
    narrative_panel(c, M, 442, W - 2 * M, 194, "证据如何保存", [
        "evidence_index 不只保存一个链接，还保存目标表、目标记录、目标字段、证据类型、值状态、来源章节、定位信息和证据摘要。",
        "原文直接报告、单位换算、图中读数和计算值采用不同 value_status，使不同类型的数据在后续使用中保持清晰。",
        "当前 6,037 条证据中，5,642 条标记为 high，395 条标记为 medium；所有关键数字均连接来源定位。",
    ], accent=TEAL)
    narrative_panel(c, M, 229, W - 2 * M, 185, "质量复核机制", [
        "review_issue_log 与 evidence_index 共同形成质量复核链，记录目标表、目标字段、相关证据、审核流转与处理结果。",
        "复核记录和业务数据相互独立，既能保持主表简洁，也便于后续补充证据、更新审核状态并保存版本轨迹。",
    ], accent=AMBER, fill=HexColor("#FFF5E0"))
    card(c, M, 112, W - 2 * M, 91, fill=NAVY, stroke=NAVY)
    text_block(c, "结构审计、证据索引和质量复核共同保证数据关系清晰、来源可查、更新过程可追踪。", M + 18, 166, W - 2 * M - 36, size=10, font=FONT_BOLD, color=white, leading=16, max_lines=2)
    finish_page(c)

    # 08 Coverage
    page_base(c, 8, "A 类成果的数据覆盖", "Dataset coverage")
    coverage = [
        ["A 类候选元数据", "208", "高相关优先级论文的题录与来源信息"],
        ["统一成果集", "66", "采用同一八表规范组织的论文数据包"],
        ["实验运行", "870", "具有稳定 run_id 的条件与结果记录"],
        ["过程阶段", "1,686", "反应器、温度、时间、压力与气体阶段"],
        ["证据索引", "6,037", "连接目标表、目标字段和原文位置的证据记录"],
    ]
    grid_table(c, M, 476, [175, 60, 276], 48, ["数据层级", "数量", "覆盖内容"], coverage, font_size=7.2, max_lines=3)
    dimensions = [
        ["来源身份", "题名、作者、年份、期刊、DOI、全文路径和来源数据库"],
        ["催化剂体系", "活性金属、载体、前驱体、配比、制备、干燥、煅烧和还原"],
        ["反应过程", "反应器、规模、温度、时间、压力、碳源及气体流量"],
        ["产品结果", "原始产率、标准化说明、CNT 类型、形貌、尺寸、纯度和表征"],
        ["规模与复现", "连续运行、规模证据、成本线索、安全、复现价值与应用信息"],
        ["证据与审核", "来源位置、证据文本、值状态、置信度和质量复核轨迹"],
    ]
    grid_table(c, M, 196, [145, 366], 40, ["覆盖维度", "字段内容"], dimensions, font_size=7.1, max_lines=2)
    card(c, M, 112, W - 2 * M, 60, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    text_block(c, "成果集已经形成从论文身份、实验条件、产品结果到字段证据的完整关联，可直接用于筛选、对比、复现准备和后续建模。", M + 16, 147, W - 2 * M - 32, size=8.5, font=FONT_BOLD, color=INK, leading=13, max_lines=2)
    finish_page(c)

    # 09 Example 1-2
    page_base(c, 9, "完整论文示例：八表展示 1/4", "Eight-table example")
    card(c, M, 642, W - 2 * M, 110, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 7.6)
    c.drawString(M + 16, 724, "示例论文")
    text_block(c, case_source.source_title, M + 16, 699, W - 2 * M - 32, size=10, font=FONT_BOLD, color=white, leading=14.5, max_lines=3)
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 6.8)
    c.drawString(M + 16, 655, "以下页面仅展示八表字段。论文包含61个实验运行；为便于阅读，运行级表统一展示 EI point 11。")
    kv_panel(c, M, 365, W - 2 * M, 247, "表1  source_master  |  论文级来源记录", [
        ("source_id", case_source.source_id), ("题名", case_source.source_title),
        ("作者", case_source.authors_or_assignee), ("年份 / 期刊", f"{case_source.publication_year} / {case_source.publication_venue}"),
        ("DOI", case_source.doi_or_patent_no), ("本地全文", case_source.local_file_path),
        ("全文状态", case_source.pdf_status), ("抽取范围", case_source.source_section_scope),
        ("来源语言", case_source.source_language),
    ], accent=TEAL, label_w=100)
    kv_panel(c, M, 112, W - 2 * M, 225, "表2  source_run  |  运行级边界记录", [
        ("run_id", case_run.run_id), ("run_label", case_run.run_label),
        ("source_id", case_run.source_id), ("data_type", case_run.data_type), ("target_track", case_run.target_track),
        ("抽取置信度", case_run.extraction_confidence), ("运行摘要", case_run.run_summary),
        ("相关类别", case_run.relevance_class),
    ], accent=BLUE, label_w=100)
    finish_page(c)

    # 10 Example 3-4
    page_base(c, 10, "完整论文示例：八表展示 2/4", "Eight-table example")
    kv_panel(c, M, 420, W - 2 * M, 332, "表3  catalyst_system  |  催化剂与制备记录", [
        ("run_id", case_cat.run_id), ("catalyst_id", case_cat.catalyst_id),
        ("催化剂标签", case_cat.catalyst_label), ("活性金属", case_cat.active_metals),
        ("载体", case_cat.support_material), ("金属配比原文", case_cat.metal_ratio_original),
        ("前驱体", case_cat.precursor_summary), ("制备方法", case_cat.preparation_method),
        ("制备详情", case_cat.preparation_detail), ("干燥条件", case_cat.drying_condition),
        ("煅烧条件", case_cat.calcination_condition), ("制备后状态", case_cat.post_preparation_condition),
    ], accent=GREEN, label_w=105)
    kv_panel(c, M, 112, W - 2 * M, 280, "表4  reactor_process_gas  |  反应器、过程与气体记录", [
        ("process_stage_id", case_proc.process_stage_id), ("阶段类型", case_proc.stage_type),
        ("反应器", case_proc.reactor_type), ("规模", case_proc.scale_level),
        ("温度 / 时间", f"{case_proc.temperature_setpoint_C} °C / {case_proc.holding_time_min} min"),
        ("压力", f"{case_proc.pressure_original} / {case_proc.pressure_kPa} kPa"),
        ("碳源", f"{case_proc.carbon_source} / {case_proc.carbon_source_flow_original}"),
        ("还原气", f"{case_proc.reducing_gas} / {case_proc.reducing_gas_flow_original}"),
        ("惰性气", f"{case_proc.inert_gas} / {case_proc.inert_gas_flow_original}"),
        ("阶段顺序", case_proc.stage_order),
    ], accent=AMBER, label_w=105)
    finish_page(c)

    # 11 Example 5-6
    page_base(c, 11, "完整论文示例：八表展示 3/4", "Eight-table example")
    kv_panel(c, M, 417, W - 2 * M, 335, "表5  yield_quality  |  产率、产品和表征记录", [
        ("product_id", case_yield.product_id), ("主要结果类型", case_yield.primary_yield_metric),
        ("原始产率", case_yield.yield_original), ("原始定义", case_yield.yield_definition_original),
        ("标准化说明", case_yield.yield_standardization_note), ("结果单位", case_yield.yield_unit_standardized),
        ("产品类型", case_yield.CNT_type_confirmed),
        ("结果摘要", case_yield.secondary_result_summary), ("类型证据", case_yield.CNT_type_evidence),
        ("表征方法", case_yield.characterization_methods),
    ], accent=CORAL, label_w=105)
    kv_panel(c, M, 112, W - 2 * M, 277, "表6  cost_scale_review  |  规模、成本线索与复现记录", [
        ("run_id", case_cost.run_id), ("展示规模", case_cost.scale_level_demonstrated),
        ("规模证据", case_cost.scale_evidence_summary), ("成本驱动", case_cost.cost_driver_summary.split(";")[0]),
        ("安全信息", case_cost.safety_risk), ("记录范围", "规模证据、主要投入、安全信息与复现价值"),
        ("复现价值", case_cost.reproduction_value), ("复现优先级", case_cost.reproduction_priority),
        ("运行类型", case_run.data_type),
    ], accent=PURPLE, label_w=105)
    finish_page(c)

    # 12 Example 7-8
    page_base(c, 12, "完整论文示例：八表展示 4/4", "Eight-table example")
    evidence_rows = []
    for _, row in case_ev.iterrows():
        evidence_rows.append([row.evidence_id.replace("EVD_LIT_DB283D1C5235DA93_EI_11_", ""), row.target_table, row.source_section, row.value_status, row.confidence])
    grid_table(c, M, 506, [58, 145, 140, 95, 73], 43, ["证据", "目标表", "来源位置", "值状态", "置信度"], evidence_rows, font_size=6.7, max_lines=2)
    narrative_panel(c, M, 344, W - 2 * M, 134, "表7  evidence_index  |  字段级证据", [
        f"该运行共有 {len(case_ev)} 条 record-level 证据，分别连接 source_run、catalyst_system、reactor_process_gas、yield_quality 和 cost_scale_review。",
        "证据类型为 manual_fulltext_transcription，来源位置为 Figure 4，来源对象指向本地验证过的 HTML 全文。",
    ], accent=TEAL)
    kv_panel(c, M, 112, W - 2 * M, 204, "表8  review_issue_log  |  质量复核表结构", [
        ("记录主键", "issue_id"), ("关联标识", "source_id / run_id / target_record_id"),
        ("目标位置", "target_table / target_field"),
        ("证据关联", "evidence_ids"), ("审核流程", "severity / review_status / reviewer / reviewed_at"),
        ("处理字段", "resolution / notes"),
        ("表的作用", "保存字段复核、证据补充、审核流转与版本轨迹"),
    ], accent=AMBER, label_w=105)
    finish_page(c)

    # 13 Summary of 66
    page_base(c, 13, "A 类66篇的汇总说明", "Aggregate summary")
    summary_rows = [
        ["时间范围", "2004-2026", "中位发表年份为2019；2020年及以后28篇"],
        ["实验运行", "870", "平均13.2条/篇，中位7条，单篇范围1-126条"],
        ["过程阶段", "1,686", "用于表示预处理、生长、吹扫、后处理等一对多过程"],
        ["主要金属覆盖", "Fe 43 / Ni 27 / Co 18 / Mo 12", "按论文去重计数，一篇可包含多种金属"],
        ["主要碳源覆盖", "甲烷/沼气21 / 乙炔18 / 其他烃14 / 乙烯12", "按论文去重且类别非互斥"],
        ["数值型原始结果", "47篇", "611条运行的 yield_original 中包含明确数字"],
        ["标准化结果", "35篇", "430条运行具有非空 yield_value_standardized"],
        ["常见表征", "TEM 58 / SEM 56 / Raman 53 / XRD 38", "按论文是否报告相应方法计数"],
        ["证据记录", "6,037", "平均91.5条/篇，中位51条/篇"],
        ["高置信证据", "93.5%", "5,642条证据的 confidence 为 high"],
    ]
    grid_table(c, M, 271, [128, 168, 215], 44, ["统计项目", "当前结果", "口径说明"], summary_rows, font_size=6.8, max_lines=3)
    narrative_panel(c, M, 112, W - 2 * M, 128, "汇总数据可以支持的工作", [
        "按照金属、载体、碳源、温度、反应器和产品类型筛选相似实验，并查看对应的原始结果定义。",
        "结合运行级条件和证据定位开展路线对比、复现准备、文献回溯与模型数据准备。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    finish_page(c)

    source_list_pages(c, sm, sr, ev)

    # 16 Value and next uses
    page_base(c, 16, "成果价值与后续应用", "Value and next uses")
    applications = [
        ("01", "催化剂路线检索", "按 Fe、Ni、Co、Mo 等活性金属及载体、前驱体和制备方法组合筛选论文与实验运行。", CORAL),
        ("02", "工艺条件对比", "联动查看反应器、温度、时间、压力、碳源和各气体流量，形成同类条件集合。", TEAL),
        ("03", "结果与表征回溯", "从产率、CNT 类型、形貌和表征方法直接连接到原文位置和证据摘要。", BLUE),
        ("04", "复现实验准备", "按单条 run_id 汇总催化剂制备、反应过程、产品结果和规模信息，形成实验参考记录。", AMBER),
        ("05", "统计与模型输入", "使用统一字段构建统计数据集、相似实验检索、特征工程和模型输入。", PURPLE),
        ("06", "持续扩展成果集", "新增论文可以沿用同一八表规范进入主数据集，并自动参与筛选、汇总和证据查询。", GREEN),
    ]
    for i, item in enumerate(applications):
        section_card(c, M + (i % 2) * 263, 620 - (i // 2) * 169, 246, 148, *item)
    card(c, M, 112, W - 2 * M, 142, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 18, 226, "当前成果")
    text_block(c, "A 类66篇成果集已经形成从论文身份、实验运行、催化剂与反应过程，到产品结果、规模信息和字段证据的完整数据链。统一八表结构使文献内容可以被检索、组合、统计和持续扩展。", M + 18, 198, W - 2 * M - 36, size=9.2, font=FONT_BOLD, color=white, leading=15, max_lines=5)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(M, 83, "制作人  王扬")
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.5)
    c.drawRightString(W - M, 83, "数据提取与报告辅助模型  GPT 5.6 Sol")
    c.save()
    return OUT


if __name__ == "__main__":
    print(build())
