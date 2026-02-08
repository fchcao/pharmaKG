#!/usr/bin/env python3
#===========================================================
# 从 ChEMBL 靶点数据提取 UniProt IDs
# Extract UniProt IDs from ChEMBL Target Data
#===========================================================

import sys
import json
import logging
from pathlib import Path
from typing import List, Set
from collections import defaultdict

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def extract_uniprot_ids_from_json(json_file: Path) -> Set[str]:
    """
    从 ChEMBL JSON 文件提取 UniProt IDs

    Args:
        json_file: ChEMBL 靶点 JSON 文件路径

    Returns:
        UniProt ID 集合
    """
    uniprot_ids = set()

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 处理不同的数据结构
        if isinstance(data, list):
            entities = data
        elif isinstance(data, dict):
            if 'entities' in data:
                entities = data['entities']
            elif 'rd:Target' in data:
                entities = data['rd:Target']
            else:
                entities = []
        else:
            entities = []

        # 提取 UniProt IDs
        for entity in entities:
            if isinstance(entity, dict):
                identifiers = entity.get('identifiers', {})
                uniprot_id = identifiers.get('UniProt')

                if uniprot_id:
                    uniprot_ids.add(uniprot_id)

        logger.info(f"从 {json_file} 提取到 {len(uniprot_ids)} 个唯一 UniProt ID")

    except Exception as e:
        logger.error(f"处理文件失败 {json_file}: {e}")

    return uniprot_ids


def extract_uniprot_ids_from_multiple_files(file_pattern: Path) -> Set[str]:
    """
    从多个匹配模式的文件提取 UniProt IDs

    Args:
        file_pattern: 文件路径模式

    Returns:
        UniProt ID 集合
    """
    all_uniprot_ids = set()

    # 查找所有匹配的文件
    parent_dir = file_pattern.parent
    pattern = file_pattern.name

    if '*' in pattern or '?' in pattern:
        import glob
        matching_files = list(Path(parent_dir).glob(pattern))
    else:
        matching_files = [file_pattern] if file_pattern.exists() else []

    logger.info(f"找到 {len(matching_files)} 个匹配文件")

    for file_path in matching_files:
        uniprot_ids = extract_uniprot_ids_from_json(file_path)
        all_uniprot_ids.update(uniprot_ids)

    logger.info(f"总共提取到 {len(all_uniprot_ids)} 个唯一 UniProt ID")

    return all_uniprot_ids


def save_uniprot_ids(uniprot_ids: Set[str], output_file: Path):
    """
    保存 UniProt IDs 到文件

    Args:
        uniprot_ids: UniProt ID 集合
        output_file: 输出文件路径
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for uniprot_id in sorted(uniprot_ids):
            f.write(f"{uniprot_id}\n")

    logger.info(f"保存 {len(uniprot_ids)} 个 UniProt ID 到: {output_file}")


def analyze_uniprot_ids(uniprot_ids: Set[str]) -> dict:
    """
    分析 UniProt IDs

    Args:
        uniprot_ids: UniProt ID 集合

    Returns:
        分析结果字典
    """
    analysis = {
        'total': len(uniprot_ids),
        'by_length': defaultdict(int),
        'by_prefix': defaultdict(int),
        'examples': list(sorted(uniprot_ids))[:10]
    }

    for uniprot_id in uniprot_ids:
        # 按长度分组
        length = len(uniprot_id)
        analysis['by_length'][length] += 1

        # 按前缀分组
        if len(uniprot_id) >= 2:
            prefix = uniprot_id[:2]
            analysis['by_prefix'][prefix] += 1

    return analysis


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='从 ChEMBL 数据提取 UniProt IDs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 从单个文件提取
  python scripts/extract_uniprot_from_chembl.py data/processed/documents/chembl/chembl_targets_*.json

  # 从所有 ChEMBL 靶点文件提取
  python scripts/extract_uniprot_from_chembl.py data/processed/documents/chembl/chembl_targets_*.json -o data/sources/uniprot_ids.txt

  # 分析并显示统计信息
  python scripts/extract_uniprot_from_chembl.py data/processed/documents/chembl/chembl_targets_*.json --analyze
        """
    )

    parser.add_argument(
        'input_files',
        type=str,
        help='输入 JSON 文件路径（支持通配符）'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/sources/uniprot_ids.txt',
        help='输出文件路径（默认: data/sources/uniprot_ids.txt）'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='分析 UniProt IDs 并显示统计信息'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='限制输出的 ID 数量（用于测试）'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("开始提取 UniProt IDs...")

    # 提取 UniProt IDs
    input_path = Path(args.input_files)
    uniprot_ids = extract_uniprot_ids_from_multiple_files(input_path)

    if not uniprot_ids:
        logger.error("未找到任何 UniProt IDs")
        return 1

    # 应用限制
    if args.limit and args.limit < len(uniprot_ids):
        logger.info(f"限制输出到 {args.limit} 个 IDs")
        uniprot_ids = set(list(uniprot_ids)[:args.limit])

    # 分析（如果请求）
    if args.analyze:
        analysis = analyze_uniprot_ids(uniprot_ids)

        print(f"\n{'='*60}")
        print("UniProt ID 分析")
        print(f"{'='*60}")
        print(f"总数: {analysis['total']}")
        print(f"\n按长度分布:")
        for length, count in sorted(analysis['by_length'].items()):
            print(f"  {length} 字符: {count} 个")
        print(f"\n按前缀分布:")
        for prefix, count in sorted(analysis['by_prefix'].items())[:10]:
            print(f"  {prefix}: {count} 个")
        print(f"\n示例 IDs:")
        for example_id in analysis['examples']:
            print(f"  {example_id}")

    # 保存到文件
    output_file = Path(args.output)
    save_uniprot_ids(uniprot_ids, output_file)

    print(f"\n成功提取 {len(uniprot_ids)} 个 UniProt IDs 到: {output_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
