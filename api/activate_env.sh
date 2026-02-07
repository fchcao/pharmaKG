#!/bin/bash
#===========================================================
# PharmaKG API 环境激活脚本
# Pharmaceutical Knowledge Graph - API Environment Activation
#===========================================================
# 用途: 快速激活 PharmaKG API 虚拟环境
#===========================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "PharmaKG API - 环境激活"
echo "=========================================="
echo ""

# 检查 conda 是否可用
if command -v conda &> /dev/null; then
    echo "正在激活 Conda 虚拟环境 'pharmakg-api'..."

    # 初始化 conda（如果尚未初始化）
    if [ -z "$CONDA_DEFAULT_ENV" ]; then
        source "$(conda info --base)/etc/profile.d/conda.sh"
    fi

    # 检查环境是否存在
    if conda env list | grep -q "^pharmakg-api "; then
        conda activate pharmakg-api
        echo "✓ Conda 环境 'pharmakg-api' 已激活"
    else
        echo "✗ 错误: Conda 环境 'pharmakg-api' 不存在!"
        echo ""
        echo "请先创建虚拟环境:"
        echo "  cd $PROJECT_ROOT"
        echo "  conda create -n pharmakg-api python=3.11 -y"
        echo "  conda activate pharmakg-api"
        echo "  pip install -r api/requirements.txt"
        exit 1
    fi
else
    # 检查 venv 是否存在
    if [ -d "$PROJECT_ROOT/venv" ]; then
        echo "正在激活虚拟环境: $PROJECT_ROOT/venv"
        source "$PROJECT_ROOT/venv/bin/activate"
        echo "✓ 虚拟环境已激活"
    else
        echo "✗ 错误: 未找到虚拟环境!"
        echo ""
        echo "请先创建虚拟环境:"
        echo "  cd $PROJECT_ROOT"
        echo "  conda create -n pharmakg-api python=3.11 -y"
        echo "  或"
        echo "  python -m venv venv"
        exit 1
    fi
fi

echo ""
echo "项目根目录: $PROJECT_ROOT"
echo "当前 Python: $(which python)"
echo "Python 版本: $(python --version)"
echo ""
echo "启动 API 服务器:"
echo "  cd $PROJECT_ROOT/api"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "退出环境:"
echo "  conda deactivate"
echo "=========================================="
