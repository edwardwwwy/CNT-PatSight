# 数据目录与公开边界

CNT-PatSight 将本地生产数据与 GitHub 公开数据分开管理。`source_id` 和 `run_id` 是稳定业务键，文件路径不是业务主键；任何清洗、解析或抽取脚本都不得原地覆盖原始资料。

## 本地数据流

```text
raw/metadata
  -> raw/fulltext
  -> interim/parsed_text
  -> interim/extraction_candidates
  -> interim/extraction_batches
  -> interim/eight_table_staging
  -> review/extraction
  -> processed
```

| 本地目录 | 用途 | 默认上传 GitHub |
|---|---|---:|
| `raw/` | 元数据、合法获取的全文与冻结输入 | 否 |
| `interim/` | 解析结果、队列、批次、首轮八表包 | 否 |
| `derived/` | 可重新生成的合并数据和分析产物 | 否 |
| `review/extraction/` | 独立证据复核队列、决策和证据上下文 | 否 |
| `processed/` | 通过正式化门禁的完整数据库 | 否，单独发布版本 |
| `internal/` | 公司或实验室内部数据 | 绝不公开 |

`raw/metadata/literature_master.csv` 是采集与下载流程登记，不是正式业务表。正式来源元数据进入 `source_master.csv`。

## GitHub 中保留的数据

| 目录 | 内容 |
|---|---|
| `samples/` | 1–3 个经授权、脱敏并通过证据复核的小型八表样例 |
| `processed/templates/` | 八表 CSV 与 Excel 空白模板 |
| `review/screening_benchmark/` | 可公开、可复现的筛选和去重 benchmark |

样例发布条件与文件清单见 [`samples/README.md`](samples/README.md)。仓库级白名单和发布前检查见 [`../docs/public_repository_policy.md`](../docs/public_repository_policy.md)。

## 单篇八表包

本地的 `interim/<source_id>/` 或公开的 `samples/<source_id>/` 使用同一结构：

```text
source_master.csv
source_run.csv
catalyst_system.csv
reactor_process_gas.csv
yield_quality.csv
cost_scale_review.csv
evidence_index.csv
review_issue_log.csv
```

公开样例另附不属于正式八表的 `source_rights.json`，记录来源链接、内容许可证、数据许可证和权利检查时间。本地复核包可以附带 `extraction_workbook.xlsx`；公开样例仅在确认其中不含受限原文、个人信息和本地路径后才能附带。空白模板位于 `processed/templates/`，只有通过独立证据复核和正式化门禁的数据才能汇总进入正式数据层。
