#===========================================================
# PharmaKG KEGG Pathway API 处理器
# Pharmaceutical Knowledge Graph - KEGG Pathway API Processor
#===========================================================
# 版本: v1.0
# 描述: 从 KEGG REST API 提取通路数据和蛋白质关联
#===========================================================

import logging
import json
import time
import sqlite3
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import hashlib
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


class OrganismCode(str, Enum):
    """KEGG 生物体代码枚举"""
    HUMAN = "hsa"
    MOUSE = "mmu"
    RAT = "rno"

    @property
    def scientific_name(self) -> str:
        """获取学名"""
        mapping = {
            self.HUMAN: "Homo sapiens",
            self.MOUSE: "Mus musculus",
            self.RAT: "Rattus norvegicus"
        }
        return mapping[self]

    @property
    def taxonomy_id(self) -> str:
        """获取分类学 ID"""
        mapping = {
            self.HUMAN: "9606",
            self.MOUSE: "10090",
            self.RAT: "10116"
        }
        return mapping[self]


class PathwayCategory(str, Enum):
    """KEGG 通路分类枚举"""
    METABOLISM = "Metabolism"
    GENETIC_INFO = "Genetic Information Processing"
    ENVIRONMENTAL = "Environmental Information Processing"
    CELLULAR = "Cellular Processes"
    ORGANISMAL = "Organismal Systems"
    DISEASES = "Human Diseases"
    DRUG_DEVELOPMENT = "Drug Development"


@dataclass
class KEGGExtractionConfig:
    """KEGG 提取配置"""
    batch_size: int = 50
    rate_limit: float = 10.0  # 请求每秒
    max_retries: int = 3
    retry_backoff: float = 1.0
    timeout: int = 30
    cache_enabled: bool = True
    cache_file: str = "kegg_cache.db"
    include_genes: bool = True
    include_proteins: bool = True
    include_compounds: bool = True
    map_kegg_to_uniprot: bool = True
    use_kgml: bool = False  # 使用 KGML (XML) 格式


