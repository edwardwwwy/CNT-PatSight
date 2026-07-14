# CNT-PatSight

CNT-PatSight 是一个面向碳纳米管（CNT）研发的数据工作区，目标是把分散在论文、专利、报告和实验记录中的 CNT 制备信息，整理成结构化、可追溯、可比较的研发数据。

当前项目重点关注：**CVD / CCVD 法制备碳纳米管，尤其是以甲烷（CH4）或天然气为碳源制备多壁碳纳米管（MWCNT）的工业生产优化**。

本项目现阶段的核心不是做网页或展示系统，而是先建立可靠的数据流程：

```text
公开文献 / 专利 / 实验记录
        ↓
资料检索与候选池构建
        ↓
相关性筛选
        ↓
结构化字段抽取
        ↓
证据保留与人工校正
        ↓
标准化数据库
        ↓
统计分析与研发建议
```

---

## 项目背景

CNT 相关研究中有大量有价值的信息，例如催化剂配方、载体、助剂、CVD 温度、气体流量、反应时间、产率、产品质量和成本指标等。但这些信息通常分散在论文实验部分、图表、专利实施例、补充材料和表征结果中，直接阅读和比较效率很低。

CNT-PatSight 希望解决的问题是：

> 将零散的 CNT 文献和专利信息，转化为研发人员可以查询、比较、复现和分析的结构化数据。

它不是简单的论文摘要工具，而是面向工业 CNT 研发的数据工程项目。

---

## 当前研究重点

当前优先范围包括：

- CVD / CCVD / 催化裂解 / 催化热解制备 CNT；
- 甲烷 CH4、天然气或富甲烷气体作为碳源；
- 多壁碳纳米管 MWCNT；
- 工业生产优化；
- 催化剂配方、载体、助剂、制备与活化；
- CVD 条件，包括温度、时间、压力、气体组成、流量和反应器类型；
- 产率、生产率、甲烷转化率、产品质量、纯度、缺陷、灰分和成本；
- 可放大性、连续运行、催化剂寿命、后处理负担和安全环保问题。

该范围是当前工作重点，不是永久边界。后续可以扩展到其他碳源、其他 CNT 类型、公司内部实验数据、成本模型、机器学习建模或应用端产品指标。

---

## 项目目标

CNT-PatSight 的长期目标是建立一个 CNT 研发数据系统，用于支持：

- 文献和专利情报分析；
- 催化剂体系对比；
- CVD 工艺窗口分析；
- 产率与产品质量关系分析；
- 工业可行性评价；
- 实验复现和实验设计；
- 内部实验数据整合；
- 后续机器学习或统计建模；
- 给 CNT 研发组输出可执行的实验建议。

最终希望回答的问题包括：

- 哪些催化剂体系被反复报道？
- 哪些载体和助剂更常出现在高产率体系中？
- 甲烷 CVD 制 MWCNT 的常见温度、时间和气体窗口是什么？
- 哪些路线产率高，但产品质量或成本不理想？
- 哪些专利路线具有工业放大价值？
- 哪些条件值得研发组优先复现或改造？

---

## 数据理念

本项目强调三点：

1. **结构化**：把文献和专利中的信息转化为统一字段。
2. **可追溯**：关键字段必须保留原文证据、位置和置信度。
3. **可比较**：单位、名称、产率定义和数据来源需要标准化或明确标注。

重要原则：

- 不把没有证据的信息填入关键字段；
- 不把专利权利要求中的宽泛范围当成真实实验数据；
- 不强行统一不可比较的产率定义；
- 不把一篇论文简单当成一条实验记录；
- 不追求数量优先，而优先保证数据质量和复现价值。

---

## 推荐数据结构

当前推荐继续使用 **5 张主表** 组织数据，不再额外增加表：

```text
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
```

这 5 张表对应 CNT 研发的主链条：

```text
资料来源 / 实验编号
        ↓
催化剂体系
        ↓
反应器、温度程序和气体程序
        ↓
产率、CNT 类型和产品质量
        ↓
工业价值、放大风险和下一步建议
```

设计原则：

- 不为每一个可能出现的细节单独建表；
- 能稳定抽取、对研发判断有用的信息作为主字段；
- 细节不完整但有价值的信息，用 `summary`、`note`、`evidence_text` 记录；
- 酸化、催化剂组合、适应温度、是否单壁 CNT 等信息放入对应主表，不新增表；
- “最佳条件”“适应温度窗口”“工业推荐”属于分析判断，应与原始实验条件区分记录。

