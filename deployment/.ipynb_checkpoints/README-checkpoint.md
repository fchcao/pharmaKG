# PharmaKG 部署文档

## 📋 目录

- [概述](#概述)
- [部署架构](#部署架构)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [服务管理](#服务管理)
- [监控与日志](#监控与日志)
- [备份与恢复](#备份与恢复)
- [故障排查](#故障排查)
- [生产环境最佳实践](#生产环境最佳实践)

---

## 概述

本目录包含 PharmaKG 知识图谱系统的生产环境部署配置文件和脚本。采用 Docker Compose 进行容器化部署，确保环境一致性和易于管理。

### 组件说明

| 组件 | 描述 | 端口 |
|------|------|------|
| **Neo4j** | 图数据库，存储知识图谱数据 | 7474 (HTTP), 7687 (Bolt) |
| **FastAPI** | REST API 服务 | 8000 |
| **Nginx** | 反向代理和负载均衡 | 80 (HTTP), 443 (HTTPS) |
| **Redis** | 缓存服务 | 6379 |
| **Prometheus** | 指标收集和监控 | 9090 |
| **Grafana** | 可视化监控面板 | 3000 |

---

## 部署架构

```
                        ┌─────────────┐
                        │   Nginx     │
                        │  (80/443)   │
                        └──────┬──────┘
                               │
                    ┌──────────┴──────────┐
                    │                       │
              ┌─────▼─────┐           ┌─────▼─────┐
              │    API    │           │  Grafana   │
              │  (8000)   │           │  (3000)    │
              └─────┬─────┘           └─────┬─────┘
                    │                       │
        ┌───────────┼───────────────┬───────┴──────┐
        │           │               │               │
   ┌────▼────┐ ┌───▼────┐   ┌──────▼─────┐ ┌─────▼─────┐
   │ Neo4j   │ │ Redis  │   │ Prometheus │ │  Metrics  │
   │(7687)   │ │(6379)  │   │  (9090)    │ │ Exporter  │
   └─────────┘ └────────┘   └────────────┘ └───────────┘
```

---

## 前置要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 20 GB | 50 GB+ SSD |

### 软件要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 用于代码部署

### 验证安装

```bash
# 检查 Docker
docker --version
docker-compose --version

# 检查 Git
git --version
```

---

## 快速开始

### 1. 克隆代码

```bash
git clone <repository-url>
cd pj-pharmaKG
```

### 2. 配置环境变量

```bash
# 复制生产环境配置
cp deployment/.env.production deployment/.env

# 编辑配置文件，修改必要参数
nano deployment/.env
```

**重要配置项：**

```bash
# 修改数据库密码（务必修改）
NEO4J_PASSWORD=your_secure_password

# 设置 API 密钥
SECRET_KEY=your-secret-key-here

# 配置 API 密钥（如需要）
CLINICALTRIALS_API_KEY=your_key_here
CHEMBL_API_KEY=your_key_here
FDA_API_KEY=your_key_here
```

### 3. 配置 SSL 证书（可选）

```bash
# 创建 SSL 目录
mkdir -p deployment/ssl

# 方式1: 使用自签名证书（仅用于测试）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/ssl/key.pem \
  -out deployment/ssl/cert.pem

# 方式2: 使用 Let's Encrypt（推荐用于生产）
# certbot certonly --standalone -d api.pharmakg.com
```

### 4. 启动服务

```bash
cd deployment
./deploy.sh deploy
```

### 5. 验证部署

```bash
# 健康检查
./deploy.sh health

# 访问 API 文档
curl http://localhost:8000/docs

# 访问 Grafana
# 用户名: admin
# 密码: admin
```

---

## 详细配置

### 环境变量配置

主配置文件：`deployment/.env.production`

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `NEO4J_URI` | Neo4j 连接地址 | `bolt://neo4j:7687` |
| `NEO4J_USER` | Neo4j 用户名 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | - |
| `API_HOST` | API 监听地址 | `0.0.0.0` |
| `API_PORT` | API 端口 | `8000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `WORKERS` | 工作进程数 | `4` |
| `REDIS_HOST` | Redis 主机 | `redis` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `SECRET_KEY` | JWT 密钥 | - |

### Nginx 配置

配置文件：`deployment/nginx.conf`

**主要功能：**
- 反向代理到 FastAPI 服务
- SSL/TLS 终止
- Gzip 压缩
- 速率限制
- 静态文件服务

**自定义配置：**

```nginx
# 修改服务器名称
server_name api.pharmakg.com;

# 添加自定义限流规则
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
```

### Docker Compose 配置

配置文件：`deployment/docker-compose.yml`

**资源配置：**

```yaml
services:
  neo4j:
    environment:
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G

  api:
    environment:
      - WORKERS=4
```

---

## 服务管理

### 部署脚本使用

```bash
./deploy.sh [COMMAND] [OPTIONS]
```

**可用命令：**

| 命令 | 说明 |
|------|------|
| `deploy` | 部署所有服务 |
| `start` | 启动所有服务 |
| `stop` | 停止所有服务 |
| `restart` | 重启所有服务 |
| `logs [SERVICE]` | 查看服务日志 |
| `health` | 健康检查 |
| `backup` | 备份数据 |
| `update SERVICE` | 更新指定服务 |
| `cleanup` | 清理所有容器和卷 |
| `monitor` | 实时监控服务状态 |
| `help` | 显示帮助信息 |

### 常用操作示例

```bash
# 1. 部署应用
./deploy.sh deploy

# 2. 查看 API 日志
./deploy.sh logs api

# 3. 重启 Neo4j
docker-compose restart neo4j

# 4. 进入容器调试
docker-compose exec api bash
docker-compose exec neo4j cypher-shell

# 5. 更新 API 代码
./deploy.sh update api

# 6. 扩展服务
docker-compose up -d --scale api=3
```

---

## 监控与日志

### Prometheus 监控

访问地址：`http://localhost:9090`

**监控指标：**

- API 请求速率和延迟
- Neo4j 查询性能
- 系统资源使用
- 自定义业务指标

配置文件：`deployment/prometheus.yml`

### Grafana 可视化

访问地址：`http://localhost:3000`

**默认凭据：**
- 用户名：`admin`
- 密码：`admin`

**首次登录后请修改密码！**

### 日志管理

```bash
# 查看所有日志
./deploy.sh logs

# 查看特定服务日志
docker-compose logs -f --tail=100 api
docker-compose logs -f --tail=100 neo4j

# 导出日志
docker-compose logs > logs_$(date +%Y%m%d).log
```

**日志位置：**
- 应用日志：容器内 `/app/logs/`
- Nginx 日志：`/var/log/nginx/`
- Neo4j 日志：`neo4j_logs/` 卷

---

## 备份与恢复

### 数据备份

```bash
# 手动备份
./deploy.sh backup

# 自动备份（添加到 crontab）
0 2 * * * /path/to/deploy.sh backup
```

备份位置：`deployment/backups/`

### 数据恢复

```bash
# 从备份恢复 Neo4j 数据
docker-compose exec neo4j neo4j-admin load \
    --from=/backup/neo4j_backup_20240101 \
    --database=neo4j \
    --force
```

---

## 故障排查

### 常见问题

#### 1. 服务启动失败

```bash
# 检查服务状态
docker-compose ps

# 查看详细日志
./deploy.sh logs <service>

# 常见原因：
# - 端口被占用：netstat -tunlp | grep <port>
# - 内存不足：docker stats
# - 配置错误：docker-compose config
```

#### 2. API 无法访问 Neo4j

```bash
# 检查 Neo4j 连接
docker-compose exec api curl http://neo4j:7474

# 检查环境变量
docker-compose exec api env | grep NEO4J

# 测试 Neo4j 密码
docker-compose exec neo4j cypher-shell -u neo4j -p <password>
```

#### 3. 性能问题

```bash
# 查看资源使用
docker stats

# 进入 Neo4j 调优
docker-compose exec neo4j cypher-shell
CALL dbms.queryRouter("CALL dbms.listQueries()")

# 检查缓存
docker-compose exec redis redis-cli INFO
```

#### 4. SSL 证书问题

```bash
# 检查证书有效期
openssl x509 -in deployment/ssl/cert.pem -text -noout

# 测试 SSL 配置
docker-compose exec nginx nginx -t
```

### 调试模式

```bash
# 启用详细日志
LOG_LEVEL=DEBUG ./deploy.sh start

# 进入容器调试
docker-compose exec api bash

# 查看 Neo4j 查询日志
docker-compose exec neo4j cat logs/debug.log
```

---

## 生产环境最佳实践

### 1. 安全加固

```bash
# 修改所有默认密码
nano deployment/.env.production

# 配置防火墙
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable

# 限制容器权限
# 在 docker-compose.yml 中添加：
# user: "1000:1000"
# read_only: true
```

### 2. 性能优化

```yaml
# docker-compose.yml 优化
neo4j:
  environment:
    # 增加 JVM 堆内存
    - NEO4J_dbms_memory_heap_initial__size=1g
    - NEO4J_dbms_memory_heap_max__size=4g
    # 增加页面缓存
    - NEO4J_dbms_memory_pagecache_size=2g

api:
  environment:
    # 增加工作进程
    - WORKERS=8
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
```

### 3. 高可用性

```yaml
# 使用健康检查
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# 配置重启策略
restart: unless-stopped
```

### 4. 日志管理

```bash
# 配置日志轮转
# 在 docker-compose.yml 中添加：
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 5. 监控告警

```yaml
# prometheus alerts.yml 配置示例
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High API error rate"
```

---

## 目录结构

```
deployment/
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # API 服务 Docker 镜像
├── nginx.conf              # Nginx 配置文件
├── deploy.sh               # 部署管理脚本
├── .env.production        # 生产环境变量
├── prometheus.yml          # Prometheus 监控配置
├── ssl/                    # SSL 证书目录
│   ├── cert.pem           # 证书文件
│   └── key.pem            # 私钥文件
├── backups/               # 数据备份目录
├── grafana/               # Grafana 配置
│   └── provisioning/       # 仪表板配置
└── README.md              # 本文档
```

---

## 维护建议

### 定期维护任务

| 任务 | 频率 | 说明 |
|------|------|------|
| 数据备份 | 每天 | 自动备份 Neo4j 数据 |
| 日志清理 | 每周 | 清理旧日志文件 |
| 安全更新 | 每月 | 更新容器镜像和依赖 |
| 性能审查 | 每月 | 分析性能指标 |
| 容量规划 | 每季度 | 评估资源需求 |

### 更新流程

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新服务
./deploy.sh update api

# 3. 验证更新
./deploy.sh health
```

---

## 技术支持

### 文档资源

- [Docker 官档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Neo4j 文档](https://neo4j.com/docs/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Nginx 文档](https://nginx.org/en/docs/)

### 问题反馈

如遇到部署问题，请提供以下信息：

1. 系统环境（OS 版本、Docker 版本）
2. 错误日志
3. 配置文件（隐藏敏感信息）
4. 复现步骤

---

## 许可证

Copyright © 2024 PharmaKG Team. All rights reserved.
