#===========================================================
# PharmaKG ChEMBL SQLite 处理器
# Pharmaceutical Knowledge Graph - ChEMBL SQLite Processor
#===========================================================
# 版本: v1.0
# 描述: 从 ChEMBL SQLite 数据库提取化合物、靶点、生物活性数据
#===========================================================

import logging
import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Generator
from enum import Enum
import hashlib

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


class ExtractionType(str, Enum):
    """提取类型枚举"""
    COMPOUNDS = "compounds"
    TARGETS = "targets"
    ASSAYS = "assays"
    ACTIVITIES = "activities"
    PATHWAYS = "pathways"
    ALL = "all"


@dataclass
class ChEMBLExtractionConfig:
    """ChEMBL 提取配置"""
    batch_size: int = 10000
    limit_compounds: Optional[int] = None
    limit_targets: Optional[int] = None
    limit_assays: Optional[int] = None
    limit_activities: Optional[int] = None
    min_confidence_score: int = 8
    include_parent_only: bool = True
    include_molecular_properties: bool = True
    deduplicate_by_inchikey: bool = True
    deduplicate_by_uniprot: bool = True


@dataclass
class ExtractionStats:
    """提取统计信息"""
    compounds_extracted: int = 0
    targets_extracted: int = 0
    assays_extracted: int = 0
    activities_extracted: int = 0
    pathways_extracted: int = 0
    compounds_deduplicated: int = 0
    targets_deduplicated: int = 0
    relationships_created: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ChEMBLProcessor(BaseProcessor):
    """
    ChEMBL SQLite 数据库处理器

    提取内容：
    - 化合物（Compounds）- 从 molecule_dictionary 表
    - 靶点（Targets）- 从 target_dictionary 和 target_components 表
    - 分析（Assays）- 从 assays 表
    - 生物活性（Activities）- 从 activities 表
    - 通路（Pathways）- 从 GO/KEGG 映射

    关系类型：
    - INHIBITS, ACTIVATES, BINDS_TO - 化合物→靶点
    - TARGETS, PARTICIPATES_IN - 靶点→通路
    - TESTS_COMPOUND, TESTS_TARGET - 分析→化合物/靶点
    """

    PROCESSOR_NAME = "ChEMBLProcessor"
    SUPPORTED_FORMATS = ['.db', '.sqlite']
    OUTPUT_SUBDIR = "chembl"

    # ChEMBL 数据库表结构常量
    TABLE_COMPOUNDS = "molecule_dictionary"
    TABLE_COMPOUND_STRUCTURES = "compound_structures"
    TABLE_MOLECULE_HIERARCHY = "molecule_hierarchy"
    TABLE_TARGETS = "target_dictionary"
    TABLE_TARGET_COMPONENTS = "target_components"
    TABLE_COMPONENT_SEQUENCES = "component_sequences"
    TABLE_ASSAYS = "assays"
    TABLE_ACTIVITIES = "activities"
    TABLE_LIGAND_EFF = "ligand_eff"
    TABLE_TARGET_TYPE = "target_type"
    TABLE_GO_ANNOTATION = "component_go"  # GO 术语用于通路映射

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 ChEMBL 处理器

        Args:
            config: 处理器配置字典
        """
        super().__init__(config)

        # 初始化提取配置
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = ChEMBLExtractionConfig(**extraction_config)

        # 统计信息
        self.stats = ExtractionStats()

        # 去重集合
        self.seen_inchikeys: Set[str] = set()
        self.seen_uniprot_ids: Set[str] = set()

        # 输出文件路径
        self.output_compounds = self.entities_output_dir / "chembl_compounds.json"
        self.output_targets = self.entities_output_dir / "chembl_targets.json"
        self.output_assays = self.entities_output_dir / "chembl_assays.json"
        self.output_pathways = self.entities_output_dir / "chembl_pathways.json"
        self.output_bioactivities = self.relationships_output_dir / "chembl_bioactivities.json"
        self.output_assay_relationships = self.relationships_output_dir / "chembl_assay_relationships.json"

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录，查找 ChEMBL 数据库文件

        Args:
            source_path: 源目录路径

        Returns:
            找到的数据库文件列表
        """
        source_path = Path(source_path)
        files = []

        if source_path.is_file():
            if source_path.suffix in self.SUPPORTED_FORMATS:
                files.append(source_path)
        else:
            for ext in self.SUPPORTED_FORMATS:
                files.extend(source_path.rglob(f"*{ext}"))

            # 优先选择 chembl_34.db 或类似文件
            chembl_files = [f for f in files if 'chembl' in f.name.lower()]
            if chembl_files:
                files = chembl_files

        logger.info(f"Scanned {source_path}: found {len(files)} ChEMBL database files")
        return files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从 ChEMBL SQLite 数据库提取数据

        Args:
            file_path: 数据库文件路径

        Returns:
            提取的原始数据
        """
        logger.info(f"Extracting data from {file_path}")

        try:
            # 连接数据库
            conn = self._connect_database(file_path)
            cursor = conn.cursor()

            # 验证数据库结构
            if not self._validate_chembl_database(cursor):
                conn.close()
                return {'error': 'Not a valid ChEMBL database'}

            # 提取数据
            raw_data = {
                'compounds': list(self._extract_compounds(cursor)),
                'targets': list(self._extract_targets(cursor)),
                'assays': list(self._extract_assays(cursor)),
                'activities': list(self._extract_activities(cursor)),
                'pathways': list(self._extract_pathways(cursor)),
                'source_file': str(file_path),
                'extraction_timestamp': datetime.now().isoformat()
            }

            conn.close()

            logger.info(f"Extracted {len(raw_data['compounds'])} compounds, "
                       f"{len(raw_data['targets'])} targets, "
                       f"{len(raw_data['assays'])} assays, "
                       f"{len(raw_data['activities'])} activities")

            return raw_data

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            self.stats.errors.append(f"Extraction error: {str(e)}")
            return {'error': str(e)}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据为知识图谱格式

        Args:
            raw_data: 原始提取数据

        Returns:
            转换后的实体和关系数据
        """
        if 'error' in raw_data:
            return raw_data

        logger.info("Transforming extracted data")

        transformed = {
            'entities': {
                'rd:Compound': [],
                'rd:Target': [],
                'rd:Assay': [],
                'rd:Pathway': []
            },
            'relationships': []
        }

        # 转换化合物
        for compound_data in raw_data.get('compounds', []):
            entity = self._transform_compound(compound_data)
            if entity:
                transformed['entities']['rd:Compound'].append(entity)

        # 转换靶点
        for target_data in raw_data.get('targets', []):
            entity = self._transform_target(target_data)
            if entity:
                transformed['entities']['rd:Target'].append(entity)

        # 转换分析
        for assay_data in raw_data.get('assays', []):
            entity = self._transform_assay(assay_data)
            if entity:
                transformed['entities']['rd:Assay'].append(entity)

        # 转换通路
        for pathway_data in raw_data.get('pathways', []):
            entity = self._transform_pathway(pathway_data)
            if entity:
                transformed['entities']['rd:Pathway'].append(entity)

        # 创建关系
        transformed['relationships'] = self._create_relationships(raw_data)

        logger.info(f"Transformed {sum(len(v) for v in transformed['entities'].values())} entities "
                   f"and {len(transformed['relationships'])} relationships")

        return transformed

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证转换后的数据

        Args:
            data: 待验证数据

        Returns:
            是否验证通过
        """
        if 'error' in data:
            return False

        entities = data.get('entities', {})
        relationships = data.get('relationships', [])

        # 检查实体
        total_entities = sum(len(v) for v in entities.values())
        if total_entities == 0:
            self.stats.warnings.append("No entities extracted")
            return False

        # 检查关系
        if len(relationships) == 0:
            self.stats.warnings.append("No relationships created")

        # 验证必需字段
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if not self._validate_entity(entity):
                    self.stats.warnings.append(f"Invalid entity in {entity_type}")
                    return False

        logger.info(f"Validation passed: {total_entities} entities, {len(relationships)} relationships")
        return True

    def process(
        self,
        source_path,
        output_to: Optional[str] = None,
        save_intermediate: bool = True
    ) -> ProcessingResult:
        """
        处理 ChEMBL 数据库的主流程

        Args:
            source_path: 源数据路径
            output_to: 输出目录（可选）
            save_intermediate: 是否保存中间结果

        Returns:
            处理结果
        """
        start_time = datetime.now()
        source_path = Path(source_path)

        logger.info(f"[{self.PROCESSOR_NAME}] 开始处理: {source_path}")

        # 重置状态
        self._metrics = ProcessingMetrics()
        self.stats = ExtractionStats()
        self.seen_inchikeys.clear()
        self.seen_uniprot_ids.clear()

        try:
            # 1. 扫描文件
            files = self.scan(source_path)
            self._metrics.files_scanned = len(files)

            if not files:
                self._warnings.append(f"未找到 ChEMBL 数据库文件: {source_path}")
                return ProcessingResult(
                    status=ProcessingStatus.SKIPPED,
                    processor_name=self.PROCESSOR_NAME,
                    source_path=str(source_path),
                    metrics=self._metrics,
                    warnings=self._warnings
                )

            # 2. 处理每个文件
            all_entities = []
            all_relationships = []

            for file_path in files:
                try:
                    logger.info(f"Processing {file_path}")

                    # 提取
                    raw_data = self.extract(file_path)
                    if 'error' in raw_data:
                        self._warnings.append(f"提取失败: {file_path.name} - {raw_data['error']}")
                        self._metrics.files_failed += 1
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

                    # 收集实体和关系
                    entities_dict = transformed_data.get('entities', {})
                    relationships = transformed_data.get('relationships', [])

                    # 展平实体字典
                    for entity_type, entity_list in entities_dict.items():
                        for entity in entity_list:
                            all_entities.append({
                                **entity,
                                'entity_type': entity_type
                            })

                    all_relationships.extend(relationships)

                    self._metrics.files_processed += 1
                    self._metrics.entities_extracted += len(all_entities)
                    self._metrics.relationships_extracted += len(all_relationships)

                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}", exc_info=True)
                    self._errors.append(f"{file_path.name}: {str(e)}")
                    self._metrics.files_failed += 1

            # 3. 保存结果
            output_path = None
            if save_intermediate and (all_entities or all_relationships):
                output_path = self._save_chembl_results(
                    all_entities,
                    all_relationships,
                    transformed_data.get('entities', {}),
                    output_to
                )

            # 4. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            self._metrics.processing_time_seconds = processing_time
            self.stats.processing_time_seconds = processing_time

            # 5. 确定最终状态
            if self._metrics.files_failed > 0:
                status = ProcessingStatus.PARTIAL
            elif self._metrics.files_processed == 0:
                status = ProcessingStatus.SKIPPED
            else:
                status = ProcessingStatus.COMPLETED

            # 添加元数据
            metadata = {
                'processor': self.PROCESSOR_NAME,
                'source': 'ChEMBL SQLite Database',
                'extraction_config': {
                    'batch_size': self.extraction_config.batch_size,
                    'min_confidence': self.extraction_config.min_confidence_score,
                    'parent_only': self.extraction_config.include_parent_only
                },
                'stats': {
                    'compounds': len([e for e in all_entities if e.get('entity_type') == 'rd:Compound']),
                    'targets': len([e for e in all_entities if e.get('entity_type') == 'rd:Target']),
                    'assays': len([e for e in all_entities if e.get('entity_type') == 'rd:Assay']),
                    'pathways': len([e for e in all_entities if e.get('entity_type') == 'rd:Pathway']),
                    'bioactivities': len([r for r in all_relationships if r.get('relationship_type') in ['INHIBITS', 'ACTIVATES', 'BINDS_TO']]),
                    'dedup_compounds': self.stats.compounds_deduplicated,
                    'dedup_targets': self.stats.targets_deduplicated
                }
            }

            logger.info(f"[{self.PROCESSOR_NAME}] 处理完成: "
                       f"处理={self._metrics.files_processed}, "
                       f"失败={self._metrics.files_failed}, "
                       f"实体={len(all_entities)}, "
                       f"关系={len(all_relationships)}, "
                       f"耗时={processing_time:.2f}秒")

            return ProcessingResult(
                status=status,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_path),
                metrics=self._metrics,
                entities=all_entities,
                relationships=all_relationships,
                errors=self._errors,
                warnings=self._warnings,
                metadata=metadata,
                output_path=str(output_path) if output_path else None
            )

        except Exception as e:
            logger.error(f"[{self.PROCESSOR_NAME}] 处理失败: {e}", exc_info=True)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_path),
                metrics=self._metrics,
                errors=[str(e)]
            )

    #===========================================================
    # 数据库连接和验证
    #===========================================================

    def _connect_database(self, file_path: Path) -> sqlite3.Connection:
        """
        连接 ChEMBL 数据库

        Args:
            file_path: 数据库文件路径

        Returns:
            SQLite 连接对象
        """
        conn = sqlite3.connect(str(file_path))
        conn.row_factory = sqlite3.Row  # 返回字典样式的行
        return conn

    def _validate_chembl_database(self, cursor: sqlite3.Cursor) -> bool:
        """
        验证是否为有效的 ChEMBL 数据库

        Args:
            cursor: 数据库游标

        Returns:
            是否为有效的 ChEMBL 数据库
        """
        try:
            # 检查关键表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name IN ('molecule_dictionary', 'activities', 'assays', 'target_dictionary')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ['molecule_dictionary', 'activities', 'assays']
            has_required = all(table in tables for table in required_tables)

            if has_required:
                logger.info("Validated as ChEMBL database")
            else:
                logger.warning(f"Missing required tables. Found: {tables}")

            return has_required

        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False

    #===========================================================
    # 数据提取方法
    #===========================================================

    def _extract_compounds(self, cursor: sqlite3.Cursor) -> Generator[Dict, None, None]:
        """
        提取化合物数据

        Args:
            cursor: 数据库游标

        Yields:
            化合物数据字典
        """
        try:
            # 构建查询 - Updated for ChEMBL 36 schema
            query = f"""
                SELECT
                    md.molregno,
                    md.chembl_id,
                    md.pref_name,
                    md.molecule_type,
                    md.max_phase,
                    md.therapeutic_flag,
                    md.black_box_warning,
                    NULL as chebi_par_id,
                    md.inorganic_flag,
                    NULL as indication_class,
                    md.prodrug,
                    cs.canonical_smiles,
                    cs.standard_inchi,
                    cs.standard_inchi_key,
                    mh.parent_molregno,
                    cp.full_mwt as molecular_weight,
                    cp.num_ro5_violations,
                    cp.hbd,
                    cp.hba,
                    cp.alogp as logp,
                    cp.psa,
                    cp.full_mwt,
                    cp.aromatic_rings,
                    cp.heavy_atoms,
                    cp.qed_weighted,
                    NULL as cx_logp,
                    NULL as cx_logd,
                    NULL as num_alerts
                FROM {self.TABLE_COMPOUNDS} md
                LEFT JOIN {self.TABLE_COMPOUND_STRUCTURES} cs ON md.molregno = cs.molregno
                LEFT JOIN {self.TABLE_MOLECULE_HIERARCHY} mh ON md.molregno = mh.molregno
                LEFT JOIN compound_properties cp ON md.molregno = cp.molregno
            """

            # 添加父分子过滤
            if self.extraction_config.include_parent_only:
                query = f"""
                    {query}
                    WHERE mh.active_molregno = mh.molregno
                    OR mh.parent_molregno IS NULL
                """

            # Note: Don't add LIMIT to main query - we use OFFSET/LIMIT for batch processing
            overall_limit = self.extraction_config.limit_compounds
            logger.debug(f"Compounds query: {query}")

            # 执行查询（批量处理）
            offset = 0
            batch_size = self.extraction_config.batch_size

            while True:
                # Calculate actual limit for this batch
                if overall_limit:
                    remaining = overall_limit - offset
                    if remaining <= 0:
                        break
                    current_limit = min(batch_size, remaining)
                    batch_query = f"{query}\nLIMIT {current_limit} OFFSET {offset}"
                else:
                    batch_query = f"{query}\nLIMIT {batch_size} OFFSET {offset}"

                cursor.execute(batch_query)
                rows = cursor.fetchall()

                if not rows:
                    break

                for row in rows:
                    compound_data = dict(row)

                    # 去重
                    if self.extraction_config.deduplicate_by_inchikey:
                        inchikey = compound_data.get('standard_inchi_key')
                        if inchikey and inchikey in self.seen_inchikeys:
                            self.stats.compounds_deduplicated += 1
                            continue
                        if inchikey:
                            self.seen_inchikeys.add(inchikey)

                    self.stats.compounds_extracted += 1
                    yield compound_data

                offset += len(rows)

                # 检查限制
                if overall_limit and offset >= overall_limit:
                    break

        except Exception as e:
            logger.error(f"提取化合物失败: {e}", exc_info=True)
            self.stats.errors.append(f"Compounds extraction error: {str(e)}")

    def _extract_targets(self, cursor: sqlite3.Cursor) -> Generator[Dict, None, None]:
        """
        提取靶点数据

        Args:
            cursor: 数据库游标

        Yields:
            靶点数据字典
        """
        try:
            # 构建查询 - Updated for ChEMBL 36 schema
            query = f"""
                SELECT DISTINCT
                    td.tid,
                    td.chembl_id,
                    td.pref_name,
                    td.target_type,
                    td.organism,
                    td.chembl_id as target_chembl_id,
                    tc.component_id,
                    cs.accession,
                    cs.sequence,
                    cs.description,
                    NULL as protein_class
                FROM {self.TABLE_TARGETS} td
                LEFT JOIN {self.TABLE_TARGET_COMPONENTS} tc ON td.tid = tc.tid
                LEFT JOIN {self.TABLE_COMPONENT_SEQUENCES} cs ON tc.component_id = cs.component_id
            """

            # Note: Don't add LIMIT to main query - we use OFFSET/LIMIT for batch processing
            overall_limit = self.extraction_config.limit_targets
            logger.debug(f"Targets query: {query}")

            # 执行查询（批量处理）
            offset = 0
            batch_size = self.extraction_config.batch_size

            while True:
                # Calculate actual limit for this batch
                if overall_limit:
                    remaining = overall_limit - offset
                    if remaining <= 0:
                        break
                    current_limit = min(batch_size, remaining)
                    batch_query = f"{query}\nLIMIT {current_limit} OFFSET {offset}"
                else:
                    batch_query = f"{query}\nLIMIT {batch_size} OFFSET {offset}"

                cursor.execute(batch_query)
                rows = cursor.fetchall()

                if not rows:
                    break

                for row in rows:
                    target_data = dict(row)

                    # 去重
                    if self.extraction_config.deduplicate_by_uniprot:
                        uniprot_id = target_data.get('accession')
                        if uniprot_id and uniprot_id in self.seen_uniprot_ids:
                            self.stats.targets_deduplicated += 1
                            continue
                        if uniprot_id:
                            self.seen_uniprot_ids.add(uniprot_id)

                    self.stats.targets_extracted += 1
                    yield target_data

                offset += len(rows)

                # 检查限制
                if overall_limit and offset >= overall_limit:
                    break

        except Exception as e:
            logger.error(f"提取靶点失败: {e}", exc_info=True)
            self.stats.errors.append(f"Targets extraction error: {str(e)}")

    def _extract_assays(self, cursor: sqlite3.Cursor) -> Generator[Dict, None, None]:
        """
        提取分析数据

        Args:
            cursor: 数据库游标

        Yields:
            分析数据字典
        """
        try:
            # Updated for ChEMBL 36 schema
            query = f"""
                SELECT
                    assay_id,
                    chembl_id,
                    assay_type,
                    assay_category,
                    assay_organism,
                    description,
                    assay_test_type,
                    confidence_score,
                    relationship_type,
                    NULL as confidence_description
                FROM {self.TABLE_ASSAYS}
            """

            # Note: Don't add LIMIT to main query - we use OFFSET/LIMIT for batch processing
            overall_limit = self.extraction_config.limit_assays
            logger.debug(f"Assays query: {query}")

            # 执行查询（批量处理）
            offset = 0
            batch_size = self.extraction_config.batch_size

            while True:
                # Calculate actual limit for this batch
                if overall_limit:
                    remaining = overall_limit - offset
                    if remaining <= 0:
                        break
                    current_limit = min(batch_size, remaining)
                    batch_query = f"{query}\nLIMIT {current_limit} OFFSET {offset}"
                else:
                    batch_query = f"{query}\nLIMIT {batch_size} OFFSET {offset}"

                cursor.execute(batch_query)
                rows = cursor.fetchall()

                if not rows:
                    break

                for row in rows:
                    assay_data = dict(row)
                    self.stats.assays_extracted += 1
                    yield assay_data

                offset += batch_size

                # 检查限制
                if self.extraction_config.limit_assays and offset >= self.extraction_config.limit_assays:
                    break

        except Exception as e:
            logger.error(f"提取分析失败: {e}", exc_info=True)
            self.stats.errors.append(f"Assays extraction error: {str(e)}")

    def _extract_activities(self, cursor: sqlite3.Cursor) -> Generator[Dict, None, None]:
        """
        提取生物活性数据

        Args:
            cursor: 数据库游标

        Yields:
            活性数据字典
        """
        try:
            # Updated for ChEMBL 36 schema - target relationship is through assays table
            query = f"""
                SELECT
                    act.activity_id,
                    ass.chembl_id as assay_chembl_id,
                    md.chembl_id as molecule_chembl_id,
                    td.chembl_id as target_chembl_id,
                    ass.assay_type,
                    act.standard_type,
                    act.standard_relation,
                    act.standard_value,
                    act.standard_units,
                    act.standard_flag,
                    act.pchembl_value,
                    act.potential_duplicate,
                    act.activity_comment,
                    act.data_validity_comment,
                    ass.confidence_score
                FROM {self.TABLE_ACTIVITIES} act
                LEFT JOIN {self.TABLE_ASSAYS} ass ON act.assay_id = ass.assay_id
                LEFT JOIN {self.TABLE_COMPOUNDS} md ON act.molregno = md.molregno
                LEFT JOIN {self.TABLE_TARGETS} td ON ass.tid = td.tid
            """

            # 添加置信度过滤 - Updated for ChEMBL 36 schema
            if self.extraction_config.min_confidence_score:
                query += f"\nWHERE act.pchembl_value >= {self.extraction_config.min_confidence_score}"

            # Note: Don't add LIMIT to main query - we use OFFSET/LIMIT for batch processing
            overall_limit = self.extraction_config.limit_activities
            logger.debug(f"Activities query: {query}")

            # 执行查询（批量处理）
            offset = 0
            batch_size = self.extraction_config.batch_size

            while True:
                # Calculate actual limit for this batch
                if overall_limit:
                    remaining = overall_limit - offset
                    if remaining <= 0:
                        break
                    current_limit = min(batch_size, remaining)
                    batch_query = f"{query}\nLIMIT {current_limit} OFFSET {offset}"
                else:
                    batch_query = f"{query}\nLIMIT {batch_size} OFFSET {offset}"

                cursor.execute(batch_query)
                rows = cursor.fetchall()

                if not rows:
                    break

                for row in rows:
                    activity_data = dict(row)
                    self.stats.activities_extracted += 1
                    yield activity_data

                offset += len(rows)

                # 检查限制
                if overall_limit and offset >= overall_limit:
                    break

        except Exception as e:
            logger.error(f"提取活性数据失败: {e}", exc_info=True)
            self.stats.errors.append(f"Activities extraction error: {str(e)}")

    def _extract_pathways(self, cursor: sqlite3.Cursor) -> Generator[Dict, None, None]:
        """
        提取通路数据（从 GO 注释）

        Args:
            cursor: 数据库游标

        Yields:
            通路数据字典
        """
        try:
            # ChEMBL 36 schema: Use component_go + go_classification tables
            query = """
                SELECT
                    cg.component_id,
                    cg.go_id,
                    gc.pref_name as term,
                    gc.aspect,
                    'GO' as evidence_code
                FROM component_go cg
                LEFT JOIN go_classification gc ON cg.go_id = gc.go_id
                WHERE gc.aspect IN ('F', 'P', 'C')
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                pathway_data = dict(row)
                self.stats.pathways_extracted += 1
                yield pathway_data

        except Exception as e:
            logger.warning(f"提取通路数据失败（可能表不存在）: {e}")
            # 通路数据不是必需的，不记录为错误

    #===========================================================
    # 数据转换方法
    #===========================================================

    def _transform_compound(self, compound_data: Dict) -> Optional[Dict]:
        """
        转换化合物数据为知识图谱实体格式

        Args:
            compound_data: 原始化合物数据

        Returns:
            转换后的实体数据
        """
        try:
            # 生成主标识符
            primary_id = compound_data.get('chembl_id') or f"MOLEREGNO-{compound_data.get('molregno')}"

            # 构建标识符字典
            identifiers = {
                'ChEMBL': compound_data.get('chembl_id'),
                'InChIKey': compound_data.get('standard_inchi_key'),
                'molregno': str(compound_data.get('molregno', '')),
                'ChEBI': compound_data.get('chebi_par_id')
            }

            # 构建属性字典
            properties = {
                'name': compound_data.get('pref_name') or compound_data.get('chembl_id'),
                'molecule_type': compound_data.get('molecule_type'),
                'max_phase': compound_data.get('max_phase'),
                'therapeutic_flag': bool(compound_data.get('therapeutic_flag')),
                'canonical_smiles': compound_data.get('canonical_smiles'),
                'standard_inchi': compound_data.get('standard_inchi'),
                'standard_inchi_key': compound_data.get('standard_inchi_key'),
                'molecular_properties': {
                    'molecular_weight': compound_data.get('molecular_weight') or compound_data.get('full_mwt'),
                    'num_ro5_violations': compound_data.get('num_ro5_violations'),
                    'hbd': compound_data.get('hbd'),
                    'hba': compound_data.get('hba'),
                    'logp': compound_data.get('logp') or compound_data.get('cx_logp'),
                    'psa': compound_data.get('psa'),
                    'aromatic_rings': compound_data.get('aromatic_rings'),
                    'heavy_atoms': compound_data.get('heavy_atoms'),
                    'qed_weighted': compound_data.get('qed_weighted')
                },
                'flags': {
                    'black_box_warning': bool(compound_data.get('black_box_warning')),
                    'inorganic': bool(compound_data.get('inorganic_flag')),
                    'prodrug': bool(compound_data.get('prodrug'))
                },
                'classification': {
                    'indication_class': compound_data.get('indication_class')
                },
                'parent_molregno': compound_data.get('parent_molregno'),
                'source': 'ChEMBL',
                'version': '34'
            }

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Compound'
            }

        except Exception as e:
            logger.warning(f"转换化合物失败: {e}")
            return None

    def _transform_target(self, target_data: Dict) -> Optional[Dict]:
        """
        转换靶点数据为知识图谱实体格式

        Args:
            target_data: 原始靶点数据

        Returns:
            转换后的实体数据
        """
        try:
            # 生成主标识符
            primary_id = target_data.get('chembl_id') or f"TARGET-{target_data.get('tid')}"

            # 构建标识符字典
            identifiers = {
                'ChEMBL': target_data.get('chembl_id'),
                'UniProt': target_data.get('accession'),
                'tid': str(target_data.get('tid', ''))
            }

            # 解析蛋白质分类
            protein_class = target_data.get('protein_class')
            if isinstance(protein_class, str):
                try:
                    protein_class = json.loads(protein_class)
                except:
                    protein_class = [{'label': protein_class}]
            elif not isinstance(protein_class, list):
                protein_class = []

            # 构建属性字典
            properties = {
                'name': target_data.get('pref_name') or target_data.get('chembl_id'),
                'target_type': target_data.get('target_type'),
                'organism': target_data.get('organism'),
                'sequence': target_data.get('sequence'),
                'component_description': target_data.get('description'),
                'protein_class': protein_class,
                'classification': {
                    'l1': protein_class[0].get('label') if protein_class else None,
                    'l2': protein_class[1].get('label') if len(protein_class) > 1 else None,
                    'l3': protein_class[2].get('label') if len(protein_class) > 2 else None
                },
                'source': 'ChEMBL',
                'version': '34'
            }

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Target'
            }

        except Exception as e:
            logger.warning(f"转换靶点失败: {e}")
            return None

    def _transform_assay(self, assay_data: Dict) -> Optional[Dict]:
        """
        转换分析数据为知识图谱实体格式

        Args:
            assay_data: 原始分析数据

        Returns:
            转换后的实体数据
        """
        try:
            # 生成主标识符
            primary_id = assay_data.get('chembl_id') or f"ASSAY-{assay_data.get('assay_id')}"

            # 构建标识符字典
            identifiers = {
                'ChEMBL': assay_data.get('chembl_id'),
                'assay_id': str(assay_data.get('assay_id', ''))
            }

            # 构建属性字典
            properties = {
                'name': assay_data.get('description') or assay_data.get('chembl_id'),
                'assay_type': assay_data.get('assay_type'),
                'assay_category': assay_data.get('assay_category'),
                'organism': assay_data.get('assay_organism'),
                'test_type': assay_data.get('assay_test_type'),
                'confidence': {
                    'score': assay_data.get('confidence_score'),
                    'description': assay_data.get('confidence_description')
                },
                'relationship_type': assay_data.get('relationship_type'),
                'description': assay_data.get('description'),
                'source': 'ChEMBL',
                'version': '34'
            }

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Assay'
            }

        except Exception as e:
            logger.warning(f"转换分析失败: {e}")
            return None

    def _transform_pathway(self, pathway_data: Dict) -> Optional[Dict]:
        """
        转换通路数据为知识图谱实体格式

        Args:
            pathway_data: 原始通路数据

        Returns:
            转换后的实体数据
        """
        try:
            # GO ID 作为主标识符
            go_id = pathway_data.get('go_id', '')
            primary_id = f"GO:{go_id}" if not go_id.startswith('GO:') else go_id

            # 构建标识符字典
            identifiers = {
                'GO': primary_id,
                'component_id': str(pathway_data.get('component_id', ''))
            }

            # 构建属性字典
            properties = {
                'name': pathway_data.get('term'),
                'aspect': pathway_data.get('aspect'),
                'evidence_code': pathway_data.get('evidence_code'),
                'pathway_type': self._map_go_aspect_to_pathway_type(pathway_data.get('aspect')),
                'source': 'ChEMBL-GO',
                'version': '34'
            }

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Pathway'
            }

        except Exception as e:
            logger.warning(f"转换通路失败: {e}")
            return None

    def _map_go_aspect_to_pathway_type(self, aspect: Optional[str]) -> str:
        """
        映射 GO 方面到通路类型

        Args:
            aspect: GO 方面（biological_process, cellular_component, molecular_function）

        Returns:
            通路类型字符串
        """
        mapping = {
            'biological_process': 'biological_pathway',
            'cellular_component': 'cellular_component',
            'molecular_function': 'molecular_function'
        }
        return mapping.get(aspect, 'unknown')

    #===========================================================
    # 关系创建方法
    #===========================================================

    def _create_relationships(self, raw_data: Dict) -> List[Dict]:
        """
        从原始数据创建关系

        Args:
            raw_data: 原始提取数据

        Returns:
            关系列表
        """
        relationships = []

        # 从活性数据创建化合物-靶点关系
        activities = raw_data.get('activities', [])
        for activity in activities:
            rel = self._create_compound_target_relationship(activity)
            if rel:
                relationships.append(rel)

        # 从活性数据创建分析-化合物/靶点关系
        for activity in activities:
            assay_compound_rel = self._create_assay_compound_relationship(activity)
            if assay_compound_rel:
                relationships.append(assay_compound_rel)

            assay_target_rel = self._create_assay_target_relationship(activity)
            if assay_target_rel:
                relationships.append(assay_target_rel)

        # 从通路数据创建靶点-通路关系
        pathways = raw_data.get('pathways', [])
        for pathway in pathways:
            target_pathway_rel = self._create_target_pathway_relationship(pathway)
            if target_pathway_rel:
                relationships.append(target_pathway_rel)

        self.stats.relationships_created = len(relationships)
        return relationships

    def _create_compound_target_relationship(self, activity: Dict) -> Optional[Dict]:
        """
        创建化合物-靶点关系

        Args:
            activity: 活性数据

        Returns:
            关系字典
        """
        try:
            compound_id = activity.get('molecule_chembl_id')
            target_id = activity.get('target_chembl_id')

            if not compound_id or not target_id:
                return None

            # 根据活性类型确定关系类型
            activity_type = activity.get('standard_type', '').lower()
            if 'inhibit' in activity_type or 'ic50' in activity_type or 'ki' in activity_type:
                rel_type = 'INHIBITS'
            elif 'activate' in activity_type or 'ec50' in activity_type:
                rel_type = 'ACTIVATES'
            else:
                rel_type = 'BINDS_TO'

            return {
                'relationship_type': rel_type,
                'source_entity_id': f"Compound-{compound_id}",
                'target_entity_id': f"Target-{target_id}",
                'properties': {
                    'activity_type': activity.get('standard_type'),
                    'activity_value': activity.get('standard_value'),
                    'activity_units': activity.get('standard_units'),
                    'pchembl_value': activity.get('pchembl_value'),
                    'confidence_score': activity.get('confidence_score'),
                    'assay_chembl_id': activity.get('assay_chembl_id'),
                    'standard_relation': activity.get('standard_relation')
                },
                'source': 'ChEMBL-activities'
            }

        except Exception as e:
            logger.warning(f"创建化合物-靶点关系失败: {e}")
            return None

    def _create_assay_compound_relationship(self, activity: Dict) -> Optional[Dict]:
        """
        创建分析-化合物关系

        Args:
            activity: 活性数据

        Returns:
            关系字典
        """
        try:
            assay_id = activity.get('assay_chembl_id')
            compound_id = activity.get('molecule_chembl_id')

            if not assay_id or not compound_id:
                return None

            return {
                'relationship_type': 'TESTS_COMPOUND',
                'source_entity_id': f"Assay-{assay_id}",
                'target_entity_id': f"Compound-{compound_id}",
                'properties': {
                    'assay_type': activity.get('assay_type'),
                    'activity_id': activity.get('activity_id')
                },
                'source': 'ChEMBL-activities'
            }

        except Exception as e:
            logger.warning(f"创建分析-化合物关系失败: {e}")
            return None

    def _create_assay_target_relationship(self, activity: Dict) -> Optional[Dict]:
        """
        创建分析-靶点关系

        Args:
            activity: 活性数据

        Returns:
            关系字典
        """
        try:
            assay_id = activity.get('assay_chembl_id')
            target_id = activity.get('target_chembl_id')

            if not assay_id or not target_id:
                return None

            return {
                'relationship_type': 'TESTS_TARGET',
                'source_entity_id': f"Assay-{assay_id}",
                'target_entity_id': f"Target-{target_id}",
                'properties': {
                    'assay_type': activity.get('assay_type'),
                    'activity_id': activity.get('activity_id')
                },
                'source': 'ChEMBL-activities'
            }

        except Exception as e:
            logger.warning(f"创建分析-靶点关系失败: {e}")
            return None

    def _create_target_pathway_relationship(self, pathway: Dict) -> Optional[Dict]:
        """
        创建靶点-通路关系

        Args:
            pathway: 通路数据

        Returns:
            关系字典
        """
        try:
            component_id = pathway.get('component_id')
            go_id = pathway.get('go_id')

            if not component_id or not go_id:
                return None

            # 根据方面确定关系类型
            aspect = pathway.get('aspect')
            if aspect == 'biological_process':
                rel_type = 'PARTICIPATES_IN'
            else:
                rel_type = 'TARGETS'

            return {
                'relationship_type': rel_type,
                'source_entity_id': f"Target-component-{component_id}",
                'target_entity_id': f"Pathway-GO:{go_id}",
                'properties': {
                    'evidence_code': pathway.get('evidence_code'),
                    'aspect': aspect
                },
                'source': 'ChEMBL-GO'
            }

        except Exception as e:
            logger.warning(f"创建靶点-通路关系失败: {e}")
            return None

    #===========================================================
    # 数据验证方法
    #===========================================================

    def _validate_entity(self, entity: Dict) -> bool:
        """
        验证实体数据

        Args:
            entity: 实体数据

        Returns:
            是否有效
        """
        # 检查必需字段
        if 'primary_id' not in entity:
            return False

        if 'properties' not in entity:
            return False

        # 检查实体类型
        entity_type = entity.get('entity_type')
        if entity_type not in ['rd:Compound', 'rd:Target', 'rd:Assay', 'rd:Pathway']:
            return False

        return True

    #===========================================================
    # 结果保存方法
    #===========================================================

    def _save_chembl_results(
        self,
        all_entities: List[Dict],
        all_relationships: List[Dict],
        entities_by_type: Dict[str, List[Dict]],
        output_to: Optional[str] = None
    ) -> Path:
        """
        保存 ChEMBL 处理结果

        Args:
            all_entities: 所有实体列表
            all_relationships: 所有关系列表
            entities_by_type: 按类型分组的实体
            output_to: 自定义输出目录

        Returns:
            输出文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定输出目录
        if output_to:
            output_dir = Path(output_to)
        else:
            output_dir = self.documents_output_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # 按类型保存实体
        for entity_type, entities in entities_by_type.items():
            if not entities:
                continue

            type_name = entity_type.replace('rd:', '').lower()
            entities_file = output_dir / f"chembl_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 {len(entities)} 个 {entity_type} 到: {entities_file}")

        # 保存关系
        if all_relationships:
            relationships_file = output_dir / f"chembl_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(all_relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 {len(all_relationships)} 个关系到: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "ChEMBL SQLite Database v34",
            "timestamp": timestamp,
            "extraction_config": {
                'batch_size': self.extraction_config.batch_size,
                'min_confidence': self.extraction_config.min_confidence_score,
                'parent_only': self.extraction_config.include_parent_only
            },
            "statistics": {
                "compounds_extracted": self.stats.compounds_extracted,
                "targets_extracted": self.stats.targets_extracted,
                "assays_extracted": self.stats.assays_extracted,
                "activities_extracted": self.stats.activities_extracted,
                "pathways_extracted": self.stats.pathways_extracted,
                "compounds_deduplicated": self.stats.compounds_deduplicated,
                "targets_deduplicated": self.stats.targets_deduplicated,
                "relationships_created": self.stats.relationships_created,
                "processing_time_seconds": self.stats.processing_time_seconds
            },
            "entities_by_type": {
                entity_type: len(entities)
                for entity_type, entities in entities_by_type.items()
            },
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "errors": self.stats.errors,
            "warnings": self.stats.warnings
        }

        summary_file = output_dir / f"chembl_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"保存处理摘要到: {summary_file}")

        return summary_file


#===========================================================
# 命令行接口
#===========================================================

def main():
    """
    命令行主函数
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='ChEMBL SQLite 数据库处理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 处理整个数据库
  python -m processors.chembl_processor /path/to/chembl_34.db

  # 限制提取数量
  python -m processors.chembl_processor /path/to/chembl_34.db --limit-compounds 1000 --limit-activities 5000

  # 自定义输出目录
  python -m processors.chembl_processor /path/to/chembl_34.db --output /custom/output/path

  # 只提取特定类型
  python -m processors.chembl_processor /path/to/chembl_34.db --extract-type compounds
        """
    )

    parser.add_argument(
        'source_path',
        help='ChEMBL 数据库文件路径或目录'
    )

    parser.add_argument(
        '--output',
        help='输出目录（默认为 data/processed/documents/chembl/）'
    )

    parser.add_argument(
        '--extract-type',
        choices=['compounds', 'targets', 'assays', 'activities', 'pathways', 'all'],
        default='all',
        help='提取类型（默认: all）'
    )

    parser.add_argument(
        '--limit-compounds',
        type=int,
        help='化合物数量限制'
    )

    parser.add_argument(
        '--limit-targets',
        type=int,
        help='靶点数量限制'
    )

    parser.add_argument(
        '--limit-assays',
        type=int,
        help='分析数量限制'
    )

    parser.add_argument(
        '--limit-activities',
        type=int,
        help='活性数据数量限制'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='批处理大小（默认: 10000）'
    )

    parser.add_argument(
        '--min-confidence',
        type=int,
        default=8,
        help='最小置信度评分（默认: 8）'
    )

    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='禁用去重'
    )

    parser.add_argument(
        '--include-children',
        action='store_true',
        help='包含子分子（默认只提取父分子）'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 构建配置
    config = {
        'extraction': {
            'batch_size': args.batch_size,
            'limit_compounds': args.limit_compounds,
            'limit_targets': args.limit_targets,
            'limit_assays': args.limit_assays,
            'limit_activities': args.limit_activities,
            'min_confidence_score': args.min_confidence,
            'include_parent_only': not args.include_children,
            'deduplicate_by_inchikey': not args.no_dedup,
            'deduplicate_by_uniprot': not args.no_dedup
        }
    }

    # 创建处理器
    processor = ChEMBLProcessor(config)

    # 处理数据
    result = processor.process(
        source_path=args.source_path,
        output_to=args.output,
        save_intermediate=True
    )

    # 输出结果
    print(f"\n{'='*60}")
    print(f"处理状态: {result.status.value}")
    print(f"{'='*60}")
    print(f"处理的文件: {result.metrics.files_processed}")
    print(f"失败的文件: {result.metrics.files_failed}")
    print(f"跳过的文件: {result.metrics.files_skipped}")
    print(f"提取的实体: {result.metrics.entities_extracted}")
    print(f"提取的关系: {result.metrics.relationships_extracted}")
    print(f"处理时间: {result.metrics.processing_time_seconds:.2f} 秒")

    if result.metadata:
        stats = result.metadata.get('stats', {})
        print(f"\n详细统计:")
        print(f"  化合物: {stats.get('compounds', 0)}")
        print(f"  靶点: {stats.get('targets', 0)}")
        print(f"  分析: {stats.get('assays', 0)}")
        print(f"  生物活性: {stats.get('bioactivities', 0)}")
        print(f"  去重化合物: {stats.get('dedup_compounds', 0)}")
        print(f"  去重靶点: {stats.get('dedup_targets', 0)}")

    if result.errors:
        print(f"\n错误 ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"  - {error}")
        if len(result.errors) > 5:
            print(f"  ... 还有 {len(result.errors) - 5} 个错误")

    if result.warnings:
        print(f"\n警告 ({len(result.warnings)}):")
        for warning in result.warnings[:5]:
            print(f"  - {warning}")
        if len(result.warnings) > 5:
            print(f"  ... 还有 {len(result.warnings) - 5} 个警告")

    if result.output_path:
        print(f"\n输出文件: {result.output_path}")

    # 返回状态码
    return 0 if result.status == ProcessingStatus.COMPLETED else 1


if __name__ == '__main__':
    exit(main())
