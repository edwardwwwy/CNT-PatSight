# CNT-PatSight

CNT-PatSight 是一个面向碳纳米管（CNT）研发的数据整理项目，目标是把论文、专利和后续实验记录中的 CNT 制备信息，转化为 **结构化、可追溯、可比较** 的研发数据。

当前阶段不是做网页、看板、爬虫或机器学习系统，而是先跑通一个小样本闭环：

```text
10 篇高相关论文/专利
        ↓
约 30 条 run-level 实验记录
        ↓
LLM 辅助抽取
        ↓
人工复核
        ↓
验证 5 张主表是否够用
```

---

## 1. 当前阶段：v0.1 小样本验证

### v0.1 目标

v0.1 的目标是验证 CNT 文献/专利能否被稳定抽取成结构化数据，而不是一次性搭建完整软件系统。

第一阶段成功标准：

- 收集 10 篇高质量论文或专利；
- 抽取约 30 条可复核的 `run_id` 记录；
- 每条关键数据都有原文证据；
- 能回答初步问题：哪些催化剂、温度、气体程序、产物类型和产率值得进一步关注；
- 发现哪些字段经常有数据，哪些字段长期为空，再决定是否修改 schema。

### 当前优先范围

优先关注：

- CVD / CCVD / 催化裂解 / 催化热解制备 CNT；
- CH4、天然气或富甲烷气体作为碳源；
- 工业生产相关的 MWCNT 或 t-MWCNT；
- 催化剂配方、载体、助剂、制备和活化；
- 温度、时间、压力、气体组成、流量、反应器类型；
- 产率、生产率、纯度、灰分、金属残留、缺陷、管径和形貌；
- 放大、连续运行、催化剂寿命、后处理负担和安全环保信息。

这只是当前优先级，不是永久边界。其他碳源、SWCNT、VACNT、CNT fiber、反应器设计、失败模式、催化剂机理等信息，如果有研发价值，可以进入观察池，不应直接丢弃。

### 当前不做

v0.1 暂不做：

- 自动爬虫；
- 网页或 dashboard；
- 复杂数据库；
- 机器学习预测；
- 工业评分系统；
- 自动生成实验方案；
- 将内部实验数据发送到外部 API。

---

## 2. 核心原则

### 2.1 Schema strict, capture broad

本项目采用双层数据结构：

```text
5 张主表：严格、可比较、可复核
观察池：宽松保留暂时无法结构化但有价值的信息
```

也就是说：

- 主表字段不要随便增加；
- 不能形成完整实验记录的信息不要硬塞进主表；
- 但有潜在研发价值的信息也不要丢掉；
- 放不进主表的信息进入 `source_observations.jsonl`，等待后续人工判断是否升级为正式字段。

### 2.2 证据优先

关键字段必须尽量保留：

```text
value
unit
original_value
evidence_text
evidence_location
source_section
value_status
confidence
```

其中 `value_status` 建议使用：

```text
reported / inferred / calculated / review_assessment
```

第一轮抽取以 `reported` 为主。原文没有的信息保持 `null`、`not_reported` 或空值，不允许为了填表而猜测。

### 2.3 不把一篇论文当成一条记录

本项目以实验或专利实施例为单位，而不是以论文为单位。

一个 `run_id` 表示：

```text
一个明确的催化剂体系
+ 一个明确的 CVD 工艺程序
+ 一个对应的产物 / 产率 / 表征结果
= 一个 run_id
```

如果同一篇论文比较不同催化剂、不同温度、不同气体比例、不同时间或不同产物结果，应拆成多个 `run_id`。

### 2.4 不强行统一不可比较指标

特别注意产率和生产率。以下指标不能默认互相比较：

```text
g CNT / g catalyst
mg CNT / g catalyst / h
carbon yield %
mass gain %
methane conversion %
array height growth rate
selectivity
```

必须保留原始定义和单位。只有计算依据清楚时，才做标准化。

---

## 3. 数据流程

推荐工作流：

```text
1. 检索论文 / 专利 / 报告
2. 填入 source candidate 信息
3. 相关性筛选
4. 复制关键文本：Abstract、Experimental、表格、图注、Results 关键段落
5. LLM 按 prompt 抽取 JSON
6. 人工核对催化剂、温度、气体、产率、CNT 类型和证据
7. 写入 5 张主表
8. 无法进入主表但有价值的信息写入 observation 池
9. 小样本分析
10. 决定是否调整字段
```

