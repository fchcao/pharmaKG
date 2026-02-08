#!/usr/bin/env python3
#===========================================================
# PharmaKG 综合ID映射修复工具
# Pharmaceutical Knowledge Graph - Comprehensive ID Mapping Fix
#===========================================================
# 版本: v1.0
# 描述: 修复所有数据源的ID映射问题，包括特殊字符处理
#===========================================================

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_id_for_comparison(id_str: str) -> str:
    """
    标准化ID用于比较
    - 移除所有非字母数字字符（保留下划线）
    - 将斜杠转为短横线
    - 将连续的短横线/下划线压缩为单个
    - 转为小写
    """
    if not id_str:
        return id_str

    # 替换斜杠为短横线
    normalized = id_str.replace('/', '-')

    # 移除所有特殊字符（保留字母数字、下划线、短横线）
    normalized = re.sub(r'[^\w\-]', '', normalized)

    # 压缩连续的短横线/下划线
    while '--' in normalized:
        normalized = normalized.replace('--', '-')
    while '__' in normalized:
        normalized = normalized.replace('__', '_')
    while '-_' in normalized or '_-' in normalized:
        normalized = normalized.replace('-_', '_').replace('_-', '_')

    return normalized.lower()


def build_fuzzy_id_map(entity_ids: Set[str]) -> Dict[str, str]:
    """
    构建模糊ID映射表

    对于每个实体ID，创建多个变体映射到原始ID
    """
    id_map = {}

    # 直接映射
    for entity_id in entity_ids:
        id_map[entity_id] = entity_id

    # 为每个实体ID创建标准化变体
    for entity_id in entity_ids:
        normalized = normalize_id_for_comparison(entity_id)

        # 如果标准化后的ID与原始不同，添加映射
        if normalized != entity_id.lower():
            # 检查是否已有映射
            if normalized in id_map:
                # 如果多个实体映射到同一个标准化ID，保留第一个
                continue
            id_map[normalized] = entity_id

    return id_map


