# CNT-PatSight 数据生命周期

`data/` 只保存五类资产：原始资料、可重建中间数据、正式数据、测试数据和审计记录。

```text
data/
├─ raw/                         # 不可重建的原始资料和来源清单
│  ├─ literature/{pdf,html,metadata,supplements}/
│  ├─ api_responses/<provider>/<run>.jsonl.gz
│  └─ source_manifest.csv
├─ interim/                     # 可从 raw 重建
│  ├─ parsed_text/by_source/<source_id>.parsed.json
│  ├─ extraction/{A,B,C}/<source_id>.extraction.json
│  ├─ evidence/evidence_candidates.jsonl
│  ├─ review_queue/{pending,resolved}.jsonl
│  └─ extraction_manifest.csv
├─ processed/                   # 唯一正式数据源
│  ├─ eight_tables/
│  ├─ analysis/
│  └─ snapshots/
├─ benchmark/                   # gold、fixtures、templates、results
└─ audit/                       # 抽样、问题与迁移/质量摘要
```

约束：每个来源在 A/B/C 中最多有一个抽取 JSON；正式八表只允许出现在
`processed/eight_tables/`。运行日志写到顶层 `runs/`，渲染与数据库缓存写到
顶层 `cache/`，公司数据通过 `CNT_COMPANY_DATA_DIR` 从仓库外读取。

校验：`python -m scripts.validation.validate_data_layout`

迁移按 `inventory → migrate → verify → archive → cleanup` 执行；`cleanup` 会在校验或外部归档哈希失败时拒绝删除。公司规范数据验证通过后，再运行 `cleanup-private-company` 删除仓库外的旧目录副本。命令说明：`python -m scripts.migration.restructure_data --help`
