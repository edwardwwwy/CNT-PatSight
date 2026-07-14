# Scripts

脚本按数据流程分为 metadata 采集、候选筛选、run 级抽取、数据校验和分析五组。脚本应从 `config/` 读取规则，并明确输入、输出和是否会修改数据。

探索性代码可以先放在 `notebooks/`；验证稳定后应迁移到相应脚本目录并增加测试。

## 五表基础校验

使用项目 schema 检查五张 CSV 的文件名、字段顺序、行主键重复和 `run_id` 关联：

```powershell
python scripts/validation/validate_tables.py data/processed/templates
```

空白模板允许没有数据行；正式数据中行标识不完整会提示，重复主键或跨表孤立的 `run_id` 会导致校验失败。