---

### 1. source_run

记录数据来源和实验记录索引，包括论文、专利、报告或内部实验批次。

关注内容：

- 来源类型；
- 标题、年份、作者或申请人；
- DOI、专利号或链接；
- 是否为论文实验、专利实施例、综述或内部记录；
- 该条记录是否能形成明确的 run_id；
- 目标路线，如工业 MWCNT、SWCNT、t-MWCNT、VACNT、CNT fiber；
- 催化剂-碳源-产品类型组合键，用于后续聚合分析；
- 相关性和抽取置信度。

建议字段：

```text
source_id
run_id
source_type
source_title
year
authors_or_assignee
doi_or_patent_no
link
source_section
data_type
run_label
target_track
combo_key
relevance_class
extraction_status
extraction_confidence
run_summary
notes
```

其中：

```text
combo_key = catalyst_key + carbon_source + reactor_type + CNT_type
```

示例：

```text
Fe-Mo/MgO | CH4 | fixed-bed CCVD | t-MWCNT
Ni/Al2O3 | CH4 | fluidized-bed CVD | MWCNT
Co-Mo/MgO | C2H2 | thermal CVD | SWCNT
```

`combo_key` 不是新的实验事实，而是便于后续统计“哪些组合更常见、哪些组合更高产、哪些组合更容易得到 SWCNT/MWCNT”的分析索引。

---

### 2. catalyst_system

记录催化剂体系，包括活性金属、载体、助剂、前驱体、制备方法、酸化/络合/活化处理和催化剂基础性质。

关注内容：

- 活性金属，如 Fe、Ni、Co、Mo；
- 金属比例；
- 载体，如 MgO、Al2O3、SiO2、CaCO3；
- 助剂或促进剂；
- 前驱体；
- 制备方法；
- 酸化、络合、浸渍、沉淀、洗涤、干燥、焙烧、还原、破碎等处理；
- 催化剂粒径、比表面积、孔结构、分散度和寿命；
- 催化剂是否更倾向于生成 SWCNT、t-MWCNT 或 MWCNT。

建议字段：

```text
run_id
catalyst_id
catalyst_label
catalyst_key
active_metals
support_material
promoter
metal_ratio_original
metal_ratio_standardized
precursor_summary
preparation_method
acid_or_complexing_summary
acid_treatment_flag
acid_treatment_purpose
drying_condition
calcination_condition
reduction_condition
crushing_or_sieving_condition
catalyst_particle_size_nm
BET_surface_area_m2_g
pore_diameter_nm
pore_volume_cm3_g
phase_or_state_summary
dispersion_summary
expected_CNT_type_bias
catalyst_lifetime_or_reuse
catalyst_assessment
evidence_text
evidence_location
confidence
notes
```

#### 酸化信息如何记录

酸化相关信息放在 `catalyst_system` 中，不单独建表。

需要区分三类情况：

```text
support_acidification      载体酸化
catalyst_acidification     催化剂酸化
acid_complexing            酸作为络合剂或溶胶-凝胶组分
```

若文献只给一句话，例如 “treated with HNO3” 或 “citric acid was used as complexing agent”，不要强行拆成过多字段，直接写入：

```text
acid_or_complexing_summary
acid_treatment_flag
acid_treatment_purpose
```

示例：

```text
acid_or_complexing_summary:
citric acid as complexing agent; metal ion:citric acid = 1:1.2; solution pH≈1.0

acid_treatment_flag:
yes

acid_treatment_purpose:
complexing / improve dispersion / prevent precipitation of Mo species
```

若文献明确给出酸种、浓度、时间、温度、洗涤终点，则可以写进 summary 或 notes，不要求每篇都拆成固定列。

---

### 3. reactor_process_gas

记录反应器、温度程序和气体程序。该表是实验复现和工艺窗口分析的核心表。

关注内容：

- 反应器类型，如固定床、流化床、旋转炉、浮动催化；
- 设备尺度，如实验室、中试或工业；
- 催化剂装填量、床层位置和热电偶位置；
- 吹扫、升温、还原、预处理、生长、降温等阶段；
- 温度、时间、压力；
- CH4、天然气、H2、N2、Ar 等气体流量；
- 气体比例、空速和停留时间；
- 对某一催化剂组合报告的适应温度、最佳温度或失败温度。

建议字段：

