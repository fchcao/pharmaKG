# PharmaKG 快速参考

## 🚀 服务状态

### ✅ 当前运行状态
| 服务 | 地址 | 状态 |
|------|------|------|
| **前端开发服务器** | http://localhost:3000 | 🟢 运行中 |
| **后端API** | http://localhost:8000 | ⚪ 需启动 |
| **Neo4j** | bolt://localhost:7687 | ⚪ 需启动 |
| **Neo4j浏览器** | http://localhost:7474 | ⚪ 需启动 |

---

## 🎯 快速访问

### 前端页面
```
主页:           http://localhost:3000/
仪表板:         http://localhost:3000/dashboard
搜索:           http://localhost:3000/search
跨域查询:       http://localhost:3000/cross-domain

R&D领域:        http://localhost:3000/rd
  化合物:       http://localhost:3000/rd/compounds
  靶点:         http://localhost:3000/rd/targets
  分析:         http://localhost:3000/rd/assays
  通路:         http://localhost:3000/rd/pathways

临床领域:       http://localhost:3000/clinical
  试验:         http://localhost:3000/clinical/trials
  条件:         http://localhost:3000/clinical/conditions
  干预:         http://localhost:3000/clinical/interventions

供应链:         http://localhost:3000/supply
  制造商:       http://localhost:3000/supply/manufacturers
  设施:         http://localhost:3000/supply/facilities
  短缺:         http://localhost:3000/supply/shortages

监管:           http://localhost:3000/regulatory
  提交:         http://localhost:3000/regulatory/submissions
  批准:         http://localhost:3000/regulatory/approvals
  文档:         http://localhost:3000/regulatory/documents
```

### 后端API
```
API文档:        http://localhost:8000/docs
健康检查:       http://localhost:8000/health
搜索端点:       http://localhost:8000/api/v1/search/*
```

---

## 💻 常用命令

### 前端开发
```bash
# 进入前端目录
cd /root/autodl-tmp/pj-pharmaKG/frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm test

# 代码检查
npm run lint
```

### 后端API
```bash
# 进入API目录
cd /root/autodl-tmp/pj-pharmaKG/api

# 启动API服务器
conda activate pharmakg-api
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Neo4j
```bash
# 启动Neo4j（Docker）
docker-compose up -d neo4j

# 或使用Cypher Shell
cypher-shell -a bolt://localhost:7687 -u neo4j -p pharmaKG2024!
```

---

## 📊 数据统计

| 领域 | 节点数 | 主要实体 |
|------|--------|----------|
| R&D | 1,891,311 | 化合物、靶点、分析、通路 |
| 临床 | 0 | 试验、受试者、干预 |
| 供应链 | 324 | 制造商、设施、短缺 |
| 监管 | 1,938 | 提交、批准、文档 |
| **总计** | **1,894,173** | - |

---

## 🎨 功能特性

### 搜索功能
- ✅ 全文搜索（支持189万+化合物）
- ✅ 模糊搜索（容错匹配）
- ✅ 搜索建议（自动完成）
- ✅ 搜索聚合（按类型/域分组）

### 可视化功能
- ✅ 交互式图形（Cytoscape.js）
- ✅ 分子结构查看器
- ✅ 时间线图表
- ✅ 数据质量仪表板

### 领域功能
- ✅ R&D: 化合物、靶点、通路浏览
- ✅ 临床: 试验浏览（模拟数据）
- ✅ 供应链: 短缺实时监控
- ✅ 监管: 提交和批准跟踪

---

## 🔑 登录凭据

### Neo4j
```
用户名: neo4j
密码: pharmaKG2024!
```

### 数据库连接
```
URI: bolt://localhost:7687
```

---

## 📁 重要文件

### 配置文件
```
frontend/package.json           # 前端依赖
frontend/vite.config.ts         # Vite配置
api/config.py                   # API配置
deploy/docker/docker-compose.yml # Docker配置
```

### 文档
```
FRONTEND_STARTUP_GUIDE.md       # 前端启动指南
CLAUDE.md                       # 项目说明
docs/SEARCH_API_DOCUMENTATION.md # 搜索API文档
```

---

## ⚠️ 常见问题

**Q: 前端无法连接后端？**
A: 确保后端API正在运行在8000端口

**Q: 图形不显示？**
A: 检查Neo4j连接，确保数据库正在运行

**Q: 搜索无结果？**
A: 检查Neo4j全文索引是否已创建

**Q: 临床领域显示模拟数据？**
A: 临床域当前为空，使用模拟数据进行UI开发

---

## 📞 支持

- **项目目录**: /root/autodl-tmp/pj-pharmaKG
- **前端目录**: /root/autodl-tmp/pj-pharmaKG/frontend
- **API目录**: /root/autodl-tmp/pj-pharmaKG/api
- **文档目录**: /root/autodl-tmp/pj-pharmaKG/docs

---

**最后更新**: 2025年
**版本**: v1.0.0
