# 论文 API 元数据采集

该目录实现“OpenAlex 主检索 + DOI 定向补全”的可重跑流程：

```text
OpenAlex search
  -> provider-independent normalization
  -> DOI / API ID / title-similarity deduplication
  -> Semantic Scholar batch enrichment
  -> Crossref DOI enrichment
  -> Unpaywall DOI enrichment
  -> SQLite canonical store + CSV export + per-run report
```

这只是来源接收与筛选层，不创建 `source_run`，也不抽取催化剂、工艺或产率字段。自动评分只用于排序；API 元数据不会被自动标为 `formal_extract`。进入单篇八表复核包时，仍需人工确认并保持 `needs_review`。

## 配置

复制环境变量模板并填值：

```powershell
Copy-Item .env.example .env
```

必需或建议变量：

```text
OPENALEX_API_KEY              OpenAlex 主检索，必需
SEMANTIC_SCHOLAR_API_KEY      Semantic Scholar DOI 批量补全，建议
CROSSREF_EMAIL                Crossref polite pool，建议
UNPAYWALL_EMAIL               Unpaywall API，启用该源时必需
```

`.env` 已被 Git 忽略。程序只报告变量是否配置，不打印变量值。OpenAlex 查询参数中的 key、Semantic Scholar 请求头以及 email 参数都会在原始请求归档中脱敏。

检索式和默认限额位于 `config/literature_search.json`；筛选、分层和去重阈值位于
`config/screening_rules.json`。每个检索式都有稳定 `query_id`；命令行 `--query`
可用于临时小样本，不修改配置文件。

## 运行

先检查配置：

```powershell
python scripts/collect_metadata/collect.py doctor
```

运行默认检索与补全：

```powershell
python scripts/collect_metadata/collect.py run
```

小规模冒烟运行：

```powershell
python scripts/collect_metadata/collect.py run `
  --query "carbon nanotube methane CVD catalyst" `
  --max-results-per-query 5 `
  --max-enrich-records 5
```

只运行 OpenAlex 和 Semantic Scholar：

```powershell
python scripts/collect_metadata/collect.py run `
  --sources openalex,semantic_scholar
```

只补跑一个配置中的检索式，不重跑其他 query：

```powershell
python scripts/collect_metadata/collect.py run `
  --query-id mwnt_swnt_cvd `
  --sources openalex `
  --max-enrich-records 0
```

只补全已有 DOI，不重复执行 OpenAlex 检索：

```powershell
python scripts/collect_metadata/collect.py enrich `
  --sources semantic_scholar,crossref,unpaywall `
  --max-records 200
```

`enrich` 会按来源跳过已有成功快照的 DOI；无结果或失败 DOI 保留重试资格。
Crossref 和 Unpaywall 是逐 DOI 请求，日常增量建议每批 100–200 条。

查看最近一次 run 或重建 CSV：

```powershell
python scripts/collect_metadata/collect.py report
python scripts/collect_metadata/collect.py export
python scripts/collect_metadata/collect.py rescore
```

全局路径参数必须放在子命令之前，例如：

```powershell
python scripts/collect_metadata/collect.py `
  --database tmp/metadata.sqlite3 `
  --master-csv tmp/literature_master.csv `
  run --max-results-per-query 5
```

## 产物

```text
data/raw/metadata/literature.sqlite3
  canonical works、API 别名、字段来源、request/run/query 统计

data/raw/metadata/literature_master.csv
  面向检查和后续 source_master 登记的 UTF-8-BOM 平面导出

data/raw/metadata/api_responses/<run_id>/<source_api>/*.json
  不含明文凭据的逐请求原始返回

data/raw/metadata/run_reports/<run_id>.json
  query、各 API 返回量、入库/更新、去重、评分和链接统计
```

`literature_master.csv` 保留现有人工字段，并增加 `abstract`、`publisher`、`citation_count`、`open_access_status`、`pdf_url`、`html_url`、`source_api_ids`、采集时间和相关性说明。它是接收层导出，不是第九张正式业务表。

## 去重与更新

匹配顺序为：

1. 同一 API 的稳定外部 ID；
2. 规范化 DOI；
3. 标题长度至少 30 字符、标题相似度达到自动合并阈值、年份差不超过 1、
   文献类型相容，并且第一作者或期刊至少一项相符；
4. 达到复核阈值但不满足自动合并条件时，标为 `needs_review`；
5. 两条非空 DOI 不同则禁止自动合并，记录 `doi_conflict_review`。

字段按来源优先级合并。例如 Semantic Scholar 优先提供摘要和引用量，Crossref 优先提供出版社、期刊和出版日期，Unpaywall 优先提供 OA 与合法全文链接。每个来源的标准化快照都保留在 `work_source_records`，聚合值的来源保留在 `field_sources_json`。

重复运行不会新增同一 DOI 或 API ID 的 canonical work。`last_seen` 和原始响应会更新，但元数据内容未变化时统计为 `unchanged`，不会伪报为业务更新。

## 相关性评分

规则同时计算主题相关性、元数据证据可能性和全文可访问性，并保留原因码、
规则版本、评分时间及来源快照。主题规则覆盖：

- CNT / MWCNT / SWCNT / VACNT / MWNT / SWNT、nanotube、tubular carbon
  及常用中文身份词；
- CVD / CCVD / catalytic decomposition 路线；
- methane / CH4；
- catalyst 语境与 Fe、Co、Ni、Mo；
- fluidized bed / floating catalyst；
- yield、growth rate、growth temperature。

`catalytic decomposition` 只有同时出现 CNT 身份和合成/生长/催化语境时才加路线分；
应用词只有在缺少合成证据时才扣分。

优先层级为：

- `A`：高相关、高优先全文核查；
- `B`：相关候选，进入全文核查队列；
- `C`：背景、综述或观察性来源；
- `M`：元数据缺失，需要全文判定；
- `R`：规则拒绝或明显低相关。

元数据筛选绝不自动授予 `formal_extract`，也不直接授予 `candidate_extract`。
`A`、`B`、`M` 只进入 `screened_candidate`；必须查看全文后再由后续流程或人工分类。

## API 约定

实现依据各数据源当前官方文档：

- [OpenAlex works search and cursor pagination](https://developers.openalex.org/api-reference/works/list-works)
- [Semantic Scholar Academic Graph batch endpoint](https://api.semanticscholar.org/api-docs/graphs)
- [Crossref REST API access and authentication](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)
- [Unpaywall REST API](https://unpaywall.org/products/api)

## 测试

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

测试不调用公网 API，覆盖标准化、字段优先级、DOI/标题去重、重复运行幂等、旧 CSV 兼容、评分和凭据脱敏。
