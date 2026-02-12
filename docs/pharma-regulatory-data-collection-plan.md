# 制药监管指南数据收集与导入计划

> **项目概述**: 建立结构化的制药监管知识图谱，整合中国（NMPA）、美国（FDA）、欧盟（EMA）等主要制药监管机构的法规指南和审评原则。

**版本**: v1.0
**创建日期**: 2026-02-10
**状态**: 计划中

---

## 📋 项目目标

### 核心目标
1. 收集并结构化存储三大主要监管机构的法规指南和审评文档
2. 建立可搜索、可浏览的监管知识数据库
3. 提供RESTful API用于法规查询和知识图谱可视化
4. 实现增量数据更新机制，保持法规数据库时效性
5. 构建友好的前端展示界面，支持高级筛选和知识图谱探索

### 预期成果
- **数据库规模**: 预计存储10,000+条法规文档记录
- **数据源覆盖**: NMPA、FDA、EMA、Health Canada、PMDA、TGA等主要机构
- **API接口**: 20+个RESTful端点，支持法规搜索、机构查询、统计分析
- **可视化功能**: 监管目录浏览、法规详情展示、知识图谱D3.js可视化

---

## 📂 实施阶段

### 阶段一：数据源调研与技术验证（第1-2周）

#### 目标
- 调研各监管机构官网结构和可用数据格式
- 验证Scrapy框架用于大规模网页爬取的技术可行性
- 测试Neo4j图数据库在监管文档存储场景下的性能表现
- 确定API服务器技术栈（FastAPI vs Django/Flask对比）

#### 1.1 NMPA网站调研
**工作内容**:
- 访问国家药监局官网（www.nmpa.gov.cn）
- 分析网站结构（HTML页面组织、robots.txt规则）
- 识别法规文档下载链接模式
- 测试数据采集可行性

**预期产出**:
- NMPA网站爬取可行性报告
- 数据格式分析报告（PDF、HTML、XML）
- 爬取频率建议（遵守robots.txt，2-5秒间隔）

**技术要点**:
- 反爬虫机制：研究User-Agent、验证码
- 速率限制：每秒最多1次请求，设置10秒冷却期
- IP轮换：准备多个代理IP池，避免单一IP被封禁
- 数据备份：爬取结果实时备份到对象存储

#### 1.2 FDA/EMA网站调研
**工作内容**:
- 分析美国FDA和欧盟EMA官网结构
- 研究可用的数据API或批量下载接口
- 测试XML/JSON数据解析性能

**预期产出**:
- FDA/EMA数据采集方案
- 数据格式规范文档
- API端点清单（如果可用）

#### 1.3 Neo4j性能验证
**工作内容**:
- 在测试环境部署Neo4j社区版
- 导入测试数据集（1000条Company节点）
- 创建测试Schema（Agency、Document、Regulation节点）
- 执行Cypher查询测试（MATCH、OPTIONAL MATCH、路径查询）
- 测试图数据库性能（10万节点规模下的响应时间）

**预期产出**:
- Neo4j性能基准测试报告
- 推荐硬件配置建议

---

### 阶段二：数据采集层开发（第3-8周）

#### 2.1 NMPA采集器开发（第3-4周）
**目标**: 构建可扩展、健壮的NMPA法规文档爬取系统

**工作内容**:
- Scrapy项目架构设计
  - `spiders/`目录：按数据源组织爬虫
  - `items/`中间件：数据提取和解析Pipeline
  - `pipelines/`目录：数据处理流程定义
  - `settings/`配置：爬取规则、代理配置、速率限制

**核心组件**:
- **NMPASpider** (`spiders/nmpa/spider.py`)
  - 基于Scrapy Redis调度器（去重、优先级队列）
  - 自定义Middlewares：UserAgent、ProxyRotation、RetryPolicy
  - 数据解析器：解析HTML/PDF、提取结构化信息

**数据模型**:
```python
class NMPADocument(BaseItem):
    document_id: str  # 唯一标识符
    source: str  # NMPA
    title: str  # 法规名称
    publish_date: str  # 发布日期
    url: str  # 原文链接
    category: str  # 法规类型（注册、审评、指导等）
    content_summary: str  # 内容摘要
    full_text: str  # 完整文本
    attachments: List[Attachment]  # 附件列表
    keywords: List[str]  # 关键词
    metadata: Dict  # 其他元数据
```