```text
run_id
process_stage_id
stage_order
stage_type
reactor_type
scale_level
reactor_size_summary
catalyst_loading_mass
catalyst_bed_position
temperature_setpoint_C
temperature_actual_C
temperature_range_reported_C
holding_time_min
heating_rate_C_min
cooling_condition
pressure_original
carbon_source
CH4_flow_sccm
natural_gas_flow_sccm
H2_flow_sccm
N2_flow_sccm
Ar_flow_sccm
other_gas_flow_sccm
total_flow_sccm
gas_ratio_summary
GHSV_or_residence_time
reported_suitable_temperature
reported_optimal_temperature
temperature_effect_summary
process_note
evidence_text
evidence_location
confidence
```

#### 温度信息如何记录

温度信息分三层：

```text
temperature_setpoint_C
```

记录该 run 的实际设定生长温度，例如 900 ℃。

```text
temperature_range_reported_C
```

记录文献或专利中明确给出的可行温度范围，例如 700–900 ℃。如果只是专利权利要求中的宽泛保护范围，应在 notes 中标注，不直接当作真实实验窗口。

```text
reported_optimal_temperature / temperature_effect_summary
```

记录作者明确比较后认为较优的温度，或温度变化对产率、纯度、管径、缺陷的影响。

示例：

```text
temperature_setpoint_C: 900
reported_suitable_temperature: not_reported
reported_optimal_temperature: 900 for this catalyst/process
temperature_effect_summary: same growth temperature used for SG-1/SG-2/SG-3; catalyst decomposition atmosphere was the main compared variable
```

这样可以支持后续回答：

- 某催化剂组合常见生长温度是多少？
- 哪些组合适合高温 CH4-CVD？
- 哪些组合在高温下容易烧结、积碳或生成碳纤维？
- SWCNT 与 MWCNT 对温度窗口是否不同？

---

### 4. yield_quality

记录产率、物料衡算、CNT 类型确认和产品质量。

关注内容：

- 原始产率和标准化产率；
- g CNT / g catalyst；
- CNT 生产率；
- 甲烷转化率；
- CNT 类型确认；
- 是否为 SWCNT、DWCNT、t-MWCNT、MWCNT、VACNT、CNT fiber 或混合产物；
- SWCNT 证据，如 Raman RBM、TEM、直径范围、壁数；
- 管径、管长、壁层数、形貌；
- Raman ID/IG、纯度、灰分、金属残留；
- SEM、TEM、Raman、TGA、XPS 等表征方法；
- 导电率、分散性、浆料黏度等应用相关指标；
- 后处理和纯化条件。

建议字段：

```text
run_id
yield_original
yield_definition_original
yield_value_standardized
yield_unit_standardized
CNT_productivity
methane_conversion_percent
carbon_efficiency_percent
CNT_type_reported
CNT_type_confirmed
is_SWCNT
is_DWCNT
is_t_MWCNT
is_MWCNT
CNT_type_evidence
SWCNT_evidence_summary
RBM_peak_reported
outer_diameter_mean_nm
outer_diameter_range_nm
inner_diameter_or_wall_number
length_summary
morphology
alignment_or_array
Raman_ID_IG
Raman_IG_ID
purity_wt_percent
ash_content_wt_percent
metal_residue_wt_percent
amorphous_carbon_level
characterization_methods
post_treatment_or_purification
application_related_properties
image_or_figure_ref
evidence_text
evidence_location
confidence
notes
```

#### 是否单壁 CNT 如何记录

是否单壁放在 `yield_quality` 中，因为它是产物结果，不是催化剂字段。

推荐使用：

```text
CNT_type_reported
CNT_type_confirmed
is_SWCNT
SWCNT_evidence_summary
RBM_peak_reported
```

不要只看作者标题里写了 SWCNT 就直接确认。优先证据包括：

- TEM / HRTEM 看到单壁结构；
- Raman 出现 RBM 峰；
- 直径分布符合 SWCNT 范围；
- 文中明确排除了多壁或碳纤维。

如果文献只是声称 SWCNT 但没有足够证据：

```text
CNT_type_reported: SWCNT
CNT_type_confirmed: uncertain
is_SWCNT: unknown
SWCNT_evidence_summary: claimed by authors, but RBM/TEM evidence not found
```

`t-MWCNT` 或 few-walled CNT 不应强行归为 SWCNT。它们可以单独记录为：

```text
CNT_type_confirmed: t-MWCNT
is_SWCNT: no
is_t_MWCNT: yes
inner_diameter_or_wall_number: 4–7 walls
```

---

### 5. cost_scale_review

记录工业评价、成本、放大、复现价值和下一步建议。

