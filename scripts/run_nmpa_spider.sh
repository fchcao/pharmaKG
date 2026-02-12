#!/bin/bash
# NMPA Spider Launcher - 自动激活 data-spider 环境并运行爬虫

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== NMPA Spider Launcher ===${NC}"
echo ""

# 检查 conda 环境
if ! command -v conda &> /dev/null; then
    echo "错误: conda 未安装或未在 PATH 中"
    exit 1
fi

# 激活 data-spider 环境
echo -e "${YELLOW}激活 data-spider 环境...${NC}"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate data-spider

# 检查环境是否激活
if [[ "$CONDA_DEFAULT_ENV" != "data-spider" ]]; then
    echo "错误: 无法激活 data-spider 环境"
    echo "请先运行: conda create -n data-spider python=3.10 -y"
    exit 1
fi

echo -e "${GREEN}✓ 环境 data-spider 已激活${NC}"
echo ""

# 解析命令参数
SPIDER_NAME=${1:-"nmpa_list"}
OUTPUT_FILE=${2:-"test_output.json"}

echo -e "${YELLOW}运行爬虫:${NC} $SPIDER_NAME"
echo -e "${YELLOW}输出文件:${NC} $OUTPUT_FILE"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 运行爬虫
echo -e "${GREEN}开始爬取...${NC}"
scrapy crawl "$SPIDER_NAME" -o "$OUTPUT_FILE"

echo ""
echo -e "${GREEN}=== 爬取完成 ===${NC}"
echo -e "输出文件: ${YELLOW}$OUTPUT_FILE${NC}"
echo -e "查看结果: ${GREEN}cat $OUTPUT_FILE | python3 -m json.tool | head -30${NC}"
