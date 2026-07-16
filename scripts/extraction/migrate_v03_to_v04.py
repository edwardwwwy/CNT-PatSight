#!/usr/bin/env python3
"""One-time migration from the v0.3 five-table packages to v0.4 eight tables.

The script is intentionally conservative: it preserves original wording in summaries and
evidence rows, writes the new CSVs in place, and leaves legacy observation JSONL files for
explicit removal after validation.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim"
SCHEMA_PATH = ROOT / "config" / "schema.json"
METADATA_PATH = ROOT / "data" / "raw" / "metadata" / "literature_master.csv"
DICTIONARY_PATH = ROOT / "config" / "field_dictionary.csv"
TEMPLATE_DIR = ROOT / "data" / "processed" / "templates"

MISSING = {"", "not_reported", "not_applicable", None}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def meaningful(value: object) -> bool:
    return str(value).strip() not in MISSING


def first_meaningful(*values: object, default: str = "not_reported") -> str:
    for value in values:
        if meaningful(value):
            return str(value).strip()
    return default


def compact(values: list[object], default: str = "not_reported") -> str:
    cleaned: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text in MISSING or text in cleaned:
            continue
        cleaned.append(text)
    return "; ".join(cleaned) if cleaned else default


def strip_combo_note(value: str) -> str:
    text = value or ""
    text = re.sub(r"\s*combo_key[^.]*\.?", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ;")
    return text or "not_reported"


def parse_numeric(value: str) -> str:
    if not meaningful(value):
        return "not_reported"
    match = re.search(r"[-+]?\d+(?:\.\d+)?", value)
    return match.group(0) if match else "not_reported"


def parse_particle(value: str) -> tuple[str, str, str]:
    if not meaningful(value):
        return "not_reported", "not_reported", "not_reported"
    text = value.strip()
    range_match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*", text)
    if range_match:
        return "not_reported", f"{range_match.group(1)}-{range_match.group(2)}", "reported_numeric_range"
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return text, "not_reported", "reported_numeric_mean"
    return "not_reported", "not_reported", text


def gas_name_and_flow(value: str) -> tuple[str, str, str]:
    if not meaningful(value):
        return "not_reported", "not_reported", "not_reported"
    text = value.strip()
    name_match = re.match(r"([A-Za-z0-9₂]+)", text)
    name = name_match.group(1) if name_match else "other"
    standardized = "not_reported"
    if not re.search(r"vol%|rate not reported|flow not reported", text, flags=re.I):
        standardized = parse_numeric(text)
    return name, text, standardized


def source_object_ref(location: str) -> str:
    if not location:
        return "not_reported"
    refs = re.findall(
        r"(?:Table|Tables|Fig\.?|Figs\.?|Figure|Figures|Eq\.?|Claim|Claims|Example|Examples|Section)\s*[A-Za-z0-9.\-–]+",
        location,
        flags=re.I,
    )
    return "; ".join(dict.fromkeys(refs)) if refs else "not_reported"


def primary_yield_metric(row: dict[str, str]) -> str:
    text = " ".join(
        [row.get("yield_original", ""), row.get("yield_definition_original", "")]
    ).lower()
    if "carbon weight gain" in text or "(w_tot" in text:
        return "carbon_weight_gain_percent"
    if "/h" in text or "productivity" in text:
        return "CNT_productivity"
    if meaningful(row.get("CNT_yield_per_catalyst_g_gcat")):
        return "CNT_yield_per_catalyst"
    if meaningful(row.get("carbon_conversion_to_solid_percent")):
        return "carbon_conversion_to_solid"
    if meaningful(row.get("methane_conversion_percent")):
        return "methane_conversion"
    return "reported_yield_other"


def issue_target_field(tags: list[str]) -> str:
    joined = ";".join(tags).lower()
    mapping = [
        ("calcination", "calcination_condition"),
        ("heating", "temperature_program_summary"),
        ("yield", "yield_original"),
        ("tga", "TGA_carbon_content_wt_percent"),
        ("purity", "purity_basis"),
        ("cnt_type", "CNT_type_confirmed"),
        ("diameter", "outer_diameter_range_nm"),
        ("pressure", "pressure_original"),
        ("temperature", "temperature_setpoint_C"),
        ("scale", "scale_level_claimed"),
    ]
    for token, field in mapping:
        if token in joined:
            return field
    return "record_level"


def map_observation_target(
    observation: dict[str, object],
    source_id: str,
    run_rows: dict[str, dict[str, str]],
    catalysts: dict[str, dict[str, str]],
    processes: dict[str, list[dict[str, str]]],
    products: dict[str, dict[str, str]],
) -> tuple[str, str, str]:
    run_id = str(observation.get("related_run_id") or "not_applicable")
    obs_type = str(observation.get("observation_type") or "other")
    if run_id == "not_applicable" or run_id not in run_rows:
        return "source_master", source_id, "not_applicable"
    if obs_type in {"catalyst_preparation_hint", "mechanism", "failure_mode"}:
        catalyst = catalysts.get(run_id)
        if catalyst:
            return "catalyst_system", catalyst["catalyst_id"], run_id
    if obs_type == "temperature_effect":
        stages = processes.get(run_id, [])
        stage = next((item for item in stages if item.get("stage_type") == "growth"), None)
        if stage:
            return "reactor_process_gas", stage["process_stage_id"], run_id
    if obs_type in {"scale_up_signal", "safety_environment"}:
        return "cost_scale_review", run_id, run_id
    if obs_type == "quality_warning":
        product = products.get(run_id)
        if product:
            return "yield_quality", product["product_id"], run_id
    return "source_run", run_id, run_id


def build_dictionary(schema: dict) -> None:
    table_cn = {
        "source_master": "文献/专利主表",
        "source_run": "实验运行主表",
        "catalyst_system": "催化剂体系表",
        "reactor_process_gas": "反应器、工艺与气体程序表",
        "yield_quality": "产率与产品品质表",
        "cost_scale_review": "成本、规模与工业适配表",
        "evidence_index": "证据索引表",
        "review_issue_log": "复核与问题记录表",
    }
    labels = {
        "source_id": "来源唯一标识", "source_type": "来源类型", "source_title": "来源标题",
        "publication_year": "发表或公开年份", "authors_or_assignee": "作者或专利受让人",
        "publication_venue": "期刊、会议或公开机构", "doi_or_patent_no": "DOI 或专利号",
        "source_link": "来源链接", "source_database": "来源数据库", "source_language": "来源语言",
        "local_file_path": "本地原始文件路径", "pdf_status": "PDF 获取状态",
        "screening_class": "筛选分类", "source_section_scope": "已覆盖的来源章节范围",
        "extraction_status": "提取状态", "review_status": "复核状态", "notes": "补充说明",
        "run_id": "运行唯一标识", "run_label": "来源内运行标签", "data_type": "数据类型",
        "target_track": "目标技术路线", "relevance_class": "相关性类别",
        "extraction_confidence": "提取总体置信度", "run_summary": "运行摘要",
        "catalyst_id": "催化剂记录标识", "catalyst_label": "来源中的催化剂标签",
        "active_metals": "核心活性金属", "support_material": "载体材料", "promoter": "助剂",
        "metal_ratio_original": "金属配比原始表述", "metal_ratio_standardized": "金属配比标准化表述",
        "precursor_summary": "前驱体摘要", "preparation_method": "催化剂制备方法",
        "preparation_modifier": "制备修饰类别", "preparation_detail": "制备修饰与条件详情",
        "drying_condition": "干燥条件", "calcination_condition": "焙烧或热分解条件",
        "reduction_condition": "还原条件", "activation_condition": "活化条件",
        "post_preparation_condition": "洗涤、粉碎或筛分等后处理",
        "catalyst_particle_size_mean_nm": "催化剂颗粒平均尺寸",
        "catalyst_particle_size_range_nm": "催化剂颗粒尺寸范围",
        "catalyst_particle_size_qualifier": "颗粒尺寸证据状态",
        "BET_surface_area_m2_g": "催化剂 BET 比表面积", "pore_diameter_nm": "催化剂孔径",
        "pore_volume_cm3_g": "催化剂孔容", "phase_or_state_summary": "催化剂物相或化学态摘要",
        "dispersion_summary": "活性相分散摘要", "deactivation_summary": "催化剂失活摘要",
        "process_stage_id": "工艺阶段标识", "stage_order": "阶段顺序", "stage_type": "阶段类型",
        "reactor_type": "反应器类型", "scale_level": "阶段实验规模", "reactor_material": "反应器材料",
        "reactor_size_summary": "反应器尺寸摘要", "reactor_setup_summary": "床层、舟皿和测温位置摘要",
        "catalyst_loading_mass_g": "催化剂装载质量", "temperature_setpoint_C": "温度设定值",
        "temperature_range_reported_C": "来源报告的温度范围",
        "temperature_program_summary": "升温、实测或温度程序摘要", "holding_time_min": "保温时间",
        "heating_rate_C_min": "升温速率", "cooling_condition": "冷却条件",
        "pressure_original": "压力原始表述", "pressure_kPa": "标准化压力",
        "carbon_source": "主要碳源", "carbon_source_flow_original": "碳源流量原始表述",
        "carbon_source_flow_sccm": "碳源标准流量", "reducing_gas": "还原气体",
        "reducing_gas_flow_original": "还原气流量原始表述", "reducing_gas_flow_sccm": "还原气标准流量",
        "inert_gas": "惰性或载气", "inert_gas_flow_original": "惰性气流量原始表述",
        "inert_gas_flow_sccm": "惰性气标准流量", "cofeed_or_reactive_gas": "共进料或反应性气体",
        "cofeed_flow_original": "共进料流量原始表述", "cofeed_flow_sccm": "共进料标准流量",
        "total_flow_original": "总流量原始表述", "total_flow_sccm": "标准化总流量",
        "gas_composition_summary": "完整气体组成和比例摘要", "GHSV_or_residence_time": "空速或停留时间",
        "process_note": "工艺补充说明", "product_id": "产品结果标识",
        "primary_yield_metric": "主要产率指标类型", "yield_original": "产率原始表述",
        "yield_definition_original": "产率原始定义", "yield_calculation_method": "产率计算公式或方法",
        "yield_value_standardized": "产率标准化数值", "yield_unit_standardized": "产率标准化单位",
        "yield_standardization_note": "产率标准化说明",
        "CNT_yield_per_catalyst_g_gcat": "单位催化剂 CNT 产量",
        "CNT_productivity_g_gcat_h": "单位催化剂单位时间 CNT 生产率",
        "carbon_source_conversion_percent": "主要碳源转化率",
        "carbon_conversion_to_solid_percent": "碳向固体产物转化率",
        "secondary_result_summary": "其他转化率、效率或选择性摘要",
        "CNT_type_reported": "作者报告的 CNT 类型", "CNT_type_confirmed": "证据支持的 CNT 类型",
        "product_mixture_summary": "混合产物和杂质组成摘要", "CNT_type_evidence": "CNT 类型判定依据",
        "SWCNT_or_few_wall_evidence_summary": "单壁或少壁 CNT 证据摘要",
        "RBM_peak_reported": "RBM 峰报告情况", "outer_diameter_mean_nm": "外径平均值",
        "outer_diameter_range_nm": "外径范围", "inner_diameter_mean_nm": "内径平均值",
        "wall_number_summary": "壁数或内径/壁数摘要", "length_summary": "长度摘要",
        "morphology": "形貌", "alignment_or_array": "取向或阵列形态",
        "Raman_ratio_type": "拉曼比值方向", "Raman_ratio_value": "拉曼比值",
        "Raman_laser_wavelength_nm": "拉曼激光波长",
        "TGA_carbon_content_wt_percent": "合成后样品的 TGA 碳含量",
        "purified_product_purity_wt_percent": "纯化后产品纯度", "purity_basis": "纯度或碳含量口径",
        "residue_summary": "灰分、金属或其他残留摘要", "amorphous_carbon_level": "无定形碳水平",
        "BET_surface_area_product_m2_g": "CNT 产品 BET 比表面积",
        "characterization_methods": "表征方法", "post_treatment_or_purification": "产品后处理或纯化状态",
        "purification_condition": "纯化条件", "application_property_summary": "应用相关性能摘要",
        "scale_level_demonstrated": "实际证据支持的规模", "scale_level_claimed": "作者或专利声称的规模",
        "scale_evidence_summary": "规模证据摘要", "reactor_capacity_or_throughput": "反应器能力或吞吐量",
        "continuous_operation_time_h": "连续运行时间", "catalyst_lifetime_or_reuse": "催化剂寿命或复用表述",
        "catalyst_reuse_cycles": "催化剂复用次数", "batch_stability": "批次或运行稳定性",
        "scale_up_issue": "放大问题", "quantitative_cost_reported": "是否报告量化成本",
        "quantitative_cost_summary": "量化成本或消耗摘要", "cost_driver_summary": "成本驱动因素摘要",
        "safety_risk": "安全风险", "emission_or_waste": "排放或废物",
        "industrial_readiness_assessment": "工业成熟度人工评估", "reproduction_value": "复现实验价值",
        "reproduction_priority": "复现优先级", "industrial_value_score": "工业价值评分",
        "recommended_next_action": "建议后续动作", "review_note": "工业适配复核说明",
        "evidence_id": "证据唯一标识", "target_table": "证据指向的目标表",
        "target_record_id": "证据指向的记录标识", "target_fields": "证据支持的目标字段",
        "evidence_type": "证据类型", "value_status": "值的来源状态",
        "source_section": "来源章节", "source_locator": "页码、段落或其他位置",
        "source_object_ref": "表、图、公式、实施例或权利要求引用", "evidence_text": "简短原文摘录",
        "evidence_summary": "证据内容摘要", "confidence": "证据置信度",
        "linked_issue_id": "关联复核问题标识", "issue_id": "复核问题唯一标识",
        "issue_type": "问题类型", "target_field": "需要复核的目标字段",
        "issue_summary": "问题摘要", "conflicting_values": "冲突值或相互矛盾表述",
        "evidence_ids": "支持该问题的证据标识", "severity": "问题严重度",
        "reviewer": "复核人", "reviewed_at": "复核时间", "resolution": "复核结论",
    }
    review_only = {
        "industrial_readiness_assessment", "reproduction_value", "reproduction_priority",
        "industrial_value_score", "recommended_next_action", "reviewer", "reviewed_at", "resolution",
    }
    rare_critical = {
        "catalyst_reuse_cycles", "safety_risk", "emission_or_waste",
        "purified_product_purity_wt_percent", "residue_summary",
        "reactor_capacity_or_throughput", "quantitative_cost_reported",
        "quantitative_cost_summary", "cost_driver_summary",
    }
    class_conditional = {
        "BET_surface_area_m2_g", "pore_diameter_nm", "pore_volume_cm3_g",
        "catalyst_particle_size_mean_nm", "catalyst_particle_size_range_nm",
        "GHSV_or_residence_time", "length_summary", "BET_surface_area_product_m2_g",
        "application_property_summary", "continuous_operation_time_h",
        "catalyst_lifetime_or_reuse", "scale_level_claimed", "source_object_ref",
        "RBM_peak_reported", "SWCNT_or_few_wall_evidence_summary",
    }
    categorical = {
        "source_type", "pdf_status", "screening_class", "extraction_status", "review_status",
        "data_type", "relevance_class", "extraction_confidence", "preparation_modifier",
        "catalyst_particle_size_qualifier", "stage_type", "scale_level",
        "primary_yield_metric", "Raman_ratio_type", "purity_basis",
        "quantitative_cost_reported", "evidence_type", "value_status", "confidence",
        "issue_type", "severity",
    }
    numeric_suffixes = (
        "_year", "_order", "_nm", "_m2_g", "_cm3_g", "_mass_g", "_C", "_min",
        "_kPa", "_sccm", "_percent", "_g_gcat", "_g_gcat_h", "_time_h", "_cycles", "_score",
    )
    units = {
        "publication_year": "year", "catalyst_particle_size_mean_nm": "nm",
        "catalyst_particle_size_range_nm": "nm", "BET_surface_area_m2_g": "m2/g",
        "pore_diameter_nm": "nm", "pore_volume_cm3_g": "cm3/g",
        "catalyst_loading_mass_g": "g", "temperature_setpoint_C": "degC",
        "temperature_range_reported_C": "degC", "holding_time_min": "min",
        "heating_rate_C_min": "degC/min", "pressure_kPa": "kPa",
        "carbon_source_flow_sccm": "sccm", "reducing_gas_flow_sccm": "sccm",
        "inert_gas_flow_sccm": "sccm", "cofeed_flow_sccm": "sccm",
        "total_flow_sccm": "sccm", "CNT_yield_per_catalyst_g_gcat": "g/gcat",
        "CNT_productivity_g_gcat_h": "g/gcat/h", "carbon_source_conversion_percent": "%",
        "carbon_conversion_to_solid_percent": "%", "outer_diameter_mean_nm": "nm",
        "outer_diameter_range_nm": "nm", "inner_diameter_mean_nm": "nm",
        "Raman_laser_wavelength_nm": "nm", "TGA_carbon_content_wt_percent": "wt%",
        "purified_product_purity_wt_percent": "wt%", "BET_surface_area_product_m2_g": "m2/g",
        "continuous_operation_time_h": "h", "catalyst_reuse_cycles": "count",
    }
    controlled = {
        "source_type": "paper|patent|review|internal_record",
        "screening_class": "formal_extract|candidate_extract|source_observation_only|background_reference|reject",
        "extraction_status": "needs_review|reviewed",
        "review_status": "pending_human_review|in_review|reviewed",
        "value_status": "reported|calculated|inferred|review_assessment",
        "Raman_ratio_type": "ID/IG|IG/ID|not_reported",
        "quantitative_cost_reported": "yes|no|not_reported",
        "severity": "low|medium|high|critical",
        "issue_type": "source_conflict|definition_ambiguity|run_split_uncertainty|CNT_type_uncertainty|calculation_check|critical_data_gap|quality_warning|schema_mapping_question",
    }
    rows = []
    for table_name, spec in schema["tables"].items():
        required = set(spec.get("required_fields", []))
        for field in spec["columns"]:
            if field not in labels:
                raise KeyError(f"Missing Chinese label for {table_name}.{field}")
            if field in review_only:
                population = "review_stage_only"
            elif field in rare_critical:
                population = "rare_but_critical"
            elif field in class_conditional:
                population = "class_conditional_common"
            elif field in required:
                population = "always"
            else:
                population = "common"
            if field.endswith("_id") or field in {"target_record_id", "evidence_ids", "target_fields"}:
                data_type = "identifier"
            elif field in categorical:
                data_type = "categorical"
            elif field.endswith(numeric_suffixes):
                data_type = "number"
            else:
                data_type = "text"
            if population == "always":
                rationale = "主键、外键或解释记录所需的核心字段。"
                null_policy = "non_null"
            elif population == "class_conditional_common":
                rationale = "在主要论文、专利或技术路线子集中高概率出现且具有稳定分析价值。"
                null_policy = "not_applicable_or_not_reported"
            elif population == "rare_but_critical":
                rationale = "报告频率可能较低，但对安全、规模、纯度、成本或可复现性判断关键。"
                null_policy = "not_reported_allowed"
            elif population == "review_stage_only":
                rationale = "仅在人工复核阶段填充，用于工业适配或问题闭环。"
                null_policy = "not_assessed_until_human_review"
            else:
                rationale = "预计在数百篇 CNT 论文和专利中反复出现，适合稳定列化。"
                null_policy = "not_reported_allowed"
            rows.append({
                "table_name": table_name,
                "field_name": field,
                "description_cn": f"{table_cn[table_name]}：{labels[field]}。",
                "data_type": data_type,
                "unit": units.get(field, "not_applicable"),
                "required_level": "core" if field in required else "conditional",
                "population_expectation": population,
                "controlled_values_or_format": controlled.get(field, "free_text_or_reported_value"),
                "null_policy": null_policy,
                "inclusion_rationale": rationale,
            })
    columns = [
        "table_name", "field_name", "description_cn", "data_type", "unit",
        "required_level", "population_expectation", "controlled_values_or_format",
        "null_policy", "inclusion_rationale",
    ]
    write_csv(DICTIONARY_PATH, columns, rows)


def migrate_source(directory: Path, schema: dict, metadata: dict[str, dict[str, str]]) -> None:
    if (directory / "source_master.csv").exists():
        print(f"SKIP {directory.name}: source_master.csv already exists")
        return

    old_source_runs = read_csv(directory / "source_run.csv")
    old_catalysts = read_csv(directory / "catalyst_system.csv")
    old_processes = read_csv(directory / "reactor_process_gas.csv")
    old_products = read_csv(directory / "yield_quality.csv")
    old_costs = read_csv(directory / "cost_scale_review.csv")
    observations = [
        json.loads(line)
        for line in (directory / "source_observations.jsonl").read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    source_id = old_source_runs[0]["source_id"]
    meta = metadata[source_id]
    source_section = old_source_runs[0].get("source_section", "not_reported")

    source_master = [{
        "source_id": source_id,
        "source_type": meta.get("source_type") or old_source_runs[0].get("source_type"),
        "source_title": meta.get("title") or old_source_runs[0].get("source_title"),
        "publication_year": meta.get("year") or old_source_runs[0].get("year"),
        "authors_or_assignee": meta.get("authors_or_assignee") or old_source_runs[0].get("authors_or_assignee"),
        "publication_venue": meta.get("journal") or "not_reported",
        "doi_or_patent_no": meta.get("doi_or_patent_no") or old_source_runs[0].get("doi_or_patent_no"),
        "source_link": meta.get("source_link") or old_source_runs[0].get("source_link"),
        "source_database": meta.get("source_database") or old_source_runs[0].get("source_database"),
        "source_language": "English",
        "local_file_path": meta.get("pdf_path") or "not_reported",
        "pdf_status": meta.get("pdf_status") or "not_reported",
        "screening_class": meta.get("screening_class") or old_source_runs[0].get("relevance_class"),
        "source_section_scope": source_section,
        "extraction_status": "needs_review",
        "review_status": meta.get("review_status") or "pending_human_review",
        "notes": compact([meta.get("notes"), strip_combo_note(old_source_runs[0].get("notes", ""))]),
    }]

    source_runs = [{
        "run_id": row["run_id"], "source_id": row["source_id"],
        "run_label": row.get("run_label") or "not_reported",
        "data_type": row.get("data_type") or "experimental_run",
        "target_track": row.get("target_track") or "not_reported",
        "relevance_class": row.get("relevance_class") or "formal_extract",
        "extraction_status": "needs_review",
        "extraction_confidence": row.get("extraction_confidence") or "not_reported",
        "run_summary": row.get("run_summary") or "not_reported",
        "notes": strip_combo_note(row.get("notes", "")),
    } for row in old_source_runs]

    catalysts = []
    for row in old_catalysts:
        mean, size_range, qualifier = parse_particle(row.get("catalyst_particle_size_nm", ""))
        modifier = first_meaningful(row.get("acid_treatment_type"), row.get("acid_treatment_flag"), default="not_applicable")
        catalysts.append({
            "run_id": row["run_id"], "catalyst_id": row["catalyst_id"],
            "catalyst_label": row.get("catalyst_label") or "not_reported",
            "active_metals": row.get("active_metals") or "not_reported",
            "support_material": row.get("support_material") or "not_reported",
            "promoter": row.get("promoter") or "not_applicable",
            "metal_ratio_original": row.get("metal_ratio_original") or "not_reported",
            "metal_ratio_standardized": row.get("metal_ratio_standardized") or "not_reported",
            "precursor_summary": row.get("precursor_summary") or "not_reported",
            "preparation_method": row.get("preparation_method") or "not_reported",
            "preparation_modifier": modifier,
            "preparation_detail": compact([
                row.get("acid_or_complexing_summary"), row.get("acid_treatment_purpose"),
                row.get("complexing_agent"), row.get("complexing_ratio_original"), row.get("solution_pH"),
            ], default="not_applicable"),
            "drying_condition": row.get("drying_condition") or "not_reported",
            "calcination_condition": row.get("calcination_condition") or "not_reported",
            "reduction_condition": row.get("reduction_condition") or "not_reported",
            "activation_condition": row.get("activation_summary") or "not_reported",
            "post_preparation_condition": compact([row.get("washing_condition"), row.get("crushing_or_sieving_condition")], default="not_applicable"),
            "catalyst_particle_size_mean_nm": mean,
            "catalyst_particle_size_range_nm": size_range,
            "catalyst_particle_size_qualifier": qualifier,
            "BET_surface_area_m2_g": row.get("BET_surface_area_m2_g") or "not_reported",
            "pore_diameter_nm": row.get("pore_diameter_nm") or "not_reported",
            "pore_volume_cm3_g": row.get("pore_volume_cm3_g") or "not_reported",
            "phase_or_state_summary": row.get("phase_or_state_summary") or "not_reported",
            "dispersion_summary": row.get("dispersion_summary") or "not_reported",
            "deactivation_summary": row.get("deactivation_reason") or "not_reported",
            "notes": compact([row.get("notes"), row.get("expected_CNT_type_bias"), row.get("catalyst_assessment")]),
        })

    processes = []
    for row in old_processes:
        other_name, other_original, other_sccm = gas_name_and_flow(row.get("other_gas_flow_original", ""))
        inert_names, inert_originals, inert_sccm_values = [], [], []
        if meaningful(row.get("Ar_flow_original")):
            inert_names.append("Ar"); inert_originals.append(row["Ar_flow_original"])
            if meaningful(row.get("Ar_flow_sccm")): inert_sccm_values.append(row["Ar_flow_sccm"])
        if meaningful(row.get("N2_flow_original")):
            inert_names.append("N2"); inert_originals.append(row["N2_flow_original"])
            if meaningful(row.get("N2_flow_sccm")): inert_sccm_values.append(row["N2_flow_sccm"])
        if other_name.lower() == "he":
            inert_names.append("He"); inert_originals.append(other_original)
            if meaningful(other_sccm): inert_sccm_values.append(other_sccm)
        cofeed_name = other_name if other_name.lower() != "he" and meaningful(other_name) else "not_reported"
        cofeed_original = other_original if cofeed_name != "not_reported" else "not_reported"
        cofeed_sccm = other_sccm if cofeed_name != "not_reported" else "not_reported"
        carbon_source_raw = row.get("carbon_source", "")
        carbon_source = "CH4" if "CH4" in carbon_source_raw or meaningful(row.get("CH4_flow_original")) else "not_applicable"
        pressure_kpa = row.get("pressure_kPa") or "not_reported"
        if not meaningful(pressure_kpa) and str(row.get("pressure_original", "")).lower() in {"1 atm", "ambient", "atmospheric"}:
            pressure_kpa = "101.325"
        processes.append({
            "run_id": row["run_id"], "process_stage_id": row["process_stage_id"],
            "stage_order": row.get("stage_order") or "not_reported", "stage_type": row.get("stage_type") or "not_reported",
            "reactor_type": row.get("reactor_type") or "not_reported", "scale_level": row.get("scale_level") or "not_reported",
            "reactor_material": row.get("reactor_material") or "not_reported", "reactor_size_summary": row.get("reactor_size_summary") or "not_reported",
            "reactor_setup_summary": compact([row.get("catalyst_bed_position"), row.get("temperature_sensor_position")]),
            "catalyst_loading_mass_g": row.get("catalyst_loading_mass_g") or "not_reported",
            "temperature_setpoint_C": first_meaningful(row.get("temperature_setpoint_C"), row.get("temperature_actual_C")),
            "temperature_range_reported_C": row.get("temperature_range_reported_C") or "not_reported",
            "temperature_program_summary": compact([
                f"start {row.get('start_temperature_C')} C" if meaningful(row.get("start_temperature_C")) else "",
                row.get("reported_suitable_temperature"), row.get("reported_optimal_temperature"),
                row.get("reported_failed_temperature"), row.get("temperature_effect_summary"),
            ]),
            "holding_time_min": row.get("holding_time_min") or "not_reported",
            "heating_rate_C_min": row.get("heating_rate_C_min") or "not_reported",
            "cooling_condition": row.get("cooling_condition") or "not_applicable",
            "pressure_original": row.get("pressure_original") or "not_reported", "pressure_kPa": pressure_kpa,
            "carbon_source": carbon_source,
            "carbon_source_flow_original": first_meaningful(row.get("CH4_flow_original"), row.get("natural_gas_flow_original")),
            "carbon_source_flow_sccm": first_meaningful(row.get("CH4_flow_sccm"), row.get("natural_gas_flow_sccm")),
            "reducing_gas": "H2" if meaningful(row.get("H2_flow_original")) or carbon_source_raw == "H2" else "not_applicable",
            "reducing_gas_flow_original": row.get("H2_flow_original") or "not_reported",
            "reducing_gas_flow_sccm": row.get("H2_flow_sccm") or "not_reported",
            "inert_gas": "; ".join(dict.fromkeys(inert_names)) if inert_names else "not_applicable",
            "inert_gas_flow_original": "; ".join(inert_originals) if inert_originals else "not_reported",
            "inert_gas_flow_sccm": "; ".join(inert_sccm_values) if inert_sccm_values else "not_reported",
            "cofeed_or_reactive_gas": cofeed_name, "cofeed_flow_original": cofeed_original, "cofeed_flow_sccm": cofeed_sccm,
            "total_flow_original": row.get("total_flow_original") or "not_reported", "total_flow_sccm": row.get("total_flow_sccm") or "not_reported",
            "gas_composition_summary": compact([row.get("gas_ratio_summary"), row.get("natural_gas_composition"), row.get("other_gas_flow_original")]),
            "GHSV_or_residence_time": row.get("GHSV_or_residence_time") or "not_reported",
            "process_note": row.get("process_note") or "not_reported",
        })

    products = []
    for row in old_products:
        ratio_type, ratio_value = "not_reported", "not_reported"
        if meaningful(row.get("Raman_ID_IG")):
            ratio_type, ratio_value = "ID/IG", row["Raman_ID_IG"]
        elif meaningful(row.get("Raman_IG_ID")):
            ratio_type, ratio_value = "IG/ID", row["Raman_IG_ID"]
        partial = any(row.get(field) == "partial_mixed" for field in ("is_SWCNT", "is_DWCNT", "is_t_MWCNT", "is_MWCNT"))
        mixture = compact([row.get("CNT_type_evidence"), row.get("morphology")]) if partial else "not_reported"
        residue = compact([
            f"ash {row.get('ash_content_wt_percent')} wt%" if meaningful(row.get("ash_content_wt_percent")) else "",
            f"metal residue {row.get('metal_residue_wt_percent')} wt%" if meaningful(row.get("metal_residue_wt_percent")) else "",
        ])
        application = compact([
            row.get("application_related_properties"), row.get("conductivity"), row.get("slurry_viscosity"),
            row.get("tap_density_g_cm3"), row.get("bulk_density_g_cm3"),
        ])
        secondary = compact([
            f"space-time yield={row.get('space_time_yield_kg_m3_h')} kg/m3/h" if meaningful(row.get("space_time_yield_kg_m3_h")) else "",
            f"methane conversion={row.get('methane_conversion_percent')}%" if meaningful(row.get("methane_conversion_percent")) else "",
            f"carbon efficiency={row.get('carbon_efficiency_percent')}%" if meaningful(row.get("carbon_efficiency_percent")) else "",
            f"CNT selectivity in solid carbon={row.get('CNT_selectivity_in_solid_carbon_percent')}%" if meaningful(row.get("CNT_selectivity_in_solid_carbon_percent")) else "",
        ])
        wall_summary = compact([
            row.get("inner_diameter_or_wall_number"),
            f"mean wall number {row.get('wall_number_mean')}" if meaningful(row.get("wall_number_mean")) else "",
        ])
        length_summary = compact([
            row.get("length_summary"), f"mean {row.get('length_mean_um')} um" if meaningful(row.get("length_mean_um")) else "",
        ])
        tga_value = row.get("purity_wt_percent") if meaningful(row.get("purity_wt_percent")) else "not_reported"
        products.append({
            "run_id": row["run_id"], "product_id": row["product_id"], "primary_yield_metric": primary_yield_metric(row),
            "yield_original": row.get("yield_original") or "not_reported", "yield_definition_original": row.get("yield_definition_original") or "not_reported",
            "yield_calculation_method": row.get("yield_calculation_method") or "not_reported",
            "yield_value_standardized": row.get("yield_value_standardized") or "not_reported",
            "yield_unit_standardized": row.get("yield_unit_standardized") or "not_reported",
            "yield_standardization_note": row.get("yield_standardization_note") or "not_reported",
            "CNT_yield_per_catalyst_g_gcat": row.get("CNT_yield_per_catalyst_g_gcat") or "not_reported",
            "CNT_productivity_g_gcat_h": row.get("CNT_productivity_g_gcat_h") or "not_reported",
            "carbon_source_conversion_percent": row.get("methane_conversion_percent") or "not_reported",
            "carbon_conversion_to_solid_percent": row.get("carbon_conversion_to_solid_percent") or "not_reported",
            "secondary_result_summary": secondary, "CNT_type_reported": row.get("CNT_type_reported") or "not_reported",
            "CNT_type_confirmed": row.get("CNT_type_confirmed") or "uncertain", "product_mixture_summary": mixture,
            "CNT_type_evidence": row.get("CNT_type_evidence") or "not_reported",
            "SWCNT_or_few_wall_evidence_summary": row.get("SWCNT_evidence_summary") or "not_reported",
            "RBM_peak_reported": row.get("RBM_peak_reported") or "not_reported",
            "outer_diameter_mean_nm": row.get("outer_diameter_mean_nm") or "not_reported",
            "outer_diameter_range_nm": row.get("outer_diameter_range_nm") or "not_reported",
            "inner_diameter_mean_nm": row.get("inner_diameter_mean_nm") or "not_reported",
            "wall_number_summary": wall_summary, "length_summary": length_summary,
            "morphology": row.get("morphology") or "not_reported", "alignment_or_array": row.get("alignment_or_array") or "not_reported",
            "Raman_ratio_type": ratio_type, "Raman_ratio_value": ratio_value,
            "Raman_laser_wavelength_nm": row.get("Raman_laser_wavelength_nm") or "not_reported",
            "TGA_carbon_content_wt_percent": tga_value, "purified_product_purity_wt_percent": "not_reported",
            "purity_basis": "as_synthesized_TGA_carbon_content" if meaningful(tga_value) else "not_reported",
            "residue_summary": residue, "amorphous_carbon_level": row.get("amorphous_carbon_level") or "not_reported",
            "BET_surface_area_product_m2_g": row.get("BET_surface_area_product_m2_g") or "not_reported",
            "characterization_methods": row.get("characterization_methods") or "not_reported",
            "post_treatment_or_purification": row.get("post_treatment_or_purification") or "not_reported",
            "purification_condition": row.get("purification_condition") or "not_reported",
            "application_property_summary": application, "notes": row.get("notes") or "not_reported",
        })

    process_by_run: dict[str, list[dict[str, str]]] = {}
    for row in processes:
        process_by_run.setdefault(row["run_id"], []).append(row)
    catalyst_by_run = {row["run_id"]: row for row in catalysts}
    old_catalyst_by_run = {row["run_id"]: row for row in old_catalysts}
    product_by_run = {row["run_id"]: row for row in products}
    run_by_id = {row["run_id"]: row for row in source_runs}
    old_cost_by_run = {row["run_id"]: row for row in old_costs}

    costs = []
    for run in source_runs:
        run_id = run["run_id"]
        row = old_cost_by_run[run_id]
        demonstrated = compact([stage.get("scale_level") for stage in process_by_run.get(run_id, [])])
        quantitative_summary = compact([
            f"methane={row.get('methane_consumption_per_kg_CNT')}" if meaningful(row.get("methane_consumption_per_kg_CNT")) else "",
            f"natural gas={row.get('natural_gas_consumption_per_kg_CNT')}" if meaningful(row.get("natural_gas_consumption_per_kg_CNT")) else "",
            f"H2={row.get('H2_consumption_per_kg_CNT')}" if meaningful(row.get("H2_consumption_per_kg_CNT")) else "",
            f"N2/Ar={row.get('N2_or_Ar_consumption_per_kg_CNT')}" if meaningful(row.get("N2_or_Ar_consumption_per_kg_CNT")) else "",
            f"electricity={row.get('electricity_consumption_per_kg_CNT')}" if meaningful(row.get("electricity_consumption_per_kg_CNT")) else "",
            f"variable cost={row.get('total_variable_cost_per_kg_CNT')}" if meaningful(row.get("total_variable_cost_per_kg_CNT")) else "",
        ])
        cost_drivers = compact([
            row.get("catalyst_cost_signal"), row.get("purification_cost_signal"), row.get("waste_treatment_signal"),
            row.get("contains_expensive_metal"), row.get("needs_H2"), row.get("needs_acid_washing"), row.get("major_cost_driver"),
        ])
        costs.append({
            "run_id": run_id, "scale_level_demonstrated": demonstrated,
            "scale_level_claimed": row.get("scale_level_claimed") or "not_reported",
            "scale_evidence_summary": row.get("scale_signal_reported") or "not_reported",
            "reactor_capacity_or_throughput": "not_reported",
            "continuous_operation_time_h": row.get("continuous_operation_time_h") or "not_reported",
            "catalyst_lifetime_or_reuse": old_catalyst_by_run.get(run_id, {}).get("catalyst_lifetime_or_reuse") or "not_reported",
            "catalyst_reuse_cycles": row.get("catalyst_reuse_cycles") or "not_reported",
            "batch_stability": row.get("batch_stability") or "not_reported", "scale_up_issue": row.get("scale_up_issue") or "not_reported",
            "quantitative_cost_reported": row.get("quantitative_cost_reported") or "not_reported",
            "quantitative_cost_summary": quantitative_summary, "cost_driver_summary": cost_drivers,
            "safety_risk": row.get("safety_risk") or "not_reported", "emission_or_waste": row.get("emission_or_waste") or "not_reported",
            "industrial_readiness_assessment": row.get("reviewed_suitable_condition") or "not_assessed",
            "reproduction_value": row.get("reproduction_value") or "not_assessed",
            "reproduction_priority": row.get("reproduction_priority") or "not_assessed",
            "industrial_value_score": row.get("industrial_value_score") or "not_assessed",
            "recommended_next_action": row.get("recommended_next_action") or "not_assessed",
            "review_note": compact([row.get("review_note"), row.get("missing_critical_fields")]),
        })

    evidence = []
    sequence = 1
    source_code = source_id.split("_", 1)[0]
    def add_row_evidence(table: str, old_rows: list[dict[str, str]], target_field: str, summary_fields: list[str], id_field: str) -> None:
        nonlocal sequence
        for row in old_rows:
            evidence_id = f"EVID_{source_code}_{sequence:04d}"
            sequence += 1
            summary = compact([row.get(field) for field in summary_fields])
            evidence.append({
                "evidence_id": evidence_id, "source_id": source_id, "run_id": row.get("run_id") or "not_applicable",
                "target_table": table, "target_record_id": row.get(id_field) or row.get("run_id"),
                "target_fields": target_field, "evidence_type": "record_support",
                "value_status": "calculated" if "calculated" in compact([row.get("evidence_text"), row.get("notes"), row.get("process_note")]).lower() else "reported",
                "source_section": source_section, "source_locator": row.get("evidence_location") or "not_reported",
                "source_object_ref": source_object_ref(row.get("evidence_location", "")),
                "evidence_text": row.get("evidence_text") or "not_excerpted", "evidence_summary": summary,
                "confidence": row.get("confidence") or "not_reported", "linked_issue_id": "not_applicable", "notes": "migrated_from_v0.3_row_evidence",
            })
    add_row_evidence("catalyst_system", old_catalysts, "record_level", ["catalyst_label", "active_metals", "preparation_method"], "catalyst_id")
    add_row_evidence("reactor_process_gas", old_processes, "record_level", ["stage_type", "temperature_setpoint_C", "gas_ratio_summary", "process_note"], "process_stage_id")
    add_row_evidence("yield_quality", old_products, "record_level", ["yield_original", "CNT_type_confirmed", "morphology"], "product_id")
    add_row_evidence("cost_scale_review", old_costs, "record_level", ["scale_signal_reported", "scale_level_claimed", "review_note"], "run_id")

    issues = []
    for obs_index, observation in enumerate(observations, start=1):
        obs_type = str(observation.get("observation_type") or "other")
        tags = [str(item) for item in observation.get("topic_tags", [])]
        is_issue = obs_type in {"quality_warning", "data_gap"}
        issue_id = f"ISS_{source_code}_{len(issues) + 1:03d}" if is_issue else "not_applicable"
        target_table, target_record_id, target_run_id = map_observation_target(
            observation, source_id, run_by_id, catalyst_by_run, process_by_run, product_by_run
        )
        evidence_id = f"EVID_{source_code}_{sequence:04d}"
        sequence += 1
        summary = str(observation.get("value_summary") or "not_reported")
        original_text = str(observation.get("original_text") or "not_excerpted")
        evidence.append({
            "evidence_id": evidence_id, "source_id": source_id, "run_id": target_run_id,
            "target_table": target_table, "target_record_id": target_record_id,
            "target_fields": issue_target_field(tags) if is_issue else "record_level",
            "evidence_type": "source_observation", "value_status": "reported" if original_text != "not_excerpted" else "inferred",
            "source_section": "not_separately_reported", "source_locator": observation.get("evidence_location") or "not_reported",
            "source_object_ref": source_object_ref(str(observation.get("evidence_location") or "")),
            "evidence_text": original_text, "evidence_summary": summary,
            "confidence": observation.get("confidence") or "not_reported", "linked_issue_id": issue_id,
            "notes": compact(["tags=" + ";".join(tags), observation.get("why_valuable"), f"legacy_observation_id={observation.get('observation_id')}"]),
        })
        if is_issue:
            conflict = "source_conflict" in ";".join(tags).lower() or "conflict" in summary.lower() or "冲突" in summary
            issues.append({
                "issue_id": issue_id, "source_id": source_id, "run_id": target_run_id,
                "issue_type": "source_conflict" if conflict else ("critical_data_gap" if obs_type == "data_gap" else "quality_warning"),
                "target_table": target_table, "target_record_id": target_record_id,
                "target_field": issue_target_field(tags), "issue_summary": summary,
                "conflicting_values": original_text if conflict else "not_applicable",
                "evidence_ids": evidence_id, "severity": "high" if conflict else "medium",
                "review_status": "open", "reviewer": "not_assigned", "reviewed_at": "not_applicable",
                "resolution": "pending_human_review", "notes": observation.get("why_valuable") or "not_reported",
            })

    table_rows = {
        "source_master": source_master, "source_run": source_runs, "catalyst_system": catalysts,
        "reactor_process_gas": processes, "yield_quality": products, "cost_scale_review": costs,
        "evidence_index": evidence, "review_issue_log": issues,
    }
    for table_name, rows in table_rows.items():
        spec = schema["tables"][table_name]
        write_csv(directory / spec["filename"], spec["columns"], rows)
    print(f"MIGRATED {directory.name}: runs={len(source_runs)}, evidence={len(evidence)}, issues={len(issues)}")


def repair_source_level_targets(directory: Path, schema: dict) -> None:
    """Keep source-level observations attached to a real source_master field."""
    evidence_path = directory / "evidence_index.csv"
    issue_path = directory / "review_issue_log.csv"
    if not evidence_path.exists() or not issue_path.exists():
        return
    evidence_rows = read_csv(evidence_path)
    issue_rows = read_csv(issue_path)
    changed = False
    for row in evidence_rows:
        if row.get("target_table") == "source_master" and row.get("target_fields") != "notes":
            row["target_fields"] = "notes"
            changed = True
    for row in issue_rows:
        if row.get("target_table") == "source_master" and row.get("target_field") != "notes":
            row["target_field"] = "notes"
            changed = True
    if changed:
        write_csv(evidence_path, schema["tables"]["evidence_index"]["columns"], evidence_rows)
        write_csv(issue_path, schema["tables"]["review_issue_log"]["columns"], issue_rows)
        print(f"REPAIRED {directory.name}: source-level targets -> source_master.notes")


def main() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    metadata_rows = read_csv(METADATA_PATH)
    metadata = {row["source_id"]: row for row in metadata_rows}
    build_dictionary(schema)
    for directory in sorted(INTERIM.glob("P00[1-6]_*/")):
        migrate_source(directory, schema, metadata)
        repair_source_level_targets(directory, schema)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    for table_name, spec in schema["tables"].items():
        write_csv(TEMPLATE_DIR / spec["filename"], spec["columns"], [])


if __name__ == "__main__":
    main()
