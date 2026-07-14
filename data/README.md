# Data

本目录保存 CNT-PatSight 数据全生命周期。`raw` 保存公开原始输入，`interim` 保存待复核中间结果，`processed` 保存校验后的正式数据，`dictionaries` 保存标准化词典，`internal` 单独保存敏感内部数据。

原始资料不得被清洗脚本原地覆盖。正式五表数据必须通过 `run_id` 保持来源、催化剂、工艺、产品结果和工业评价之间的关联。

五表空白 CSV 模板位于 `processed/templates/`，可用于程序导入或作为新数据批次的起点。

## 面向大规模文献的数据位置

- `raw/papers/` 保存不可变的公开论文原件，文件名优先使用 DOI 或出版商稳定编号。
- `interim/<source_id>/` 按 `P{三位编号}_{FirstAuthor}_{Year}_{ShortTopic}` 命名，目录名与表内 `source_id` 完全一致，不使用原始 PDF 文件名、DOI 片段或不清楚的缩写。
- 每个来源目录固定保存五张 CSV、`extraction_workbook.xlsx` 和 `source_observations.jsonl`；这些是逐篇复核包，不代表为每篇文献建立五套正式数据库。
- `interim/source_observations.jsonl` 跨来源保存完整结构化的 warning 和 observation，并通过 `source_id`、`related_run_id` 回连来源与正式 run。
- `processed/` 最终按五张主表跨来源汇总，不按论文拆成五套正式表。只有人工复核通过的数据才能进入该层。

当前 10 篇样本阶段保持一篇一个 `interim/<source_id>/` 目录，便于逐篇复核。来源达到数千篇后，可在不改变 `source_id` 和五表关系的前提下按年份或哈希前缀对 `raw`、`interim` 做目录分片；不要把路径本身当作业务主键。