不建议第一阶段直接进行全文自动抽取。先用人工选择的高质量论文跑通闭环。

---

## 4. 筛选分级

文献和专利筛选不是简单删除，而是分级处理。

| 等级 | 含义 | 处理方式 |
|---|---|---|
| `formal_extract` | 有催化剂、工艺条件、产物/产率，能形成 run_id | 进入 5 张主表 |
| `candidate_extract` | 可能能形成 run_id，但证据不完整 | 暂存，等待人工复核 |
| `source_observation_only` | 不能形成完整 run，但有研发价值 | 进入观察池 |
| `background_reference` | 综述、机理、背景或字段设计参考 | 保留为背景 |
| `reject` | 明显无关 | 不进入项目数据 |

不要因为一篇文献不是 CH4-MWCNT 就直接丢弃。如果它提供了催化剂制备、活化、酸化、温度影响、CNT 类型证据、失败模式、反应器设计、放大风险或安全环保信息，可以进入观察池。

---

## 5. v0.1 数据结构

v0.1 使用 5 张主表：

```text
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
```

这 5 张表是当前工作模型，不是最终数据库本体。第一阶段默认不新增主表，不随意扩展字段。

另外设置一个观察池：

```text
data/interim/source_observations.jsonl
```

它不是正式业务表，而是用于保存暂时无法进入主表的有价值信息。

---

## 6. 五张主表的职责

### 6.1 `source_run`

记录资料来源和 run 索引。

核心内容：

- source_id；
- run_id；
- source_type：paper / patent / review / internal；
- source_title；
- year；
- authors_or_assignee；
- DOI、专利号或链接；
- data_type：experiment / patent_example / patent_claim / review_summary；
- run_label；
- target_track；
- relevance_class；
- extraction_status；
- extraction_confidence；
- run_summary；
- notes。

`combo_key` 可以作为后续分析脚本生成的派生字段，不建议由 LLM 第一轮手动填写。

---

### 6.2 `catalyst_system`

记录催化剂体系。

核心内容：

- active_metals：Fe、Co、Ni、Mo 等；
- support_material：MgO、Al2O3、SiO2、CaCO3 等；
- promoter；
- metal_ratio_original；
- metal_ratio_standardized；
- precursor_summary；
- preparation_method；
- acid_or_complexing_summary；
- acid_treatment_flag；
- acid_treatment_type；
- drying_condition；
- calcination_condition；
- reduction_condition；
- crushing_or_sieving_condition；
- catalyst_particle_size_nm；
- BET_surface_area_m2_g；
- phase_or_state_summary；
- evidence_text；
- evidence_location；
- confidence；
- notes。

酸化、络合、浸渍、沉淀、干燥、煅烧、还原、破碎等都归入此表。酸化信息不单独建表。

推荐酸处理类型：

```text
support_acidification
catalyst_acidification
acid_complexing
unknown
not_reported
```

如果文献只写一句 `treated with HNO3` 或 `citric acid was used as complexing agent`，不要强拆为过多字段，写入 summary 和 evidence 即可。

---

### 6.3 `reactor_process_gas`

记录具体工艺阶段的反应器、温度和气体程序。

核心内容：

- run_id；
- process_stage_id；
- stage_order；
- stage_type；
- reactor_type；
- scale_level；
- catalyst_loading_mass；
- temperature_setpoint_c；
- temperature_actual_c；
- holding_time_min；
- heating_rate_c_min；
- cooling_condition；
- pressure_original；
- carbon_source；
- carbon_source_flow_sccm；
- H2_flow_sccm；
- N2_flow_sccm；
- Ar_flow_sccm；
- other_gas_flow_sccm；
- total_flow_sccm；
- gas_ratio_summary；
- process_note；
- evidence_text；
- evidence_location；
- confidence。

推荐 `stage_type`：

```text
purge
heating
drying
calcination
reduction
activation
growth
cooling
post_treatment
other
```

温度处理原则：

- 生长温度、煅烧温度、还原温度必须通过 `stage_type` 区分；
- 不要把煅烧温度误填为 CNT 生长温度；
- `reported_optimal_temperature`、`suitable_temperature_range`、`temperature_effect_summary` 暂不作为 v0.1 主字段，优先放入 `process_note` 或观察池。

---

### 6.4 `yield_quality`

记录产率、CNT 类型、产品质量和表征。

核心内容：