**技术特性**:
- 分布式架构：主控节点 + Redis消息队列
- 智能调度：基于文档更新时间和优先级
- 断点续爬：支持从上次中断位置继续
- 数据验证：多格式校验和去重机制
- 监控：实时统计爬取状态、成功率、错误率

**预期产出**:
- 可运行的NMPA爬虫系统
- 完整的数据模型定义

#### 2.2 FDA/EMA采集器开发（第4-5周）
**目标**: 构建FDA和EMA法规文档采集系统

**工作内容**:
- 分析FDA Drugs@FDA和EMA官网可用API
- 开发XML/JSON数据解析器
- 实现批量下载和增量更新机制

**技术选型**:
- FDA: 使用`drugs@fda.gov` NHParser API
- EMA: 使用`www.ema.europa.eu` medicinal product data API

**预期产出**:
- FDA/EMA采集器原型
- 数据格式规范文档

#### 2.3 其他机构采集器（第5-6周）
**目标**: 扩展到Health Canada、PMDA（日本）、TGA（土耳其）等监管机构

**工作内容**:
- 调研各机构官网结构
- 开发通用采集模板
- 实现多源数据聚合

**预期产出**:
- 多机构采集框架

---

### 阶段三：数据库设计与后端开发（第6-9周）

#### 3.1 数据库Schema设计（第6-7周）
**目标**: 设计Neo4j图数据库Schema，支持监管文档存储和查询

**工作内容**:
- 设计节点类型和属性
  - Agency（机构）节点
  - Document（法规文档）节点
  - Regulation（法规）节点
  - Submission（提交）节点
  - Approval（批准）节点
  - Reference（引用）节点

- 设计关系类型
  - PUBLISHES（发布关系）：Agency → Document
  - ISSUES（评审关系）：Agency → Document
  - ASSOCIATED_WITH（关联关系）：Document → Submission
  - SUBMITTED_TO（提交关系）：Submission → Approval
  - REFERENCES（引用关系）：Document → Regulation, Document

- 设计Cypher查询优化
  - 创建索引和约束
  - 全文搜索、模糊搜索、前缀搜索

**预期产出**:
- 完整的Neo4j Schema设计文档
- Cypher优化脚本

#### 3.2 后端API开发（第7-10周）
**目标**: 基于FastAPI开发法规知识图谱RESTful API

**API端点规划**:
```
/api/v1/regulations/search          # 法规搜索
/api/v1/regulations/{id}            # 法规详情
/api/v1/agencies/search             # 机构搜索
/api/v1/agencies/{id}             # 机构详情
/api/v1/statistics/regulatory    # 监管统计
/api/v1/admin/regulations/import   # 批量导入
/api/v1/admin/statistics/rebuild     # 重建索引
```

**技术栈**:
- FastAPI 0.100+
- SQLAlchemy 1.4+
- Neo4j Driver 4.4+
- Redis（缓存和任务队列）
- Celery（异步任务处理）

**预期产出**:
- 可运行的FastAPI后端服务

#### 3.3 前端可视化开发（第8-11周）
**目标**: 构建友好的监管知识图谱浏览和查询界面

**工作内容**:
- 监管目录页面：按机构、年份、类型浏览法规
- 高级筛选器：多维度筛选（地区、时间、关键词）
- 法规详情页：完整文档展示、版本对比、引用分析
- 知识图谱D3.js可视化：机构关系网络、法规影响力分析

**技术选型**:
- React 18 + TypeScript
- Ant Design 5.x
- Cytoscape.js（图谱可视化）
- ECharts/D3.js（统计图表）

---

### 阶段四：数据导入与系统集成（第10-12周）

#### 4.1 数据采集执行（第10-12周）
**目标**: 全面执行各监管机构数据采集

**工作内容**:
- 启动NMPA爬虫（生产环境）
- 启动FDA/EMA爬虫
- 启动其他机构爬虫
- 监控爬取状态和数据质量
- 收集数据并解析入库

**预期产出**:
- 完整的法规文档数据库（10,000+条记录）
- 采集监控仪表板

