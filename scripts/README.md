# 脚本目录

脚本按来源登记、筛选、抽取、验证、报告和分析分组。脚本应明确输入、输出和是否修改数据。

## 八表校验

```text
python scripts/validation/validate_tables.py data/interim/<source_id>
```

校验器读取 `config/schema.json` 和 `config/field_dictionary.csv`，检查八表字段、顺序、主外键、证据目标、证据覆盖和复核问题链接。

## v0.3 到 v0.4 迁移

`scripts/extraction/migrate_v03_to_v04.py` 用于把历史五表复核包迁移为八表结构。已迁移目录会被跳过；迁移后的数据仍需逐篇校验和人工复核。
