from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from build_a_class_result_pdf import (
    AMBER, BASE, BLUE, CASE_BASE, CORAL, FONT, FONT_BOLD, GREEN, H, INK,
    M, MASTER, MUTED, NAVY, PURPLE, SLATE, TEAL, W, card, finish_page,
    kpi, page_base, pill, register_fonts, section_card, text_block,
)
from build_a_class_result_pdf_v2 import grid_table, kv_panel, narrative_panel


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pdf/CNT-PatSight_External_Result_Report_WangYang.pdf"
RUN_ID = "LIT_DB283D1C5235DA93_EI_11"


def clean(value) -> str:
    return re.sub(r"<[^>]+>", "", str(value).strip())


def source_list_pages(c: canvas.Canvas, sm: pd.DataFrame, sr: pd.DataFrame, ev: pd.DataFrame) -> None:
    run_counts = sr.groupby("source_id").size()
    evidence_counts = ev.groupby("source_id").size()
    rows = sm.copy()
    rows["source_title"] = rows["source_title"].map(clean)
    rows["run_count"] = rows["source_id"].map(run_counts).fillna(0).astype(int)
    rows["evidence_count"] = rows["source_id"].map(evidence_counts).fillna(0).astype(int)
    rows = rows.sort_values(["publication_year", "source_title"], ascending=[False, True]).reset_index(drop=True)
    for page_no, start in [(10, 0), (11, 33)]:
        page_base(c, page_no, f"A 类66篇分析对象清单 {1 if start == 0 else 2}/2", "Complete A-class corpus")
        subset = rows.iloc[start : start + 33]
        per_col = 17
        row_h = 35.2
        for local_i, (_, row) in enumerate(subset.iterrows()):
            col = local_i // per_col
            rr = local_i % per_col
            x = M + col * 263
            y = 724 - rr * row_h
            if rr % 2 == 0:
                c.setFillColor(white)
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
        c.drawString(M + 12, 93, "R = 实验运行数，E = 证据索引数。清单覆盖当前统一成果集的全部66篇论文。")
        finish_page(c)


