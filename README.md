# 制药行业知识图谱 (PharmaKG)

**项目版本**: v1.1
**最后更新**: 2026-02-12
**项目状态**: 技术实施阶段 (Phase 1 - 前后端集成完成)

---

## 项目概述

制药行业知识图谱（PharmaKG）是一个覆盖制药行业全流程的知识图谱项目，整合研究与发现（R&D）、临床试验、供应链管理和监管合规四个核心业务领域。

### 核心特性

- **全流程覆盖**: R&D → 临床 → 供应链 → 监管合规
- **多维分类体系**: 分面分类避免组合爆炸
- **上下文依赖关系**: 关系携带丰富属性和时态信息
- **跨域关联**: 支持跨领域查询和分析
- **版本控制**: Git-like分支管理
- **数据质量框架**: 四维度质量管理

---

## 快速开始

### 部署方式选择

根据您的部署环境选择合适的部署方式：

#### 方式 A: AutoDL 云服务（推荐）

如果您使用 AutoDL GPU 云服务：

| 项目 | 文档 |
|-----|------|
| 快速开始指南 | [deploy/QUICKSTART_AUTODL.md](deploy/QUICKSTART_AUTODL.md) |
| 完整部署指南 | [deploy/README_AUTODL.md](deploy/README_AUTODL.md) |
| Neo4j 安装指南 | [docs/NEO4J_INSTALL_AUTODL.md](docs/NEO4J_INSTALL_AUTODL.md) ✅ 新增 |
| 部署脚本 | `./deploy/deploy-autodl.sh` |

**特点**:
- ✅ 无需Docker，直接安装
- ✅ 针对 AutoDL 容器环境优化
- ✅ 一键部署脚本
- ✅ 集成 JupyterLab 开发
- ✅ Neo4j 5.26.21 + Java 17 已安装 ✅ 新增

#### 方式 B: Docker 部署

如果您有自己的服务器或本地环境：

| 项目 | 文档 |
|-----|------|
| 快速开始指南 | [deploy/README.md](deploy/README.md) |
| 部署脚本 | `./deploy/deploy.sh` |

**特点**:
- ✅ Docker Compose 编排
- ✅ 完整服务栈（Neo4j + PostgreSQL + Redis）
- ✅ 服务隔离和易于管理

---

## 访问 Neo4j 浏览器

部署完成后，Neo4j 浏览器可通过以下地址访问：

**本地/内网**:
- URL: http://localhost:7474
- Bolt: bolt://localhost:7687

**AutoDL 外网访问**（需开放端口）:
- URL: http://<autodl-ip>:7474
- Bolt: bolt://<autodl-ip>:7687

**认证信息**:
- 用户名: neo4j
- 密码: pharmaKG2024!

---

## 部署环境状态

**AutoDL 环境 (当前运行环境)**:

| 组件 | 状态 | 版本 | 说明 |
|------|------|------|------|
| Neo4j | ✅ 运行中 | 5.26.21 | RPM 包安装 |
| Java | ✅ 已安装 | OpenJDK 17.0.18 | 系统级安装 |
| Python | ✅ 已配置 | 3.11.14 | conda 环境 `pharmakg-api` |
| Neo4j Python Driver | ✅ 已安装 | 5.14.1 | ETL 管道依赖 |

**服务端口**:
- HTTP: 7474 (Neo4j Browser)
- Bolt: 7687 (Cypher/Python)

**相关命令**:
```bash
# 启动 Neo4j
cd /root/autodl-tmp/pj-pharmaKG/neo4j/current
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
./bin/neo4j start

# 运行 ETL 测试
conda activate pharmakg-api
python3 scripts/run_etl_test.py --all -l 10 -v
```

详细安装指南: [docs/NEO4J_INSTALL_AUTODL.md](docs/NEO4J_INSTALL_AUTODL.md)

---

## 研究范围

**业务领域覆盖**：
- **研究与发现 (R&D)**: 靶点发现、化合物筛选、构效关系
- **临床试验**: 试验设计、受试者管理、数据采集
- **供应链管理**: 原料采购、生产制造、物流配送
- **监管合规**: 注册申报、药物警戒、合规检查

## 项目结构

