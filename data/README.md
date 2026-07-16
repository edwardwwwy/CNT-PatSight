# 数据目录规则

原始资料不得被清洗脚本原地覆盖。`source_id` 和 `run_id` 是稳定业务键，文件路径不是业务主键。

## 分层

- `raw/`：来源登记、公开论文 PDF、专利原文和其他只读原始资料。
- `interim/<source_id>/`：单篇来源的八张 CSV 与 `extraction_workbook.xlsx`，全部为待人工复核数据。
- `processed/`：人工复核通过后的跨来源八表数据。
- `internal/`：公司或实验室内部数据，默认敏感并与公开数据分离。

`raw/metadata/literature_master.csv` 是接收和下载流程登记，不是正式业务表。正式来源元数据进入 `source_master.csv`。

## 单篇复核包

每个 `interim/<source_id>/` 固定包含：

```text
source_master.csv
source_run.csv
catalyst_system.csv
reactor_process_gas.csv
yield_quality.csv
cost_scale_review.csv
evidence_index.csv
review_issue_log.csv
extraction_workbook.xlsx
```

不再保留独立 `source_observations.jsonl`；其内容进入 `evidence_index`，真实冲突和关键缺口同时进入 `review_issue_log`。

空白八表模板位于 `processed/templates/`。只有人工复核通过的数据才能汇总进入 `processed/`。