@dataclass
class ExtractionStats:
    """提取统计信息"""
    pathways_processed: int = 0
    pathways_extracted: int = 0
    genes_extracted: int = 0
    proteins_extracted: int = 0
    compounds_extracted: int = 0
    relationships_created: int = 0
    api_requests_made: int = 0
    cache_hits: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class KEGGProcessor(BaseProcessor):
    """
    KEGG REST API 处理器

    提取内容：
    - 通路（Pathways）- 从 KEGG PATHWAY 数据库
    - 基因（Genes）- 通路相关基因
    - 蛋白质（Proteins）- 基因编码的蛋白质
    - 化合物（Compounds）- 通路中的小分子化合物

    关系类型：
    - PARTICIPATES_IN - 蛋白质→通路
    - REGULATES_PATHWAY - 蛋白质→通路（酶、调节因子）
    - PATHWAY_HAS_COMPOUND - 通路→化合物
    """

    PROCESSOR_NAME = "KEGGProcessor"
    SUPPORTED_FORMATS = ['.txt', '.csv', '.json']
    OUTPUT_SUBDIR = "kegg"

    # KEGG REST API 端点
    API_BASE = "http://rest.kegg.jp"
    LIST_PATHWAY_ENDPOINT = f"{API_BASE}/list/pathway"
    GET_PATHWAY_ENDPOINT = f"{API_BASE}/get/{{pathway_id}}"
    CONV_GENES_UNIPROT = f"{API_BASE}/conv/genes/uniprot"
    LINK_PATHWAY_GENES = f"{API_BASE}/link/pathway/{{organism}}"
    LINK_GENES_PATHWAY = f"{API_BASE}/link/genes/{{pathway_id}}"
    GET_KGML = f"{API_BASE}/get/{{pathway_id}}/kgml"

    # 通路分类映射
    PATHWAY_CATEGORIES = {
        "Metabolism": {
            "prefix": "map",
            "subcategories": ["Carbohydrate", "Lipid", "Amino acid", "Nucleotide", "Energy", "Vitamin"]
        },
        "Genetic Information Processing": {
            "prefix": "map",
            "subcategories": ["Transcription", "Translation", "Replication", "Repair"]
        },
        "Environmental Information Processing": {
            "prefix": "map",
            "subcategories": ["Signal transduction", "Signaling molecules"]
        },
        "Cellular Processes": {
            "prefix": "map",
            "subcategories": ["Cell growth", "Cell death", "Cell motility"]
        },
        "Organismal Systems": {
            "prefix": "map",
            "subcategories": ["Immune", "Nervous", "Endocrine", "Circulatory", "Digestive"]
        },
        "Human Diseases": {
            "prefix": "hsa",
            "subcategories": ["Cancers", "Immune", "Neurodegenerative", "Metabolic"]
        },
        "Drug Development": {
            "prefix": "hsa",
            "subcategories": ["Drug resistance", "Drug metabolism"]
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 KEGG 处理器

        Args:
            config: 处理器配置字典
        """
        super().__init__(config)

        # 初始化提取配置
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = KEGGExtractionConfig(**extraction_config)

        # 统计信息
        self.stats = ExtractionStats()

        # 去重集合
        self.seen_pathway_ids: Set[str] = set()
        self.seen_gene_ids: Set[str] = set()

        # 输出文件路径
        self.output_pathways = self.entities_output_dir / "kegg_pathways.json"
        self.output_relationships = self.relationships_output_dir / "kegg_pathway_relationships.json"

        # 初始化 HTTP 会话
        self.session = self._create_session()

        # 初始化缓存
        self.cache_conn = None
        if self.extraction_config.cache_enabled:
            self._init_cache()

        # 速率限制控制
        self.last_request_time = 0
        self.min_request_interval = 1.0 / self.extraction_config.rate_limit

        # 基因到 UniProt 映射缓存
        self.gene_to_uniprot_cache: Dict[str, str] = {}

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录，查找 KEGG 配置文件或 ID 文件

        Args:
            source_path: 源目录路径

        Returns:
            找到的文件列表
        """
        source_path = Path(source_path)
        files = []

        # 如果源路径是文件
        if source_path.is_file():
            if source_path.suffix in self.SUPPORTED_FORMATS:
                files.append(source_path)
        # 如果是目录
        else:
            # 查找所有支持的文件格式
            for ext in self.SUPPORTED_FORMATS:
                files.extend(source_path.rglob(f"*{ext}"))

            # 优先选择包含 kegg 或 pathway 的文件
            kegg_files = [f for f in files if any(kw in f.name.lower() for kw in ['kegg', 'pathway'])]
            if kegg_files:
                files = kegg_files

        logger.info(f"Scanned {source_path}: found {len(files)} potential KEGG files")
        return files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从文件中提取 KEGG 通路 ID 并获取数据

        Args:
            file_path: 文件路径

        Returns:
            提取的原始数据
        """
        logger.info(f"Extracting KEGG data from {file_path}")

        try:
            # 读取 KEGG 通路 ID
            pathway_ids = self._read_pathway_ids(file_path)

            if not pathway_ids:
                logger.warning(f"No KEGG pathway IDs found in {file_path}")
                return {'error': 'No KEGG pathway IDs found'}

            logger.info(f"Found {len(pathway_ids)} KEGG pathway IDs to process")

            # 获取通路数据
            raw_data = {
                'pathways': [],
                'genes': [],
                'proteins': [],
                'compounds': [],
                'source_file': str(file_path),
                'extraction_timestamp': datetime.now().isoformat(),
                'pathway_ids': pathway_ids
            }

            # 批量获取通路数据
            for i in range(0, len(pathway_ids), self.extraction_config.batch_size):
                batch_ids = pathway_ids[i:i + self.extraction_config.batch_size]
                batch_data = self._fetch_batch_pathway_data(batch_ids)

                if batch_data:
                    for pathway_data in batch_data:
                        raw_data['pathways'].append(pathway_data)
                        self.stats.pathways_processed += 1

                        # 提取基因/蛋白质
                        if self.extraction_config.include_genes:
                            genes = self._extract_pathway_genes(pathway_data)
                            raw_data['genes'].extend(genes)

                        # 提取化合物
                        if self.extraction_config.include_compounds:
                            compounds = self._extract_pathway_compounds(pathway_data)
                            raw_data['compounds'].extend(compounds)

            logger.info(f"Extracted {len(raw_data['pathways'])} pathways from KEGG")

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

        logger.info("Transforming extracted KEGG data")

        transformed = {
            'entities': {
                'rd:Pathway': [],
                'rd:Target': [],
                'rd:Gene': [],
                'rd:Compound': []
            },
            'relationships': []
        }

        # 去重集合
        targets_set = {}
        genes_set = {}
        compounds_set = {}

        # 转换通路
        for pathway_data in raw_data.get('pathways', []):
            pathway_entity = self._transform_pathway(pathway_data)
            if pathway_entity:
                transformed['entities']['rd:Pathway'].append(pathway_entity)
                self.stats.pathways_extracted += 1

                # 提取通路参与关系
                rels = self._create_pathway_relationships(pathway_data, pathway_entity)
                for rel in rels:
                    transformed['relationships'].append(rel)

                    # 收集靶点/基因实体
                    if rel['relationship_type'] in ['PARTICIPATES_IN', 'REGULATES_PATHWAY']:
                        target_data = rel.get('target_entity_data')
                        if target_data:
                            target_entity = self._transform_target_from_gene(target_data)
                            if target_entity:
                                target_id = target_entity['primary_id']
                                if target_id not in targets_set:
                                    targets_set[target_id] = target_entity

                    # 收集化合物实体
                    elif rel['relationship_type'] == 'PATHWAY_HAS_COMPOUND':
                        compound_data = rel.get('target_entity_data')
                        if compound_data:
                            compound_entity = self._transform_compound(compound_data)
                            if compound_entity:
                                compound_id = compound_entity['primary_id']
                                if compound_id not in compounds_set:
                                    compounds_set[compound_id] = compound_entity

        # 添加实体
        transformed['entities']['rd:Target'] = list(targets_set.values())
        transformed['entities']['rd:Compound'] = list(compounds_set.values())

        self.stats.proteins_extracted = len(targets_set)
        self.stats.compounds_extracted = len(compounds_set)
        self.stats.relationships_created = len(transformed['relationships'])

        logger.info(f"Transformed {len(transformed['entities']['rd:Pathway'])} pathways, "
                   f"{len(transformed['entities']['rd:Target'])} targets, "
                   f"{len(transformed['entities']['rd:Compound'])} compounds, "
                   f"{len(transformed['relationships'])} relationships")

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
        处理 KEGG 数据的主流程

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
        self.seen_pathway_ids.clear()
        self.seen_gene_ids.clear()
        self.gene_to_uniprot_cache.clear()

        try:
            # 1. 扫描文件
            files = self.scan(source_path)
            self._metrics.files_scanned = len(files)

            if not files:
                self._warnings.append(f"未找到 KEGG 文件: {source_path}")
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
                output_path = self._save_kegg_results(
                    all_entities,
                    all_relationships,
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
                'source': 'KEGG REST API',
                'extraction_config': {
                    'batch_size': self.extraction_config.batch_size,
                    'rate_limit': self.extraction_config.rate_limit,
                    'cache_enabled': self.extraction_config.cache_enabled,
                    'include_genes': self.extraction_config.include_genes,
                    'include_proteins': self.extraction_config.include_proteins,
                    'map_kegg_to_uniprot': self.extraction_config.map_kegg_to_uniprot
                },
                'stats': {
                    'pathways_processed': self.stats.pathways_processed,
                    'pathways_extracted': self.stats.pathways_extracted,
                    'genes_extracted': self.stats.genes_extracted,
                    'proteins_extracted': self.stats.proteins_extracted,
                    'compounds_extracted': self.stats.compounds_extracted,
                    'relationships_created': self.stats.relationships_created,
                    'api_requests_made': self.stats.api_requests_made,
                    'cache_hits': self.stats.cache_hits
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

        finally:
            # 关闭缓存连接
            if self.cache_conn:
                self.cache_conn.close()

    #===========================================================
    # HTTP 会话和缓存管理
    #===========================================================

    def _create_session(self) -> requests.Session:
        """
        创建带重试机制的 HTTP 会话

        Returns:
            配置好的 requests.Session 对象
        """
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.extraction_config.max_retries,
            backoff_factor=self.extraction_config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _init_cache(self):
        """初始化 SQLite 缓存数据库"""
        cache_path = self.data_root / "cache" / self.extraction_config.cache_file
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        self.cache_conn = sqlite3.connect(str(cache_path))
        self.cache_conn.execute("""
            CREATE TABLE IF NOT EXISTS kegg_cache (
                pathway_id TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _get_cached_data(self, pathway_id: str) -> Optional[Dict]:
        """
        从缓存获取数据

        Args:
            pathway_id: KEGG 通路 ID

        Returns:
            缓存的数据或 None
        """
        if not self.cache_conn:
            return None

        cursor = self.cache_conn.cursor()
        cursor.execute("SELECT data FROM kegg_cache WHERE pathway_id = ?", (pathway_id,))
        row = cursor.fetchone()

        if row:
            self.stats.cache_hits += 1
            return json.loads(row[0])

        return None

    def _set_cached_data(self, pathway_id: str, data: Dict):
        """
        将数据存入缓存

        Args:
            pathway_id: KEGG 通路 ID
            data: 要缓存的数据
        """
        if not self.cache_conn:
            return

        cursor = self.cache_conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO kegg_cache (pathway_id, data, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (pathway_id, json.dumps(data))
        )
        self.cache_conn.commit()

    #===========================================================
    # 速率限制和 API 请求
    #===========================================================

    def _respect_rate_limit(self):
        """遵守速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_api_request(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """
        发起 API 请求

        Args:
            url: 请求 URL
            params: 查询参数

        Returns:
            响应文本或 None
        """
        self._respect_rate_limit()

        try:
            self.stats.api_requests_made += 1

            response = self.session.get(
                url,
                params=params,
                timeout=self.extraction_config.timeout
            )

            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            self.stats.errors.append(f"API request error: {str(e)}")
            return None

    #===========================================================
    # KEGG 数据获取
    #===========================================================

    def _read_pathway_ids(self, file_path: Path) -> List[str]:
        """
        从文件读取 KEGG 通路 ID

        Args:
            file_path: 文件路径

        Returns:
            KEGG 通路 ID 列表
        """
        pathway_ids = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 提取通路 ID（处理可能的额外列）
                        pathway_id = line.split('\t')[0].split(',')[0].strip()
                        if pathway_id:
                            # 确保以 pathway: 开头（如果不是则添加）
                            if not pathway_id.startswith('path:'):
                                pathway_id = f"path:{pathway_id}"
                            pathway_ids.append(pathway_id)

            logger.info(f"Read {len(pathway_ids)} KEGG pathway IDs from {file_path}")

        except Exception as e:
            logger.error(f"Failed to read KEGG pathway IDs from {file_path}: {e}")

        return pathway_ids

    def list_pathways(
        self,
        organism: OrganismCode = OrganismCode.HUMAN
    ) -> List[str]:
        """
        列出指定生物体的所有通路

        Args:
            organism: 生物体代码

        Returns:
            通路 ID 列表
        """
        logger.info(f"Listing pathways for organism: {organism.value}")

        url = f"{self.LIST_PATHWAY_ENDPOINT}/{organism.value}"
        response_text = self._make_api_request(url)

        if not response_text:
            return []

        pathway_ids = []
        for line in response_text.strip().split('\n'):
            if line:
                # 格式: path:hsa04110\tCell Cycle - Homo sapiens (human)
                parts = line.split('\t')
                if parts:
                    pathway_id = parts[0].strip()
                    pathway_ids.append(pathway_id)

        logger.info(f"Found {len(pathway_ids)} pathways for {organism.value}")
        return pathway_ids

    def _fetch_batch_pathway_data(self, pathway_ids: List[str]) -> List[Dict]:
        """
        批量获取通路数据

        Args:
            pathway_ids: KEGG 通路 ID 列表

        Returns:
            通路数据列表
        """
        logger.debug(f"Fetching batch of {len(pathway_ids)} KEGG pathways")

        results = []

        for pathway_id in pathway_ids:
            # 检查缓存
            cached_data = self._get_cached_data(pathway_id)
            if cached_data:
                results.append(cached_data)
                continue

            # 从 API 获取
            pathway_data = self._fetch_single_pathway(pathway_id)
            if pathway_data:
                results.append(pathway_data)
                # 缓存数据
                self._set_cached_data(pathway_id, pathway_data)

        return results

    def _fetch_single_pathway(self, pathway_id: str) -> Optional[Dict]:
        """
        获取单个通路数据

        Args:
            pathway_id: KEGG 通路 ID（例如: path:hsa04110）

        Returns:
            通路数据字典或 None
        """
        # 移除 path: 前缀（如果有）
        clean_id = pathway_id.replace('path:', '')

        # 决定使用哪种格式
        if self.extraction_config.use_kgml:
            return self._fetch_pathway_kgml(clean_id)
        else:
            return self._fetch_pathway_text(clean_id)

    def _fetch_pathway_text(self, pathway_id: str) -> Optional[Dict]:
        """
        以文本格式获取通路数据

        Args:
            pathway_id: KEGG 通路 ID（例如: hsa04110）

        Returns:
            通路数据字典或 None
        """
        url = f"{self.GET_PATHWAY_ENDPOINT.format(pathway_id=pathway_id)}"
        response_text = self._make_api_request(url)

        if not response_text:
            return None

        # 解析文本格式
        pathway_data = self._parse_pathway_text(response_text, pathway_id)
        return pathway_data

    def _fetch_pathway_kgml(self, pathway_id: str) -> Optional[Dict]:
        """
        以 KGML (XML) 格式获取通路数据

        Args:
            pathway_id: KEGG 通路 ID（例如: hsa04110）

        Returns:
            通路数据字典或 None
        """
        url = f"{self.GET_KGML.format(pathway_id=pathway_id)}"
        response_text = self._make_api_request(url)

        if not response_text:
            return None

        # 解析 KGML
        pathway_data = self._parse_pathway_kgml(response_text, pathway_id)
        return pathway_data

    def _parse_pathway_text(self, text: str, pathway_id: str) -> Optional[Dict]:
        """
        解析 KEGG 通路文本格式

        Args:
            text: KEGG 响应文本
            pathway_id: 通路 ID

        Returns:
            解析后的通路数据
        """
        pathway_data = {
            'pathway_id': pathway_id,
            'name': '',
            'description': '',
            'organism': '',
            'category': '',
            'genes': [],
            'compounds': [],
            'modules': [],
            'diseases': [],
            'references': []
        }

        current_section = None
        gene_entry = None

        for line in text.split('\n'):
            line = line.strip()

            # 检测节
            if line.startswith('ENTRY'):
                current_section = 'ENTRY'
            elif line.startswith('NAME'):
                current_section = 'NAME'
            elif line.startswith('DESCRIPTION'):
                current_section = 'DESCRIPTION'
            elif line.startswith('ORGANISM'):
                current_section = 'ORGANISM'
            elif line.startswith('CLASS'):
                current_section = 'CLASS'
            elif line.startswith('DISEASE'):
                current_section = 'DISEASE'
            elif line.startswith('DBLINKS'):
                current_section = 'DBLINKS'
            elif line.startswith('RELATIVE'):
                current_section = 'RELATIVE'
            elif line.startswith('MODULE'):
                current_section = 'MODULE'
            elif line.startswith('///'):
                current_section = None
                gene_entry = None

            # 解析内容
            if current_section == 'ENTRY':
                if 'EC' in line:
                    pathway_data['ec_number'] = line.split('EC')[1].strip()
            elif current_section == 'NAME':
                pathway_data['name'] = line
            elif current_section == 'DESCRIPTION':
                pathway_data['description'] = line
            elif current_section == 'ORGANISM':
                if not line.startswith('ORGANISM'):
                    pathway_data['organism'] = line
            elif current_section == 'CLASS':
                if not line.startswith('CLASS'):
                    # 提取分类
                    category = self._extract_pathway_category(line)
                    if category:
                        pathway_data['category'] = category
            elif current_section == 'MODULE':
                if not line.startswith('MODULE'):
                    pathway_data['modules'].append(line.strip())
            elif current_section == 'DISEASE':
                if line and not line.startswith('DISEASE'):
                    pathway_data['diseases'].append(line.strip())

            # 解析基因条目（简化版）
            if line.startswith('GENE'):
                gene_match = re.match(r'GENE\s+(\S+):\s+(.+)', line)
                if gene_match:
                    gene_id = gene_match.group(1)
                    gene_name = gene_match.group(2)
                    pathway_data['genes'].append({
                        'gene_id': gene_id,
                        'gene_symbol': gene_name.split()[0] if gene_name else gene_id,
                        'description': gene_name
                    })

            # 解析化合物
            if line.startswith('COMPOUND'):
                compound_match = re.match(r'COMPOUND\s+(\S+):\s+(.+)', line)
                if compound_match:
                    compound_id = compound_match.group(1)
                    compound_name = compound_match.group(2)
                    pathway_data['compounds'].append({
                        'compound_id': compound_id,
                        'name': compound_name
                    })

        return pathway_data

    def _parse_pathway_kgml(self, text: str, pathway_id: str) -> Optional[Dict]:
        """
        解析 KEGG 通路 KGML (XML) 格式

        Args:
            text: KGML XML 文本
            pathway_id: 通路 ID

        Returns:
            解析后的通路数据
        """
        try:
            root = ET.fromstring(text)

            pathway_data = {
                'pathway_id': pathway_id,
                'name': root.get('name', ''),
                'org': root.get('org', ''),
                'number': root.get('number', ''),
                'title': root.get('title', ''),
                'image': root.get('image', ''),
                'link': root.get('link', ''),
                'genes': [],
                'compounds': [],
                'reactions': [],
                'relations': []
            }

            # 解析条目
            for entry in root.findall('entry'):
                entry_id = entry.get('id')
                entry_name = entry.get('name')
                entry_type = entry.get('type')

                if entry_type == 'gene':
                    # 基因/蛋白质
                    for gene_id in entry_name.split():
                        pathway_data['genes'].append({
                            'gene_id': gene_id,
                            'entry_id': entry_id
                        })
                elif entry_type == 'compound':
                    # 化合物
                    pathway_data['compounds'].append({
                        'compound_id': entry_name,
                        'entry_id': entry_id
                    })

            # 解析反应
            for reaction in root.findall('reaction'):
                reaction_data = {
                    'id': reaction.get('id', ''),
                    'name': reaction.get('name', ''),
                    'type': reaction.get('type', ''),
                    'substrates': [],
                    'products': []
                }

                for substrate in reaction.findall('substrate'):
                    reaction_data['substrates'].append(substrate.get('name', ''))

                for product in reaction.findall('product'):
                    reaction_data['products'].append(product.get('name', ''))

                pathway_data['reactions'].append(reaction_data)

            # 解析关系
            for relation in root.findall('relation'):
                relation_data = {
                    'entry1': relation.get('entry1', ''),
                    'entry2': relation.get('entry2', ''),
                    'type': relation.get('type', ''),
                    'subtypes': []
                }

                for subtype in relation.findall('subtype'):
                    relation_data['subtypes'].append({
                        'name': subtype.get('name', ''),
                        'value': subtype.get('value', '')
                    })

                pathway_data['relations'].append(relation_data)

            return pathway_data

        except ET.ParseError as e:
            logger.error(f"Failed to parse KGML: {e}")
            return None

    def _extract_pathway_category(self, class_line: str) -> str:
        """
        从 CLASS 行提取通路分类

        Args:
            class_line: CLASS 行内容

        Returns:
            通路分类
        """
        # KEGG 分类模式
        categories = [
            "Metabolism",
            "Genetic Information Processing",
            "Environmental Information Processing",
            "Cellular Processes",
            "Organismal Systems",
            "Human Diseases"
        ]

        for category in categories:
            if category.lower() in class_line.lower():
                return category

        # 默认分类
        return "Other"

    def _extract_pathway_genes(self, pathway_data: Dict) -> List[Dict]:
        """
        从通路数据提取基因

        Args:
            pathway_data: 通路数据

        Returns:
            基因列表
        """
        genes = []

        for gene_data in pathway_data.get('genes', []):
            gene_id = gene_data.get('gene_id', '')
            if gene_id and gene_id not in self.seen_gene_ids:
                genes.append(gene_data)
                self.seen_gene_ids.add(gene_id)
                self.stats.genes_extracted += 1

        return genes

    def _extract_pathway_compounds(self, pathway_data: Dict) -> List[Dict]:
        """
        从通路数据提取化合物

        Args:
            pathway_data: 通路数据

        Returns:
            化合物列表
        """
        return pathway_data.get('compounds', [])

    def _map_kegg_gene_to_uniprot(self, gene_id: str, organism: OrganismCode) -> Optional[str]:
        """
        映射 KEGG 基因 ID 到 UniProt 登录号

        Args:
            gene_id: KEGG 基因 ID
            organism: 生物体代码

        Returns:
            UniProt 登录号或 None
        """
        # 检查缓存
        if gene_id in self.gene_to_uniprot_cache:
            return self.gene_to_uniprot_cache[gene_id]

        # 构建转换查询
        kegg_gene_id = f"{organism.value}:{gene_id}"
        url = f"{self.CONV_GENES_UNIPROT}/{kegg_gene_id}"
        response_text = self._make_api_request(url)

        if not response_text:
            return None

        # 解析响应（格式: hsa:10458\tup:Q9Y258）
        for line in response_text.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    uniprot_id = parts[1].replace('up:', '')
                    self.gene_to_uniprot_cache[gene_id] = uniprot_id
                    return uniprot_id

        return None

    #===========================================================
    # 数据转换方法
    #===========================================================

    def _transform_pathway(self, pathway_data: Dict) -> Optional[Dict]:
        """
        转换通路数据为知识图谱实体格式

        Args:
            pathway_data: 原始 KEGG 通路数据

        Returns:
            转换后的实体数据
        """
        try:
            pathway_id = pathway_data.get('pathway_id', '')

            if not pathway_id:
                return None

            # 提取生物体
            organism = pathway_data.get('org') or pathway_data.get('organism', '')
            if not organism:
                # 从 pathway_id 提取
                if pathway_id.startswith('hsa'):
                    organism = 'Homo sapiens'
                elif pathway_id.startswith('mmu'):
                    organism = 'Mus musculus'
                elif pathway_id.startswith('rno'):
                    organism = 'Rattus norvegicus'

            # 提取名称
            name = pathway_data.get('title') or pathway_data.get('name', '')
            description = pathway_data.get('description', '')

            # 提取分类
            category = pathway_data.get('category')
            if not category:
                # 从描述或名称推断
                category = self._infer_pathway_category(name, description)

            # 构建标识符字典
            identifiers = {
                'KEGG': pathway_id,
                'KEGG_ID': pathway_id.replace('path:', ''),
                'PathwayNumber': pathway_data.get('number', '')
            }

            # 提取外部链接
            for db_link in pathway_data.get('dblinks', []):
                if 'Reactome' in str(db_link):
                    identifiers['Reactome'] = db_link.split(':')[1] if ':' in str(db_link) else db_link
                elif 'BioCarta' in str(db_link):
                    identifiers['BioCarta'] = db_link.split(':')[1] if ':' in str(db_link) else db_link

            # 构建属性字典
            properties = {
                'name': name,
                'description': description,
                'organism': organism,
                'pathway_type': self._map_pathway_type(category),
                'pathway_category': category,
                'associated_genes': [
                    gene.get('gene_id') for gene in pathway_data.get('genes', [])
                ],
                'associated_gene_symbols': [
                    gene.get('gene_symbol', gene.get('gene_id', ''))
                    for gene in pathway_data.get('genes', [])
                ],
                'associated_proteins': [],  # 稍后填充
                'modules': pathway_data.get('modules', []),
                'diseases': pathway_data.get('diseases', []),
                'reference_links': pathway_data.get('link', ''),
                'source': 'KEGG',
                'version': '2024.1'
            }

            # 如果启用 UniProt 映射
            if self.extraction_config.map_kegg_to_uniprot:
                uniprot_ids = []
                for gene in pathway_data.get('genes', []):
                    gene_id = gene.get('gene_id', '')
                    if gene_id:
                        # 确定生物体代码
                        if pathway_id.startswith('hsa'):
                            organism_code = OrganismCode.HUMAN
                        elif pathway_id.startswith('mmu'):
                            organism_code = OrganismCode.MOUSE
                        elif pathway_id.startswith('rno'):
                            organism_code = OrganismCode.RAT
                        else:
                            organism_code = OrganismCode.HUMAN  # 默认

                        uniprot_id = self._map_kegg_gene_to_uniprot(gene_id, organism_code)
                        if uniprot_id:
                            uniprot_ids.append(uniprot_id)

                properties['associated_proteins'] = uniprot_ids

            return {
                'primary_id': pathway_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Pathway'
            }

        except Exception as e:
            logger.warning(f"转换通路失败 {pathway_data.get('pathway_id', 'unknown')}: {e}")
            return None

    def _infer_pathway_category(self, name: str, description: str) -> str:
        """
        从名称和描述推断通路分类

        Args:
            name: 通路名称
            description: 通路描述

        Returns:
            通路分类
        """
        text = f"{name} {description}".lower()

        # 关键词映射
        keywords_to_category = {
            # Metabolism
            'metabolism': 'Metabolism',
            'carbohydrate': 'Metabolism',
            'lipid': 'Metabolism',
            'amino acid': 'Metabolism',
            'nucleotide': 'Metabolism',
            'energy': 'Metabolism',
            'vitamin': 'Metabolism',

            # Genetic Information Processing
            'transcription': 'Genetic Information Processing',
            'translation': 'Genetic Information Processing',
            'replication': 'Genetic Information Processing',
            'repair': 'Genetic Information Processing',

            # Environmental Information Processing
            'signal transduction': 'Environmental Information Processing',
            'signaling': 'Environmental Information Processing',

            # Cellular Processes
            'cell growth': 'Cellular Processes',
            'cell death': 'Cellular Processes',
            'apoptosis': 'Cellular Processes',
            'cell motility': 'Cellular Processes',

            # Organismal Systems
            'immune': 'Organismal Systems',
            'nervous': 'Organismal Systems',
            'endocrine': 'Organismal Systems',
            'circulatory': 'Organismal Systems',
            'digestive': 'Organismal Systems',

            # Diseases
            'cancer': 'Human Diseases',
            'tumor': 'Human Diseases',
            'immune disease': 'Human Diseases',
            'neurodegenerative': 'Human Diseases',
            'metabolic disease': 'Human Diseases'
        }

        for keyword, category in keywords_to_category.items():
            if keyword in text:
                return category

        return 'Other'

    def _map_pathway_type(self, category: str) -> str:
        """
        映射分类到通路类型

        Args:
            category: 通路分类

        Returns:
            通路类型
        """
        mapping = {
            'Metabolism': 'metabolic',
            'Genetic Information Processing': 'genetic_information',
            'Environmental Information Processing': 'signaling',
            'Cellular Processes': 'cellular',
            'Organismal Systems': 'organismal',
            'Human Diseases': 'disease',
            'Other': 'other'
        }
        return mapping.get(category, 'other')

    def _transform_target_from_gene(self, gene_data: Dict) -> Optional[Dict]:
        """
        从基因数据转换靶点实体

        Args:
            gene_data: 基因数据

        Returns:
            转换后的靶点实体
        """
        try:
            gene_id = gene_data.get('gene_id', '')
            gene_symbol = gene_data.get('gene_symbol', gene_id)

            return {
                'primary_id': f"GENE-{gene_id}",
                'identifiers': {
                    'KEGG_Gene': gene_id,
                    'GeneSymbol': gene_symbol
                },
                'properties': {
                    'name': gene_symbol,
                    'gene_symbol': gene_symbol,
                    'gene_id': gene_id,
                    'description': gene_data.get('description', ''),
                    'source': 'KEGG',
                    'version': '2024.1'
                },
                'entity_type': 'rd:Target'
            }

        except Exception as e:
            logger.warning(f"转换靶点失败: {e}")
            return None

    def _transform_compound(self, compound_data: Dict) -> Optional[Dict]:
        """
        转换化合物数据

        Args:
            compound_data: 化合物数据

        Returns:
            转换后的化合物实体
        """
        try:
            compound_id = compound_data.get('compound_id', '')
            name = compound_data.get('name', compound_id)

            return {
                'primary_id': compound_id,
                'identifiers': {
                    'KEGG_Compound': compound_id,
                    'CompoundID': compound_id.replace('cpd:', '')
                },
                'properties': {
                    'name': name,
                    'compound_type': 'small_molecule',
                    'source': 'KEGG',
                    'version': '2024.1'
                },
                'entity_type': 'rd:Compound'
            }

        except Exception as e:
            logger.warning(f"转换化合物失败: {e}")
            return None

    def _create_pathway_relationships(
        self,
        pathway_data: Dict,
        pathway_entity: Dict
    ) -> List[Dict]:
        """
        创建通路相关关系

        Args:
            pathway_data: 原始通路数据
            pathway_entity: 转换后的通路实体

        Returns:
            关系列表
        """
        relationships = []
        pathway_id = pathway_entity['primary_id']

        # 创建基因/蛋白质→通路关系
        for gene_data in pathway_data.get('genes', []):
            gene_id = gene_data.get('gene_id', '')
            gene_symbol = gene_data.get('gene_symbol', gene_id)

            if not gene_id:
                continue

            # 确定关系类型（简化版，实际可以根据更多信息判断）
            rel_type = 'PARTICIPATES_IN'

            relationships.append({
                'relationship_type': rel_type,
                'source_entity_id': f"Target-GENE-{gene_id}",
                'target_entity_id': f"Pathway-{pathway_id}",
                'target_entity_data': gene_data,
                'properties': {
                    'gene_id': gene_id,
                    'gene_symbol': gene_symbol,
                    'role': 'participant'
                },
                'source': 'KEGG-PATHWAY'
            })

        # 创建通路→化合物关系
        for compound_data in pathway_data.get('compounds', []):
            compound_id = compound_data.get('compound_id', '')

            if not compound_id:
                continue

            relationships.append({
                'relationship_type': 'PATHWAY_HAS_COMPOUND',
                'source_entity_id': f"Pathway-{pathway_id}",
                'target_entity_id': f"Compound-{compound_id}",
                'target_entity_data': compound_data,
                'properties': {
                    'compound_id': compound_id,
                    'compound_name': compound_data.get('name', '')
                },
                'source': 'KEGG-PATHWAY'
            })

        return relationships

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
        if entity_type not in ['rd:Pathway', 'rd:Target', 'rd:Gene', 'rd:Compound']:
            return False

        return True

    #===========================================================
    # 结果保存方法
    #===========================================================

    def _save_kegg_results(
        self,
        all_entities: List[Dict],
        all_relationships: List[Dict],
        output_to: Optional[str] = None
    ) -> Path:
        """
        保存 KEGG 处理结果

        Args:
            all_entities: 所有实体列表
            all_relationships: 所有关系列表
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
        pathways = [e for e in all_entities if e.get('entity_type') == 'rd:Pathway']
        targets = [e for e in all_entities if e.get('entity_type') == 'rd:Target']
        compounds = [e for e in all_entities if e.get('entity_type') == 'rd:Compound']

        if pathways:
            pathways_file = output_dir / f"kegg_pathways_{timestamp}.json"
            with open(pathways_file, 'w', encoding='utf-8') as f:
                json.dump(pathways, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(pathways)} 个通路到: {pathways_file}")

        if targets:
            targets_file = output_dir / f"kegg_targets_{timestamp}.json"
            with open(targets_file, 'w', encoding='utf-8') as f:
                json.dump(targets, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(targets)} 个靶点到: {targets_file}")

        if compounds:
            compounds_file = output_dir / f"kegg_compounds_{timestamp}.json"
            with open(compounds_file, 'w', encoding='utf-8') as f:
                json.dump(compounds, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(compounds)} 个化合物到: {compounds_file}")

        # 保存关系
        if all_relationships:
            relationships_file = output_dir / f"kegg_pathway_relationships_{timestamp}.json"
            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(all_relationships, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(all_relationships)} 个关系到: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "KEGG REST API",
            "timestamp": timestamp,
            "extraction_config": {
                "batch_size": self.extraction_config.batch_size,
                "rate_limit": self.extraction_config.rate_limit,
                "cache_enabled": self.extraction_config.cache_enabled,
                "include_genes": self.extraction_config.include_genes,
                "map_kegg_to_uniprot": self.extraction_config.map_kegg_to_uniprot,
                "use_kgml": self.extraction_config.use_kgml
            },
            "statistics": {
                "pathways_processed": self.stats.pathways_processed,
                "pathways_extracted": self.stats.pathways_extracted,
                "genes_extracted": self.stats.genes_extracted,
                "proteins_extracted": self.stats.proteins_extracted,
                "compounds_extracted": self.stats.compounds_extracted,
                "relationships_created": self.stats.relationships_created,
                "api_requests_made": self.stats.api_requests_made,
                "cache_hits": self.stats.cache_hits,
                "processing_time_seconds": self.stats.processing_time_seconds
            },
            "entities_by_type": {
                "rd:Pathway": len(pathways),
                "rd:Target": len(targets),
                "rd:Compound": len(compounds)
            },
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "errors": self.stats.errors,
            "warnings": self.stats.warnings
        }

        summary_file = output_dir / f"kegg_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"保存处理摘要到: {summary_file}")

        return summary_file

    def fetch_pathways_by_organism(
        self,
        organism: OrganismCode = OrganismCode.HUMAN,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        按生物体获取通路数据

        Args:
            organism: 生物体代码
            category: 通路分类过滤（可选）
            limit: 数量限制（可选）

        Returns:
            通路数据列表
        """
        logger.info(f"Fetching KEGG pathways for organism: {organism.value}")

        # 列出所有通路
        pathway_ids = self.list_pathways(organism)

        if category:
            # 过滤分类（需要获取详细信息）
            filtered_ids = []
            for pathway_id in pathway_ids[:limit] if limit else pathway_ids:
                pathway_data = self._fetch_single_pathway(pathway_id)
                if pathway_data:
                    pathway_category = pathway_data.get('category', '')
                    if category.lower() in pathway_category.lower():
                        filtered_ids.append(pathway_id)
            pathway_ids = filtered_ids

        if limit:
            pathway_ids = pathway_ids[:limit]

        # 批量获取数据
        results = []
        for i in range(0, len(pathway_ids), self.extraction_config.batch_size):
            batch_ids = pathway_ids[i:i + self.extraction_config.batch_size]
            batch_data = self._fetch_batch_pathway_data(batch_ids)
            results.extend(batch_data)

        return results


#===========================================================
# 命令行接口
#===========================================================

def main():
    """
    命令行主函数
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='KEGG Pathway API 处理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 从 KEGG 通路 ID 文件处理
  python -m processors.kegg_processor /path/to/pathway_ids.txt

  # 按生物体获取所有通路
  python -m processors.kegg_processor --organism human --limit 100

  # 按分类过滤
  python -m processors.kegg_processor --organism human --category "Metabolism" --limit 50

  # 自定义输出目录
  python -m processors.kegg_processor /path/to/pathway_ids.txt --output /custom/output/path

  # 使用 KGML 格式
  python -m processors.kegg_processor --organism human --use-kgml --limit 50

  # 禁用缓存
  python -m processors.kegg_processor --organism human --no-cache
        """
    )

    parser.add_argument(
        'source_path',
        nargs='?',
        help='KEGG 通路 ID 文件路径（如果使用 --organism 则可选）'
    )

    parser.add_argument(
        '--output',
        help='输出目录（默认为 data/processed/documents/kegg/）'
    )

    parser.add_argument(
        '--organism',
        choices=['human', 'mouse', 'rat'],
        default='human',
        help='生物体代码（默认: human）'
    )

    parser.add_argument(
        '--category',
        help='通路分类过滤（例如: "Metabolism", "Signaling"）'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='提取数量限制'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='批处理大小（默认: 50）'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=10.0,
        help='API 请求速率限制（请求/秒，默认: 10）'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='禁用缓存'
    )

    parser.add_argument(
        '--no-uniprot-mapping',
        action='store_true',
        help='禁用 KEGG 到 UniProt 的映射'
    )

    parser.add_argument(
        '--use-kgml',
        action='store_true',
        help='使用 KGML (XML) 格式而非文本格式'
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
            'rate_limit': args.rate_limit,
            'cache_enabled': not args.no_cache,
            'map_kegg_to_uniprot': not args.no_uniprot_mapping,
            'use_kgml': args.use_kgml
        }
    }

    # 创建处理器
    processor = KEGGProcessor(config)

    # 确定数据源
    if args.limit or args.category:
        # 使用生物体搜索模式
        logger.info(f"使用生物体搜索模式: {args.organism}")

        organism_code = OrganismCode(args.organism)

        # 获取通路数据
        pathways_data = processor.fetch_pathways_by_organism(
            organism=organism_code,
            category=args.category,
            limit=args.limit
        )

        # 创建临时数据结构
        raw_data = {
            'pathways': pathways_data,
            'source_file': f'organism_search_{args.organism}',
            'extraction_timestamp': datetime.now().isoformat(),
            'pathway_ids': [p.get('pathway_id', '') for p in pathways_data]
        }

        # 转换数据
        transformed_data = processor.transform(raw_data)

        # 验证
        if not processor.validate(transformed_data):
            logger.error("数据验证失败")
            return 1

        # 收集实体和关系
        all_entities = []
        all_relationships = []

        entities_dict = transformed_data.get('entities', {})
        relationships = transformed_data.get('relationships', [])

        for entity_type, entity_list in entities_dict.items():
            for entity in entity_list:
                all_entities.append({
                    **entity,
                    'entity_type': entity_type
                })

        all_relationships.extend(relationships)

        # 保存结果
        output_path = processor._save_kegg_results(
            all_entities,
            all_relationships,
            args.output
        )

        # 创建处理结果
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            processor_name=processor.PROCESSOR_NAME,
            source_path=f'organism_search_{args.organism}',
            metrics=ProcessingMetrics(
                files_processed=1,
                entities_extracted=len(all_entities),
                relationships_extracted=len(all_relationships),
                processing_time_seconds=processor.stats.processing_time_seconds
            ),
            entities=all_entities,
            relationships=all_relationships,
            metadata={
                'processor': processor.PROCESSOR_NAME,
                'source': 'KEGG REST API',
                'stats': {
                    'pathways_processed': processor.stats.pathways_processed,
                    'pathways_extracted': processor.stats.pathways_extracted,
                    'genes_extracted': processor.stats.genes_extracted,
                    'api_requests_made': processor.stats.api_requests_made,
                    'cache_hits': processor.stats.cache_hits
                }
            },
            output_path=str(output_path)
        )

    else:
        # 使用文件模式
        if not args.source_path:
            parser.error('必须指定 source_path 或使用 --organism with --limit')

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
        print(f"  通路处理: {stats.get('pathways_processed', 0)}")
        print(f"  通路提取: {stats.get('pathways_extracted', 0)}")
        print(f"  基因提取: {stats.get('genes_extracted', 0)}")
        print(f"  蛋白质提取: {stats.get('proteins_extracted', 0)}")
        print(f"  化合物提取: {stats.get('compounds_extracted', 0)}")
        print(f"  API请求: {stats.get('api_requests_made', 0)}")
        print(f"  缓存命中: {stats.get('cache_hits', 0)}")

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
