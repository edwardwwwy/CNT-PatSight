# Config

本目录用于可复用、可审查的项目配置。后续建议逐步增加：

- `project_scope.yaml`：当前研究边界、首批问题、筛选等级与暂不强求的内容；
- `data_sources.yaml`：数据源、查询和速率限制；
- `screening_rules.yaml`：七问题筛选与分类阈值；
- `schema.json`：当前五张主表的轻量字段清单；
- `paths.yaml`：仓库内数据和输出路径；
- `models.yaml`：允许使用的模型及任务分工，不保存 API 密钥。

配置应在真实规则确定后再填写，避免创建看似完整但未经验证的默认值。
