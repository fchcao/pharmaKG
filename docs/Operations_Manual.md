# PharmaKG 运维手册

**版本**: v1.0
**最后更新**: 2026-02-12
**环境**: AutoDL 云服务

---

## 服务状态概览

| 服务 | 端口 | 进程 | 状态 |
|------|------|------|------|
| Neo4j 数据库 | 7474 (HTTP), 7687 (Bolt) | java | ✅ |
| FastAPI 后端 | 8000 | uvicorn | ✅ |
| Vite 前端 | 3000 | node | ✅ |

---

## 快速启动命令

### 启动所有服务

```bash
#!/bin/bash
# 保存为 scripts/start_all.sh

echo "=== PharmaKG 服务启动 ==="

# 1. 启动 Neo4j
echo "[1/3] 启动 Neo4j..."
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j start

# 2. 启动后端 API
echo "[2/3] 启动 FastAPI 后端..."
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api
cd /root/autodl-tmp/pj-pharmaKG

# 检查是否已运行
if lsof -i :8000 > /dev/null 2>&1; then
    echo "后端已在运行"
else
    nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload \
        > logs/backend.log 2>&1 &
    echo $! > logs/backend.pid
    echo "后端已启动，PID: $(cat logs/backend.pid)"
fi

# 3. 启动前端
echo "[3/3] 启动 Vite 前端..."
cd /root/autodl-tmp/pj-pharmaKG/frontend

if lsof -i :3000 > /dev/null 2>&1; then
    echo "前端已在运行"
else
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    echo $! > ../logs/frontend.pid
    echo "前端已启动，PID: $(cat ../logs/frontend.pid)"
fi

# 等待服务就绪
sleep 5

# 健康检查
echo ""
echo "=== 服务健康检查 ==="
curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
echo ""
echo "前端访问: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo "Neo4j 浏览器: http://localhost:7474"
```

### 停止所有服务

```bash
#!/bin/bash
# 保存为 scripts/stop_all.sh

echo "=== PharmaKG 服务停止 ==="

# 1. 停止前端
if [ -f /root/autodl-tmp/pj-pharmaKG/logs/frontend.pid ]; then
    kill $(cat /root/autodl-tmp/pj-pharmaKG/logs/frontend.pid) 2>/dev/null
    rm -f /root/autodl-tmp/pj-pharmaKG/logs/frontend.pid
    echo "前端已停止"
fi

# 2. 停止后端
if [ -f /root/autodl-tmp/pj-pharmaKG/logs/backend.pid ]; then
    kill $(cat /root/autodl-tmp/pj-pharmaKG/logs/backend.pid) 2>/dev/null
    rm -f /root/autodl-tmp/pj-pharmaKG/logs/backend.pid
    echo "后端已停止"
fi

# 3. 停止 Neo4j
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j stop
echo "Neo4j 已停止"
```

---

## 单独服务管理

### Neo4j 数据库

```bash
# 启动
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j start

# 停止
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j stop

# 重启
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j restart

# 状态
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j status

# 日志
tail -f /var/log/neo4j/neo4j.log

# Cypher Shell 连接
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/cypher-shell -u neo4j -p pharmaKG2024!
```

### FastAPI 后端

```bash
# 激活环境
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api

# 启动（前台，用于调试）
cd /root/autodl-tmp/pj-pharmaKG
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 启动（后台）
nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload \
    > logs/backend.log 2>&1 &

# 停止
kill $(cat logs/backend.pid)

# 查看日志
tail -f logs/backend.log
```

### Vite 前端

```bash
# 启动（前台）
cd /root/autodl-tmp/pj-pharmaKG/frontend
npm run dev

# 启动（后台）
nohup npm run dev > ../logs/frontend.log 2>&1 &

# 停止
kill $(cat /root/autodl-tmp/pj-pharmaKG/logs/frontend.pid)

# 查看日志
tail -f logs/frontend.log
```

---

## 健康检查

```bash
#!/bin/bash
# 保存为 scripts/health_check.sh

echo "=== PharmaKG 健康检查 ==="

# 检查端口
echo -e "\n[端口检查]"
for port in 3000 8000 7474 7687; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✓ 端口 $port: 正常"
    else
        echo "✗ 端口 $port: 未监听"
    fi
done

# 检查后端健康
echo -e "\n[后端健康]"
curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health

# 检查 Neo4j
echo -e "\n[Neo4j 状态]"
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j status

# 检查进程
echo -e "\n[进程列表]"
ps aux | grep -E "uvicorn|vite|neo4j" | grep -v grep | awk '{printf "%-10s %6s  %s\n", $1, $2, $11}'
```

---

## 日志位置

| 服务 | 日志路径 |
|------|----------|
| Neo4j | `/var/log/neo4j/neo4j.log` |
| 后端 | `logs/backend.log` |
| 前端 | `logs/frontend.log` |
| 数据导入 | `logs/chembl_import.log` |

---

## 环境配置

### Conda 环境

```bash
# API 环境
conda activate pharmakg-api

# 数据采集环境
conda activate data-spider

# Playwright 测试环境
conda activate playwright-env
```

### 环境变量

```bash
# 后端配置 (api/.env)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pharmaKG2024!

# 前端配置 (frontend/.env.development)
VITE_API_BASE_URL=/api
```

---

## 常见问题

### 端口占用

```bash
# 查看端口占用
lsof -i :8000
lsof -i :3000
lsof -i :7474

# 释放端口
kill -9 <PID>
```

### Neo4j 连接失败

```bash
# 检查 Neo4j 状态
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j status

# 重启 Neo4j
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j restart

# 查看错误日志
tail -100 /var/log/neo4j/neo4j.log
```

