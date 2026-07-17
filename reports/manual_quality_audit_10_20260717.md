# 八表数据随机 10 篇人工复核报告

复核日期：2026-07-17  
数据范围：66 篇已合并八表数据  
抽样方法：固定随机种子 `20260717`，无放回随机抽取 10 篇  
复核深度：每篇抽取 2 个运行，共核对 20 个 `run_id`  
数据处理：只读正式八表，未修改任何正式 CSV

## 结论先行

这批八表不是“整体提取失败”。抽样结果显示，催化剂、温度、时间、气体流量和主要结果等数值核心总体较好；真正阻碍直接用于机器学习或升级为 `formal_extract` 的，是证据定位、论文级信息误绑运行、推断状态和指标定义。

- 共检查 121 个关键值：113 个能在原文直接支持，6 个属于有依据但必须保留“标准化/图中估读”限定，2 个在原文没有依据。
- 直接支持率为 93.4%；把明确限定的标准化和图中估读值计入后，支持率为 98.3%。
- 另做 160 个类别级检查点，严格通过 117 个、部分通过 24 个、失败 19 个。
- 两处明确无原文依据的值都属于压力：论文未报告压力，却填成 `atmospheric / 101.325 kPa`。
- 10 篇中，2 篇证据层不合格，3 篇存在必须修正的运行级归属问题，4 篇可在小修后用于限定范围分析，1 篇可在保留图中估读限定后使用。

因此，本次抽样建议继续保持：

```text
extraction_status = needs_review
numeric_core_status = mostly_passed
provenance_status = inconsistent
formal_extract = false
```

## 复核口径

每个选中运行检查八类内容：催化剂身份、制备方法、反应器与温度时间、气体与压力、主要结果、产品表征、证据定位、`reported/inferred/not_reported` 状态。检查点是质量审计单位，不代表把整张八表的每一个空值都重新抽取了一遍。

9 篇通过本地 PDF 原页和解析正文双重核对；`LIT_79F908D3DA4AE6F8` 本地没有 PDF，使用完整解析正文核对。抽样清单见 [random_sample.csv](../data/derived/manual_quality_audit_10_20260717/random_sample.csv)，机器可读结果见 [audit_results.json](../data/derived/manual_quality_audit_10_20260717/audit_results.json)。

## 逐篇判定

| 序号 | source_id | 检查点（通过/部分/失败） | 判定 | 主要结论 |
|---:|---|---:|---|---|
| 1 | `LIT_A590E23A531DD9BE` | 12 / 2 / 2 | 需要修正 | 数值正确；成本、规模和安全推断全部被标成 reported，证据页码过宽。 |
| 2 | `LIT_82A4395696545B8B` | 8 / 2 / 6 | 证据不合格 | 575°C 与气体流量正确；压力为臆补，证据只是八表内容的再转录。 |
| 3 | `LIT_6731BD3F12EC3922` | 12 / 3 / 1 | 限定通过 | 实验条件可靠；图中 340–355 μm 被压成 348 μm，产生虚假精度。 |
| 4 | `LIT_79F908D3DA4AE6F8` | 13 / 3 / 0 | 小修通过 | 600→400→200 sccm 与直径层正确；定位只写 local_span，固定流量对照信息不足。 |
| 5 | `LIT_FB76AA75976322C2` | 8 / 2 / 6 | 证据不合格 | 725/875°C、乙醇和时间正确；压力为臆补，SWNT 被弱化成 CNT，证据循环。 |
| 6 | `LIT_427378A0096D943B` | 13 / 2 / 1 | 小修通过 | 615°C、4 μm/min、99.4% 等正确；180/112 μm 数值被装进定性字段。 |
| 7 | `LIT_42CA430104DA72AA` | 14 / 2 / 0 | 小修通过 | 2.5/5 min、750°C、30/200/420 mL/min 正确；结果本质是 SEM 视觉等级。 |
| 8 | `LIT_169EACB657CC8523` | 12 / 3 / 1 | 需要修正 | 0.98 与 0.41 mg/min 正确；10 wt% 运行错误继承了 5 wt% 样品的形貌。 |
| 9 | `LIT_849AD7FB325763D1` | 11 / 3 / 2 | 需要修正 | 64%/83% TGA 碳含量正确；2 bar 运行继承了未明确属于它的 TEM/Raman 结果。 |
| 10 | `LIT_A4E38E9C51ED6D44` | 14 / 2 / 0 | 小修通过 | Modified 2、26.1 μm 和 G/D 4.5 正确；需标明压力标准化和配方继承。 |

## 关键问题明细

### 1. 原文没有报告压力，却填入精确大气压

在 `LIT_82A4395696545B8B` 和 `LIT_FB76AA75976322C2` 中，正文没有明确报告所选运行压力，但八表写入：

```text
pressure_original = atmospheric
pressure_kPa = 101.325
```

这两处应改为 `not_reported`。即使论文写了 atmospheric，把它换算成 101.325 kPa 也应标为 `normalized`，不能与作者直接报告的精确压力混为一谈。

