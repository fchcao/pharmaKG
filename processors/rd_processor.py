#===========================================================
# PharmaKG R&D数据处理器
# Pharmaceutical Knowledge Graph - R&D Data Processor
#===========================================================

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus
from extractors.base import EntityType
from mappers.entity_mapper import EntityMapper

logger = logging.getLogger(__name__)


class RDDataProcessor(BaseProcessor):
    """R&D数据处理器"""

    PROCESSOR_NAME = "RDDataProcessor"
    SUPPORTED_FORMATS = ['.db', '.sqlite', '.json', '.csv']
    OUTPUT_SUBDIR = "rd"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
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

        if suffix in ['.db', '.sqlite']:
            return self._extract_sqlite(file_path)
        else:
            return {'raw_data': f"Unsupported format: {suffix}"}

    def _extract_sqlite(self, file_path: Path) -> Dict[str, Any]:
        """提取SQLite数据库"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()

            # 检查是否是ChEMBL数据库
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            if any('molecule' in t or 'compound' in t or 'chembl' in t for t in tables):
                return self._extract_chembl(cursor, file_path)

            conn.close()
            return {'raw_data': 'Unknown database format'}

        except Exception as e:
            return {'error': str(e)}

    def _extract_chembl(self, cursor, file_path: Path) -> Dict[str, Any]:
        """提取ChEMBL数据"""
        entities = []

        # 提取化合物
        try:
            cursor.execute("""
                SELECT chembl_id, canonical_smiles, molecule_type
                FROM compound_structures
                JOIN molecule_dictionary USING (molregno)
                LIMIT 1000
            """)
            for row in cursor.fetchall():
                entities.append({
                    'entity_type': EntityType.COMPOUND,
                    'text': row[0] or f"Compound-{hash(row[1]) % 10000:04d}",
                    'properties': {
                        'primary_id': row[0] or f"CHEMBL-{hash(row[1]) % 10000:04d}",
                        'canonical_smiles': row[1] or '',
                        'molecule_type': row[2] or 'Small molecule',
                        'source': 'ChEMBL',
                    }
                })
        except Exception as e:
            logger.warning(f"提取ChEMBL化合物失败: {e}")

        # 提取靶点
        try:
            cursor.execute("""
                SELECT chembl_id, target_type, organism
                FROM target_dictionary
                LIMIT 500
            """)
            for row in cursor.fetchall():
                entities.append({
                    'entity_type': EntityType.TARGET,
                    'text': row[0] or f"Target-{hash(row[2]) % 10000:04d}",
                    'properties': {
                        'primary_id': row[0] or f"TARGET-{hash(row[2]) % 10000:04d}",
                        'target_type': row[1] or 'Unknown',
                        'organism': row[2] or 'Unknown',
                        'source': 'ChEMBL',
                    }
                })
        except Exception as e:
            logger.warning(f"提取ChEMBL靶点失败: {e}")

        return {'entities': entities, 'relationships': []}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据"""
        if 'entities' in raw_data:
            mapped_entities = []
            for entity_data in raw_data['entities']:
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