### 后端启动失败

```bash
# 检查 Python 环境
conda activate pharmakg-api
pip list | grep neo4j

# 重新安装依赖
pip install -r api/requirements.txt

# 查看错误日志
tail -100 logs/backend.log
```

---

## 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 前端应用 | http://localhost:3000 | React 应用 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| API 文档 | http://localhost:8000/redoc | ReDoc |
| Neo4j 浏览器 | http://localhost:7474 | 图数据库管理界面 |

---

## 备份与恢复

### 数据备份

```bash
# Neo4j 备份
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j-admin backup \
  --backup-dir=/root/backup \
  --from=/root/autodl-tmp/pj-pharmaKG/neo4j/data \
  --name=graph.db-backup-$(date +%Y%m%d)
```

### 数据恢复

```bash
# 停止 Neo4j
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j stop

# 恢复备份
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j-admin load \
  --from=/root/backup/graph.db-backup-YYYYMMDD \
  --database=neo4j \
  --force

# 启动 Neo4j
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j start
```

---

## 附录：完整启动脚本

创建 `/root/autodl-tmp/pj-pharmaKG/scripts/start_all.sh`:

```bash
#!/bin/bash
set -e

PROJECT_DIR="/root/autodl-tmp/pj-pharmaKG"
cd "$PROJECT_DIR"

echo "=== PharmaKG 服务启动 ==="

# 1. Neo4j
echo "[1/3] 启动 Neo4j..."
$PROJECT_DIR/neo4j/current/bin/neo4j start || echo "Neo4j already running"

# 2. 后端
echo "[2/3] 启动 FastAPI 后端..."
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api

if ! lsof -i :8000 > /dev/null 2>&1; then
    nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload \
        > logs/backend.log 2>&1 &
    echo $! > logs/backend.pid
fi

# 3. 前端
echo "[3/3] 启动 Vite 前端..."
cd "$PROJECT_DIR/frontend"

if ! lsof -i :3000 > /dev/null 2>&1; then
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    echo $! > ../logs/frontend.pid
fi

sleep 3

echo ""
echo "=== 服务状态 ==="
curl -s http://localhost:8000/health
echo ""
echo "前端: http://localhost:3000"
echo "API: http://localhost:8000/docs"
```

---

---

## 故障排查教训 (实战经验)

### 教训 1: 端口占用检测不可靠

**问题**: `lsof` 命令在某些环境不可用或需要 root 权限，导致误判端口状态。

**解决方案**: 使用 `ss -tlnp` 或 `netstat -tlnp` 检查端口，或直接通过进程名检查。

```bash
# 不推荐（可能失败）
lsof -i :8000

# 推荐（更可靠）
ss -tlnp | grep :8000
# 或
ps aux | grep uvicorn | grep -v grep
```

### 教训 2: 多次启动产生僵尸进程

**问题**: 重复执行启动脚本会创建多个进程，前端会自动切换端口（3000→3001→3002...）。

**解决方案**: 启动前必须先清理旧进程，使用 `pkill -9 -f` 强制清理。

```bash
# 停止服务时必须清理干净
pkill -9 -f "uvicorn" 2>/dev/null
pkill -9 -f "vite" 2>/dev/null
# 检查是否清理成功
ps aux | grep -E "uvicorn|vite" | grep -v grep
```

### 教训 3: 后端 uvicorn 有多个进程

**问题**: uvicorn 使用 `--reload` 时会启动多个进程（主进程 + 重载进程 + 工作进程），`kill` 主进程后子进程可能仍在运行。

**解决方案**: 使用 `pkill -9 -f "uvicorn"` 清理所有相关进程，而不是只杀 PID。

### 教训 4: 必须激活专用虚拟环境

**问题**: 未激活 `pharmakg-api` 环境可能导致依赖缺失或路径错误。

**解决方案**: 启动后端时必须先激活环境。

```bash
# 错误示例
nohup python3 -m uvicorn ...

# 正确示例
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api
nohup python3 -m uvicorn ...
```

### 教训 5: 日志路径必须使用绝对路径

**问题**: 在 `frontend` 目录启动时使用相对路径 `../logs/` 可能失败。

**解决方案**: 使用绝对路径或先确保目录存在。

```bash
# 推荐使用绝对路径
nohup npm run dev > /root/autodl-tmp/pj-pharmaKG/logs/frontend.log 2>&1 &
```

### 教训 6: Neo4j 必须先于后端启动

**问题**: 后端启动时如果 Neo4j 未就绪，`neo4j_connected` 会显示 `false`。

**解决方案**: 启动 Neo4j 后等待 5-10 秒让它完全就绪，再启动后端。

### 正确的启动流程

```bash
# 1. 清理旧进程（最重要！）
pkill -9 -f "uvicorn" 2>/dev/null
pkill -9 -f "vite" 2>/dev/null
sleep 2

# 2. 启动 Neo4j
/root/autodl-tmp/pj-pharmaKG/neo4j/current/bin/neo4j start
sleep 5  # 等待 Neo4j 完全启动

# 3. 启动后端（激活环境！）
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api
cd /root/autodl-tmp/pj-pharmaKG
nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload \
    > logs/backend.log 2>&1 &
echo $! > logs/backend.pid

# 4. 启动前端
cd /root/autodl-tmp/pj-pharmaKG/frontend
nohup npm run dev > /root/autodl-tmp/pj-pharmaKG/logs/frontend.log 2>&1 &
echo $! > /root/autodl-tmp/pj-pharmaKG/logs/frontend.pid

# 5. 验证
sleep 5
curl -s http://localhost:8000/health
```

---

**文档维护**: 每次服务配置变更时更新此文档。