```
pj-pharmaKG/
├── frontend/                      # React前端应用 ✅ 新增
│   ├── src/                       # TypeScript源码
│   │   ├── pages/                 # 页面组件
│   │   ├── domains/               # 领域页面(R&D, Clinical, Supply, Regulatory)
│   │   ├── shared/                # 共享组件和API客户端
│   │   └── layouts/               # 布局组件
│   ├── vite.config.ts             # Vite配置(含API代理)
│   └── package.json              # NPM依赖
│
├── api/                          # FastAPI后端服务
│   ├── main.py                   # API主应用
│   ├── services/                 # 领域服务
│   └── models.py                 # 数据模型
│
├── docs/                          # 文档目录
│   ├── research-plan/            # 研究计划
│   ├── literature/               # 文献资料（已保存6篇）
│   ├── interview-notes/          # 访谈纪要（3轮完成）
│   │   ├── 2025-02-04_第一轮访谈综合总结.md
│   │   ├── 2025-02-04_第二轮访谈综合总结.md
│   │   ├── 2025-02-06_第三轮访谈综合总结.md ✅ 新增
│   │   ├── rd-domain/            # R&D领域访谈
│   │   ├── clinical-domain/       # 临床领域访谈
│   │   ├── supply-chain/          # 供应链领域访谈
│   │   └── regulatory/            # 监管合规领域访谈
│   └── schema/                   # Schema设计文档
│       ├── 制药行业知识图谱Schema设计文档.md v2.0 ✅ 更新
│       └── 实施路线图.md v2.0 ✅ 更新
│
├── deploy/                        # 部署配置 ✅ 合并
│   ├── docker/                    # Docker配置
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── prometheus.yml
│   ├── config/                   # 配置文件
│   │   └── neo4j/neo4j.conf
│   ├── scripts/                  # 脚本文件
│   │   └── init_constraints.cypher
│   ├── data/                     # 数据目录
│   ├── deploy.sh                 # 部署脚本
│   └── README_DOCKER.md          # Docker部署说明
│
├── environments/                 # 环境配置 ✅ 新增
│   └── environment-testing.yml    # Playwright测试环境
│
├── ontologies/                   # 本体文件
│   └── mappings/                 # 标识符映射
│
├── data/                         # 数据目录
├── scripts/                      # ETL脚本
│   └── utils/                    # 工具函数
│
└── visualizations/               # 可视化图表
```

---

## 核心文档

### 访谈文档（3轮完成）

| 文档 | 描述 |
|-----|------|
| [第一轮访谈综合总结](docs/interview-notes/2025-02-04_第一轮访谈综合总结.md) | 3领域第一轮，12问题，12决策 |
| [第二轮访谈综合总结](docs/interview-notes/2025-02-04_第二轮访谈综合总结.md) | 3领域第二轮，27问题，42决策 |
| [第三轮访谈综合总结](docs/interview-notes/2025-02-06_第三轮访谈综合总结.md) | 技术选型确认，17问题，17决策 |

### 设计文档

| 文档 | 描述 |
|-----|------|
| [Schema设计文档](docs/schema/制药行业知识图谱Schema设计文档.md) | 70+实体类，100+关系类型，分9章详细说明 |
| [实施路线图](docs/schema/实施路线图.md) | 12个月计划，分3Phase，资源预算730K USD |

### 部署文档

| 文档 | 描述 |
|-----|------|
| [部署README](deploy/README.md) | Docker部署，故障排除，维护指南 |
| [Neo4j 安装指南](docs/NEO4J_INSTALL_AUTODL.md) | AutoDL 环境下 Neo4j 安装（RPM/Tarball） ✅ 新增 |
| [Git 工作流指南](docs/GIT_WORKFLOW.md) | Git 提交规范，分支策略 ✅ 新增 |
| [变更日志](CHANGELOG.md) | 项目变更记录 ✅ 新增 |

---

## 技术架构

### 技术栈（第三轮确认）

