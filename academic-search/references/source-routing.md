# 学科与来源路由

只在需要选择检索平台、扩展关键词或判断学科评价规则时读取。平台能力和访问政策会变化，优先核对官方说明；不可用时换互补来源，不反复撞击同一失败端点。

## 通用底座

| 目标 | 优先来源 | 用途与限制 |
| --- | --- | --- |
| 跨学科发现与引用图谱 | OpenAlex、Semantic Scholar | 覆盖广；引用统计口径不同，不能视为质量分 |
| DOI 与出版元数据 | Crossref、出版商记录 | 核验题名、作者、日期、期刊和 DOI |
| 合法开放全文 | Unpaywall、CORE、OpenAIRE、机构仓储 | 有 DOI 时检查作者存档版或正式 OA 版 |
| 广泛发现 | Google Scholar | 覆盖书籍、学位论文和灰色文献较好；元数据需回原始来源核验 |
| 中文研究 | CNKI、万方、国家哲学社会科学文献中心、高校仓储 | 登录和全文权限各异；同时用英文数据库交叉检索 |

## 计算机、AI 与大模型

- 发现：arXiv（cs.CL、cs.LG、cs.AI、cs.CV、cs.IR 等）、Semantic Scholar、OpenAlex。
- 正式发表：ACL Anthology、DBLP、ACM Digital Library、IEEE Xplore、会议/期刊官网。
- 代码与复现：论文官方 GitHub、Papers with Code、模型/数据集官方页面。
- 查询扩展：缩写与全称、任务名、模型族、数据集/benchmark、关键机制、`survey`、`benchmark`、`replication`、`failure`、`limitations`。

## 医学、公共卫生与生命科学

- PubMed/MEDLINE 用于权威书目和 MeSH；PMC、Europe PMC 用于开放全文。
- Cochrane Library、WHO、各国卫生机构和专业学会用于系统综述与临床指南。
- ClinicalTrials.gov、WHO ICTRP 用于注册和未发表/进行中试验；bioRxiv、medRxiv 只作预印本追踪。
- 查询优先使用 PICO：人群、干预/暴露、比较、结局；补疾病同义词、药物通用名和 MeSH。
- 承重结论检查 PubMed 的 publication type、勘误/撤稿链接、试验注册号和指南日期。

## 心理学、社会学、教育与政策

- PsycINFO/PsycArticles（有权限时）、PubMed、OpenAlex、Web of Science/Scopus（有权限时）。
- PsyArXiv、SocArXiv、OSF 用于预印本、预注册和材料；SSRN、RePEc/NBER 用于经济和政策工作论文。
- 查询加入人群、文化/地区、年代、测量工具和方法词：RCT、纵向、自然实验、差分法、访谈、民族志等。
- 特别检查测量效度、样本代表性、WEIRD 偏差、分析灵活性、预注册和跨文化复现。

## 历史、哲学、文学与其他人文

- Google Scholar、OpenAlex、Crossref 用于发现；JSTOR、Project MUSE、PhilPapers 和专业书目用于领域检索。
- WorldCat、国家/高校图书馆目录用于专著和版本；档案馆、博物馆、政府/宗教机构目录用于一手材料。
- 查询加入人物/地名的原文与译名、时代、区域、文本版本、档案号、`historiography`、`primary source`、`critical edition`。
- 哲学优先追踪论证链和回应文献；历史优先区分同时代材料、后世记述和现代史学解释。

## 地理、地球与环境科学

- OpenAlex、Crossref、Web of Science/Scopus（有权限时）、EarthArXiv。
- NASA Earthdata、USGS、Copernicus、各国测绘/气象/统计机构用于数据与技术报告。
- 查询必须加入地点、尺度、时期、数据产品、遥感传感器或模型名；不同空间尺度的结果不能直接外推。

## 天文、物理与数学

- arXiv（astro-ph、physics、math、stat）、NASA ADS（天文/天体物理）、INSPIRE HEP（高能物理）、Crossref。
- 查询加入实验/望远镜/巡天名称、对象编号、理论/定理名称、常用符号变体和 arXiv 分类。
- 物理天文前沿重视预印本版本变化；数学重视定理条件、勘误和权威发表版本，引用数与发表时间只作辅助。

## 检索失败时

1. 检查拼写、标识符和 URL 编码。
2. 缩短查询，再逐个加入筛选条件；尝试同义词、原文名和受控词表。
3. 从聚合索引取得 DOI/PMID/arXiv ID，再回官方记录。
4. 遇到 429、验证码或 403 时换 API/数据库或稍后再查，不规避访问控制。
5. 只有单一数据库可用时标注覆盖缺口，不宣称检索完整。
