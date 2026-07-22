from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from build_a_class_result_pdf import (
    AMBER,
    BLUE,
    CORAL,
    FONT,
    FONT_BOLD,
    GREEN,
    H,
    INK,
    M,
    MASTER,
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
    text_block,
)
from build_a_class_result_pdf_v2 import grid_table, kv_panel, narrative_panel


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "output/delivery/CNT-LitSight_结构化数据交付_2026-07-17/01_A类66篇_合并八表"
OUT = ROOT / "output/pdf/CNT-LitSight_Client_Report_WangYang.pdf"


def info_box(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    number: str,
    title: str,
    body: str,
    *,
    accent=TEAL,
) -> None:
    card(c, x, y, w, h)
    c.setFillColor(accent)
    c.circle(x + 25, y + h - 27, 12, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FONT_BOLD, 8)
    c.drawCentredString(x + 25, y + h - 30, number)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 10)
    c.drawString(x + 48, y + h - 31, title)
    text_block(c, body, x + 15, y + h - 55, w - 30, size=7.7, color=SLATE, leading=12.3, max_lines=6)


def source_note(c: canvas.Canvas, lines: list[str], y: float = 63) -> None:
    c.setFillColor(MUTED)
    c.setFont(FONT, 5.7)
    yy = y
    for line in lines:
        yy = text_block(c, line, M, yy, W - 2 * M, size=5.7, color=MUTED, leading=8, max_lines=2) - 2