### 2. 证据循环，不能独立验证提取

`LIT_82A4395696545B8B` 和 `LIT_FB76AA75976322C2` 的证据位置写成“local full text/PDF; source-specific values transcribed”，证据文本则基本是八表行重新拼成的句子。它只能证明“某条八表记录被复制到 evidence”，不能证明“该字段来自论文某一页”。

这两篇核心条件虽然大多正确，但证据层仍判定失败。正式放行前，应至少做到：

```text
具体字段 -> PDF 页码/表格/图号 -> 可核对的原文片段
```

### 3. 论文级表征错误绑定到单次运行

抽样中发现两处重要的运行级污染：

- `LIT_169EACB657CC8523_PARTICLE_300_FLOW_240` 是 10 wt% Ni 的粒径筛选运行，但形貌字段写入了论文明确针对 5 wt% Ni 样品观察到的空心/实心 CNT 结构。
- `LIT_849AD7FB325763D1_R02` 是升压到 2 bar 的运行，却完整继承了常规样品的直径、壁数、RBM、Raman 和 TEM 形貌。论文只清楚地把 TGA 的 83% 碳含量与 2 bar 样品关联，其他表征样品归属没有被明确说明。

这类字段必须增加：

```text
characterization_scope
linked_run_id
scope_status = confirmed / representative_sample / unresolved / other_sample
```

### 4. 图中估读值被包装成精确数值

`LIT_6731BD3F12EC3922` 的同一名义条件在不同图中约为 340–355 μm，八表保留了范围，但又生成标准化值 348 μm。348 是项目计算出的中间值，不是论文精确报告值。

建议训练视图默认只保留：

```text
reported_range = 340-355 um
value_status = visually_digitized_approximate
```

若保留 348，应另写 `derivation_method = midpoint_of_visual_range`，并从严格监督学习目标中排除。

### 5. 推断被标成 reported

4 篇较早整理的样本中，`evidence_index` 的全部记录都是 `reported`：

- `LIT_A590E23A531DD9BE`
- `LIT_82A4395696545B8B`
- `LIT_FB76AA75976322C2`
- `LIT_849AD7FB325763D1`

但它们的 `cost_scale_review` 包含成本驱动、安全风险、工业成熟度、复现优先级等项目判断。这些内容可以有价值，但应标为 `review_assessment` 或 `inferred`，不能伪装成论文实验结果。

### 6. 有数值，却没有进入机器可用的数值字段

`LIT_427378A0096D943B_RED615` 明确报告 180 μm，相比标准 80 min 运行的 112 μm，但当前结构是：

```text
primary_yield_metric = qualitative_VACNT_growth_outcome
yield_original = 180 micrometer ... versus 112 micrometers
yield_value_standardized = empty
yield_unit_standardized = not_applicable
```

数值没有丢，但机器无法直接读取。应拆为数值字段，并把“与标准运行比较”另存为比较关系。

### 7. 产率不是一个统一目标

抽样中的“结果”至少包括：

- CNT/CNF 定性形貌；
- VACNT 高度和生长速率；
- TGA 产品碳含量；
- 碳沉积速率；
- 出口气体组成；
- Raman 质量指标。

它们不能直接合并成一个 `yield` 标签。用于机器学习时，应先按 `yield_metric + definition + unit + basis` 分组，只在定义一致的子集中建模。

## 对后续机器学习的放行建议

本次抽样说明，八表可以作为正式数据源继续建设，但不能把当前全部 `needs_review` 行直接送入模型。建议生成一个只读训练视图：

1. 只纳入 `reported`、`calculated` 或明确 `normalized` 的值。
2. 排除 `review_assessment`、`inferred`、`figure_digitized_approximate` 和 `scope_status=unresolved`。
3. 压力原始文本与标准化 kPa 分列保存。
4. 产品表征只有在 `linked_run_id` 明确时进入运行级特征。
5. 产率按定义和单位建立白名单，不把 TGA 碳含量、气体组成、质量产率和生长高度混成同一目标。
6. 空值统一为状态字段，避免空字符串、`not_reported`、`not_assessed` 和 `not_applicable` 混用。

## 修正优先级

最高优先级：

- 删除两篇论文中无来源的 `101.325 kPa`。
- 解除 10 wt%/5 wt% 和 1 bar/2 bar 样品之间错误或未确认的表征绑定。
- 把四篇论文的成本、规模、安全判断从 `reported` 改为 `review_assessment/inferred`。
- 为两篇证据循环的论文建立页码级证据。

第二优先级：

- 为图中估读值保留近似性和读取方法。
- 把文本中的数值结果拆入数值字段。
- 为共享基线和继承配方增加字段级状态。

## 最终判断

如果只看被抽中的核心实验数字，这批数据表现较好；如果看是否已经能被审计、复现并安全用于机器学习，当前仍需一轮针对性的修正。最准确的表述是：

> 数值核心大多通过，但证据、运行归属和语义状态尚未整体通过。

本报告是独立审计层，没有修改正式八表。修正应先形成问题清单并经确认，再回写正式数据源。