- yield_original；
- yield_value；
- yield_unit；
- yield_definition；
- yield_standardization_status；
- CNT_productivity；
- methane_conversion_percent；
- carbon_efficiency_percent；
- CNT_type_reported；
- CNT_type_confirmed；
- CNT_type_confidence；
- CNT_type_evidence；
- RBM_peak_reported；
- outer_diameter_mean_nm；
- outer_diameter_range_nm；
- inner_diameter_or_wall_number；
- length_summary；
- morphology；
- alignment_or_array；
- Raman_ID_IG；
- purity_wt_percent；
- ash_content_wt_percent；
- metal_residue_wt_percent；
- amorphous_carbon_level；
- characterization_methods；
- post_treatment_or_purification；
- application_related_properties；
- image_or_figure_ref；
- evidence_text；
- evidence_location；
- confidence；
- notes。

CNT 类型建议使用：

```text
SWCNT
DWCNT
t-MWCNT
MWCNT
VACNT
CNT_fiber
mixed
unknown
```

SWCNT 判断要谨慎。不能只看标题或作者声称。优先证据包括：

- TEM / HRTEM 直接看到单壁结构；
- Raman RBM 峰；
- 直径分布支持单壁；
- 文中明确排除多壁 CNT 或碳纤维。

若证据不足：

```text
CNT_type_reported: SWCNT
CNT_type_confirmed: uncertain
CNT_type_confidence: low
CNT_type_evidence: claimed by authors, but RBM/TEM evidence not found
```

---

### 6.5 `cost_scale_review`

记录原文明确给出的放大、成本、安全和工业相关信息，以及人工复核后的缺失项说明。

v0.1 中此表不要做工业评分。第一轮 LLM 不应自动生成“高工业价值”“值得复现”等强判断。

核心内容：

- scale_level_claimed；
- continuous_operation_time_h；
- catalyst_reuse_cycles；
- needs_H2；
- needs_acid_washing；
- scale_up_issue；
- safety_risk；
- missing_critical_fields；
- industrial_value_note；
- recommended_next_action；
- reviewer_notes；
- evidence_text；
- evidence_location；
- confidence。

其中：

- `scale_level_claimed`、`continuous_operation_time_h`、`catalyst_reuse_cycles`、`safety_risk` 可以来自原文；
- `industrial_value_note` 和 `recommended_next_action` 更适合人工 review 或二次分析后填写；
- 如果没有真实成本、电耗、连续运行、催化剂寿命、甲烷转化率等信息，应写入 `missing_critical_fields`，不要让 LLM 推测。

---

## 7. 观察池：`source_observations.jsonl`

观察池用于保存不能稳定进入五张主表，但可能对研发有价值的信息。

适合进入观察池的信息：

- 机制解释；
- 失败条件；
- 催化剂失活；
- 温度影响；
- 酸处理启发；
- 反应器设计；
- 专利装置结构；
- 安全环保信息；
- 其他碳源或 CNT 类型的可迁移信息；
- 图注、讨论段或综述中有价值但不能形成 run 的信息。

建议 JSONL 格式：

```json
{
  "observation_id": "OBS_P001_001",
  "source_id": "P001",
  "related_run_id": null,
  "observation_type": "temperature_effect",
  "related_table": "reactor_process_gas",
  "related_field": "process_note",
  "topic_tags": ["CH4-CVD", "Fe-Mo/MgO", "temperature", "deactivation"],
  "value_summary": "High temperature increased methane decomposition but may accelerate catalyst deactivation.",
  "original_text": "original sentence from the source",
  "evidence_location": "Results section, paragraph 3",
  "why_valuable": "May help define upper temperature limit for Fe-Mo/MgO methane CVD.",
  "action_status": "keep_for_review",
  "promotion_decision": "not_promoted_yet",
  "confidence": "medium",
  "notes": ""
}
```

当同类 observation 在 20–30 篇样本中频繁出现，并且确实影响研发分析时，再考虑升级为正式字段。

---

## 8. 专利处理原则

专利资料必须区分不同文本区域。

| 专利内容 | 是否可形成 run |
|---|---|
| 实施例 / Example / Embodiment | 可以，若有具体条件和结果 |
| 具体实施方式 | 可以，若有明确配方、工艺和产物 |
| 权利要求 / Claim | 不直接形成 run |
| 背景技术 | 只作为背景或 observation |
| 宽泛保护范围 | 不当作真实实验数据 |

例如：

```text
催化剂可选 Fe、Co、Ni，温度范围 500–1100 ℃。
```

这通常是保护范围，不是实验结果。可以记录为 observation，但不能直接进入 `reactor_process_gas` 作为真实工艺窗口。

