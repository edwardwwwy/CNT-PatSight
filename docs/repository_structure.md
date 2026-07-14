# CNT-PatSight 仓库结构

本仓库按“配置、原始资料、处理中间数据、正式数据、规则文档、脚本、分析输出”分层。目录结构服务于以下数据流：

```text
公开元数据 / 论文 / 专利                    内部实验数据（敏感）
             |                                      |
             v                                      v
          data/raw                             data/internal
             |                                      |
             +---------- 筛选与 run 级抽取 ----------+
                              |
                              v
                         data/interim
                              |
                     校验、标准化、人工复核
                              |
                              v
                        data/processed
                              |
                   分析、图表和研发建议报告
                              |
                              v
                           reports
```

## 顶层目录

| 路径 | 作用 | 放置规则 |
|---|---|---|
| `skills/` | Codex/Agent 执行项目任务时使用的专业工作规范 | 项目技能位于 `skills/cnt-patsight/SKILL.md` |
| `config/` | 项目范围、数据源、筛选规则、字段 schema、路径和模型配置 | 只放可复用配置，不放密钥 |
| `data/` | 研究数据全生命周期 | 公开资料与内部敏感资料必须分开 |
| `docs/` | 字段定义、抽取规则、专利规则和架构说明 | 规则变化应先更新文档，再调整脚本 |
| `scripts/` | 数据采集、筛选、抽取、校验和分析程序 | 按工作阶段拆分，避免一次性脚本散落根目录 |
| `reports/` | 可交付的分析报告、图表和研发建议 | 最终输出与临时中间数据分开 |
| `notebooks/` | 探索性分析和原型验证 | 稳定逻辑应迁移到 `scripts/` 并补测试 |
| `tests/` | 数据规则和脚本测试 | `fixtures/` 只放小型、脱敏的测试样本 |

## `data/` 分层

| 路径 | 作用 |
|---|---|
| `data/raw/metadata/` | OpenAlex、Crossref、WoS、Scopus、CNKI 等原始 metadata 导出 |
| `data/raw/papers/` | 下载的公开论文及补充材料；默认不提交 Git |
| `data/raw/patents/` | 下载的专利全文、附图和法律状态材料；默认不提交 Git |
| `data/interim/` | 去重、筛选、OCR、候选 run 和待人工复核数据 |
| `data/processed/` | 通过校验的五表数据库及可发布数据版本 |
| `data/dictionaries/` | 催化剂、载体、碳源、单位和同义词映射字典 |
| `data/internal/` | 公司或实验室内部数据；默认敏感并被 Git 忽略 |

## `scripts/` 分工

| 路径 | 作用 |
|---|---|
| `scripts/collect_metadata/` | 获取和合并论文、专利候选 metadata |
| `scripts/screening/` | 七问题筛选、相关性评分和候选分类 |
| `scripts/extraction/` | PDF/专利实施例解析和 run 级字段抽取 |
| `scripts/validation/` | schema、单位、外键、证据和产率定义校验 |
| `scripts/analysis/` | 催化剂、工艺窗口、产品质量和工业价值分析 |

## 文件放置原则

1. 根目录只保留项目入口和仓库级配置，不堆放数据或临时脚本。
2. 一份文献可以对应多个 `run_id`；正式数据以 run 为核心，不以 PDF 为核心。
3. 原始数据只读保存，所有清洗结果写入 `interim` 或 `processed`。
4. `processed` 数据必须保留来源、证据位置、抽取方法和置信度。
5. 专利 claim、背景描述和具体实施例必须区分存储。
6. 内部实验数据不得默认上传外部 API，也不得提交到公开仓库。