该表不要求每条 run 都有完整成本数据。公开论文常常不给真实单耗、电耗和连续运行数据，因此本表应分为：

```text
事实字段：原文明确给出的成本、连续运行、循环次数等
判断字段：基于现有信息做的工业价值评价和下一步建议
缺失字段：说明哪些工业关键信息没有给出
```

关注内容：

- 甲烷、天然气、氢气、氮气和电力单耗；
- 催化剂成本、纯化成本和废弃物处理成本；
- 催化剂寿命和循环次数；
- 连续运行时间和批次稳定性；
- 放大问题，如堵塞、积碳、传热、流化；
- 安全风险，如 CH4/H2 爆炸、高温、粉尘；
- 该催化剂-工艺-产品组合是否值得复现；
- 工业价值评分和下一步建议。

建议字段：

```text
run_id
quantitative_cost_reported
methane_consumption_per_kg_CNT
natural_gas_consumption_per_kg_CNT
H2_consumption_per_kg_CNT
N2_or_Ar_consumption_per_kg_CNT
electricity_consumption_per_kg_CNT
catalyst_cost_signal
purification_cost_signal
waste_treatment_signal
continuous_operation_time_h
catalyst_reuse_cycles
batch_stability
scale_signal_reported
scale_level_claimed
scale_up_issue
safety_risk
needs_H2
needs_acid_washing
major_cost_driver
missing_critical_fields
industrial_value_score
recommended_next_action
review_note
evidence_text
evidence_location
confidence
```

#### 组合催化剂适应温度和工业推荐如何记录

“某个组合最适合什么条件”不单独建表，先由 `source_run.combo_key` 聚合，再在 `cost_scale_review` 中做轻量判断。

例如：

```text
combo_key:
Fe-Mo/MgO | CH4 | fixed-bed CCVD | t-MWCNT

recommended_next_action:
prioritize Ar-decomposed Fe-Mo/MgO; reproduce CH4-CVD near 900 ℃; compare lower H2/Ar consumption and catalyst lifetime

review_note:
high yield and good purity reported, but methane conversion, catalyst lifetime, continuous operation and real cost data are missing
```

这样可以保留“最合适条件”的判断，但不把它伪装成原始实验事实。

---

### 字段优先级

为避免表格过空，每个字段建议分为三类。

#### A 类：必要字段，优先抽取

```text
run_id
source_id
catalyst_key
active_metals
support_material
preparation_method
calcination_condition
reactor_type
carbon_source
temperature_setpoint_C
holding_time_min
gas_ratio_summary
CNT_type_reported
CNT_type_confirmed
yield_original
purity_wt_percent
outer_diameter_range_nm
evidence_text
evidence_location
confidence
```

#### B 类：有就抽取

```text
metal_ratio_original
promoter
precursor_summary
acid_or_complexing_summary
catalyst_particle_size_nm
BET_surface_area_m2_g
pore_diameter_nm
reduction_condition
temperature_range_reported_C
reported_optimal_temperature
methane_conversion_percent
Raman_ID_IG
RBM_peak_reported
ash_content_wt_percent
scale_signal_reported
recommended_next_action
```

#### C 类：暂不强求

```text
GHSV_or_residence_time
actual_temperature_C
temperature_sensor_position
complete_XPS_peak_fitting
complete_Raman_peak_fitting
full_pore_size_distribution
methane_consumption_per_kg_CNT
electricity_consumption_per_kg_CNT
catalyst_cost_per_kg_CNT
SWCNT_chirality
metallic_semiconducting_ratio
long_term_continuous_operation_data
```

A 类字段决定一条数据是否有研发价值；B 类字段用于提高分析深度；C 类字段只在原文明确给出时收集，不因缺失而否定该 run 的可用性。

---

## run_id 原则

本项目不以“一篇论文 = 一条记录”为原则，而是以实验或实施例为单位。

推荐定义：

```text
一个明确的催化剂体系
+ 一个明确的 CVD 工艺程序
+ 一个对应的产物 / 产率结果
= 一个 run_id
```

如果同一篇论文中比较了多个催化剂、温度、气体比例、反应时间或产物结果，则应拆成多个 run_id。

例如，一篇论文中包含以下催化剂：

```text
Fe/MgO
Fe-Mo/MgO
Co/MgO
Co-Mo/MgO
Ni/MgO
```

这应被视为多条实验记录，而不是一条文献记录。

---

## 证据要求

关键字段应尽量保留以下信息：

```text
value
unit
original_value
evidence_text
evidence_location
source_section
extraction_method
confidence
```

