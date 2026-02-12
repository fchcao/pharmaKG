# 数据采集策略

## 更新时间
2026-02-12

## 已排除的数据源

以下数据源因强反爬虫保护，**暂不采集**：

| 数据源 | 状态 | 原因 | 替代方案 |
|--------|------|------|----------|
| NMPA.gov.cn | ❌ 暂停 | 阿里云Anti-Bot保护，HTTP 412 | 使用其他已采集数据 |
| CDE.org.cn | ❌ 暂停 | HTTP 202持续导航，反爬虫 | 使用FDA/EMA数据 |

> 注：爬虫代码已保留在 `processors/` 目录，未来如需使用可参考 `docs/nmpa-spider-status.md` 和 `docs/cde-spider-status.md`

## 当前数据采集重点

### 1. R&D Domain (研发领域)
- ✅ **ChEMBL 36** - 已测试成功，28GB SQLite
- ✅ **UniProt** - 已完成处理器
- ✅ **KEGG** - 已完成处理器
- ✅ **DrugBank** - 已完成处理器

### 2. Clinical Domain (临床领域)
- ✅ **ClinicalTrials.gov** - API v2支持，已测试
- ✅ **FAERS** - FDA不良事件报告

### 3. Supply Chain Domain (供应链)
- ✅ **FDA Drug Shortages** - 药品短缺数据
- ✅ **FDA Drugs@FDA** - 已完成处理器

### 4. Regulatory Domain (监管领域)
- ✅ **FDA CRLs** - 完整回应函
- ✅ **PDA Technical Reports** - 108份PDF报告
- ✅ **DailyMed** - FDA产品标签
- ✅ **EMA** - 欧洲药品管理局（待开发）

## 推荐采集优先级

| 优先级 | 数据源 | 领域 | 复杂度 | 状态 |
|--------|--------|------|--------|------|
| 1 | ChEMBL 36 | R&D | 中 | ✅ 就绪 |
| 2 | ClinicalTrials.gov | Clinical | 低 | ✅ 就绪 |
| 3 | FDA Drugs@FDA | Regulatory | 低 | ✅ 就绪 |
| 4 | DailyMed | Regulatory | 中 | ✅ 就绪 |
| 5 | FAERS | Supply | 中 | ✅ 就绪 |
| 6 | EMA | Regulatory | 高 | 🔄 开发中 |

## 环境配置

### 虚拟环境

```bash
# 数据采集环境（主要）
conda activate data-spider

# Playwright测试环境
conda activate playwright-env

# 主API环境
conda activate pharmakg-api
```

### 运行示例

```bash
# R&D 数据采集
conda activate data-spider
python -m processors.chembl_processor /path/to/chembl_36.db --limit-compounds 1000

# 临床试验数据
python -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"

# FDA数据
python -m processors.drugsatfda_processor --mode all --max-applications 100
```

## 已创建的任务

| ID | 任务 | 状态 |
|----|------|------|
| #3 | 启动团队协作任务 | pending |
| #4 | 修复ManufacturersPage地理分布图、CRLsPage统计、Dashboard首页数据对接 | pending |
| #6 | 创建FDA法规指南收集员任务 | pending |
| #7 | 创建EMA法规收集员任务 | pending |
| #8 | 制药监管数据采集项目管理 | pending |
| #9 | 协调3个数据采集员工作 | pending |

## 贡献指南

如需添加新数据源：

1. 创建对应的 Processor 类继承 `BaseProcessor`
2. 实现 `extract()`, `transform()`, `load()` 方法
3. 添加配置到 `etl/config.py`
4. 更新本文档