| 组件 | 技术选型 | 版本/配置 |
|-----|---------|----------|
| 图数据库 | Neo4j | 5.x LTS |
| 容器平台 | Docker | 24.x+ |
| 本体语言 | Turtle + OWL + SHACL | W3C标准 |
| 部署环境 | autodl 云服务器 | 自有服务器 |

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  查询界面     │  │  API 服务      │  │  数据导入     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    服务层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Neo4j       │  │  PostgreSQL  │  │  Redis       │  │
│  │  图数据库     │  │  元数据库     │  │  缓存        │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    数据层                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         知识图谱数据 (70+ 实体类, 100+ 关系类型)         │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 开发路线图

### Phase 1: 核心基础 (Month 1-3) ✅ 已完成

- [x] 三轮访谈完成（56问题，71决策）
- [x] 技术栈选型确认
- [x] 部署配置完成
- [x] R&D核心实体建模（Compound, Target, Assay, Pathway等）
- [x] 临床核心实体建模（ClinicalTrial, Subject, Intervention等）
- [x] 供应链+监管核心实体建模（Manufacturer, DrugShortage, Submission, Approval等）
- [x] 标识符映射服务（Identifier mappings）
- [x] 基础查询API开发（60+ REST API端点）

### Phase 1 完成总结

**本体定义** (4个领域完整):
- ✅ R&D领域: Compound, Target, Assay, Pathway等8个实体类
- ✅ 临床领域: ClinicalTrial, Subject, Intervention, Outcome等11个实体类
- ✅ 供应链领域: Manufacturer, DrugShortage, Distributor等8个实体类
- ✅ 监管领域: Submission, Approval, Inspection, ComplianceAction等7个实体类

**API服务** (5个服务类，60+端点):
- ✅ ResearchDomainService: 化合物、靶点、实验查询
- ✅ ClinicalDomainService: 试验、受试者、不良事件查询
- ✅ SupplyChainService: 制造商、短缺、供应链查询
- ✅ RegulatoryService: 申报、批准、合规查询
- ✅ AdvancedQueryService: 多跳查询、药物重定位、竞争分析
- ✅ AggregateQueryService: 统计分析、时序分析、地理分布

**ETL管道** (4个领域):
- ✅ R&D Pipeline: ChEMBL数据导入
- ✅ Clinical Pipeline: ClinicalTrials.gov数据导入
- ✅ Supply Chain Pipeline: FDA短缺数据导入
- ✅ Regulatory Pipeline: FDA产品和应用数据导入

**其他组件**:
- ✅ 数据模型定义 (Pydantic models)
- ✅ SHACL约束规则
- ✅ 图分析算法 (graph_analytics/)
- ✅ ML分析模块 (ml_analytics/)
- ✅ React前端应用 (frontend/) ✅ 新增
  - ✅ 四领域页面 (R&D, Clinical, Supply, Regulatory)
  - ✅ Dashboard统计页面
  - ✅ API集成完成 (使用/api前缀)
  - ✅ SPA路由配置

### Phase 2: 增强功能 (Month 4-6) ⏳ 下一阶段

- [ ] 不确定性数据表示
- [ ] RWE数据整合
- [ ] 质量管理框架
- [ ] 跨域关联查询优化

### Phase 3: 高级功能 (Month 7-12) ⏳ 规划中

- [ ] 版本控制完整实现
- [ ] 适应性试验建模
- [ ] 智能预警系统
- [ ] 性能优化

## 核心实体类型

### 生物医学核心实体
- Chemical/Drug (化学物质/药物)
- Gene/Protein/Target (基因/蛋白/靶点)
- Disease (疾病)
- Phenotype/Symptom (表型/症状)
- Pathway (通路)

### 临床试验实体
- Clinical Trial (临床试验)
- Patient/Subject (患者/受试者)
- Assay/Bioassay (实验/生物检测)
- Outcome (结局)

### 供应链实体
- Manufacturer (制造商)
- Supplier (供应商)
- Authorization Holder (授权持有人)
- Drug Shortage (药品短缺)

### 监管与市场实体
- Regulatory Agency (监管机构)
- Policy/Guideline (政策/指南)
- KOL/Stakeholder (关键意见领袖/利益相关者)

## 实施阶段

Phase 1: 核心本体设计 → Phase 2: 关系语义细化 → Phase 3: 数据源映射 → Phase 4: 验证与迭代

## 交付物

- [ ] 本体Schema文档
- [ ] 交流纪要
- [ ] 实施路线图
- [ ] 可视化图谱
