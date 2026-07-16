# 配置目录

- `project_scope.yaml`：项目范围和当前阶段边界；
- `schema.json`：八张长期维护表的文件名、字段顺序、主键、外键和必填字段；
- `field_dictionary.csv`：字段含义、类型、单位、预期出现概率、空值规则和保留理由。

修改正式字段时必须同步更新 schema、字段字典、项目 Skill、验证脚本和现有数据迁移逻辑。
