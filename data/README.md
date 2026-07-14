# Data

本目录保存 CNT-PatSight 数据全生命周期。`raw` 保存公开原始输入，`interim` 保存待复核中间结果，`processed` 保存校验后的正式数据，`dictionaries` 保存标准化词典，`internal` 单独保存敏感内部数据。

原始资料不得被清洗脚本原地覆盖。正式五表数据必须通过 `run_id` 保持来源、催化剂、工艺、产品结果和工业评价之间的关联。

五表空白 CSV 模板位于 `processed/templates/`，可用于程序导入或作为新数据批次的起点。