class ComprehensiveIDFixer:
    """
    综合ID映射修复器
    处理所有数据源的ID映射问题
    """

    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.log_dir = data_root / 'logs'
        self.log_dir.mkdir(exist_ok=True)

    def fix_regulatory_data(self):
        """修复监管数据"""
        logger.info("\n### 修复监管数据 ###")
        reg_dir = self.data_root / 'processed' / 'documents' / 'regulatory'

        # 查找最新的实体文件
        entity_files = sorted(reg_dir.glob('entities_fixed_*.json'), reverse=True)
        if not entity_files:
            entity_files = sorted(reg_dir.glob('entities_*.json'), reverse=True)
            entity_files = [f for f in entity_files if 'fixed' not in f.name]

        if not entity_files:
            logger.warning("未找到监管实体文件")
            return

        entities_file = entity_files[0]
        logger.info(f"实体文件: {entities_file.name}")

        # 加载实体
        with open(entities_file, 'r') as f:
            entities = json.load(f)

        # 查找最新的关系文件
        rel_files = sorted(reg_dir.glob('relationships_fixed_*.json'), reverse=True)
        if not rel_files:
            rel_files = sorted(reg_dir.glob('relationships_*.json'), reverse=True)
            rel_files = [f for f in rel_files if 'fixed' not in f.name]

        if not rel_files:
            logger.warning("未找到监管关系文件")
            return

        relationships_file = rel_files[0]
        logger.info(f"关系文件: {relationships_file.name}")

        # 加载关系
        with open(relationships_file, 'r') as f:
            relationships = json.load(f)

        logger.info(f"加载 {len(entities)} 个实体, {len(relationships)} 个关系")

        # 修复（监管数据已经在之前修复过，这里主要是验证）
        self._fix_and_save(entities, relationships, reg_dir, 'regulatory')

    def fix_crl_data(self):
        """修复CRL数据"""
        logger.info("\n### 修复CRL数据 ###")
        crl_dir = self.data_root / 'processed' / 'documents' / 'clinical_crl'

        # 查找最新的实体文件
        entity_files = sorted(crl_dir.glob('entities_*.json'), reverse=True)
        entity_files = [f for f in entity_files if 'fixed' not in f.name]

        if not entity_files:
            logger.warning("未找到CRL实体文件")
            return

        entities_file = entity_files[0]
        logger.info(f"实体文件: {entities_file.name}")

        # 加载实体
        with open(entities_file, 'r') as f:
            entities = json.load(f)

        # 查找最新的关系文件（可能是修复过的）
        rel_files = sorted(crl_dir.glob('relationships_*.json'), reverse=True)
        rel_files = [f for f in rel_files if 'summary' not in f.name]

        if not rel_files:
            logger.warning("未找到CRL关系文件")
            return

        relationships_file = rel_files[0]
        logger.info(f"关系文件: {relationships_file.name}")

        # 加载关系
        with open(relationships_file, 'r') as f:
            relationships = json.load(f)

        logger.info(f"加载 {len(entities)} 个实体, {len(relationships)} 个关系")

        # 修复
        self._fix_and_save(entities, relationships, crl_dir, 'crl')

    def _fix_and_save(self, entities: List[Dict], relationships: List[Dict], output_dir: Path, data_type: str):
        """修复并保存"""
        # 收集实体ID
        entity_ids = set()
        entity_by_normalized = {}

        for entity in entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            if primary_id:
                entity_ids.add(primary_id)
                normalized = normalize_id_for_comparison(primary_id)
                entity_by_normalized[normalized] = primary_id

        logger.info(f"实体ID数量: {len(entity_ids)}")
        logger.info(f"标准化实体ID数量: {len(entity_by_normalized)}")

        # 修复关系
        fixed_relationships = []
        fix_stats = defaultdict(int)

        for rel in relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            # 尝试直接匹配
            new_from = from_id if from_id in entity_ids else None
            new_to = to_id if to_id in entity_ids else None

            # 尝试标准化匹配
            if new_from is None:
                normalized_from = normalize_id_for_comparison(from_id)
                new_from = entity_by_normalized.get(normalized_from, from_id)
                if new_from != from_id:
                    fix_stats['from_normalized'] += 1

            if new_to is None:
                normalized_to = normalize_id_for_comparison(to_id)
                new_to = entity_by_normalized.get(normalized_to, to_id)
                if new_to != to_id:
                    fix_stats['to_normalized'] += 1

            # 检查是否仍不匹配
            if new_from not in entity_ids:
                fix_stats['from_unmatched'] += 1
            if new_to not in entity_ids:
                fix_stats['to_unmatched'] += 1

            fixed_relationships.append({
                **rel,
                'from': new_from,
                'to': new_to
            })

        # 验证修复结果
        after_from_match = sum(1 for r in fixed_relationships if r.get('from', '') in entity_ids)
        after_to_match = sum(1 for r in fixed_relationships if r.get('to', '') in entity_ids)

        logger.info(f"\n修复统计:")
        logger.info(f"  From ID标准化: {fix_stats['from_normalized']}")
        logger.info(f"  To ID标准化: {fix_stats['to_normalized']}")
        logger.info(f"  From ID未匹配: {fix_stats['from_unmatched']}")
        logger.info(f"  To ID未匹配: {fix_stats['to_unmatched']}")
        logger.info(f"\n修复后:")
        logger.info(f"  From ID匹配: {after_from_match}/{len(relationships)} ({100*after_from_match/len(relationships):.1f}%)")
        logger.info(f"  To ID匹配: {after_to_match}/{len(relationships)} ({100*after_to_match/len(relationships):.1f}%)")

        # 保存修复后的关系
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'relationships_fixed_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_relationships, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ 修复后的关系已保存: {output_file.name}")

        # 保存分析
        analysis = {
            'data_type': data_type,
            'timestamp': timestamp,
            'entities_count': len(entities),
            'relationships_count': len(relationships),
            'fix_stats': dict(fix_stats),
            'from_match_rate': 100 * after_from_match / len(relationships),
            'to_match_rate': 100 * after_to_match / len(relationships)
        }

        analysis_file = self.log_dir / f'{data_type}_id_fix_analysis_{timestamp}.json'
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 分析已保存: {analysis_file.name}")


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("PharmaKG 综合ID映射修复")
    logger.info("=" * 80)

    data_root = Path('/root/autodl-tmp/pj-pharmaKG/data')
    fixer = ComprehensiveIDFixer(data_root)

    # 修复监管数据
    fixer.fix_regulatory_data()

    # 修复CRL数据
    fixer.fix_crl_data()

    logger.info("\n" + "=" * 80)
    logger.info("✅ 综合ID映射修复完成")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