---

## 9. 推荐目录结构

```text
CNT-PatSight/
  README.md
  AGENTS.md

  skills/
    cnt-patsight/
      SKILL.md
      references/
        schema.md

  data/
    raw/
      metadata/
      papers/
      patents/
    interim/
      parsed_text/
      extraction_json/
      source_observations.jsonl
    processed/
      source_run.csv
      catalyst_system.csv
      reactor_process_gas.csv
      yield_quality.csv
      cost_scale_review.csv
    dictionaries/
      synonym_dictionary.csv
      unit_rules.csv
      catalyst_terms.csv
    internal/
      README.md

  docs/
    field_definitions.md
    extraction_rules.md
    patent_rules.md
    screening_rules.md
    repository_structure.md

  prompts/
    01_screening_prompt.md
    02_extraction_prompt.md
    03_normalization_prompt.md

  scripts/
    validation/
    analysis/

  notebooks/
  reports/
  tests/
```

---

## 10. 建议的第一轮操作

### Step 1：建立候选池

先找 10 篇高质量论文或专利，优先选择：

- 有催化剂制备；
- 有 CVD 条件；
- 有气体流量；
- 有温度和时间；
- 有产率或产品质量；
- 有 SEM/TEM/Raman/TGA 等表征；
- 有多组对比实验。

### Step 2：复制关键文本

每篇优先复制：

```text
Abstract
Experimental / Materials and methods
Catalyst preparation
CNT synthesis / CVD growth
Characterization
Results 中的关键段落
表格
图注
Supplementary information 中的实验条件
```

### Step 3：LLM 抽取

LLM 第一轮只做：

- 判断文献等级；
- 拆分 run_id；
- 抽取 reported facts；
- 保留 evidence；
- 标记 uncertainty；
- 把非 run 但有价值的信息放入 observation。

不要让 LLM 第一轮做工业评分或推荐实验。

### Step 4：人工复核

人工重点核对：

- 催化剂成分和比例；
- 煅烧 / 还原 / 生长温度是否混淆；
- CH4 / H2 / N2 / Ar 流量是否分清；
- 反应时间是否对应 CNT 生长阶段；
- 产率定义和单位；
- CNT 类型，尤其是否真的支持 SWCNT；
- 专利 claim 是否被误当成实验数据。

### Step 5：小样本分析

完成 30 条左右记录后再分析：

- 哪些催化剂体系出现频率高；
- CH4-CVD 温度和气体窗口；
- 高产率路线的共同条件；
- 产品质量和产率是否冲突；
- 哪些字段经常缺失；
- 哪些 observation 值得升级为正式字段。

---

## 11. 保密说明

如果后续加入公司或实验室内部实验数据，应默认视为敏感数据。

建议原则：

- 公开文献和专利数据可以进入公开数据区；
- 内部实验数据单独存放在 `data/internal/`；
- 不将内部配方、供应商报价、未公开实验结果发送到外部 API；
- 不把内部数据提交到公开仓库；
- 模型调用和报告分享应遵守所在机构或公司的保密要求。

---

## 12. 路线图

### v0.1：小样本验证

- 10 篇论文/专利；
- 约 30 条 run；
- 5 张主表；
- 观察池；
- 人工复核；
- 初步统计。

### v0.2：字段稳定与规则文档

- 完善 `field_definitions.md`；
- 完善 `extraction_rules.md`；
- 建立同义词和单位规则；
- 形成稳定 prompt；
- 输出第一份小样本分析报告。

### v0.3：半自动抽取

- 批量处理 metadata；
- 半自动筛选；
- LLM JSON 输出校验；
- 表格验证脚本；
- 统计图表。

### Future

- 扩展专利样本；
- 融合内部实验数据；
- 成本和放大模型；
- 工艺窗口分析；
- 机器学习或贝叶斯优化；
- 面向研发组的实验建议报告。

---

## 13. 成功定义

CNT-PatSight 的成功不是收集很多 PDF，也不是生成很多摘要。

真正有价值的结果是：

- 能看出哪些催化剂体系被尝试过；
- 能知道它们对应什么 CVD 条件；
- 能比较产率、纯度、管径、缺陷和后处理负担；
- 能追溯每个关键值来自哪一句原文；
- 能区分真实实验、专利保护范围和作者推测；
- 能发现值得研发组复现、改造或避开的路线。

一句话概括：

> CNT-PatSight 不是论文摘要项目，而是 CNT-CVD 研发数据资产的构建项目。
