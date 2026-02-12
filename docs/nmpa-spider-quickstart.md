# NMPA Spider 快速开始指南

## 📋 项目概述
**NMPA Spider** 是用于采集中国国家药监局（NMPA）网站的药品注册管理办法、GMP、药品审评等法规文档的数据采集器。

## 🚀 快速开始

### 方式一：Scrapy命令行

```bash
# 进入项目目录
cd /root/autodl-tmp/pj-pharmaKG

# 运行NMPA爬虫（测试模式）
scrapy crawl nmpa_spider -a test.html -o test_output.json

# 运行NMPA爬虫（生产模式，单条目）
scrapy crawl nmpa_spider -a LOG_LEVEL=INFO
```

### 方式二：测试脚本

```bash
# 运行测试脚本
python scripts/test_nmpa_spider.py
```

## 📂 项目结构

```
processors/
├── nmpa_spider.py          # NMPA爬虫主文件
└── settings/                     # 配置文件
scripts/
├── test_nmpa_spider.py       # 测试脚本
└── run_nmpa_spider.sh         # 生产环境运行脚本（待创建）
```

## 🔧 核心功能

### 数据模型
- `NMPADocument`: NMPA法规文档数据模型
  - url: 文档链接
  - title: 法规名称
  - publish_date: 发布日期
  - category: 法规类型（药品注册、GMP、药品审评等）
  - content: 文档内容摘要
  - attachments: 附件列表

### 爬虫特性
- ✅ 遵守robots.txt（2-5秒请求间隔）
- ✅ User-Agent轮换机制
- ✅ 增量更新（基于LOOKBACK_DAYS）
- ✅ 支持Redis去重（可选）
- ✅ 完整的错误处理和日志记录

### 支持的法规类别
- 药品注册
- GMP/GMP认证
- 药品审评
- 药品不良反应监测
- 检查
- 通告
- 其他（指导原则、说明书等）

## 📊 下一步

1. 运行测试脚本验证功能
2. 完善Scrapy项目结构（items、pipelines、middlewares）
3. 开发FDA/EMA爬虫（第2阶段）
4. 集成到Neo4j数据库（第3阶段）