#### 4.2 后端API集成测试（第11-13周）
**目标**: 完成后端开发和前端集成

**工作内容**:
- API接口联调测试
- 前后端性能优化
- 数据一致性验证
- 错误处理和监控

**预期产出**:
- 稳定运行的法规知识图谱系统

---

## 🎯 关键里程碑

| 里程碑 | 目标完成时间 | 交付物 |
|--------|-----------|--------|
| 计划制定 | 第0天 | 完整的项目计划文档 |
| 技术验证完成 | 第14天 | 性能测试报告、技术选型确认 |
| NMPA爬虫就绪 | 第35天 | 可运行的采集系统 |
| 后端API上线 | 第63天 | 完整的RESTful API |
| 前端可视化完成 | 第77天 | 监管知识图谱前端 |
| 系统集成完成 | 第84天 | 端到端的生产系统 |

---

## 🛠️ 技术栈确定

### 后端技术
- **Web框架**: FastAPI 0.100+
- **数据库**: Neo4j 4.4+ Community
- **缓存**: Redis 6.x
- **任务队列**: Celery 5.x
- **数据采集**: Scrapy 2.0+
- **API文档解析**: BeautifulSoup4, lxml, PyPDF2

### 前端技术
- **框架**: React 18 + TypeScript 4.x
- **UI库**: Ant Design 5.x
- **图谱可视化**: Cytoscape.js 3.x
- **图表库**: ECharts 5.x
- **HTTP客户端**: Axios 1.x

---

## 📋 风险评估与缓解措施

### 数据采集风险
| 风险类型 | 风险描述 | 缓解措施 |
|---------|--------|---------|
| 反爬虫机制 | 实施User-Agent检测、CAPTCHA验证 | 严格遵守robots.txt |
| IP封禁风险 | 使用代理IP池、定期轮换 | 监控异常IP |
| 法律合规 | 仅收集公开监管信息，不涉及敏感数据 |
| 数据质量 | 多格式校验、去重机制、内容完整性检查 |

### 项目风险等级
**总体评估**: 🟡 中等风险（可控风险，建议分阶段实施以降低风险）

---

## 📊 资源需求

### 人力资源
| 角色 | 人数 | 技能要求 |
|------|------|--------|
| 后端开发工程师 | 2名 | Python、FastAPI、Neo4j、SQLAlchemy |
| 数据采集工程师 | 2名 | Python、Scrapy、Redis、Celery |
| 前端开发工程师 | 2名 | React、TypeScript、Ant Design |
| DevOps工程师 | 1名 | Docker、Nginx、Redis、Celery |
| 测试工程师 | 1名 | Pytest、Selenium |
| 项目经理 | 1名 | 项目管理、进度控制 |

**总计**: 8名全职人员

### 基础设施需求
| 设施类型 | 数量 | 配置 |
|---------|--------|--------|
| 开发服务器 | 2台 | 16核/32GB RAM、1TB SSD |
| 数据库服务器 | 1台 | 16核/32GB RAM、2TB SSD |
| Redis服务器 | 1台 | 8核/16GB RAM、500GB SSD |
| 代理IP池 | 20个代理IP | 用于IP轮换 |

---

## 📈 下一步建议

建议从**阶段一：数据源调研**开始执行，理由：
1. 技术风险低，容易快速验证和调整
2. NMPA网站结构相对简单，适合作为起始点
3. 可以在1-2周内完成可行性验证报告

**立即行动项**:
1. 在`processors/`目录创建`nmpa_spider/`子目录
2. 配置Scrapy项目结构和settings.py
3. 编写基础的NMPA爬虫原型（10-20行代码）
4. 在`scripts/`目录创建测试脚本`test_nmpa_spider.py`
5. 运行爬虫测试，验证基本功能
6. 编写简短的技术方案文档（TECH_PROPOSAL.md）
7. 提交到Git仓库

---

**备注**:
- 所有代码提交到`/root/autodl-tmp/pj-pharmaKG/docs/pharma-regulatory-data-collection-plan.md`
- 建议创建专门的项目计划跟踪目录（`docs/plans/`）
- 技术方案文档保存为Markdown格式
- 每个阶段完成后更新进度

**用户确认**: 请确认是否开始执行阶段一（数据源调研）？