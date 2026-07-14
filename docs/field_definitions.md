# 五表数据收集基础

本文件说明 CNT-PatSight v0.3 的五张数据表如何开始使用。当前字段是便于启动采集的建议集合，不要求每条记录全部填写，也可以根据真实资料增加字段。第一批建议关注范围和推荐字段由 `config/project_scope.yaml` 与 `config/schema.json` 中的 `v1_recommended_fields` 定义；它们用于排序，不是硬性限制。

## 基本关系

```text
source_run.run_id
    ├── catalyst_system.run_id
    ├── reactor_process_gas.run_id
    ├── yield_quality.run_id
    └── cost_scale_review.run_id
```

一篇论文或一项专利可以拆成多个 `run_id`。`reactor_process_gas` 可以按吹扫、升温、还原、生长、降温等阶段为同一 run 保存多行；其他表也可以在确有多个催化剂或产品对象时保存多行。

## 五张表的分工

| 表 | 主要内容 | 首要关联字段 |
|---|---|---|
| `source_run` | 来源、run 身份、路线分类、组合键和抽取状态 | `run_id`, `source_id` |
| `catalyst_system` | 催化剂组成、载体、制备、酸化/络合/活化和性质 | `run_id`, `catalyst_id` |
| `reactor_process_gas` | 反应器、阶段、温度、压力、气体和温度影响 | `run_id`, `process_stage_id` |
| `yield_quality` | 原始产率定义、CNT 类型、SWCNT 证据、结构和质量 | `run_id`, `product_id` |
| `cost_scale_review` | 成本与放大事实、适合条件、复现价值和工业判断 | `run_id` |

## 填写原则

- 先填写原文明确报告的值；推断、计算或评价内容应在文字中说明。
- 原始产率、单位和定义优先保留，只有口径清楚时才填写标准化值。
- 专利实施例可以形成 run；claim 或宽泛范围可以记录，但不要当成已经完成的实验。
- `combo_key` 用于后续聚合，建议由催化剂、碳源、反应器和 CNT 类型组合而成；组成字段仍应单独保留。
- 酸化、络合和活化信息放入 `catalyst_system`。
- 适应温度、最优温度和温度影响放入 `reactor_process_gas`。
- SWCNT 声称与证据放入 `yield_quality`。
- 最适条件、复现价值和工业判断放入 `cost_scale_review`，并与原文事实区分。
- 找不到合适字段时，可以先放入 `notes`、`process_note` 或 `review_note`，不要因此丢失有价值信息。

## 文件位置

- 字段清单：`config/schema.json`
- CSV 模板：`data/processed/templates/`
- Excel 模板：`outputs/cnt-patsight-foundation/cnt_patsight_collection_template.xlsx`
- 校验脚本：`scripts/validation/validate_tables.py`

运行基础校验：

```powershell
python scripts/validation/validate_tables.py data/processed/templates
```

校验主要关注文件、表头、重复 `run_id` 和表间关联。字段为空通常只提示，不会阻止继续收集。
