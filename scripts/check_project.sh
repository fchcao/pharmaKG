#!/bin/bash
#===========================================================
# PharmaKG - 项目快速检查脚本
# Pharmaceutical Knowledge Graph - Quick Check Script
#===========================================================
# 版本: v1.0
# 描述: 快速验证项目文件和配置完整性
#===========================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# 计数器
TOTAL=0
PASSED=0
FAILED=0

# 项目根目录 (scripts/的父目录)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}PharmaKG 项目完整性检查${NC}"
echo -e "${BOLD}============================================${NC}\n"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    PASSED=$((PASSED + 1))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    FAILED=$((FAILED + 1))
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

# 检查文件或目录
check_exists() {
    local path=$1
    local desc=$2

    TOTAL=$((TOTAL + 1))
    if [ -e "$path" ]; then
        log_success "$desc 存在"
        return 0
    else
        log_error "$desc 不存在: $path"
        return 1
    fi
}

# 检查 Python 文件语法
check_python_syntax() {
    local file=$1
    TOTAL=$((TOTAL + 1))

    if python3 -m py_compile "$file" 2>/dev/null; then
        log_success "$file 语法正确"
        return 0
    else
        log_error "$file 语法错误"
        return 1
    fi
}

# 检查可执行权限
check_executable() {
    local file=$1
    TOTAL=$((TOTAL + 1))

    if [ -x "$file" ]; then
        log_success "$file 有执行权限"
        return 0
    else
        log_warn "$file 无执行权限"
        chmod +x "$file"
        log_success "已添加执行权限到 $file"
        return 0
    fi
}

# 检查文件非空
check_not_empty() {
    local file=$1
    local desc=$2
    TOTAL=$((TOTAL + 1))

    if [ -s "$file" ]; then
        log_success "$desc 内容完整"
        return 0
    else
        log_error "$desc 内容为空或不存在"
        return 1
    fi
}

# ============================================
# 1. 核心代码模块检查
# ============================================
log_info "检查核心代码模块..."

# API 模块
check_exists "api/main.py" "API 主文件"
check_exists "api/config.py" "API 配置"
check_exists "api/database.py" "数据库连接"

# ETL 模块
check_exists "etl/__init__.py" "ETL 模块"
check_exists "etl/config.py" "ETL 配置"
check_exists "etl/cli.py" "ETL CLI"
check_exists "etl/scheduler.py" "ETL 调度器"

# 图分析模块
check_exists "graph_analytics/__init__.py" "图分析模块"
check_exists "graph_analytics/algorithms.py" "图算法"
check_exists "graph_analytics/api.py" "图分析 API"

# ML 分析模块
check_exists "ml_analytics/__init__.py" "ML 分析模块"
check_exists "ml_analytics/models.py" "ML 模型"
check_exists "ml_analytics/predictors.py" "预测器"

# ============================================
# 2. 管道检查
# ============================================
log_info "\n检查 ETL 管道..."

check_exists "etl/pipelines/rd_pipeline.py" "R&D 管道"
check_exists "etl/pipelines/clinical_pipeline.py" "临床管道"
check_exists "etl/pipelines/sc_pipeline.py" "供应链管道"
check_exists "etl/pipelines/regulatory_pipeline.py" "监管管道"

# ============================================
# 3. API 服务检查
# ============================================
log_info "\n检查 API 服务..."

check_exists "api/services/research_domain.py" "R&D 服务"
check_exists "api/services/clinical_domain.py" "临床服务"
check_exists "api/services/supply_regulatory.py" "供应链监管服务"
check_exists "api/services/advanced_queries.py" "高级查询服务"
check_exists "api/services/aggregate_queries.py" "聚合查询服务"

# ============================================
# 4. 部署配置检查
# ============================================
log_info "\n检查部署配置..."

check_exists "deployment/docker-compose.yml" "Docker Compose 配置"
check_exists "deployment/Dockerfile" "Docker 镜像"
check_exists "deployment/nginx.conf" "Nginx 配置"
check_executable "deployment/deploy.sh" "部署脚本"
check_exists "deployment/.env.production" "环境变量配置"

# ============================================
# 5. 文档检查
# ============================================
log_info "\n检查文档..."

