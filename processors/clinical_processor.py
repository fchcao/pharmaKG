#===========================================================
# PharmaKG 临床数据处理器
# Pharmaceutical Knowledge Graph - Clinical Data Processor
#===========================================================

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus
from extractors.base import EntityType
from extractors.named_entity import NamedEntityExtractor
from extractors.attribute import AttributeExtractor
from mappers.entity_mapper import EntityMapper

logger = logging.getLogger(__name__)


class ClinicalDataProcessor(BaseProcessor):
    """临床数据处理器"""

    PROCESSOR_NAME = "ClinicalDataProcessor"
    SUPPORTED_FORMATS = ['.json', '.csv', '.txt']
    OUTPUT_SUBDIR = "clinical"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.entity_extractor = NamedEntityExtractor(config)
        self.attribute_extractor = AttributeExtractor(config)
        self.entity_mapper = EntityMapper(config)

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """扫描源目录"""
        source_path = Path(source_path)
        files = []

        if source_path.is_file():
            return [source_path] if source_path.suffix in self.SUPPORTED_FORMATS else []

        for ext in self.SUPPORTED_FORMATS:
            files.extend(source_path.rglob(f"*{ext}"))

        return [f for f in files if not self.is_processed(f)]

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """从文件中提取数据"""
        suffix = file_path.suffix

        if suffix == '.json':
            return self._extract_json(file_path)
        elif suffix == '.csv':
            return self._extract_csv(file_path)
        else:
            return self._extract_text(file_path)

    def _extract_json(self, file_path: Path) -> Dict[str, Any]:
        """提取JSON数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 处理CRL数据
        if 'results' in data:
            return self._process_crl_data(data, file_path)

        return {'raw_data': data, 'file_path': str(file_path)}

    def _process_crl_data(self, data: Dict, file_path: Path) -> Dict[str, Any]:
        """处理CRL数据"""
        results = data.get('results', [])
        entities = []
        relationships = []

        for record in results:
            # 提取公司实体
            company = record.get('company_name', '')
            if company:
                entities.append({
                    'entity_type': EntityType.COMPANY,
                    'text': company,
                    'properties': {
                        'company_name': company,
                        'source': 'FDA_CRL',
                    }
                })

            # 提取监管行动实体
            app_number = record.get('application_number', [''])[0] if record.get('application_number') else ''
            if app_number:
                entities.append({
                    'entity_type': EntityType.REGULATORY_ACTION,
                    'text': f"Application {app_number}",
                    'properties': {
                        'application_number': app_number,
                        'letter_type': record.get('letter_type', ''),
                        'letter_date': record.get('letter_date', ''),
                        'approval_status': record.get('approval_status', ''),
                        'source': 'FDA_CRL',
                    }
                })

        return {
            'entities': entities,
            'relationships': relationships,
            'metadata': {'source_file': str(file_path)},
        }

    def _extract_csv(self, file_path: Path) -> Dict[str, Any]:
        """提取CSV数据"""
        import csv
        entities = []
        relationships = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 根据列名提取实体
                for key, value in row.items():
                    if value and self._is_entity_key(key):
                        entities.append({
                            'entity_type': self._infer_entity_type(key),
                            'text': value,
                            'properties': {key: value}
                        })

        return {'entities': entities, 'relationships': relationships}

    def _extract_text(self, file_path: Path) -> Dict[str, Any]:
        """提取文本数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取实体
        entities = self.entity_extractor.extract_entities(content)

        return {
            'entities': entities,
            'relationships': [],
            'content': content,
        }

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据"""
        if 'entities' in raw_data:
            # 已经是提取的实体
            mapped_entities = []
            for entity_data in raw_data['entities']:
                if isinstance(entity_data, dict):
                    if 'entity_type' in entity_data:
                        # 创建ExtractedEntity
                        from ..extractors.base import ExtractedEntity
                        entity = ExtractedEntity(
                            entity_type=entity_data['entity_type'],
                            text=entity_data.get('text', ''),
                            properties=entity_data.get('properties', {})
                        )
                        mapped = self.entity_mapper.map_entity(entity)
                        if mapped.success:
                            mapped_entities.append({
                                'label': mapped.ontology_class,
                                'properties': mapped.properties
                            })

            return {'entities': mapped_entities, 'relationships': []}

        return {}

    def validate(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        return bool(data.get('entities'))

    def _is_entity_key(self, key: str) -> bool:
        """判断是否为实体键"""
        entity_keywords = ['name', 'title', 'company', 'drug', 'disease', 'target']
        return any(kw in key.lower() for kw in entity_keywords)

    def _infer_entity_type(self, key: str) -> EntityType:
        """推断实体类型"""
        key_lower = key.lower()

        if 'company' in key_lower or 'manufacturer' in key_lower:
            return EntityType.COMPANY
        elif 'drug' in key_lower or 'compound' in key_lower:
            return EntityType.COMPOUND
        elif 'disease' in key_lower or 'condition' in key_lower:
            return EntityType.DISEASE
        elif 'target' in key_lower or 'protein' in key_lower:
            return EntityType.TARGET
        else:
            return EntityType.ORGANIZATION
