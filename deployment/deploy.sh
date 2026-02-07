#!/bin/bash
#===========================================================
# PharmaKG - 部署脚本
# Pharmaceutical Knowledge Graph - Deployment Script
#===========================================================
# 版本: v1.0
# 描述: 生产环境部署脚本
#===========================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
COMPOSE_FILE="deployment/docker-compose.yml"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_info "Docker and Docker Compose are installed"
}

# 创建必要的目录
create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "deployment/ssl"
    mkdir -p "deployment/grafana/provisioning"
}

# 备份数据
backup_data() {
    log_info "Backing up data..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="$BACKUP_DIR/pharmakg_backup_$timestamp.tar.gz"

    docker-compose exec -T neo4j neo4j-admin dump \
        --database=neo4j \
        --to=/backup/neo4j_backup_$timestamp

    log_info "Backup completed: $backup_file"
}

# 启动服务
start_services() {
    log_info "Starting PharmaKG services..."

    # 构建镜像
    log_info "Building Docker images..."
    docker-compose build

    # 启动服务
    log_info "Starting services..."
    docker-compose up -d

    # 等待服务就绪
    log_info "Waiting for services to be ready..."
    sleep 10

    # 检查服务状态
    docker-compose ps

    log_info "Services started successfully!"
    log_info "API available at: http://localhost:8000"
    log_info "API docs at: http://localhost:8000/docs"
    log_info "Grafana at: http://localhost:3000 (admin/admin)"
}

# 停止服务
stop_services() {
    log_info "Stopping PharmaKG services..."
    docker-compose down
    log_info "Services stopped"
}

# 重启服务
restart_services() {
    log_info "Restarting PharmaKG services..."
    docker-compose restart
    log_info "Services restarted"
}

# 查看日志
view_logs() {
    service=${1:-api}
    docker-compose logs -f --tail=100 "$service"
}

# 健康检查
health_check() {
    log_info "Performing health check..."

    # 检查 API
    if curl -sf http://localhost:8000/health > /dev/null; then
        log_info "✓ API is healthy"
    else
        log_error "✗ API is not healthy"
    fi

    # 检查 Neo4j
    if curl -sf http://localhost:7474 > /dev/null; then
        log_info "✓ Neo4j is healthy"
    else
        log_error "✗ Neo4j is not healthy"
    fi

    # 检查 Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis is healthy"
    else
        log_warn "Redis might not be healthy"
    fi
}

# 更新服务
update_service() {
    service=${1:-api}

    log_info "Updating $service service..."

    # 拉取最新代码
    log_info "Pulling latest code..."
    git pull

    # 重新构建和启动
    docker-compose build "$service"
    docker-compose up -d "$service"

    log_info "$service updated successfully!"
}

# 清理资源
cleanup() {
    log_warn "Cleaning up resources..."
    docker-compose down -v
    docker system prune -f
    log_info "Cleanup completed"
}

# 监控
monitor() {
    log_info "Starting monitoring..."

    while true; do
        clear
        echo "=== PharmaKG Service Status ==="
        echo ""
        docker-compose ps
        echo ""
        echo "=== Resource Usage ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        echo ""
        echo "Press Ctrl+C to exit"
        sleep 5
    done
}

# 显示帮助
show_help() {
    cat << EOF
PharmaKG Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    deploy          Deploy all services
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    logs [SERVICE]   View logs for a service
    health          Perform health check
    backup          Backup Neo4j data
    update SERVICE   Update a specific service
    cleanup          Remove all containers and volumes
    monitor          Monitor service status
    help            Show this help message

Examples:
    $0 deploy
    $0 logs api
    $0 health
    $0 update api
EOF
}

# 主函数
main() {
    check_docker
    create_directories

    case "${1:-help}" in
        deploy)
            start_services
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs "${2:-api}"
            ;;
        health)
            health_check
            ;;
        backup)
            backup_data
            ;;
        update)
            update_service "${2:-api}"
            ;;
        cleanup)
            cleanup
            ;;
        monitor)
            monitor
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
