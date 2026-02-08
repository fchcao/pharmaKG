#!/usr/bin/env python3
#===========================================================
# PharmaKG CRL ID映射修复工具
# Pharmaceutical Knowledge Graph - CRL ID Mapping Fix
#===========================================================
# 版本: v1.0
# 描述: 修复CRL关系ID与实体primary_id不匹配的问题
#===========================================================

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class CRLIDMappingFixer:
    """
    CRL数据ID映射修复器

    修复关系ID与实体primary_id不匹配的问题
    """

    def __init__(self, entities_file: Path, relationships_file: Path):
        self.entities_file = entities_file
        self.relationships_file = relationships_file

        # 加载数据
        with open(entities_file, 'r', encoding='utf-8') as f:
            self.entities = json.load(f)

        with open(relationships_file, 'r', encoding='utf-8') as f:
            self.relationships = json.load(f)

        logger.info(f"加载 {len(self.entities)} 个实体, {len(self.relationships)} 个关系")

        # ID映射表
        self.id_map: Dict[str, str] = {}
        self.fix_stats = defaultdict(int)

    def _build_id_mapping(self) -> None:
        """构建ID映射表"""
        logger.info("构建ID映射表...")

        # 收集所有实体primary_id
        entity_ids = set()
        for entity in self.entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            if primary_id:
                entity_ids.add(primary_id)

        # 为每个关系ID查找匹配的实体ID
        all_rel_ids = set()
        for rel in self.relationships:
            all_rel_ids.add(rel.get('from', ''))
            all_rel_ids.add(rel.get('to', ''))

        # 构建映射：relationship_id -> entity_id
        for rel_id in all_rel_ids:
            if not rel_id:
                continue

            # 如果直接匹配，记录
            if rel_id in entity_ids:
                self.id_map[rel_id] = rel_id
                continue

            # 尝试日期格式转换：/ -> -
            if '/' in rel_id:
                normalized = rel_id.replace('/', '-')
                if normalized in entity_ids:
                    self.id_map[rel_id] = normalized
                    self.fix_stats['date_slash_to_dash'] += 1
                    continue

            # 尝试日期格式转换：- -> /
            if '-' in rel_id and rel_id.count('-') >= 2:
                normalized = rel_id.replace('-', '/')
                if normalized in entity_ids:
                    self.id_map[rel_id] = normalized
                    self.fix_stats['date_dash_to_slash'] += 1
                    continue

            # 尝试下划线转换：_ -> -
            if '_' in rel_id:
                normalized = rel_id.replace('_', '-')
                if normalized in entity_ids:
                    self.id_map[rel_id] = normalized
                    self.fix_stats['underscore_to_dash'] += 1
                    continue

            # 尝试下划线转换：- -> _
            if '-' in rel_id:
                normalized = rel_id.replace('-', '_')
                if normalized in entity_ids:
                    self.id_map[rel_id] = normalized
                    self.fix_stats['dash_to_underscore'] += 1
                    continue

            # 尝试组合转换：_/ -> -_
            if '/' in rel_id and '_' in rel_id:
                normalized = rel_id.replace('/', '_')
                if normalized in entity_ids:
                    self.id_map[rel_id] = normalized
                    self.fix_stats['combined_1'] += 1
                    continue

            # 未找到匹配
            self.fix_stats['unmatched'] += 1
            self.id_map[rel_id] = rel_id  # 保持原样

        logger.info(f"ID映射表构建完成: {len(self.id_map)} 个条目")

    def _analyze_matches(self) -> Tuple[int, int, List[str]]:
        """分析匹配情况"""
        logger.info("分析ID匹配情况...")

        # 收集所有实体primary_id
        entity_ids = set()
        for entity in self.entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            if primary_id:
                entity_ids.add(primary_id)

        # 检查修复前的匹配情况
        before_from_match = 0
        before_to_match = 0
        unmatched_samples = []

        for rel in self.relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            if from_id in entity_ids:
                before_from_match += 1
            elif len(unmatched_samples) < 20:
                unmatched_samples.append(f"FROM: {from_id}")

            if to_id in entity_ids:
                before_to_match += 1
            elif len(unmatched_samples) < 20:
                unmatched_samples.append(f"TO: {to_id}")

        total_rels = len(self.relationships)
        logger.info(f"\n修复前:")
        logger.info(f"  From ID匹配: {before_from_match}/{total_rels} ({100*before_from_match/total_rels:.1f}%)")
        logger.info(f"  To ID匹配: {before_to_match}/{total_rels} ({100*before_to_match/total_rels:.1f}%)")

        return before_from_match, before_to_match, unmatched_samples

    def fix_relationships(self) -> List[Dict]:
        """修复关系ID"""
        logger.info("\n开始修复关系ID...")

        # 先分析
        before_from, before_to, _ = self._analyze_matches()

        # 构建映射
        self._build_id_mapping()

        # 修复关系
        fixed_relationships = []
        from_fixed = 0
        to_fixed = 0

        for rel in self.relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            new_from = self.id_map.get(from_id, from_id)
            new_to = self.id_map.get(to_id, to_id)

            if new_from != from_id:
                from_fixed += 1
            if new_to != to_id:
                to_fixed += 1

            fixed_relationships.append({
                **rel,
                'from': new_from,
                'to': new_to
            })

        logger.info(f"\n修复统计:")
        logger.info(f"  From ID修复: {from_fixed}")
        logger.info(f"  To ID修复: {to_fixed}")
        logger.info(f"  未变化: {len(self.relationships) - from_fixed - to_fixed}")

        # 验证修复后
        entity_ids = set()
        for entity in self.entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            if primary_id:
                entity_ids.add(primary_id)

        after_from_match = sum(1 for r in fixed_relationships if r.get('from', '') in entity_ids)
        after_to_match = sum(1 for r in fixed_relationships if r.get('to', '') in entity_ids)

        logger.info(f"\n修复后:")
        logger.info(f"  From ID匹配: {after_from_match}/{len(fixed_relationships)} ({100*after_from_match/len(fixed_relationships):.1f}%)")
        logger.info(f"  To ID匹配: {after_to_match}/{len(fixed_relationships)} ({100*after_to_match/len(fixed_relationships):.1f}%)")

        return fixed_relationships

    def save_results(self, fixed_relationships: List[Dict], output_dir: Path) -> None:
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存修复后的关系
        rel_output = output_dir / f'relationships_fixed_{timestamp}.json'
        with open(rel_output, 'w', encoding='utf-8') as f:
            json.dump(fixed_relationships, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ 修复后的关系已保存: {rel_output}")

        # 保存统计
        stats = {
            'timestamp': timestamp,
            'input_files': {
                'entities': str(self.entities_file),
                'relationships': str(self.relationships_file)
            },
            'entities_count': len(self.entities),
            'relationships_count': len(self.relationships),
            'fix_statistics': dict(self.fix_stats),
            'id_map_size': len(self.id_map)
        }

        stats_output = output_dir / f'crl_fix_statistics_{timestamp}.json'
        with open(stats_output, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 修复统计已保存: {stats_output}")

        # 保存详细分析
        entity_ids = set()
        for entity in self.entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            if primary_id:
                entity_ids.add(primary_id)

        analysis = {
            'total_relationships': len(self.relationships),
            'id_map_size': len(self.id_map),
            'fix_statistics': dict(self.fix_stats),
            'unmatched_relationship_ids': [],
            'unmatched_entity_ids': []
        }

        # 找出未匹配的关系ID
        for rel in fixed_relationships[:50]:  # 只记录前50个
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')
            if from_id and from_id not in entity_ids:
                analysis['unmatched_relationship_ids'].append({'role': 'from', 'id': from_id})
            if to_id and to_id not in entity_ids:
                analysis['unmatched_relationship_ids'].append({'role': 'to', 'id': to_id})

        analysis_output = output_dir / f'crl_id_mapping_analysis_{timestamp}.json'
        with open(analysis_output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        logger.info(f"🔍 详细分析已保存: {analysis_output}")


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("PharmaKG CRL ID映射修复")
    logger.info("=" * 80)

    # 数据目录
    data_root = Path('/root/autodl-tmp/pj-pharmaKG/data')
    crl_dir = data_root / 'processed' / 'documents' / 'clinical_crl'
    log_dir = data_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    # 查找最新的数据文件
    entity_files = sorted(crl_dir.glob('entities_*.json'), reverse=True)
    rel_files = sorted(crl_dir.glob('relationships_*.json'), reverse=True)

    if not entity_files or not rel_files:
        logger.error("未找到CRL数据文件")
        return

    # 跳过已修复的文件
    entity_files = [f for f in entity_files if 'fixed' not in f.name]
    rel_files = [f for f in rel_files if 'fixed' not in f.name]

    if not entity_files or not rel_files:
        logger.warning("未找到未修复的CRL数据文件")
        return

    entities_file = entity_files[0]
    relationships_file = rel_files[0]

    logger.info(f"\n输入文件:")
    logger.info(f"  实体: {entities_file.name}")
    logger.info(f"  关系: {relationships_file.name}")

    # 创建修复器并执行
    fixer = CRLIDMappingFixer(entities_file, relationships_file)
    fixed_relationships = fixer.fix_relationships()
    fixer.save_results(fixed_relationships, crl_dir)

    logger.info("\n" + "=" * 80)
    logger.info("✅ CRL ID映射修复完成")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