def build() -> Path:
    register_fonts()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    sm = pd.read_csv(BASE / "source_master.csv", keep_default_na=False)
    sr = pd.read_csv(BASE / "source_run.csv", keep_default_na=False)
    proc = pd.read_csv(BASE / "reactor_process_gas.csv", keep_default_na=False)
    evidence = pd.read_csv(BASE / "evidence_index.csv", keep_default_na=False)
    literature = pd.read_csv(MASTER, low_memory=False)

    indexed_count = len(literature)
    structured_papers = len(sm)
    remaining_papers = indexed_count - structured_papers
    run_count = len(sr)
    stage_count = len(proc)
    evidence_count = len(evidence)

    c = canvas.Canvas(str(OUT), pagesize=A4, pageCompression=1)
    c.setTitle("CNT-LitSight 碳纳米管文献数据工程阶段成果与扩展测算")
    c.setAuthor("王扬")
    c.setCreator("GPT 5.6 Sol")
    c.setSubject("项目成果、核验案例、API成本与文献资源扩展说明")

    # 01 Cover
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 11, W, 11, fill=1, stroke=0)
    pill(c, "CLIENT PROGRESS REPORT / 2026", M, H - 94, bg=TEAL)
    c.setFillColor(white)
    c.setFont(FONT_BOLD, 31)
    c.drawString(M, H - 166, "CNT-LitSight")
    c.setFont(FONT_BOLD, 23)
    c.drawString(M, H - 208, "碳纳米管文献数据工程")
    c.drawString(M, H - 244, "阶段成果与扩展测算")
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.line(M, H - 278, W - M, H - 278)
    text_block(
        c,
        "本报告说明当前已经交付了什么、数据如何形成、如何核验，以及将检索范围扩大到千篇级文献时可能发生的模型调用和全文获取成本。",
        M,
        H - 320,
        W - 2 * M,
        size=10.1,
        color=HexColor("#C6D5DF"),
        leading=17,
        max_lines=5,
    )
    stats = [
        (f"{indexed_count:,}", "已建立索引的文献记录"),
        ("208", "与CNT制备直接相关的优先候选"),
        (f"{structured_papers}", "已完成首轮全文结构化的论文"),
        (f"{run_count:,}", "已拆分的独立实验条件"),
    ]
    for i, (value, label) in enumerate(stats):
        x = M + i * 128
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 18)
        c.drawString(x, 363, value)
        text_block(c, label, x, 343, 112, size=6.7, color=HexColor("#9FB6C6"), leading=9, max_lines=2)
    card(c, M, 207, W - 2 * M, 94, fill=HexColor("#102B43"), stroke=HexColor("#29475F"), radius=10)
    text_block(
        c,
        "与普通文献综述不同，本项目把论文中的催化剂配方、制备步骤、反应器、温度、气体、产率、CNT结构表征和原文证据转换为可以检索、比较和继续建模的数据记录。",
        M + 17,
        267,
        W - 2 * M - 34,
        size=8.5,
        color=HexColor("#D6E1E8"),
        leading=13.5,
        max_lines=4,
    )
    card(c, M, 83, W - 2 * M, 91, fill=HexColor("#102B43"), stroke=HexColor("#29475F"), radius=10)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 7.4)
    c.drawString(M + 17, 145, "REPORT CREDITS")
    c.setFillColor(white)
    c.setFont(FONT_BOLD, 9)
    c.drawString(M + 17, 121, "制作人  王扬")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 7.1)
    c.drawString(M + 17, 100, "数据整理与报告辅助模型  GPT 5.6 Sol  |  数据截止 2026-07-17")
    c.showPage()

    # 02 Project overview
    page_base(c, 2, "项目基本信息与总体目标", "Project overview")
    grid_table(c, M, 430, [105, 406], 37, ["基本信息", "内容"], [
        ["项目名称", "CNT-LitSight 碳纳米管文献数据工程"],
        ["数据库名称", "CNT-LitSight 碳纳米管文献实验数据库"],
        ["负责人", "王扬"],
        ["本周工作时间", "2026年7月13日周一至7月17日周五"],
        ["工作地点", "CNT研发室"],
        ["数据库位置", "王扬本地电脑"],
        ["当前进度", f"已索引{indexed_count:,}条来源；筛选208篇高相关论文；首批{structured_papers}篇已拆分为{run_count:,}个实验条件。"],
    ], font_size=7.3, max_lines=3)
    narrative_panel(c, M, 285, W - 2 * M, 120, "为什么建设这个数据库", [
        "CNT制备参数分散在不同论文的正文、表格、图和补充材料中，仅依靠摘要无法比较催化剂、工艺和真实实验结果。",
        "项目通过统一实验边界、单位、原始定义和证据位置，把分散文献转化为可检索、可比较、可继续积累的数据。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    card(c, M, 130, W - 2 * M, 130, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(M + 17, 231, "后续核心目标")
    text_block(c, "数据收集不是终点。项目希望在样本数量、字段一致性和证据质量达到要求后，将催化剂组成、制备参数、反应条件与产率、CNT类型、直径、壁数及质量表征组成机器学习数据，用于预测实验结果、识别更有潜力的工艺窗口，并减少无效试验。", M + 17, 207, W - 2 * M - 34, size=8.4, color=white, leading=14, max_lines=6)
    finish_page(c)

    # 03 Why, objectives and progress
    page_base(c, 3, "建库必要性、当前完成度与目标衔接", "Purpose and current progress")
    narrative_panel(c, M, 610, W - 2 * M, 126, "从文献阅读到结果预测之间缺少什么", [
        "论文提供了大量实验结果，但格式、单位、对象层级和产率定义不一致；机器学习无法直接使用未经整理的PDF和自然语言段落。",
        "数据库需要先把每个实验条件转化为清晰的输入与输出，并保留证据和重复次数，才能形成可信的训练样本。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    grid_table(c, M, 300, [128, 92, 291], 48, ["当前阶段", "完成情况", "对后续预测的意义"], [
        ["文献索引", f"{indexed_count:,}条", "确定研究范围，并保留题名、DOI、年份和来源。"],
        ["高相关筛选", "208篇", "形成优先全文池，减少无关文献进入训练数据。"],
        ["全文结构化", f"{structured_papers}篇 / 31.7%", "建立首批可比较样本和字段规则。"],
        ["独立实验条件", f"{run_count:,}个", "形成催化剂与工艺输入、产率和质量输出的样本单位。"],
        ["字段证据", f"{evidence_count:,}条", "支持质量筛选、错误修订和训练数据审计。"],
    ], font_size=7.1, max_lines=3)
    narrative_panel(c, M, 150, W - 2 * M, 118, "当前进度应如何理解", [
        "目前已经证明从全文到实验条件级数据的流程能够运行，但66篇仍是首批样本，不代表全部论文已经完成正式核验。",
        "下一阶段的重点是扩大高质量样本覆盖、统一预测目标字段，并保证不同论文之间的数据定义可以合理比较。",
    ], accent=BLUE, fill=HexColor("#EEF4FC"))
    card(c, M, 82, W - 2 * M, 44, fill=NAVY, stroke=NAVY)
    text_block(c, "逻辑链：合法全文 -> 实验级结构化 -> 字段证据与质量控制 -> 机器学习样本 -> 预测与实验决策支持。", M + 14, 109, W - 2 * M - 28, size=7.6, color=white, leading=11.5, max_lines=2)
    finish_page(c)

    # 04 Workflow and legal access
    page_base(c, 4, "从合法文献来源到可核验数据", "Acquisition and implementation")
    narrative_panel(c, M, 545, W - 2 * M, 191, "机构资源与合规访问", [
        "我先通过DOI、出版社页面和开放元数据核对论文身份、正式卷期、在线发表日期与版本关系，避免将预印本、在线日期和正式出版年份混为一谈。",
        "需要机构资格验证时，我提供英国伦敦大学学院（University College London, UCL）的institution证明与相应机构访问权限，在出版社许可和机构授权范围内检索或申请文献。",
        "全文优先来自出版社授权HTML/PDF、开放获取平台、机构知识库、作者合法存档和补充材料。无法由现有授权覆盖的内容不会绕过付费墙，而是进入购买、文献传递或后续授权评估。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    process_rows = [
        ["01", "身份与版本核验", "核对DOI、题名、作者、正式出版年、在线日期、卷期和文章号。"],
        ["02", "合法全文发现", "依次检查出版社、开放获取、机构知识库、作者存档、补充材料和机构授权。"],
        ["03", "实验边界识别", "区分论文级通用方法、独立实验条件、重复实验和代表性表征样本。"],
        ["04", "结构化抽取", "拆分催化剂、过程、气体、产率、产品质量、规模信息和证据位置。"],
        ["05", "字段级证据", "报告值、未报告值和工程推断分别标记，并连接到表格、章节或图。"],
        ["06", "复核与发布", "检查单位、跨表关联、来源位置和版本记录后，再形成对外数据包。"],
    ]
    grid_table(c, M, 208, [35, 112, 364], 42, ["步骤", "阶段", "处理内容"], process_rows, font_size=7.2, max_lines=3)
    card(c, M, 112, W - 2 * M, 68, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    text_block(c, "该流程的核心不是单纯获得PDF，而是同时保存文献身份、合法来源路径、实验边界和字段证据，使每一条数据都能回到可核验的原始位置。", M + 16, 154, W - 2 * M - 32, size=8.0, color=INK, leading=13, max_lines=4)
    finish_page(c)

    # 05 Deliverable explanation
    page_base(c, 5, "数据库中一篇论文如何被组织", "Data organization")
    text_block(c, "每篇论文会被转换为八类相互关联的信息。它们共同回答三个问题：实验输入是什么、实验结果是什么、每个值能否回到原文。", M, 735, W - 2 * M, size=8.6, color=SLATE, leading=14, max_lines=3)
    grid_table(c, M, 165, [35, 116, 234, 126], 57, ["序号", "信息层级", "记录内容", "对预测的作用"], [
        ["01", "论文身份与版本", "题名、作者、DOI、正式卷期、在线日期、全文来源和整理范围。", "避免重复样本并保留来源。"],
        ["02", "独立实验条件", "将每个实验设计点单独记录，并保存实验标签、重复次数和数据类型。", "确定训练样本边界。"],
        ["03", "催化剂与制备", "活性金属、载体、前驱体、配比、制备方法、干燥和煅烧条件。", "构成催化剂输入特征。"],
        ["04", "反应器与气体过程", "反应器、催化剂用量、温度、时间、压力状态、气体组成与流量。", "构成工艺输入特征。"],
        ["05", "产率与材料质量", "产率数值、误差、定义以及CNT类型、直径、壁数、Raman和TGA。", "构成主要预测目标。"],
        ["06", "规模与复现信息", "实验规模、主要投入、连续性和可复现条件；报告值与推断值分开。", "限定预测的适用范围。"],
        ["07", "字段来源证据", "每个关键值连接到章节、表格、图或补充材料，并标记值状态。", "用于样本质量筛选。"],
        ["08", "复核与修订记录", "保存问题、处理结论、复核人和版本轨迹。", "避免错误进入训练数据。"],
    ], font_size=6.7, max_lines=4)
    text_block(c, "这些信息通过论文标识和实验标识连接，因此既能按论文查看，也能按催化剂、工艺条件或结果筛选，并在需要时返回原文证据。", M, 133, W - 2 * M, size=8.0, color=SLATE, leading=13, max_lines=3)
    finish_page(c)

    # 06 First corpus analysis
    page_base(c, 6, "首批全文结构化成果：覆盖范围与研究特征", "First structured corpus")
    narrative_panel(c, M, 630, W - 2 * M, 105, "这66篇论文代表什么", [
        "它们是从当前1,487条文献索引和208篇高相关候选中，优先完成全文级实验数据整理的第一批论文，覆盖2004-2026年的CNT制备、催化剂开发和工艺研究。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    kpi(c, M, 494, 118, 108, f"{structured_papers}", "全文论文", "第一批高相关样本", TEAL)
    kpi(c, M + 131, 494, 118, 108, f"{run_count:,}", "实验条件", "按设计点拆分", BLUE)
    kpi(c, M + 262, 494, 118, 108, f"{stage_count:,}", "过程阶段", "制备、反应与处理", GREEN)
    kpi(c, M + 393, 494, 118, 108, f"{evidence_count:,}", "证据连接", "指向章节、表格或图", AMBER)
    grid_table(c, M, 252, [123, 388], 44, ["分析维度", "首批样本呈现的特征"], [
        ["研究时间跨度", "覆盖2004-2026年；近年研究集中在自动优化、废塑料转化、低碳原料和高性能阵列。"],
        ["催化剂路线", "Fe相关体系出现最频繁，Ni、Co及Fe-Co、Co-Mo等组合构成主要比较路径。"],
        ["碳源与工艺", "C2H4、C2H2和CH4是最常见的明确碳源；研究主体仍以CVD/CCVD和实验室批次条件为主。"],
        ["可比较变量", "金属负载、载体、前驱体、温度、时间、气体流量、反应器、产率和CNT结构均可形成筛选条件。"],
        ["可形成的数据产品", "可继续构建催化剂路线对比、工艺窗口、复现实验清单、证据回溯和监督学习数据集。"],
    ], font_size=7.3, max_lines=3)
    card(c, M, 132, W - 2 * M, 88, fill=NAVY, stroke=NAVY)
    text_block(c, "首批样本的价值在于验证了从全文到实验条件级数据的完整流程。它不是全部文献的终点，而是可用于统一字段、校准规则和测算扩展成本的基线数据集。", M + 16, 184, W - 2 * M - 32, size=8.0, color=white, leading=13, max_lines=4)
    finish_page(c)

    # 07 Verified example 1/2
    page_base(c, 7, "核验案例：一篇论文如何变成可计算数据 1/2", "Verified example")
    card(c, M, 645, W - 2 * M, 108, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 7.4)
    c.drawString(M + 16, 724, "Nanomaterials 2024, 14(1), 75  |  DOI 10.3390/nano14010075")
    text_block(c, "Bayesian Optimization of Wet-Impregnated Co-Mo/Al2O3 Catalyst for Maximizing the Yield of Carbon Nanotube Synthesis", M + 16, 698, W - 2 * M - 32, size=9.4, color=white, font=FONT_BOLD, leading=13.5, max_lines=3)
    text_block(c, "正式出版年份为2024；在线发表日期为2023-12-26。以下展示经正文、方法和Table 1-3重新核验后的结构化方式。", M + 16, 661, W - 2 * M - 32, size=7.4, color=HexColor("#BFD0DB"), leading=11, max_lines=2)
    kv_panel(c, M, 425, 249, 190, "论文与实验层级", [
        ("实验设计", "13个Sobol初始点 + 24个EI点 + 24个OKG点"),
        ("条件点总数", "61 experimental design points"),
        ("重复次数", "每个条件点4次重复实验"),
        ("实际执行", "共244次实验执行"),
        ("公开结果", "论文公开每个条件点的均值和离散度"),
    ], accent=TEAL, label_w=82)
    kv_panel(c, M + 263, 425, 248, 190, "EI point 11 催化剂", [
        ("实际标签", "46 wt% Co/Al2O3"),
        ("金属组成", "Co 46 wt%; Mo 0 wt%"),
        ("Co前驱体", "cobalt nitrate hexahydrate"),
        ("Mo前驱体", "该运行点未使用"),
        ("制备", "湿浸渍；139°C干燥；766°C空气中煅烧2 h"),
    ], accent=GREEN, label_w=80)
    kv_panel(c, M, 180, 249, 218, "载体与反应规模", [
        ("载体", "Al2O3, 99%"),
        ("粒径", "32-63 μm"),
        ("比表面积", "200 m2/g"),
        ("催化剂质量", "0.01 g per run"),
        ("反应器", "水平石英管炉，内径5.5 cm，长度1.3 m"),
        ("规模判断", "lab batch，依据0.01 g用量"),
    ], accent=BLUE, label_w=82)
    kv_panel(c, M + 263, 180, 248, 218, "反应条件", [
        ("温度", "690°C"),
        ("时间", "10 min"),
        ("C2H4", "30 sccm"),
        ("H2", "30 sccm"),
        ("N2", "150 sccm"),
        ("压力", "not reported"),
    ], accent=AMBER, label_w=80)
    card(c, M, 108, W - 2 * M, 48, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    text_block(c, "该例通过论文级方法、单个实验点和重复执行的分层记录，使EI point 11只保留实际使用的Co前驱体；当Mo=0时，不记录Mo前驱体。", M + 15, 137, W - 2 * M - 30, size=7.4, color=INK, leading=11.5, max_lines=3)
    finish_page(c)

    # 08 Verified example 2/2
    page_base(c, 8, "核验案例：结果、材料质量与证据边界 2/2", "Verified example")
    kv_panel(c, M, 505, 249, 247, "产率结果", [
        ("指标", "carbon yield"),
        ("数值", "499.0"),
        ("离散度", "21.1，论文未进一步命名误差类型"),
        ("单位", "percent"),
        ("重复次数", "4"),
        ("计算定义", "(Mf - Mcat) / Mcat x 100"),
        ("证据", "Table 2, row 11"),
    ], accent=CORAL, label_w=82)
    kv_panel(c, M + 263, 505, 248, 247, "代表性CNT表征", [
        ("适用范围", "representative sample；具体run_id未解决"),
        ("形貌", "randomly entangled"),
        ("类型", "MWCNT"),
        ("直径", "15.75 ± 5.59 nm"),
        ("壁数", "14 ± 6"),
        ("Raman", "IG/ID 1.23；532 nm"),
        ("TGA", "最终残留<17 wt%；空气；900°C；10°C/min"),
    ], accent=PURPLE, label_w=80)
    grid_table(c, M, 260, [125, 386], 44, ["数据内容", "正确证据位置与记录方式"], [
        ["EI point 11参数与产率", "Table 2, row 11；保存数值、离散度、单位和4次重复实验。"],
        ["催化剂通用制备方法", "Section 2.1；运行点只保留实际使用的Co前驱体，Mo前驱体不绑定。"],
        ["反应器、温度、时间与气体", "Section 2.2；催化剂用量0.01 g；压力记为not reported。"],
        ["CNT形貌、直径、壁数、Raman和TGA", "Section 3.4 / Figure 6；标为代表性样本，暂不强行绑定EI point 11。"],
        ["成本、安全与复现判断", "属于domain inference时单独标记inferred和medium，不伪装成论文直接报告。"],
    ], font_size=7.0, max_lines=3)
    card(c, M, 138, W - 2 * M, 88, fill=NAVY, stroke=NAVY)
    text_block(c, "一个可交付样本不仅要数值正确，还要明确数值属于哪一级对象、原文在哪里、是否由作者直接报告，以及是否可以和其他实验点进行机器比较。", M + 16, 189, W - 2 * M - 32, size=8.1, color=white, leading=13, max_lines=4)
    finish_page(c)

    # 09 Value and prediction goals
    page_base(c, 9, "这些数据最终要解决什么问题", "Use and prediction goals")
    narrative_panel(c, M, 630, W - 2 * M, 105, "数据收集的意义", [
        "近期价值是把不同论文的催化剂、工艺和结果放在同一结构下比较，并能回到原文证据。",
        "长期价值是形成足够可靠的实验输入与输出，使机器学习能够学习条件与结果之间的关系。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    grid_table(c, M, 430, [135, 376], 44, ["当前可以支持的工作", "具体作用"], [
        ["催化剂和工艺路线比较", "按金属、载体、前驱体、温度、时间和气体条件检索可比较实验。"],
        ["实验复现与证据回溯", "汇总单个实验点的制备、反应、结果和未报告信息，并返回原文位置。"],
        ["机器学习样本准备", "将输入变量、结果、重复次数和证据质量整理为可以筛选的训练数据。"],
    ], font_size=7.2, max_lines=3)
    grid_table(c, M, 162, [132, 379], 43, ["未来预测目标", "希望由数据支持的判断"], [
        ["产率预测", "根据催化剂组成、制备参数和反应条件预测carbon yield或productivity。"],
        ["CNT结构与质量预测", "预测CNT类型、直径、壁数、形貌、Raman指标和TGA残留等结果。"],
        ["高潜力条件识别", "识别更可能获得高产率或较好材料质量的催化剂与工艺窗口。"],
        ["结果可信度判断", "判断输入条件是否超出已有数据范围，并提示预测不确定性。"],
        ["实验优先级支持", "优先验证更有信息价值的条件，减少重复检索和低价值试验。"],
    ], font_size=7.0, max_lines=3)
    card(c, M, 88, W - 2 * M, 50, fill=NAVY, stroke=NAVY)
    text_block(c, "项目是否成功，最终应由数据能否支持可验证的预测和实验决策来判断，而不只是收集了多少篇论文。", M + 15, 118, W - 2 * M - 30, size=7.8, color=white, leading=12, max_lines=2)
    finish_page(c)

    # 10 API cost
    page_base(c, 10, "扩大到千篇级全文抽取时的模型API成本", "Model API cost estimate")
    narrative_panel(c, M, 650, W - 2 * M, 85, "测算口径", [
        f"以当前索引{indexed_count:,}篇、已完成首轮结构化{structured_papers}篇计算，剩余约{remaining_papers:,}篇。每篇每轮按40,000输入token和8,000输出token估算；生产预算包含两轮抽取/校验及30%重试余量。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    grid_table(c, M, 422, [125, 116, 116, 154], 42, ["当前官方单价", "输入 / 1M token", "输出 / 1M token", "适合的角色"], [
        ["DeepSeek V4 Flash", "$0.14", "$0.28", "大批量首轮抽取和格式化"],
        ["DeepSeek V4 Pro", "$0.435", "$0.87", "较复杂的复核与推理"],
        ["GPT-5.6 Terra", "$2.50", "$15.00", "平衡质量与成本的批量处理"],
        ["GPT-5.6 Sol", "$5.00", "$30.00", "复杂样本、证据复核和最终审计"],
    ], font_size=6.9, max_lines=3)
    grid_table(c, M, 224, [151, 116, 116, 128], 46, ["处理方案", "估算API费", "约合人民币", "适用说明"], [
        ["DeepSeek两轮 + GPT Sol复核20%", "约$190", "约¥1,370", "推荐：批量抽取与重点复核分层"],
        ["GPT Terra两轮 + GPT Sol复核20%", "约$975", "约¥7,020", "更统一的模型体系和输出风格"],
        ["GPT Sol全量两轮", "约$1,626", "约¥11,710", "高质量路线，成本明显提高"],
    ], font_size=7.0, max_lines=3)
    card(c, M, 105, W - 2 * M, 95, fill=NAVY, stroke=NAVY)
    text_block(c, "API费用由输入长度、推理token、输出字段数、失败重试和二次证据核验共同决定。以上为可比口径，不包含OCR、向量检索、服务器存储、独立专家复核和文献版权费用；人民币按1 USD = 7.2 CNY作内部测算。", M + 16, 164, W - 2 * M - 32, size=7.7, color=white, leading=12.5, max_lines=5)
    source_note(c, [
        "价格来源（访问日期2026-07-17）：OpenAI Models - https://developers.openai.com/api/docs/models",
        "DeepSeek Models & Pricing - https://api-docs.deepseek.com/quick_start/pricing/",
    ], y=82)
    finish_page(c)

    # 11 Paywall cost
    page_base(c, 11, "扩大合法全文来源时可能发生的付费墙成本", "Full-text access cost estimate")
    narrative_panel(c, M, 617, W - 2 * M, 118, "为什么这项成本与API费用不同", [
        "模型费用解决的是取得全文后的结构化处理；付费墙费用解决的是对未被开放获取或现有机构授权覆盖的论文取得合法全文。两类费用不能相互替代。",
        "实际流程会先使用UCL机构访问、开放获取、机构知识库、作者存档和补充材料，只对剩余无法合法免费取得的论文评估单篇购买、文献传递或批量授权。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    card(c, M, 515, W - 2 * M, 72, fill=NAVY, stroke=NAVY)
    text_block(c, "公开价格基准：Elsevier ScienceDirect显示，多数单篇文章或章节为$31.50，部分标题为$19.95-$39.95；其他出版社会按期刊和文章单独显示价格，批量或机构方案通常需要询价。", M + 16, 559, W - 2 * M - 32, size=8.0, color=white, leading=13, max_lines=4)
    grid_table(c, M, 324, [121, 110, 139, 141], 47, ["剩余付费墙比例", "可能需购买篇数", "按$19.95-$39.95", "约合人民币"], [
        ["10%", "约142篇", "$2,800-$5,700", "约¥20,000-¥41,000"],
        ["25%", "约355篇", "$7,100-$14,200", "约¥51,000-¥102,000"],
        ["40%", "约568篇", "$11,300-$22,700", "约¥82,000-¥163,000"],
    ], font_size=7.0, max_lines=3)
    grid_table(c, M, 98, [135, 376], 42, ["降低全文成本的顺序", "执行方式"], [
        ["1. 现有机构授权", "先核对UCL可访问范围、年份和平台许可。"],
        ["2. 合法开放版本", "检查出版社开放页、PMC、机构知识库、作者存档和补充材料。"],
        ["3. 文献传递或馆际服务", "对零散高价值论文优先采用合规文献申请渠道。"],
        ["4. 单篇购买或批量授权", "仅针对仍无法取得且确有抽取价值的论文；大规模时向出版社询价。"],
    ], font_size=7.1, max_lines=3)
    source_note(c, [
        "价格来源（访问日期2026-07-17）：Elsevier ScienceDirect Subscription Options - https://www.elsevier.com/products/sciencedirect/journals/subscription-options",
        "Springer Nature Support说明单篇价格在Buy article PDF入口显示 - https://support.springernature.com/en/support/solutions/articles/6000272608-purchasing-an-article-on-nature-com",
    ], y=75)
    finish_page(c)

    # 12 Long-term objective
    page_base(c, 12, "后续目标：让数据产生可验证的预测能力", "Long-term objective")
    narrative_panel(c, M, 610, W - 2 * M, 125, "数据收集之后要实现什么", [
        "项目的后续重点不是单纯增加论文数量，而是让新增数据持续提高预测覆盖范围和结果可信度。",
        "最终希望输入催化剂组成、制备方法和反应条件后，对可能的产率、CNT结构与材料质量给出有证据基础的预测，为实验方案选择提供参考。",
    ], accent=TEAL, fill=HexColor("#E7F4F3"))
    grid_table(c, M, 355, [42, 133, 336], 48, ["阶段", "目标", "完成后应形成的能力"], [
        ["01", "扩大可训练样本", "继续补充高相关论文和合法全文，使主要催化剂、碳源和工艺路线具有足够覆盖。"],
        ["02", "统一输入与输出", "把催化剂和工艺字段整理为稳定输入，把产率、结构和质量表征整理为明确目标。"],
        ["03", "建立预测验证", "使用未参与训练的论文或实验结果检验预测误差、适用范围和稳定性。"],
        ["04", "支持实验决策", "根据预测结果比较候选条件，优先安排更可能高产或获得目标CNT结构的实验。"],
    ], font_size=7.0, max_lines=3)
    grid_table(c, M, 135, [135, 376], 43, ["重点预测对象", "希望回答的问题"], [
        ["Carbon yield / productivity", "给定催化剂与反应条件，预期产率或生产率处于什么水平。"],
        ["CNT类型与结构", "更可能形成SWCNT、MWCNT或阵列，以及直径、壁数和形貌范围。"],
        ["材料质量", "Raman、TGA残留和纯度等指标可能达到什么水平。"],
        ["工艺窗口", "哪些温度、时间、气体流量和催化剂组合更值得优先验证。"],
    ], font_size=7.1, max_lines=3)
    card(c, M, 70, W - 2 * M, 42, fill=NAVY, stroke=NAVY)
    text_block(c, "最终成果应从“可查询的文献数据库”进一步发展为“能够预测并辅助实验选择的数据基础”。", M + 14, 96, W - 2 * M - 28, size=7.7, color=white, leading=11.5, max_lines=2)
    finish_page(c)

    c.save()
    return OUT


if __name__ == "__main__":
    print(build())