def build() -> Path:
    register_fonts()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    sm = pd.read_csv(BASE / "source_master.csv", keep_default_na=False)
    sr = pd.read_csv(BASE / "source_run.csv", keep_default_na=False)
    ev = pd.read_csv(BASE / "evidence_index.csv", keep_default_na=False)
    literature = pd.read_csv(MASTER, low_memory=False)

    case = {name: pd.read_csv(CASE_BASE / f"{name}.csv", keep_default_na=False) for name in [
        "source_master", "source_run", "catalyst_system", "reactor_process_gas",
        "yield_quality", "cost_scale_review", "evidence_index"
    ]}
    s = case["source_master"].iloc[0]
    run = case["source_run"].query("run_id == @RUN_ID").iloc[0]
    cat = case["catalyst_system"].query("run_id == @RUN_ID").iloc[0]
    proc = case["reactor_process_gas"].query("run_id == @RUN_ID").iloc[0]
    result = case["yield_quality"].query("run_id == @RUN_ID").iloc[0]
    cost = case["cost_scale_review"].query("run_id == @RUN_ID").iloc[0]
    evidence = case["evidence_index"].query("run_id == @RUN_ID")

    c = canvas.Canvas(str(OUT), pagesize=A4, pageCompression=1)
    c.setTitle("CNT-PatSight 当前成果展示与 A 类文献数据说明")
    c.setAuthor("王扬")
    c.setCreator("GPT 5.6 Sol")
    c.setSubject("CNT 文献结构化提取、A 类66篇成果与八表示例")

    # 01 Cover
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 11, W, 11, fill=1, stroke=0)
    pill(c, "EXTERNAL RESULT REPORT / 2026", M, H - 95, bg=TEAL)
    c.setFillColor(white)
    c.setFont(FONT_BOLD, 31)
    c.drawString(M, H - 170, "CNT-PatSight")
    c.setFont(FONT_BOLD, 25)
    c.drawString(M, H - 210, "当前成果展示与 A 类文献数据说明")
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 11)
    c.drawString(M, H - 244, "从合规文献来源到运行级八表数据与字段证据")
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.line(M, H - 278, W - M, H - 278)
    text_block(c, "本报告集中展示项目目标、合法学术文献来源、结构化实现流程、A 类66篇成果集，以及一篇完整论文如何落实到来源、运行、催化剂、过程、结果、规模、证据和质量复核八张关联表。", M, H - 322, W - 2 * M, size=10.2, color=HexColor("#C5D4DE"), leading=17, max_lines=6)
    stats = [("1,487", "全库文献元数据"), ("208", "A 类候选"), ("66", "统一八表论文"), ("870", "实验运行")]
    for i, (value, label) in enumerate(stats):
        x = M + i * 128
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 19)
        c.drawString(x, 370, value)
        c.setFillColor(HexColor("#9EB5C5"))
        c.setFont(FONT, 7.4)
        c.drawString(x, 351, label)
    card(c, M, 244, W - 2 * M, 82, fill=HexColor("#102B43"), stroke=HexColor("#29475F"), radius=10)
    text_block(c, "成果集进一步包含 1,686 条反应过程阶段和 6,037 条字段级证据，可按照活性金属、载体、碳源、温度、反应器、产品类型与表征方法组合筛选。", M + 16, 291, W - 2 * M - 32, size=8.5, color=HexColor("#C5D4DE"), leading=13.5, max_lines=3)
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

    # 02 Goal + current results
    page_base(c, 2, "项目目标、当前成果与数据价值", "Goal and current results")
    kpi(c, M, 674, 119, 96, "1,487", "文献元数据", "当前全库唯一来源数", TEAL)
    kpi(c, M + 129, 674, 119, 96, "208", "A 类候选", "高相关优先级论文", BLUE)
    kpi(c, M + 258, 674, 119, 96, "66", "八表成果集", "同一结构统一读取", GREEN)
    kpi(c, M + 387, 674, 119, 96, "870", "实验运行", "每条具有稳定 run_id", AMBER)
    narrative_panel(c, M, 458, 246, 186, "项目目标", [
        "把 CNT 论文中的催化剂制备、反应器、气体条件、产率、形貌和表征结果转化为可计算的运行级记录。",
        "使用稳定标识连接论文、实验运行、催化剂、过程阶段、产品结果和原文证据。",
        "形成可以继续补充、组合筛选、统计汇总和模型使用的文献数据基础。",
    ], accent=TEAL)
    narrative_panel(c, M + 263, 458, 246, 186, "当前成果", [
        "66 篇论文已经进入统一八表目录，形成 870 条实验运行和 1,686 条过程阶段。",
        "6,037 条证据记录连接目标表、目标字段、原文位置、值状态和置信度。",
        "完整论文示例包含 61 个物理实验点，可直接展示八表的实际字段关系。",
    ], accent=BLUE)
    outcome_rows = [
        ["来源可追溯", "题名、作者、期刊、DOI、正式链接、全文路径和来源数据库统一登记"],
        ["实验可拆分", "配方、温度、时间点、对照条件和结果分别进入稳定运行记录"],
        ["条件可组合", "可按金属、载体、碳源、温度、反应器和产品表征联合筛选"],
        ["证据可核验", "关键字段连接正文、表格、图号、补充材料和本地来源对象"],
        ["数据可扩展", "新增论文沿用同一八表规范进入主数据集并参与汇总"],
    ]
    grid_table(c, M, 180, [145, 366], 43, ["成果能力", "具体内容"], outcome_rows, font_size=7.2, max_lines=2)
    card(c, M, 112, W - 2 * M, 45, fill=NAVY, stroke=NAVY)
    text_block(c, "当前成果已经形成从学术文献身份到实验条件、产品结果和字段证据的完整数据链。", M + 14, 137, W - 2 * M - 28, size=8.6, font=FONT_BOLD, color=white, leading=12, max_lines=2)
    finish_page(c)

    # 03 Legal access + workflow
    page_base(c, 3, "我如何合法取得文献并完成结构化", "Institutional access and workflow")
    card(c, M, 514, W - 2 * M, 238, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 18, 724, "第一人称来源说明")
    paragraphs = [
        "我首先使用 DOI、出版社官方页面和开放元数据索引确认论文身份，核对题名、作者、年份、期刊、正式链接与版本关系。",
        "在需要机构资格验证的环节，我提供我的英国伦敦大学学院（University College London, UCL）institution 证明与相应机构访问权限，用于验证学术身份，并完成出版社、机构知识库和学术数据库的合规访问或文献申请流程。",
        "这一机构凭证使我能够在许可范围内连接多个国家和地区的出版平台、大学仓储与学术资源，提升跨来源检索、版本确认和授权边界识别的可信度。其稀缺价值来自可验证的学术背景和机构级访问资格。",
        "全文来源包括出版社授权的 HTML/PDF、开放获取版本、机构知识库、作者合法存档、补充材料和项目已有来源记录。整个流程遵循出版社许可、机构授权和开放获取规则。",
    ]
    yy = 690
    for para in paragraphs:
        c.setFillColor(TEAL)
        c.circle(M + 23, yy + 3, 2.5, fill=1, stroke=0)
        yy = text_block(c, para, M + 34, yy + 7, W - 2 * M - 52, size=8.2, color=HexColor("#D0DDE5"), leading=13.2, max_lines=4) - 6
    workflow = [
        ["01", "身份与版本核验", "DOI、题名、作者、年份、期刊、正式链接和版本关系"],
        ["02", "合法来源发现", "出版社页面、机构仓储、作者存档、开放版本和补充材料"],
        ["03", "文件内容验证", "PDF/HTML 格式签名、正文内容、来源对象和本地登记"],
        ["04", "正文与表格解析", "章节、表格、图注、补充文件和实验候选片段"],
        ["05", "运行级八表抽取", "实验边界、催化剂、过程、结果、规模信息和字段证据"],
        ["06", "结构与语义审计", "标识唯一性、表间关联、证据覆盖和质量复核轨迹"],
    ]
    grid_table(c, M, 175, [38, 142, 331], 45, ["步骤", "阶段", "处理内容"], workflow, font_size=7.1, max_lines=2)
    card(c, M, 112, W - 2 * M, 40, fill=HexColor("#E7F4F3"), stroke=HexColor("#B9DEDB"))
    text_block(c, "最终保留来源链接、本地路径、来源对象、解析状态和字段证据，形成完整的合法来源链路。", M + 14, 135, W - 2 * M - 28, size=8.2, font=FONT_BOLD, color=INK, leading=11, max_lines=1)
    finish_page(c)

    # 04 Eight tables + QA
    page_base(c, 4, "八表架构、行数与质量审计", "Data architecture and quality")
    table_rows = [
        ["01", "source_master", "论文级", "题名、作者、期刊、DOI、全文与来源", "66"],
        ["02", "source_run", "运行级", "实验边界、标签、摘要与置信度", "870"],
        ["03", "catalyst_system", "运行级", "金属、载体、前驱体、制备与热处理", "870"],
        ["04", "reactor_process_gas", "阶段级", "反应器、温度、时间、压力与气体", "1,686"],
        ["05", "yield_quality", "运行级", "原始产率、产品、形貌与表征", "870"],
        ["06", "cost_scale_review", "运行级", "规模、主要投入、安全与复现信息", "870"],
        ["07", "evidence_index", "证据级", "目标字段、来源位置、值状态与置信度", "6,037"],
        ["08", "review_issue_log", "复核级", "字段复核、证据补充与审核流转", "-"],
    ]
    grid_table(c, M, 358, [30, 106, 52, 268, 55], 40, ["序号", "表名", "粒度", "主要内容", "行数"], table_rows, font_size=6.8, max_lines=2)
    kpi(c, M, 225, 158, 105, "61", "语义审计包", "手工结构化包全部完成审计", TEAL)
    kpi(c, M + 176, 225, 158, 105, "840", "已审计运行", "运行标识与表间关联一致", GREEN)
    kpi(c, M + 352, 225, 157, 105, "93.5%", "高置信证据", "5,642条 evidence 为 high", BLUE)
    narrative_panel(c, M, 112, W - 2 * M, 88, "质量控制方法", [
        "原始表述、标准化字段、证据位置和值状态同时保存；来源、运行、过程、产品和证据通过稳定标识关联。",
        "结构审计、证据索引和质量复核共同保证数据关系清晰、来源可查、更新过程可追踪。",
    ], accent=AMBER, fill=HexColor("#FFF5E0"))
    finish_page(c)

    # 05 Coverage + aggregate summary
    page_base(c, 5, "A 类66篇成果集汇总", "A-class aggregate summary")
    kpi(c, M, 674, 119, 96, "66", "论文来源", "统一八表成果集", TEAL)
    kpi(c, M + 129, 674, 119, 96, "870", "实验运行", "平均13.2条/篇", BLUE)
    kpi(c, M + 258, 674, 119, 96, "1,686", "过程阶段", "平均1.94阶段/运行", GREEN)
    kpi(c, M + 387, 674, 119, 96, "6,037", "证据索引", "平均91.5条/篇", AMBER)
    summary_rows = [
        ["时间范围", "2004-2026", "中位发表年份2019；2020年及以后28篇"],
        ["运行密度", "1-126条/篇", "平均13.2条/篇，中位7条/篇"],
        ["主要金属", "Fe 43 / Ni 27 / Co 18 / Mo 12", "按论文去重，一篇可包含多种金属"],
        ["主要碳源", "甲烷/沼气21 / 乙炔18 / 其他烃14 / 乙烯12", "按论文去重且类别可重叠"],
        ["数值型结果", "47篇 / 611条运行", "yield_original 中包含明确数字"],
        ["标准化结果", "35篇 / 430条运行", "具有非空 yield_value_standardized"],
        ["常见表征", "TEM 58 / SEM 56 / Raman 53 / XRD 38", "按论文是否报告相应方法计数"],
        ["高置信证据", "5,642条 / 93.5%", "confidence 标记为 high"],
    ]
    grid_table(c, M, 292, [112, 185, 214], 43, ["统计项目", "当前结果", "口径说明"], summary_rows, font_size=6.8, max_lines=3)
    use_rows = [
        ["催化剂筛选", "活性金属、载体、前驱体、配比、制备和热处理"],
        ["工艺筛选", "反应器、温度、时间、压力、碳源和气体流量"],
        ["产品筛选", "产率定义、CNT 类型、形貌、尺寸、纯度和表征方法"],
        ["证据回溯", "来源章节、页码、表号、图号、证据摘要和本地对象"],
    ]
    grid_table(c, M, 112, [140, 371], 36, ["应用维度", "可检索内容"], use_rows, font_size=7.0, max_lines=2)
    finish_page(c)

    # 06 Example tables 1-2
    page_base(c, 6, "完整论文示例：八表展示 1/4", "Eight-table example")
    card(c, M, 646, W - 2 * M, 106, fill=NAVY, stroke=NAVY)
    c.setFillColor(TEAL)
    c.setFont(FONT_BOLD, 7.5)
    c.drawString(M + 16, 724, "示例论文 | Nanomaterials 2023 | DOI 10.3390/nano14010075")
    text_block(c, s.source_title, M + 16, 698, W - 2 * M - 32, size=9.7, font=FONT_BOLD, color=white, leading=14, max_lines=3)
    c.setFillColor(HexColor("#AFC3D1"))
    c.setFont(FONT, 6.8)
    c.drawString(M + 16, 660, "论文包含61个物理实验点；运行级表统一展示 EI point 11，以同一 run_id 串联八表。")
    kv_panel(c, M, 379, W - 2 * M, 239, "表1  source_master  |  论文级来源记录", [
        ("source_id", s.source_id), ("题名", s.source_title), ("作者", s.authors_or_assignee),
        ("年份 / 期刊", f"{s.publication_year} / {s.publication_venue}"), ("DOI", s.doi_or_patent_no),
        ("本地全文", s.local_file_path), ("全文状态", s.pdf_status), ("抽取范围", s.source_section_scope),
    ], accent=TEAL, label_w=100)
    kv_panel(c, M, 112, W - 2 * M, 239, "表2  source_run  |  运行级边界记录", [
        ("run_id", run.run_id), ("source_id", run.source_id), ("run_label", run.run_label),
        ("data_type", run.data_type), ("target_track", run.target_track),
        ("抽取置信度", run.extraction_confidence), ("运行摘要", run.run_summary), ("相关类别", run.relevance_class),
    ], accent=BLUE, label_w=100)
    finish_page(c)

    # 07 Example tables 3-4
    page_base(c, 7, "完整论文示例：八表展示 2/4", "Eight-table example")
    kv_panel(c, M, 425, W - 2 * M, 327, "表3  catalyst_system  |  催化剂与制备记录", [
        ("run_id", cat.run_id), ("catalyst_id", cat.catalyst_id), ("催化剂标签", cat.catalyst_label),
        ("活性金属", cat.active_metals), ("载体", cat.support_material), ("金属配比原文", cat.metal_ratio_original),
        ("前驱体", cat.precursor_summary), ("制备方法", cat.preparation_method), ("制备详情", cat.preparation_detail),
        ("干燥条件", cat.drying_condition), ("煅烧条件", cat.calcination_condition), ("制备后状态", cat.post_preparation_condition),
    ], accent=GREEN, label_w=105)
    kv_panel(c, M, 112, W - 2 * M, 285, "表4  reactor_process_gas  |  反应器、过程与气体记录", [
        ("process_stage_id", proc.process_stage_id), ("阶段类型", proc.stage_type), ("阶段顺序", proc.stage_order),
        ("反应器", proc.reactor_type), ("规模", proc.scale_level),
        ("温度 / 时间", f"{proc.temperature_setpoint_C} °C / {proc.holding_time_min} min"),
        ("压力", f"{proc.pressure_original} / {proc.pressure_kPa} kPa"),
        ("碳源", f"{proc.carbon_source} / {proc.carbon_source_flow_original}"),
        ("还原气", f"{proc.reducing_gas} / {proc.reducing_gas_flow_original}"),
        ("惰性气", f"{proc.inert_gas} / {proc.inert_gas_flow_original}"),
    ], accent=AMBER, label_w=105)
    finish_page(c)

    # 08 Example tables 5-6
    page_base(c, 8, "完整论文示例：八表展示 3/4", "Eight-table example")
    kv_panel(c, M, 420, W - 2 * M, 332, "表5  yield_quality  |  产率、产品和表征记录", [
        ("product_id", result.product_id), ("主要结果类型", result.primary_yield_metric),
        ("原始产率", result.yield_original), ("原始定义", result.yield_definition_original),
        ("标准化说明", result.yield_standardization_note), ("结果单位", result.yield_unit_standardized),
        ("产品类型", result.CNT_type_confirmed), ("结果摘要", result.secondary_result_summary),
        ("类型证据", result.CNT_type_evidence), ("表征方法", result.characterization_methods),
    ], accent=CORAL, label_w=105)
    kv_panel(c, M, 112, W - 2 * M, 280, "表6  cost_scale_review  |  规模、投入与复现记录", [
        ("run_id", cost.run_id), ("展示规模", cost.scale_level_demonstrated),
        ("规模证据", cost.scale_evidence_summary), ("主要投入", cost.cost_driver_summary.split(";")[0]),
        ("安全信息", cost.safety_risk), ("记录范围", "规模证据、主要投入、安全信息与复现价值"),
        ("复现价值", cost.reproduction_value), ("复现优先级", cost.reproduction_priority),
        ("运行类型", run.data_type),
    ], accent=PURPLE, label_w=105)
    finish_page(c)

    # 09 Example tables 7-8
    page_base(c, 9, "完整论文示例：八表展示 4/4", "Eight-table example")
    evidence_rows = []
    for _, row in evidence.iterrows():
        evidence_rows.append([row.evidence_id.replace("EVD_LIT_DB283D1C5235DA93_EI_11_", ""), row.target_table, row.source_section, row.value_status, row.confidence])
    grid_table(c, M, 500, [58, 145, 140, 95, 73], 43, ["证据", "目标表", "来源位置", "值状态", "置信度"], evidence_rows, font_size=6.7, max_lines=2)
    narrative_panel(c, M, 344, W - 2 * M, 128, "表7  evidence_index  |  字段级证据", [
        f"该运行共有 {len(evidence)} 条 record-level 证据，分别连接 source_run、catalyst_system、reactor_process_gas、yield_quality 和 cost_scale_review。",
        "证据类型为 manual_fulltext_transcription，来源位置为 Figure 4，来源对象指向本地验证过的 HTML 全文。",
    ], accent=TEAL)
    kv_panel(c, M, 112, W - 2 * M, 204, "表8  review_issue_log  |  质量复核表结构", [
        ("记录主键", "issue_id"), ("关联标识", "source_id / run_id / target_record_id"),
        ("目标位置", "target_table / target_field"), ("证据关联", "evidence_ids"),
        ("审核流程", "severity / review_status / reviewer / reviewed_at"),
        ("处理字段", "resolution / notes"), ("表的作用", "保存字段复核、证据补充、审核流转与版本轨迹"),
    ], accent=AMBER, label_w=105)
    finish_page(c)

    source_list_pages(c, sm, sr, ev)

    # 12 Value + deliverables
    page_base(c, 12, "成果价值、交付内容与后续应用", "Value and deliverables")
    applications = [
        ("01", "催化剂路线检索", "按金属、载体、前驱体、配比和制备方法组合筛选。", CORAL),
        ("02", "工艺条件对比", "联动查看反应器、温度、时间、压力、碳源与气体流量。", TEAL),
        ("03", "结果证据回溯", "从产率、CNT 类型与表征方法直接连接原文位置。", BLUE),
        ("04", "复现实验准备", "按 run_id 汇总催化剂、过程、结果和规模信息。", AMBER),
        ("05", "统计与模型输入", "构建统计数据集、相似实验检索、特征工程和模型输入。", PURPLE),
        ("06", "持续扩展成果集", "新增论文沿用同一八表规范进入主数据集。", GREEN),
    ]
    for i, item in enumerate(applications):
        section_card(c, M + (i % 2) * 263, 646 - (i // 2) * 123, 246, 104, *item)
    deliverables = [
        ["统一八表 CSV", "66篇论文、870条运行、1,686条过程阶段和6,037条证据"],
        ["论文级数据包", "每篇论文独立目录、稳定标识、来源路径和八表记录"],
        ["完整论文示例", "61个物理实验点，并以同一 run_id 展示八表连接"],
        ["汇总统计与清单", "A类66篇总体数据说明和完整论文对象清单"],
        ["可重复生成报告", "生成脚本、固定版式、PDF元数据和逐页渲染验证"],
    ]
    grid_table(c, M, 179, [145, 366], 39, ["交付资产", "内容"], deliverables, font_size=7.0, max_lines=2)
    card(c, M, 112, W - 2 * M, 45, fill=NAVY, stroke=NAVY)
    text_block(c, "A 类66篇成果集已经形成可检索、可组合、可统计、可回溯并可持续扩展的文献数据资产。", M + 14, 137, W - 2 * M - 28, size=8.7, font=FONT_BOLD, color=white, leading=12, max_lines=2)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(M, 84, "制作人  王扬")
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.2)
    c.drawRightString(W - M, 84, "数据提取与报告辅助模型  GPT 5.6 Sol")
    c.save()
    return OUT


if __name__ == "__main__":
    print(build())
