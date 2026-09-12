# 审计记录：2026-09-12

范围：本机安装的 fundamental-signal-intake 与 evidence-driven-valuation。未修改 WorkBuddy，未同步或推送 Git 仓库。原始备份位于 D:/skills/audit-backups/evidence-models-20260912。

## 实际修复

- 时间比较保留时分秒和时区；拒绝日期/无时区、同日未来信息、截止后修订。保留真实历史版本的晚采集能力。
- provenance 从非空声明改为存在性、数值、业务/驱动、单位、时间及递归依赖解析；覆盖嵌套数组，拒绝循环和市场信息污染正向价值。
- 研究计划独立于闸门，重算重大业务/驱动覆盖、来源组、primary 组、时效、口径、覆盖和支持区间，检查隐藏 missing/conflicted。
- 行业白名单失败关闭；SOTP 经济权益登记及归属桥阻止已登记权益/债权重复计价。
- 剩余收益终值更正期初账面价值时点；中周期改用 incremental_roe；资产增加处置折现；新产品核验条件路径闭合。
- 融资侧项计入融资款、投入、发行费用、新债权、新股和失败残值，显示原股东增量，不污染基础价值。
- 每股价值由金额缩放单位转为 currency/share；未知缩放拒绝。侧项使用的假设在 combined_input_audit 另行披露。
- 文档升级 v2，保留业务原则，详细契约按需加载；新增合成交接样例。未测量实际 Token 节省，不能宣称具体下降比例。

## 验证结果

本轮最终回归：估值 59/59、账本 5/5。估值套件包含真实 intake CLI → valuation CLI 交接及错误输入非零退出。两 Skill 的 quick_validate 均通过（Windows 使用 python -X utf8 -B）。示例 CLI 独立运行成功。

独立算例：

- 10×3−10−5−5=FCFF 10；零增长、10% 折现的价值 100；10 股对应每股 10。
- 剩余收益 B0=100、NI1=12、B1=110、ke=10%、终期 ROE=15%、g=2%：164.3181818181818。
- 资产 121、两年、10% 折现：100。
- 分阶段新产品算例：26.5；同时拒绝不闭合、重叠路径与错误联合概率。
- 基础价值100，融资20发5股（原10股），投入20获项目PV30：项目NPV+10，老股东价值增量−13.3333333333333。
- 经营EV100加40%×被投企业股权价值200=180，母公司债20后160；重复扣被投企业债务被拒绝。

回归通过只说明这些案例成立，不证明体系完整或真实估值有效。

## 开源机制核验（固定版本）

未复制上游代码，未安装依赖或实现实时数据适配器。

- [OpenBB Fetcher](https://github.com/OpenBB-finance/OpenBB/blob/3e071fcc2cd9f891cac6040ae60296dba76dab46/openbb_platform/core/openbb_core/provider/abstract/fetcher.py)：核验 transform_query → extract_data/aextract_data → transform_data 及类型/schema 校验。借鉴统一接口，不声称本地已有供应商连接。
- [TradingAgents 财报过滤](https://github.com/TauricResearch/TradingAgents/blob/be952b8eccb49720509af544c6675233bc1f10d0/tradingagents/dataflows/stockstats_utils.py)：filter_financials_by_date 按财务列日期≤cutoff 过滤，不能单独证明公告/修订版本在截止前可用。
- 同版本 [date_window.py](https://github.com/TauricResearch/TradingAgents/blob/be952b8eccb49720509af544c6675233bc1f10d0/tradingagents/dataflows/date_window.py) 和 [y_finance.py](https://github.com/TauricResearch/TradingAgents/blob/be952b8eccb49720509af544c6675233bc1f10d0/tradingagents/dataflows/y_finance.py) 确有历史研究屏蔽实时 profile 等保护；不能据上述缺口断言整个项目没有点时保护。日期窗口及 naive 时间处理仍不同于本地严格时区/盘中截止契约。
- [FinanceToolkit 估值公式测试](https://github.com/JerBouma/FinanceToolkit/blob/9fa19f9e97fee229dad4d65cf9c1448597af5df5/tests/ratios/test_valuation_model.py)：核验显式确定性输入和 recorder.capture；仅据已检查测试借鉴可复现方式，不扩张为全库正确性背书。

## 剩余缺口与使用限制

1. 来源 URL/快照是元数据，不自动下载、验证真实性或判断是否支持原文结论。来源独立性、覆盖分母、业务完整性、假设区间依据仍可被错误声明；必须人工审核。
2. 乘除单位维度未完整形式化；阶段转换 guards 不证明因果。多期间营运资金、税/折旧、增长再投资一致性仍需审核。
3. 银行清洁盈余、OCI、资本充足和终期经济可行性无独立自动验证。
4. holding 不递归求解复杂所有权/交叉持股，经济 ID 只能防止已登记重复；同一权益用不同 ID 的语义重复仍可能漏检。
5. 保险、矿业、REIT、生物科技等专门行业模型未实现，必须报告缺口。融资仅 t0 单轮，不支持复杂可转债、多轮或延迟融资。
6. 反向 DCF 只解恒定增长一个维度；不自动唯一识别全部隐含经营条件。
7. 尚无真实公司点时数据集、真实供应商适配器、独立模型行为评测或实际 Token 基准。合成案例不能代替这些验证。
8. v1 输入破坏性不兼容。须补查真实来源和版本重建 v2，禁止自动填零/默认假设迁移。

验证命令：

```text
python -B -m unittest discover -s <valuation-skill>/scripts -q
python -B -m unittest discover -s <intake-skill>/scripts -q
python -X utf8 -B <skill-creator>/scripts/quick_validate.py <skill-dir>
python -B <valuation-skill>/scripts/valuation_engine.py <valuation-skill>/examples/synthetic-handoff.json
```

