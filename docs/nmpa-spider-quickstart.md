# NMPA Spider Quickstart Guide

## 概述

NMPA Spider 是专门用于爬取国家药品监督管理局（NMPA）官网法规文档的 Scrapy 爬虫。

## 环境要求

### 虚拟环境：data-spider

所有数据抓取任务必须在 `data-spider` conda 虚拟环境中运行，避免与主 API 环境产生依赖冲突。

```bash
# 创建环境（首次使用）
conda create -n data-spider python=3.10 -y

# 激活环境
conda activate data-spider

# 安装依赖
pip install scrapy requests lxml
```

## 快速开始

### 方法1: 使用便捷脚本（推荐）

```bash
# 使用默认配置运行 nmpa_list 爬虫
./scripts/run_nmpa_spider.sh

# 指定爬虫名称和输出文件
./scripts/run_nmpa_spider.sh nmpa_list custom_output.json
```

### 方法2: 手动运行

```bash
# 1. 激活 data-spider 环境
conda activate data-spider

# 2. 运行爬虫
scrapy crawl nmpa_list -o test_output.json

# 3. 查看结果
cat test_output.json | python3 -m json.tool | head -30
```

## 可用爬虫

| 爬虫名称 | 说明 | 配置文件 |
|-----------|------|----------|
| `nmpa_list` | NMPA 列表页爬虫（基础版） | `processors/nmpa/spiders/nmpa_list_spider.py` |
| `nmpa_full` | NMPA 完整列表页爬虫（含下载） | `processors/nmpa/spiders/nmpa_full_spider.py` |

## 测试爬虫

```bash
# 运行单元测试
conda activate data-spider
python3 scripts/test_nmpa_spider.py
```

## 相关文档

- [CLAUDE.md](../CLAUDE.md) - 项目开发指南
