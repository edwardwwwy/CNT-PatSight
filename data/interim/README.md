# Interim data

这里只保存可由 `raw/` 重建的当前状态：

- `parsed_text/by_source/<source_id>.parsed.json`：每来源一个解析文件；
- `extraction/{A,B,C}/<source_id>.extraction.json`：每来源一个八表抽取包；
- `evidence/evidence_candidates.jsonl`：候选证据；
- `review_queue/pending.jsonl` 与 `resolved.jsonl`：当前审核队列；
- `extraction_manifest.csv`：抽取包索引和 SHA-256。

批次日志、旧尝试、渲染文件和 SQLite 运行状态不属于这里。