check_not_empty "README.md" "项目主文档"
check_not_empty "CHECKLIST.md" "检查清单文档"
check_not_empty "deployment/README.md" "部署文档"

# ============================================
# 6. 代码质量检查
# ============================================
log_info "\n检查代码质量..."

# 关键 Python 文件语法
critical_files=(
    "api/main.py"
    "etl/config.py"
    "etl/scheduler.py"
    "graph_analytics/algorithms.py"
    "ml_analytics/models.py"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        check_python_syntax "$file"
    fi
done

# ============================================
# 7. 依赖检查
# ============================================
log_info "\n检查依赖配置..."

if [ -f "api/requirements.txt" ]; then
    log_success "requirements.txt 存在"

    # 检查关键依赖
    key_packages=("fastapi" "neo4j" "pydantic" "uvicorn")
    for pkg in "${key_packages[@]}"; do
        if grep -qi "^$pkg" api/requirements.txt > /dev/null; then
            log_success "依赖 $pkg 已声明"
        else
            log_error "依赖 $pkg 未声明"
        fi
    done
else
    log_error "requirements.txt 不存在"
fi

# ============================================
# 8. 集成检查
# ============================================
log_info "\n检查模块集成..."

# 检查 API 是否导入了图分析模块
if grep -q "graph_analytics" api/main.py 2>/dev/null; then
    log_success "API 已集成图分析模块"
else
    log_error "API 未集成图分析模块"
fi

# 检查 ETL 模块是否完整
etl_modules=(
    "extractors"
    "transformers"
    "loaders"
    "pipelines"
    "quality"
)

for module in "${etl_modules[@]}"; do
    if [ -d "etl/$module" ]; then
        file_count=$(find "etl/$module" -name "*.py" | wc -l)
        if [ "$file_count" -gt 0 ]; then
            log_success "ETL/$module 模块存在 ($file_count 个文件)"
        else
            log_error "ETL/$module 模块为空"
        fi
    else
        log_error "ETL/$module 模块不存在"
    fi
done

# ============================================
# 9. 配置验证检查
# ============================================
log_info "\n验证配置..."

# 检查环境变量模板
if [ -f "deployment/.env.production" ]; then
    # 检查必需的配置项
    required_vars=("NEO4J_URI" "NEO4J_USER" "NEO4J_PASSWORD")
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" deployment/.env.production; then
            log_success "配置项 $var 已设置"
        else
            log_error "配置项 $var 未设置"
        fi
    done
else
    log_error "环境变量配置文件不存在"
fi

# 检查 Docker Compose 配置
if command -v docker-compose &> /dev/null; then
    if docker-compose -f deployment/docker-compose.yml config > /dev/null 2>&1; then
        log_success "Docker Compose 配置有效"
    else
        log_error "Docker Compose 配置无效"
    fi
else
    log_warn "Docker Compose 未安装，跳过配置验证"
fi

# ============================================
# 10. 测试套件检查
# ============================================
log_info "\n检查测试套件..."

if [ -f "api/tests/test_main.py" ] || [ -f "tests/" ]; then
    log_success "测试套件存在"
else
    log_warn "未找到测试套件（建议添加）"
fi

# ============================================
# 生成检查报告
# ============================================
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}检查报告总结${NC}"
echo -e "${BOLD}============================================${NC}\n"

# 打印统计
echo -e "${BOLD}统计信息:${NC}"
echo "  总检查项: $TOTAL"
echo -e "  通过: ${GREEN}$PASSED${NC}"
echo -e "  失败: ${RED}$FAILED${NC}"
echo ""

# 计算完成率
if [ $TOTAL -gt 0 ]; then
    rate=$((PASSED * 100 / TOTAL))
    echo -e "  完成率: $rate%"

    if [ $rate -ge 80 ]; then
        echo -e "\n${GREEN}✅ 项目验收通过！${NC}\n"
    elif [ $rate -ge 60 ]; then
        echo -e "\n${YELLOW}⚠️  项目基本就绪，有少量问题需改进${NC}\n"
    else
        echo -e "\n${RED}❌ 项目未达到验收标准${NC}\n"
        echo "请查看上述失败项并进行修复。"
    fi
fi

echo -e "${BOLD}============================================${NC}"

# 退出码：根据检查结果设置
if [ $FAILED -gt 0 ]; then
    exit 1
fi