其中 `extraction_method` 可以是：

- `explicit`：原文明确给出；
- `inferred`：根据上下文推断；
- `calculated`：由原始数据计算得到。

如果字段是推断或计算得到，必须保留说明，不能伪装成原文数据。

---

## 专利处理原则

专利资料需要区分不同部分：

| 专利部分 | 是否可作为实验数据 |
|---|---|
| 实施例 / Example / Embodiment | 可以，若条件具体 |
| 具体实施方式 | 可以，若有明确配方和条件 |
| 权利要求 / Claim | 不直接作为实验数据 |
| 背景技术 | 只作为背景信息 |
| 宽泛范围描述 | 只能作为候选或保护范围信息 |

例如，专利中写：

```text
催化剂可选 Fe、Co、Ni，温度范围 500–1100 ℃。
```

这通常是保护范围或宽泛描述，不能直接当作真实实验记录。

---

## 数据来源

项目可能使用的数据来源包括：

- OpenAlex；
- Crossref；
- Semantic Scholar；
- CORE；
- arXiv；
- Web of Science / SCI / SCIE 导出；
- Scopus 导出；
- CNKI、万方、维普等中文数据库导出；
- Google Patents；
- Lens；
- EPO OPS；
- WIPO PATENTSCOPE；
- CNIPA 中国专利；
- 公司或实验室内部数据。

不同数据源的可信度、字段完整度和使用限制不同。公开数据、专利数据和内部实验数据应分开管理。

---

## 当前目录结构与规划

```text
CNT-PatSight/
  AGENTS.md
  README.md

  skills/
    cnt-patsight/
      SKILL.md

  config/
    README.md

  data/
    README.md
    raw/
      metadata/
      papers/
      patents/
    interim/
    processed/
    dictionaries/
    internal/
      README.md

  docs/
    repository_structure.md
    field_definitions.md      # 规划：字段定义稳定后创建
    extraction_rules.md       # 规划：小样本抽取后创建
    patent_rules.md           # 规划：专利样本验证后创建
    project_scope.md          # 规划：研究边界配置化时创建

  scripts/
    collect_metadata/
    screening/
    extraction/
    validation/
    analysis/

  reports/
    figures/

  notebooks/

  tests/
    fixtures/
```

当前仓库已按这一骨架初始化。各目录的具体用途和文件放置规则见
[`docs/repository_structure.md`](docs/repository_structure.md)。尚未创建的配置和规则文档将在小样本闭环验证后逐步补充，避免用未经验证的占位值固化流程。

---

## 阶段性成果

本项目可逐步形成以下成果：

1. metadata 候选资料池；
2. 结构化的 CNT 文献/专利数据库；
3. 字段定义文档；
4. 抽取规则文档；
5. 同义词和单位标准化字典；
6. 催化剂、载体、助剂、温度和产率统计图；
7. 工业评分和路线推荐；
8. 面向研发组的实验建议报告；
9. 后续可选的数据看板或模型辅助抽取系统。

---

## 使用方式

建议先完成小样本闭环：

```text
少量高相关论文/专利
        ↓
手工或半自动抽取
        ↓
填入 5 张主表
        ↓
人工校正
        ↓
验证字段是否够用
        ↓
再扩大 metadata 搜集和自动化抽取
```

不建议一开始就追求海量全文抽取或复杂网页系统。数据结构和抽取规则稳定之后，再扩大自动化程度。

---

## 保密说明

如果后续加入公司或实验室内部实验数据，应默认视为敏感数据。

建议原则：

- 公开文献和专利数据可以进入公开数据区；
- 内部实验数据单独存放；
- 不将内部实验数据默认发送到外部 API；
- 不提交包含商业敏感信息、供应商报价、未公开配方或内部实验结果的文件到公开仓库；
- 模型调用、数据上传和报告分享应遵守所在机构或公司的保密要求。

---

## 项目成功标准

CNT-PatSight 的成功不只是收集很多 PDF，也不是生成很多摘要。

更重要的是形成一个能帮助研发人员回答实际问题的数据资产：

- 已经有哪些催化剂体系被尝试过？
- 它们对应什么 CVD 条件？
- 产率和产品质量如何？
- 哪些结果有原文证据支持？
- 哪些数据适合复现？
- 哪些路线更可能工业化？
- 下一步实验应该优先尝试什么？

最终目标是帮助 CNT 研发从零散经验和文献阅读，逐步走向系统化、数据化和可复现的研发决策。
