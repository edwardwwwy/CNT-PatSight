# 脚本目录

脚本按生产职责分组：

| 目录 | 职责 |
|---|---|
| `collect_metadata/` | API 采集、规范化、保守去重和筛选输入 |
| `fetch_fulltext/` | 合法 OA 全文定位、下载、签名与哈希校验 |
| `parse_fulltext/` | PDF/HTML 解析、章节识别和候选 span |
| `extraction/` | 提取输入包、规范化和 JSON 结果校验 |
| `production/` | 队列、租约、恢复、监控和事务性八表暂存 |
| `validation/` | 八表文件、字段、关系、证据和状态校验 |
| `screening_benchmark/` | 元数据筛选与去重基准 |
| `regression/` | 固定回归样例的可重复构建脚本 |

常用检查：

```powershell
python -m pytest -q
ruff check scripts tests
python scripts/validation/validate_tables.py data/interim/<source_id>
```

所有写入型脚本必须明确输入、输出和恢复策略，不得覆盖原始 PDF、冻结快照或既有提取尝试。
