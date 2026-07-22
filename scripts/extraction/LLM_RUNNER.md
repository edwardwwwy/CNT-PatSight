# 通用 LLM 八表抽取器

`llm_runner.py` 不是“每篇论文写一个八表脚本”。它把任意已经过全文解析的来源送入同一条流水线：

1. 规则解析器生成不可变的章节与候选证据片段；
2. LLM 第一次调用只规划独立实验运行（run）；
3. LLM 第二次调用按统一字段 Schema 提取候选事实，并且每个值只能引用输入片段 ID；
4. 程序从原片段确定性回填原文证据，不接受模型自己复制或改写的“引文”；
5. 共用映射器写入固定八表，共用校验器检查主外键、字段、证据和语义约束；
6. 结果始终为 `needs_review`，模型不能自己把数据标成已复核。

远程 API、Ollama 和 llama.cpp 只在“怎么发送结构化请求”这一层不同。运行规划、字段范围、证据规则、八表映射和校验代码完全共用。

## 准备解析结果

先注册并解析论文，然后导出中间 CSV：

```powershell
python scripts/parse_fulltext/parse.py run --source-id YOUR_SOURCE_ID
python scripts/parse_fulltext/parse.py export
```

默认读取：

- `cache/parse_exports/paper_text_section.csv`
- `cache/parse_exports/candidate_experiment_span.csv`

抽取器会同时使用“科学槽位检索”和“通用相关性排序”。即使新论文没有命中已有术语模式，通用候选片段仍能进入模型上下文。

## 远程 API

严格 JSON Schema（推荐，服务端支持 `response_format=json_schema` 时使用）：

```powershell
$env:LLM_API_KEY = "YOUR_KEY"
python scripts/extraction/llm_runner.py `
  --source-id YOUR_SOURCE_ID `
  --provider api `
  --model YOUR_MODEL_ID `
  --base-url https://api.example.com/v1
```

较旧的 OpenAI-compatible 服务如果只支持 JSON object：

```powershell
python scripts/extraction/llm_runner.py `
  --source-id YOUR_SOURCE_ID `
  --provider api `
  --model YOUR_MODEL_ID `
  --base-url https://api.example.com/v1 `
  --api-schema-mode json-object
```

API key 默认从 `LLM_API_KEY` 读取；可用 `--api-key-env` 改成其他环境变量名。密钥不会写入请求日志。远程模式会发送筛选后的论文证据片段，因此用于公司资料前应确认所选服务的数据合规要求。

## Ollama 本地模型

先让 Ollama 服务和目标模型可用，再运行：

```powershell
python scripts/extraction/llm_runner.py `
  --source-id YOUR_SOURCE_ID `
  --provider ollama `
  --model YOUR_LOCAL_MODEL `
  --base-url http://127.0.0.1:11434
```

请求走 Ollama 的 `/api/chat`，以原生 `format` JSON Schema 约束输出。论文片段不会发往远程 API。

## llama.cpp 本地服务

先启动兼容 `/v1/chat/completions` 的 `llama-server`，再运行：

```powershell
python scripts/extraction/llm_runner.py `
  --source-id YOUR_SOURCE_ID `
  --provider llama-cpp `
  --model YOUR_LOCAL_MODEL `
  --base-url http://127.0.0.1:8080/v1
```

## 输出与失败处理

默认输出目录：

```text
runs/extraction/llm/<source_id>/<revision_id>/
```

其中只有固定的八个 CSV 和 `llm_extraction_manifest.json`。每次模型请求、原始响应和校验错误单独保存在同级 `<revision_id>_attempts/`，不会混进正式八表目录。

模型若引用不存在的片段、虚构值、漏拆实验运行、输出未知字段或破坏表间关系，程序会把校验错误反馈给同一个模型修复；默认最多修复两轮。仍不通过时不会发布八表目录。

常用控制参数：

- `--max-repairs 2`：模型修复轮数；
- `--max-total-chars 32000`：发送给模型的证据字符上限；
- `--max-per-slot 4`：每类科学证据的优先片段数；
- `--metadata-json PATH`：显式提供来源题名、年份、DOI 等元数据；
- `--revision-id ID`：为可复现实验固定版本号。

代码层面需要接入其他模型服务时，只需实现 `StructuredModel.generate_json(...)`；不要复制或重写八表生成逻辑。
