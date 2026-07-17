# 八表数据结构说明

CNT-PatSight v0.4 使用八张长期维护表。字段是否进入正式结构，依据其在数百篇论文与专利中的预期复用价值，而不是当前六篇样本的非空率：保留跨来源常见字段、特定来源类别中常见字段，以及虽少见但对安全、规模或证据判断不可替代的字段。

## 基本关系

```text
source_master.source_id
    └── source_run.source_id
            ├── catalyst_system.run_id
            ├── reactor_process_gas.run_id
            ├── yield_quality.run_id
            └── cost_scale_review.run_id

evidence_index ──> 任一来源、运行或事实记录
review_issue_log ──> 任一待复核记录，并可关联 evidence_id
```

## 八张表的分工

| 表 | 主要内容 |
|---|---|
| `source_master` | 文献或专利唯一元数据、文件状态、筛选与总审核状态 |
| `source_run` | 实验运行身份、路线、抽取状态和运行摘要 |
| `catalyst_system` | 催化剂组成、载体、制备、热处理与结构性质 |
| `reactor_process_gas` | 分阶段反应器条件、温度、压力和角色化气体程序 |
| `yield_quality` | 原始产率口径、CNT 类型、形貌、Raman、TGA 与后处理 |
| `cost_scale_review` | 已展示规模、连续运行、寿命、成本事实与复核阶段评价位 |
| `evidence_index` | 原文证据、位置、对象、值状态、置信度及问题关联 |
| `review_issue_log` | 冲突、数据缺口、质量警告及独立复核结论 |

## 字段管理原则

- 来源元数据只放 `source_master`，不在每个 run 重复。
- 事实表不嵌入证据文本与位置；所有证据统一进入 `evidence_index`。
- 冲突、警告和待决定事项只进入 `review_issue_log`，不混入一般备注。
- 缺失使用 `not_reported`、`not_applicable` 或受控状态；不猜测，不用空字符串掩盖含义。
- 条件性字段可以在不适用的来源类别中为空或标记不适用；不能仅因当前样本为空就删除。
- 高维、低复用信息优先放入摘要字段和证据表；同一信息反复出现后，再按字段变更协议评估是否结构化。
- `ml_runs_clean.csv` 是后期由八表自动拼接的宽表，不手工维护。

机器可读字段、文件名和关系以 `config/schema.json` 为准；字段用途、预期出现率、空值策略和保留理由见 `config/field_dictionary.csv`。

## 文件位置与校验

- CSV/Excel 空白模板：`data/processed/templates/`
- 单篇抽取包：`data/interim/<source_id>/`
- 校验脚本：`scripts/validation/validate_tables.py`

校验一个已经抽取的数据包：

```powershell
python scripts/validation/validate_tables.py data/interim/<source_id>
```

空白模板仅用于录入起点，不按“完整来源包”规则执行校验。
