# CNT-PatSight 仓库结构

## 目录职责

| 路径 | 作用 |
|---|---|
| `skills/cnt-patsight/` | CNT 文献/专利提取、证据和复核规范 |
| `config/` | 八表 schema、字段字典和项目范围 |
| `data/raw/` | 只读原始 PDF、专利和来源接收登记 |
| `data/raw/fulltext/` | 全文获取登记、原始 PDF/HTML 缓存和获取报告 |
| `data/interim/` | 解析候选层和单篇来源待复核八表包 |
| `data/interim/extraction_candidates/` | Python 正文分段与实验候选 span |
| `data/interim/llm_extraction/` | Qwen 请求、原始响应和验证后 staging JSON |
| `data/review/llm_extraction/` | LLM 抽取人工复核队列和校验问题 |
| `data/processed/` | 人工复核通过后的跨来源数据和空模板 |
| `data/internal/` | 敏感内部数据 |
| `scripts/fetch_fulltext/` | 幂等全文获取与覆盖登记 |
| `scripts/parse_fulltext/` | PDF/HTML 分段、表格和候选 span 解析 |
| `scripts/extraction/` | 提取与结构迁移脚本 |
| `scripts/validation/` | schema、关系、证据和问题校验 |
| `scripts/reporting/` | 可再生成的展示材料 |
| `reports/` | 阶段报告、统计结果和研发建议 |
| `tmp/` | 可删除的解析、渲染和调试文件 |

## 推荐结构

```text
config/
  schema.json
  field_dictionary.csv

data/
  raw/
    metadata/
      literature_master.csv      # 接收/下载流程登记
    papers/                       # 原始论文 PDF
    patents/                      # 原始专利
    fulltext/                     # 全文登记、原始缓存和获取报告
  interim/
    parsed_text/                  # 可再生成的全文分段文本
    extraction_candidates/       # section/span CSV、SQLite 和解析报告
    llm_extraction/               # Qwen staging JSON 和本地运行记录
    <source_id>/
      source_master.csv
      source_run.csv
      catalyst_system.csv
      reactor_process_gas.csv
      yield_quality.csv
      cost_scale_review.csv
      evidence_index.csv
      review_issue_log.csv
      extraction_workbook.xlsx
  processed/
    templates/                    # 八表空模板
    # 人工复核后再汇总跨来源八表
```

`literature_master.csv` 只管理来源接收和 PDF 状态；正式来源数据以 `source_master.csv` 为准。实验事实、证据和复核问题分别进入对应表。

## 扩展规则

- 当前按来源保存复核包，便于人工检查；汇总数据库仍是跨来源八表，不是每篇论文一套独立数据库。
- 来源达到数百或数千篇后，可按年份或哈希前缀分片目录，但不得改变 `source_id` 和 `run_id`。
- PDF 使用 DOI、出版商编号或其他稳定文件名；不要为单个 PDF 增加无意义嵌套目录。
- 页面图片、OCR 文本和工作簿预览放入 `tmp/`，需要时重新生成。
- 不创建含义模糊的根目录 `output/` 或 `outputs/`。原始/中间数据按 `data/` 分层，运行报告跟随对应数据层，面向人的阶段报告统一放入 `reports/`。
- 内部数据不得默认上传外部服务或提交到公开仓库。
