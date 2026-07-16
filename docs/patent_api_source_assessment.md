# 专利 API 数据源预留评估

当前阶段不实现专利采集器，只固定后续适配器边界与凭据名。预留配置位于 `config/patent_sources.json`，默认 `enabled = false`。

| 数据源 | 当前判断 | 后续定位 | 预留凭据 |
|---|---|---|---|
| Lens Patent API | 若能获批 token，优先作为全球专利检索入口；同一 REST API 覆盖 patent 与 scholarly corpus，并有版本化 schema。 | 全球检索、专利族/引用/申请人等统一标准化 | `LENS_API_TOKEN` |
| EPO OPS | 官方 REST/XML 服务，含全球书目、法律状态、全文和图像数据；需注册应用并使用 OAuth，且受 fair-use quota 管理。 | Lens 不可用时的全球书目主源，或关键字段交叉验证 | `EPO_OPS_CONSUMER_KEY`, `EPO_OPS_CONSUMER_SECRET` |
| USPTO Open Data Portal | 官方 ODP 提供 API 与批量数据，但更适合作为美国专利的定向补全；API 需要 key，ODP 自 2026-06-18 起要求登录账户。 | US publication/application、file wrapper 或专门数据集补全 | `USPTO_ODP_API_KEY` |
| WIPO PATENTSCOPE | PATENTSCOPE 网页覆盖 PCT 及参与局文献，但官方程序化 PCT Webservice 属条件/付费访问，主要是 SOAP/Java API；不宜假设网页搜索等同于开放 REST API。 | PCT 文献、IASR 和授权文档的定向校验 | `WIPO_PATENTSCOPE_USERNAME`, `WIPO_PATENTSCOPE_PASSWORD` |

官方资料：

- [Lens API documentation](https://docs.api.lens.org/index.html)
- [EPO Open Patent Services developer portal](https://developers.epo.org/)
- [USPTO Open Data Portal API](https://data.uspto.gov/apis/bulk-data/search)
- [WIPO PCT data products and webservices](https://www.wipo.int/en/web/patentscope/data/index)

## 建议实现顺序

1. 先确认 Lens 的授权、许可和 token；若可用，实现 `lens_patent_api` 作为主检索适配器。
2. 同步实现 EPO OPS OAuth、XML 解析、quota/header 记录，作为全球书目补全或备援。
3. 按实际研究范围接入 USPTO ODP 的具体 patent dataset，而不是把 bulk dataset catalog 误当全文检索 API。
4. 仅在获得 WIPO Webservice 授权后实现 PCT 适配器；网页 PATENTSCOPE 保留为人工检索工具。

所有专利适配器应复用当前论文链路的 `RawArchive`、run/request 统计、stable external ID、canonical merge 和 CSV 导出接口，但规范化对象需要增加 publication/application/family identifiers、priority date、assignee/inventor、jurisdiction、legal status 和 claims/full-text availability。正式进入八表时仍以 `source_master.source_type = patent` 登记，只有具体实施例才能规划 `patent_example` run。

