# Public samples

此目录只保存少量可公开复现 CNT-PatSight 八表契约的样例。当前六篇固定样本位于 `data/benchmark/fixtures/six_papers/`；新增公开样例必须先完成授权检查、独立证据复核和脱敏。

## 每个样例应包含

```text
data/benchmark/fixtures/public/<source_id>/
├── source_rights.json
├── source_master.csv
├── source_run.csv
├── catalyst_system.csv
├── reactor_process_gas.csv
├── yield_quality.csv
├── cost_scale_review.csv
├── evidence_index.csv
└── review_issue_log.csv
```

`source_rights.json` 是公开发布清单，不属于正式八表；它至少记录 `doi_or_patent_no`、`oa_url`、`source_license`、`data_license`、`rights_checked_at` 和检查说明。

```json
{
  "doi_or_patent_no": "",
  "oa_url": "",
  "source_license": "",
  "data_license": "",
  "rights_checked_at": "YYYY-MM-DD",
  "notes": ""
}
```

## 发布条件

- 来源身份清楚，在 `source_rights.json` 中保留 DOI/专利号、OA URL 和许可证信息；
- 数据已经由复核 agent 检查 run 拆分、单位、产率口径、CNT 类型和表间关系；
- 不含公司数据、个人信息、真实密钥、未脱敏日志和本地绝对路径；
- 不包含论文 PDF、付费补充材料或大段可替代原文的摘录；
- `evidence_index` 只保留支持可追溯性所需的最短证据片段与精确位置；
- 发布者已经确认结构化数据和必要摘录可按仓库的数据许可证公开；
- 运行 `python scripts/validation/validate_tables.py data/benchmark/fixtures/public/<source_id>` 后无校验错误。

在真实样例完成上述检查前，可使用 [`../processed/templates/`](../processed/templates/) 查看空白字段结构。
