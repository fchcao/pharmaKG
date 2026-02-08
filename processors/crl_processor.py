#===========================================================
# PharmaKG 临床CRL数据处理器
# Pharmaceutical Knowledge Graph - Clinical CRL Processor
#===========================================================
# 版本: v1.0
# 描述: 处理FDA CRL JSON数据，提取实体和关系
#===========================================================

import json
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from collections import defaultdict

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics
from extractors.named_entity import NamedEntityExtractor
from extractors.relationship import RelationshipExtractor
from extractors.attribute import AttributeExtractor
from extractors.base import EntityType, ExtractedEntity, ExtractedRelationship, RelationshipType
from mappers.entity_mapper import EntityMapper
from extractors import entity_enhancer

logger = logging.getLogger(__name__)


class CRLProcessor(BaseProcessor):
    """
    CRL数据处理器

    处理FDA Complete Response Letter JSON数据
    """

    PROCESSOR_NAME = "CRLProcessor"
    SUPPORTED_FORMATS = ['.json']
    OUTPUT_SUBDIR = "clinical_crl"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        super().__init__(config)

        # 初始化提取器
        self.entity_extractor = NamedEntityExtractor(config)
        self.relationship_extractor = RelationshipExtractor(config)
        self.attribute_extractor = AttributeExtractor(config)
        self.entity_mapper = EntityMapper(config)

        # CRL特有配置
        self.extract_drug_names = config.get('extract_drug_names', True)
        self.extract_companies = config.get('extract_companies', True)
        self.extract_applications = config.get('extract_applications', True)

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """扫描源目录"""
        source_path = Path(source_path)

        if source_path.is_file():
            return [source_path] if source_path.suffix in self.SUPPORTED_FORMATS else []

        files = []
        for ext in self.SUPPORTED_FORMATS:
            files.extend(source_path.rglob(f"*{ext}"))

        # 排除已处理的文件
        unprocessed_files = [f for f in files if not self.is_processed(f)]

        return unprocessed_files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """从CRL JSON文件中提取数据"""
        self.logger.debug(f"提取文件: {file_path}")

        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取元数据
        metadata = self._extract_metadata(file_path, data)

        # 提取CRL记录
        results = data.get('results', [])
        if not results:
            return {}

        # 处理每条CRL记录
        all_entities = []
        all_relationships = []

        for idx, record in enumerate(results):
            entities, relationships = self._process_crl_record(record, idx)
            all_entities.extend(entities)
            all_relationships.extend(relationships)

        return {
            'file_path': str(file_path),
            'metadata': metadata,
            'records_count': len(results),
            'entities': all_entities,
            'relationships': all_relationships,
        }

    def _process_crl_record(
        self,
        record: Dict[str, Any],
        idx: int
    ) -> tuple[List[ExtractedEntity], List[ExtractedRelationship]]:
        """处理单条CRL记录"""
        entities = []
        relationships = []

        # 1. 提取公司实体
        company_name = record.get('company_name', '') or ''
        company_name = company_name.strip()
        if company_name:
            company_entity = ExtractedEntity(
                entity_type=EntityType.COMPANY,
                text=company_name,
                confidence=1.0,
                properties={
                    'company_name': company_name,
                    'address': record.get('company_address', '') or '',
                    'representative': record.get('company_rep', '') or '',
                    'data_source': 'FDA_CRL'
                },
                source='crl_json'
            )
            entities.append(company_entity)

        # 2. 提取药物/化合物实体
        text = record.get('text', '')
        drug_names = self._extract_drug_names(text)
        for drug_name in drug_names:
            drug_entity = ExtractedEntity(
                entity_type=EntityType.COMPOUND,
                text=drug_name,
                confidence=0.9,
                properties={
                    'name': drug_name,
                    'data_source': 'FDA_CRL',
                    'extracted_from': 'letter_text'
                },
                source='crl_text_extraction'
            )
            entities.append(drug_entity)

        # 3. 提取申请号实体
        application_numbers = record.get('application_number', [])
        for app_num in application_numbers:
            if app_num:
                # 标准化申请号格式
                app_num_clean = app_num.strip().replace(' ', '')
                app_entity = ExtractedEntity(
                    entity_type=EntityType.REGULATORY_SUBMISSION,
                    text=app_num_clean,
                    confidence=1.0,
                    properties={
                        'submission_number': app_num_clean,
                        'submission_type': app_num_clean.split()[0] if ' ' in app_num_clean else 'NDA',
                        'data_source': 'FDA_CRL'
                    },
                    identifiers={'submission_number': app_num_clean},
                    source='crl_json'
                )
                entities.append(app_entity)

        # 4. 提取监管机构实体
        approver_centers = record.get('approver_center', [])
        for center in approver_centers:
            if center:
                agency_entity = ExtractedEntity(
                    entity_type=EntityType.REGULATORY_AGENCY,
                    text=center,
                    confidence=0.95,
                    properties={
                        'name': center,
                        'data_source': 'FDA_CRL',
                        'agency_type': 'FDA_Center'
                    },
                    source='crl_json'
                )
                entities.append(agency_entity)

        # 添加FDA作为顶级机构
        fda_entity = ExtractedEntity(
            entity_type=EntityType.REGULATORY_AGENCY,
            text='FDA',
            confidence=1.0,
            properties={
                'name': 'Food and Drug Administration',
                'abbreviation': 'FDA',
                'data_source': 'FDA_CRL'
            },
            source='crl_json'
        )
        entities.append(fda_entity)

        # 5. 提取人员实体
        approver_name = record.get('approver_name') or ''
        approver_name = approver_name.strip()
        if approver_name and len(approver_name) > 3:
            person_entity = ExtractedEntity(
                entity_type=EntityType.PERSON,
                text=approver_name,
                confidence=0.9,
                properties={
                    'name': approver_name,
                    'title': record.get('approver_title') or '',
                    'data_source': 'FDA_CRL'
                },
                source='crl_json'
            )
            entities.append(person_entity)

        # 6. 创建关系
        # CRL文档与公司之间的关系
        letter_id = self._generate_letter_id(record, idx)
        letter_entity = ExtractedEntity(
            entity_type=EntityType.DOCUMENT,
            text=f"CRL_{record.get('application_number', ['UNKNOWN'])[0]}_{record.get('letter_date', '')}",
            confidence=1.0,
            properties={
                'letter_type': record.get('letter_type', ''),
                'letter_date': record.get('letter_date', ''),
                'approval_status': record.get('approval_status', ''),
                'file_name': record.get('file_name', ''),
                'data_source': 'FDA_CRL'
            },
            identifiers={'letter_id': letter_id},
            source='crl_json'
        )
        entities.insert(0, letter_entity)  # 文档实体放在第一个

        # 创建关系
        if company_name:
            relationships.append(ExtractedRelationship(
                source_entity=letter_entity,
                target_entity=company_entity,
                relationship_type=RelationshipType.ISSUED_TO,
                confidence=1.0,
                source='crl_structure'
            ))

        for app_num in application_numbers:
            if app_num:
                # 找到对应的申请实体
                for entity in entities:
                    if entity.entity_type == EntityType.REGULATORY_SUBMISSION and entity.text == app_num.strip():
                        relationships.append(ExtractedRelationship(
                            source_entity=letter_entity,
                            target_entity=entity,
                            relationship_type=RelationshipType.ABOUT,
                            confidence=1.0,
                            source='crl_structure'
                        ))
                        break

        if approver_name:
            # 找到审批人实体
            for entity in entities:
                if entity.entity_type == EntityType.PERSON and entity.text == approver_name:
                    relationships.append(ExtractedRelationship(
                        source_entity=entity,
                        target_entity=letter_entity,
                        relationship_type=RelationshipType.APPROVED,
                        confidence=0.9,
                        source='crl_structure'
                    ))
                    break

        return entities, relationships

    def _extract_drug_names(self, text: str) -> List[str]:
        """从文本中提取药物名称"""
        import re

        drug_names = []

        # 模式1: "for [DrugName]" 或 "for [DrugName] (generic)"
        pattern1 = r'\bfor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:\(|\.|,|for)'
        matches = re.findall(pattern1, text)
        drug_names.extend(matches)

        # 模式2: 括号中的化学名 "(acyclovir ophthalmic ointment)"
        pattern2 = r'\(([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:ointment|injection|tablets?|capsules?|solution)\)'
        matches = re.findall(pattern2, text)
        drug_names.extend(matches)

        # 模式3: 专有名称标记 "proprietary name"
        pattern3 = r'proprietary name.*?:\s*([A-Z][a-z]+)'
        matches = re.findall(pattern3, text, re.IGNORECASE)
        drug_names.extend(matches)

        # 去重并返回
        seen = set()
        unique_names = []
        for name in drug_names:
            name_clean = name.strip()
            if len(name_clean) > 2 and len(name_clean) < 100 and name_clean not in seen:
                seen.add(name_clean)
                unique_names.append(name_clean)

        return unique_names[:5]  # 限制返回数量

    def _generate_letter_id(self, record: Dict[str, Any], idx: int) -> str:
        """生成CRL信函ID"""
        app_num = record.get('application_number', ['UNKNOWN'])[0]
        letter_date = record.get('letter_date', '').replace('/', '')
        file_name = record.get('file_name', '')

        id_string = f"{app_num}_{letter_date}_{idx}"
        hash_value = hashlib.md5(id_string.encode()).hexdigest()[:8]
        return f"CRL-{hash_value}"

    def _extract_metadata(
        self,
        file_path: Path,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取元数据"""
        meta = data.get('meta', {})

        return {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'last_updated': meta.get('last_updated', ''),
            'total_results': meta.get('results', {}).get('total', 0),
            'data_source': 'FDA_openFDA'
        }

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换提取的数据"""
        if not raw_data:
            return {}

        # 映射实体到本体
        mapped_entities = self.entity_mapper.map_entities(raw_data.get('entities', []))

        # 映射关系到本体
        mapped_relationships = self._map_relationships(
            raw_data.get('relationships', []),
            raw_data.get('entities', [])
        )

        return {
            'entities': mapped_entities,
            'relationships': mapped_relationships,
            'metadata': raw_data.get('metadata', {}),
        }

    def _map_relationships(
        self,
        relationships: List[ExtractedRelationship],
        entities: List[ExtractedEntity]
    ) -> List[Dict[str, Any]]:
        """映射关系到本体"""
        mapped = []

        for rel in relationships:
            from_id = rel.source_entity.get_primary_id()
            to_id = rel.target_entity.get_primary_id()

            if not from_id or not to_id:
                continue

            mapped.append({
                'from': from_id,
                'to': to_id,
                'relationship_type': rel.relationship_type.value,
                'properties': {
                    'confidence': rel.confidence,
                    'source': rel.source,
                }
            })

        return mapped

    def validate(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        # 检查是否有实体
        if not data.get('entities'):
            return False

        # 检查是否有主标识符
        for entity in data['entities']:
            if 'properties' in entity and 'primary_id' in entity['properties']:
                return True

        return False

    def process_batch(
        self,
        source_dir: Union[str, Path],
        batch_size: int = 50
    ) -> ProcessingResult:
        """批量处理CRL文件"""
        source_dir = Path(source_dir)

        self.logger.info(f"开始处理CRL数据: {source_dir}")

        # 扫描文件
        files = self.scan(source_dir)
        total_files = len(files)

        if total_files == 0:
            return ProcessingResult(
                status=ProcessingStatus.SKIPPED,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_dir),
                metrics=ProcessingMetrics(),
            )

        self.logger.info(f"找到 {total_files} 个文件待处理")

        # 处理文件
        all_entities = []
        all_relationships = []

        for i, file_path in enumerate(files):
            self.logger.info(f"处理文件 {i+1}/{total_files}: {file_path.name}")

            try:
                # 提取
                raw_data = self.extract(file_path)
                if not raw_data:
                    self._metrics.files_skipped += 1
                    continue

                # 转换
                transformed_data = self.transform(raw_data)
                if not transformed_data:
                    self._metrics.files_skipped += 1
                    continue

                # 验证
                if not self.validate(transformed_data):
                    self._warnings.append(f"数据验证失败: {file_path.name}")
                    self._metrics.files_skipped += 1
                    continue

                # 收集
                all_entities.extend(transformed_data.get('entities', []))
                all_relationships.extend(transformed_data.get('relationships', []))

                self._metrics.files_processed += 1
                self._metrics.entities_extracted += len(transformed_data.get('entities', []))
                self._metrics.relationships_extracted += len(transformed_data.get('relationships', []))

                # 标记为已处理
                self.mark_as_processed(file_path)

            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                self._errors.append(f"{file_path.name}: {str(e)}")
                self._metrics.files_failed += 1

        # 增强实体和关系
        self.logger.info("增强实体和关系...")
        all_entities, all_relationships = entity_enhancer.enhance_entities(
            all_entities,
            all_relationships
        )

        # 保存结果
        output_path = None
        if all_entities or all_relationships:
            output_path = self._save_results(all_entities, all_relationships)

        # 更新指标
        self._metrics.files_scanned = total_files
        self._metrics.entities_mapped = len(all_entities)
        self._metrics.relationships_mapped = len(all_relationships)

        # 确定状态
        if self._metrics.files_failed > 0:
            status = ProcessingStatus.PARTIAL
        elif self._metrics.files_processed == 0:
            status = ProcessingStatus.SKIPPED
        else:
            status = ProcessingStatus.COMPLETED

        return ProcessingResult(
            status=status,
            processor_name=self.PROCESSOR_NAME,
            source_path=str(source_dir),
            metrics=self._metrics,
            entities=all_entities,
            relationships=all_relationships,
            errors=self._errors,
            warnings=self._warnings,
            output_path=str(output_path) if output_path else None,
        )


# 便捷函数
def process_crl_data(
    source_dir: Union[str, Path],
    config: Optional[Dict[str, Any]] = None
) -> ProcessingResult:
    """
    处理CRL数据的便捷函数

    Args:
        source_dir: 源目录
        config: 配置

    Returns:
        处理结果
    """
    processor = CRLProcessor(config)
    return processor.process_batch(source_dir)
