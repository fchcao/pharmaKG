#===========================================================
# PharmaKG ID映射修复工具
# Pharmaceutical Knowledge Graph - ID Mapping Fix Tool
#===========================================================
# 版本: v1.0
# 描述: 修复关系ID与实体ID不匹配的问题
#===========================================================

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IDMappingFixer:
    """
    ID映射修复工具

    解决关系中的from/to ID与实体primary_id不匹配的问题
    """

    def __init__(self, entities: List[Dict], relationships: List[Dict]):
        """
        初始化

        Args:
            entities: 实体列表
            relationships: 关系列表
        """
        self.entities = entities
        self.relationships = relationships

        # 创建日志目录
        self.log_dir = Path('/root/autodl-tmp/pj-pharmaKG/logs')
        self.log_dir.mkdir(exist_ok=True)

        # 分析结果
        self.analysis = {
            'entity_id_formats': defaultdict(int),
            'relationship_from_formats': defaultdict(int),
            'relationship_to_formats': defaultdict(int),
            'id_mappings': {},
            'unmatched_from': [],
            'unmatched_to': []
        }

    def analyze(self) -> Dict[str, Any]:
        """
        分析ID映射问题

        Returns:
            分析结果字典
        """
        logger.info("开始分析ID映射问题...")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. 分析实体ID格式
        for entity in self.entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            doc_id = props.get('document_id', '')

            if primary_id:
                self._categorize_id(primary_id, self.analysis['entity_id_formats'])

            # 构建document_id -> primary_id映射
            if doc_id and primary_id:
                if doc_id not in self.analysis['id_mappings']:
                    self.analysis['id_mappings'][doc_id] = primary_id

        # 2. 分析关系ID格式
        for rel in self.relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            self._categorize_id(from_id, self.analysis['relationship_from_formats'])
            self._categorize_id(to_id, self.analysis['relationship_to_formats'])

        # 3. 计算匹配率
        all_entity_ids = self._get_all_entity_primary_ids()

        for rel in self.relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            if from_id and from_id not in all_entity_ids:
                self.analysis['unmatched_from'].append(from_id)

            if to_id and to_id not in all_entity_ids:
                self.analysis['unmatched_to'].append(to_id)

        # 4. 生成分析报告
        self._generate_analysis_report(timestamp)

        return {
            'entity_id_formats': dict(self.analysis['entity_id_formats']),
            'relationship_from_formats': dict(self.analysis['relationship_from_formats']),
            'relationship_to_formats': dict(self.analysis['relationship_to_formats']),
            'id_mappings': self.analysis['id_mappings'],
            'unmatched_from_count': len(self.analysis['unmatched_from']),
            'unmatched_to_count': len(self.analysis['unmatched_to']),
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships)
        }

    def _categorize_id(self, id_val: str, counter: Dict[str, int]):
        """分类ID"""
        if id_val.startswith('REG-'):
            counter['REG-xxx'] += 1
        elif id_val.startswith('RegulatoryDocument-'):
            counter['RegulatoryDocument-xxx'] += 1
        elif id_val.startswith('RegulatoryAgency-'):
            counter['RegulatoryAgency-xxx'] += 1
        elif id_val.startswith('Company-'):
            counter['Company-xxx'] += 1
        else:
            counter['Other'] += 1

    def _get_all_entity_primary_ids(self) -> set:
        """获取所有实体的primary_id"""
        ids = set()
        for entity in self.entities:
            pid = entity.get('properties', {}).get('primary_id', '')
            if pid:
                ids.add(pid)
        return ids

    def _generate_analysis_report(self, timestamp: str):
        """生成分析报告"""
        report_file = self.log_dir / f"id_mapping_analysis_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'entity_id_formats': dict(self.analysis['entity_id_formats']),
                'relationship_from_formats': dict(self.analysis['relationship_from_formats']),
                'relationship_to_formats': dict(self.analysis['relationship_to_formats']),
            },
            'id_mappings': self.analysis['id_mappings'],
            'unmatched_sample': {
                'from': self.analysis['unmatched_from'][:100],
                'to': self.analysis['unmatched_to'][:100]
            },
            'statistics': {
                'total_entities': len(self.entities),
                'total_relationships': len(self.relationships),
                'unmatched_from_count': len(self.analysis['unmatched_from']),
                'unmatched_to_count': len(self.analysis['unmatched_to'])
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"分析报告已保存: {report_file}")

    def fix_relationships(self) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        修复关系ID

        Returns:
            (修复后的关系列表, 修复统计)
        """
        logger.info("开始修复关系ID...")

        # 构建完整的ID映射表
        id_map = self._build_complete_id_mapping()

        # 应用映射到关系
        fixed_relationships = []
        fix_stats = {
            'total': len(self.relationships),
            'fixed_from': 0,
            'fixed_to': 0,
            'both_fixed': 0,
            'already_valid': 0,
            'failed': 0
        }

        all_entity_ids = self._get_all_entity_primary_ids()

        for rel in self.relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            fixed_from = False
            fixed_to = False

            # 修复from_id
            if from_id and from_id not in all_entity_ids:
                if from_id in id_map:
                    from_id = id_map[from_id]
                    fixed_from = True
                else:
                    # 尝试从实体中查找
                    mapped = self._find_entity_mapping(from_id)
                    if mapped:
                        from_id = mapped
                        fixed_from = True

            # 修复to_id
            if to_id and to_id not in all_entity_ids:
                if to_id in id_map:
                    to_id = id_map[to_id]
                    fixed_to = True
                else:
                    # 尝试从实体中查找
                    mapped = self._find_entity_mapping(to_id)
                    if mapped:
                        to_id = mapped
                        fixed_to = True

            # 统计
            if fixed_from and fixed_to:
                fix_stats['both_fixed'] += 1
            elif fixed_from:
                fix_stats['fixed_from'] += 1
            elif fixed_to:
                fix_stats['fixed_to'] += 1
            elif from_id in all_entity_ids and to_id in all_entity_ids:
                fix_stats['already_valid'] += 1
            else:
                fix_stats['failed'] += 1
                continue  # 跳过无法修复的关系

            # 创建修复后的关系
            fixed_rel = rel.copy()
            fixed_rel['from'] = from_id
            fixed_rel['to'] = to_id
            fixed_relationships.append(fixed_rel)

        # 记录修复统计
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = self.log_dir / f"fix_statistics_{timestamp}.json"

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(fix_stats, f, indent=2)

        logger.info(f"修复完成: {len(fixed_relationships)}/{fix_stats['total']} 条关系成功")
        logger.info(f"  From ID修复: {fix_stats['fixed_from'] + fix_stats['both_fixed']}")
        logger.info(f"  To ID修复: {fix_stats['fixed_to'] + fix_stats['both_fixed']}")
        logger.info(f"  已有效: {fix_stats['already_valid']}")
        logger.info(f"  失败: {fix_stats['failed']}")
        logger.info(f"统计已保存: {stats_file}")

        return fixed_relationships, fix_stats

    def _build_complete_id_mapping(self) -> Dict[str, str]:
        """构建完整的ID映射表"""
        id_map = {}

        # 1. document_id -> primary_id映射
        for entity in self.entities:
            props = entity.get('properties', {})
            doc_id = props.get('document_id', '')
            primary_id = props.get('primary_id', '')

            if doc_id and primary_id and doc_id != primary_id:
                id_map[doc_id] = primary_id

        # 2. 处理带换行符的ID
        for rel in self.relationships:
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')

            # 清理ID中的换行符
            if '\n' in from_id:
                clean_id = from_id.replace('\n', '_').replace('\r', '')
                if clean_id not in id_map:
                    id_map[from_id] = clean_id

            if '\n' in to_id:
                clean_id = to_id.replace('\n', '_').replace('\r', '')
                if clean_id not in id_map:
                    id_map[to_id] = clean_id

        return id_map

    def _find_entity_mapping(self, target_id: str) -> Optional[str]:
        """从实体中查找映射"""
        # 模糊匹配
        for entity in self.entities:
            props = entity.get('properties', {})
            primary_id = props.get('primary_id', '')
            text = props.get('text', '')

            # 检查是否包含目标ID的一部分
            if primary_id and target_id.replace('\n', '_') in primary_id:
                return primary_id

            # 检查text是否匹配
            if text and text.lower() in target_id.lower():
                return primary_id

        return None


def fix_and_save_relationships(
    entities_file: Path,
    relationships_file: Path,
    output_dir: Optional[Path] = None
) -> Tuple[Path, Path]:
    """
    修复并保存关系数据的便捷函数

    Args:
        entities_file: 实体JSON文件
        relationships_file: 关系JSON文件
        output_dir: 输出目录

    Returns:
        (修复后的实体文件路径, 修复后的关系文件路径)
    """
    output_dir = output_dir or Path('/root/autodl-tmp/pj-pharmaKG/data/processed/documents/regulatory')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载数据
    logger.info(f"加载实体数据: {entities_file}")
    with open(entities_file, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    logger.info(f"加载关系数据: {relationships_file}")
    with open(relationships_file, 'r', encoding='utf-8') as f:
        relationships = json.load(f)

    # 创建修复器
    fixer = IDMappingFixer(entities, relationships)

    # 分析
    analysis = fixer.analyze()

    # 修复
    fixed_relationships, stats = fixer.fix_relationships()

    # 保存修复后的数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    fixed_entities_file = output_dir / f'entities_fixed_{timestamp}.json'
    fixed_relationships_file = output_dir / f'relationships_fixed_{timestamp}.json'

    # 保存实体（也需要清理换行符等）
    cleaned_entities = []
    for entity in entities:
        props = entity.get('properties', {})
        primary_id = props.get('primary_id', '')

        # 清理primary_id中的换行符
        if primary_id and '\n' in primary_id:
            props['primary_id'] = primary_id.replace('\n', '_').replace('\r', '')
            entity['properties']['primary_id'] = props['primary_id']

        cleaned_entities.append(entity)

    with open(fixed_entities_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_entities, f, ensure_ascii=False, indent=2)

    with open(fixed_relationships_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_relationships, f, ensure_ascii=False, indent=2)

    logger.info(f"修复后的实体已保存: {fixed_entities_file}")
    logger.info(f"修复后的关系已保存: {fixed_relationships_file}")

    return fixed_entities_file, fixed_relationships_file


if __name__ == '__main__':
    import sys

    # 使用默认文件路径
    entities_file = Path('/root/autodl-tmp/pj-pharmaKG/data/processed/documents/regulatory/entities_20260208_001804.json')
    relationships_file = Path('/root/autodl-tmp/pj-pharmaKG/data/processed/documents/regulatory/relationships_20260208_001804.json')

    fixed_entities, fixed_rels = fix_and_save_relationships(entities_file, relationships_file)

    print(f"\n✅ 修复完成!")
    print(f"实体文件: {fixed_entities}")
    print(f"关系文件: {fixed_rels}")
