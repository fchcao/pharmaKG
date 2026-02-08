#===========================================================
# PharmaKG UniProt API 处理器
# Pharmaceutical Knowledge Graph - UniProt API Processor
#===========================================================
# 版本: v1.0
# 描述: 从 UniProt REST API 提取增强的靶点数据
#===========================================================

import logging
import json
import time
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import hashlib

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


class OrganismFilter(str, Enum):
    """生物体过滤枚举"""
    HUMAN = "human"
    MOUSE = "mouse"
    RAT = "rat"
    ALL = "all"

    @property
    def taxonomy_id(self) -> Optional[str]:
        """获取分类学 ID"""
        mapping = {
            self.HUMAN: "9606",
            self.MOUSE: "10090",
            self.RAT: "10116",
            self.ALL: None
        }
        return mapping[self]


@dataclass
class UniProtExtractionConfig:
    """UniProt 提取配置"""
    batch_size: int = 100
    rate_limit: float = 10.0  # 请求每秒
    max_retries: int = 3
    retry_backoff: float = 1.0
    timeout: int = 30
    cache_enabled: bool = True
    cache_file: str = "uniprot_cache.db"
    include_go_annotations: bool = True
    include_diseases: bool = True
    include_subcellular_location: bool = True
    min_quality: str = "reviewed"  # reviewed, unreviewed, all


@dataclass
class ExtractionStats:
    """提取统计信息"""
    targets_processed: int = 0
    targets_enhanced: int = 0
    diseases_extracted: int = 0
    go_annotations_extracted: int = 0
    relationships_created: int = 0
    api_requests_made: int = 0
    cache_hits: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class UniProtProcessor(BaseProcessor):
    """
    UniProt REST API 处理器

    提取内容：
    - 靶点（Targets）- 从 UniProt API
    - GO 注释 - 分子功能、生物过程、细胞组分
    - 疾病关联 - 疾病注释
    - 亚细胞位置 - 细胞位置信息

    关系类型：
    - ASSOCIATED_WITH_DISEASE - 靶点→疾病
    - BIOMARKER_FOR - 靶点→疾病（生物标志物）
    - ENCODED_BY - 靶点→基因
    """

    PROCESSOR_NAME = "UniProtProcessor"
    SUPPORTED_FORMATS = ['.txt', '.csv', '.json']
    OUTPUT_SUBDIR = "uniprot"

    # UniProt API 端点
    API_BASE = "https://rest.uniprot.org/uniprotkb"
    STREAM_ENDPOINT = f"{API_BASE}/stream"
    SEARCH_ENDPOINT = f"{API_BASE}/search"
    ENTRY_ENDPOINT = f"{API_BASE}/{{accession}}"

    # 支持的生物体
    ORGANISM_TAXONOMY = {
        "human": "9606",
        "mouse": "10090",
        "rat": "10116"
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 UniProt 处理器

        Args:
            config: 处理器配置字典
        """
        super().__init__(config)

        # 初始化提取配置
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = UniProtExtractionConfig(**extraction_config)

        # 统计信息
        self.stats = ExtractionStats()

        # 去重集合
        self.seen_uniprot_ids: Set[str] = set()

        # 输出文件路径
        self.output_targets = self.entities_output_dir / "uniprot_targets.json"
        self.output_diseases = self.entities_output_dir / "uniprot_diseases.json"
        self.output_relationships = self.relationships_output_dir / "uniprot_relationships.json"

        # 初始化 HTTP 会话
        self.session = self._create_session()

        # 初始化缓存
        self.cache_conn = None
        if self.extraction_config.cache_enabled:
            self._init_cache()

        # 速率限制控制
        self.last_request_time = 0
        self.min_request_interval = 1.0 / self.extraction_config.rate_limit

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录，查找 UniProt ID 文件

        Args:
            source_path: 源目录路径

        Returns:
            找到的文件列表
        """
        source_path = Path(source_path)
        files = []

        if source_path.is_file():
            if source_path.suffix in self.SUPPORTED_FORMATS or source_path.name.startswith('uniprot'):
                files.append(source_path)
        else:
            # 查找所有支持的文件格式
            for ext in self.SUPPORTED_FORMATS:
                files.extend(source_path.rglob(f"*{ext}"))

            # 优先选择包含 uniprot 的文件
            uniprot_files = [f for f in files if 'uniprot' in f.name.lower()]
            if uniprot_files:
                files = uniprot_files

        logger.info(f"Scanned {source_path}: found {len(files)} UniProt ID files")
        return files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从文件中提取 UniProt ID 并获取数据

        Args:
            file_path: 文件路径

        Returns:
            提取的原始数据
        """
        logger.info(f"Extracting UniProt data from {file_path}")

        try:
            # 读取 UniProt IDs
            uniprot_ids = self._read_uniprot_ids(file_path)

            if not uniprot_ids:
                logger.warning(f"No UniProt IDs found in {file_path}")
                return {'error': 'No UniProt IDs found'}

            logger.info(f"Found {len(uniprot_ids)} UniProt IDs to process")

            # 批量获取 UniProt 数据
            raw_data = {
                'targets': [],
                'diseases': [],
                'source_file': str(file_path),
                'extraction_timestamp': datetime.now().isoformat(),
                'uniprot_ids': uniprot_ids
            }

            # 使用批量请求处理
            for i in range(0, len(uniprot_ids), self.extraction_config.batch_size):
                batch_ids = uniprot_ids[i:i + self.extraction_config.batch_size]
                batch_data = self._fetch_batch_uniprot_data(batch_ids)

                if batch_data:
                    raw_data['targets'].extend(batch_data)
                    self.stats.targets_processed += len(batch_data)

            logger.info(f"Extracted {len(raw_data['targets'])} targets from UniProt")

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

        logger.info("Transforming extracted UniProt data")

        transformed = {
            'entities': {
                'rd:Target': [],
                'rd:Disease': []
            },
            'relationships': []
        }

        # 转换靶点
        diseases_set = {}  # 用于去重疾病

        for target_data in raw_data.get('targets', []):
            # 转换靶点实体
            entity = self._transform_target(target_data)
            if entity:
                transformed['entities']['rd:Target'].append(entity)
                self.stats.targets_enhanced += 1

            # 提取疾病关联
            disease_rels = self._extract_disease_relationships(target_data)
            for rel in disease_rels:
                transformed['relationships'].append(rel)
                disease_id = rel['target_entity_id']
                if disease_id not in diseases_set:
                    disease_data = rel.get('target_entity_data')
                    if disease_data:
                        disease_entity = self._transform_disease(disease_data)
                        if disease_entity:
                            diseases_set[disease_id] = disease_entity

        # 添加疾病实体
        transformed['entities']['rd:Disease'] = list(diseases_set.values())
        self.stats.diseases_extracted = len(diseases_set)

        logger.info(f"Transformed {len(transformed['entities']['rd:Target'])} targets "
                   f"and {len(transformed['entities']['rd:Disease'])} diseases "
                   f"with {len(transformed['relationships'])} relationships")

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
        处理 UniProt 数据的主流程

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
        self.seen_uniprot_ids.clear()

        try:
            # 1. 扫描文件
            files = self.scan(source_path)
            self._metrics.files_scanned = len(files)

            if not files:
                self._warnings.append(f"未找到 UniProt ID 文件: {source_path}")
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
                output_path = self._save_uniprot_results(
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
                'source': 'UniProt REST API',
                'extraction_config': {
                    'batch_size': self.extraction_config.batch_size,
                    'rate_limit': self.extraction_config.rate_limit,
                    'cache_enabled': self.extraction_config.cache_enabled,
                    'include_go_annotations': self.extraction_config.include_go_annotations,
                    'include_diseases': self.extraction_config.include_diseases
                },
                'stats': {
                    'targets_processed': self.stats.targets_processed,
                    'targets_enhanced': self.stats.targets_enhanced,
                    'diseases_extracted': self.stats.diseases_extracted,
                    'go_annotations_extracted': self.stats.go_annotations_extracted,
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
            CREATE TABLE IF NOT EXISTS uniprot_cache (
                accession TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _get_cached_data(self, accession: str) -> Optional[Dict]:
        """
        从缓存获取数据

        Args:
            accession: UniProt 登录号

        Returns:
            缓存的数据或 None
        """
        if not self.cache_conn:
            return None

        cursor = self.cache_conn.cursor()
        cursor.execute("SELECT data FROM uniprot_cache WHERE accession = ?", (accession,))
        row = cursor.fetchone()

        if row:
            self.stats.cache_hits += 1
            return json.loads(row[0])

        return None

    def _set_cached_data(self, accession: str, data: Dict):
        """
        将数据存入缓存

        Args:
            accession: UniProt 登录号
            data: 要缓存的数据
        """
        if not self.cache_conn:
            return

        cursor = self.cache_conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO uniprot_cache (accession, data, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (accession, json.dumps(data))
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

    def _make_api_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        发起 API 请求

        Args:
            url: 请求 URL
            params: 查询参数

        Returns:
            响应数据或 None
        """
        self._respect_rate_limit()

        try:
            self.stats.api_requests_made += 1

            response = self.session.get(
                url,
                params=params,
                timeout=self.extraction_config.timeout,
                headers={"Accept": "application/json"}
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            self.stats.errors.append(f"API request error: {str(e)}")
            return None

    #===========================================================
    # UniProt 数据获取
    #===========================================================

    def _read_uniprot_ids(self, file_path: Path) -> List[str]:
        """
        从文件读取 UniProt IDs

        Args:
            file_path: 文件路径

        Returns:
            UniProt ID 列表
        """
        uniprot_ids = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 提取 UniProt ID（处理可能的额外列）
                        uniprot_id = line.split('\t')[0].split(',')[0].strip()
                        if uniprot_id:
                            uniprot_ids.append(uniprot_id)

            logger.info(f"Read {len(uniprot_ids)} UniProt IDs from {file_path}")

        except Exception as e:
            logger.error(f"Failed to read UniProt IDs from {file_path}: {e}")

        return uniprot_ids

    def _fetch_batch_uniprot_data(self, accession_list: List[str]) -> List[Dict]:
        """
        批量获取 UniProt 数据

        Args:
            accession_list: UniProt 登录号列表

        Returns:
            UniProt 数据列表
        """
        logger.debug(f"Fetching batch of {len(accession_list)} UniProt entries")

        results = []

        # 对于大批量，使用 POST stream 端点
        if len(accession_list) > 10:
            results = self._fetch_via_stream(accession_list)
        else:
            # 对于小批量，使用单独的请求
            for accession in accession_list:
                # 检查缓存
                cached_data = self._get_cached_data(accession)
                if cached_data:
                    results.append(cached_data)
                    continue

                # 从 API 获取
                entry_data = self._fetch_single_entry(accession)
                if entry_data:
                    results.append(entry_data)
                    # 缓存数据
                    self._set_cached_data(accession, entry_data)

        return results

    def _fetch_single_entry(self, accession: str) -> Optional[Dict]:
        """
        获取单个 UniProt 条目

        Args:
            accession: UniProt 登录号

        Returns:
            UniProt 条目数据或 None
        """
        url = self.ENTRY_ENDPOINT.format(accession=accession)
        return self._make_api_request(url)

    def _fetch_via_stream(self, accession_list: List[str]) -> List[Dict]:
        """
        使用流式端点批量获取 UniProt 数据

        Args:
            accession_list: UniProt 登录号列表

        Returns:
            UniProt 数据列表
        """
        results = []

        try:
            # 构建查询
            query = " OR ".join([f"accession:{acc}" for acc in accession_list])

            params = {
                "query": query,
                "format": "json",
                "size": str(len(accession_list))
            }

            data = self._make_api_request(self.SEARCH_ENDPOINT, params)

            if data and "results" in data:
                results = data["results"]

                # 缓存所有结果
                for entry in results:
                    accession = entry.get("primaryAccession")
                    if accession:
                        self._set_cached_data(accession, entry)

        except Exception as e:
            logger.error(f"Stream fetch failed: {e}")
            # 回退到单独请求
            for accession in accession_list:
                entry_data = self._fetch_single_entry(accession)
                if entry_data:
                    results.append(entry_data)

        return results

    def fetch_by_organism(
        self,
        organism: OrganismFilter = OrganismFilter.HUMAN,
        limit: Optional[int] = None,
        query: Optional[str] = None
    ) -> List[Dict]:
        """
        按生物体搜索 UniProt 条目

        Args:
            organism: 生物体过滤器
            limit: 结果数量限制
            query: 额外的查询条件

        Returns:
            UniProt 条目列表
        """
        logger.info(f"Fetching UniProt entries for organism: {organism.value}")

        # 构建查询
        query_parts = []

        if organism != OrganismFilter.ALL:
            query_parts.append(f"organism_id:{organism.taxonomy_id}")

        if self.extraction_config.min_quality == "reviewed":
            query_parts.append("reviewed:true")
        elif self.extraction_config.min_quality == "unreviewed":
            query_parts.append("reviewed:false")

        if query:
            query_parts.append(query)

        final_query = " AND ".join(query_parts) if query_parts else "*"

        params = {
            "query": final_query,
            "format": "json",
            "size": str(limit) if limit else "500"
        }

        data = self._make_api_request(self.SEARCH_ENDPOINT, params)

        if data and "results" in data:
            results = data["results"]
            logger.info(f"Fetched {len(results)} entries for {organism.value}")
            return results

        return []

    #===========================================================
    # 数据转换方法
    #===========================================================

    def _transform_target(self, target_data: Dict) -> Optional[Dict]:
        """
        转换靶点数据为知识图谱实体格式

        Args:
            target_data: 原始 UniProt 数据

        Returns:
            转换后的实体数据
        """
        try:
            # 生成主标识符
            primary_id = target_data.get("primaryAccession")

            if not primary_id:
                return None

            # 提取基因信息
            gene_data = target_data.get("genes", [])
            gene_symbols = []
            gene_names = []

            for gene in gene_data:
                gene_symbols.extend(gene.get("geneName", {}).get("value", "").split(" "))
                gene_names.extend(gene.get("geneSynonyms", []))

            # 去重
            gene_symbols = list(set([s for s in gene_symbols if s]))
            gene_names = list(set([n for n in gene_names if n]))

            # 提取蛋白名称
            protein_name = target_data.get("proteinDescription", {}) \
                                        .get("recommendedName", {}) \
                                        .get("fullName", {}) \
                                        .get("value", "")

            if not protein_name:
                # 尝试替代名称
                protein_name = target_data.get("proteinDescription", {}) \
                                            .get("submittedNames", [{}])[0] \
                                            .get("fullName", {}) \
                                            .get("value", "")

            # 提取亚细胞位置
            subcellular_locations = []
            if self.extraction_config.include_subcellular_location:
                for comment in target_data.get("comments", []):
                    if comment.get("commentType") == "SUBCELLULAR_LOCATION":
                        for location in comment.get("subcellularLocations", []):
                            loc_value = location.get("location", {}) \
                                                 .get("value", "")
                            if loc_value:
                                subcellular_locations.append(loc_value)

            # 提取 GO 注释
            go_annotations = {
                "molecular_function": [],
                "biological_process": [],
                "cellular_component": []
            }

            if self.extraction_config.include_go_annotations:
                for db_ref in target_data.get("uniProtKBCrossReferences", []):
                    if db_ref.get("database") == "GO":
                        go_id = db_ref.get("id")
                        go_props = db_ref.get("properties", [])

                        # 确定GO方面
                        go_aspect = None
                        for prop in go_props:
                            if prop.get("key") == "term":
                                go_term = prop.get("value")
                                for prop2 in go_props:
                                    if prop2.get("key") == "aspect":
                                        go_aspect = prop2.get("value")
                                        break

                                if go_aspect and go_id and go_term:
                                    go_annotations[go_aspect].append({
                                        "go_id": go_id,
                                        "term": go_term
                                    })

            # 提取药物靶向信息
            druggability = self._extract_druggability(target_data)

            # 构建标识符字典
            identifiers = {
                "UniProt": primary_id,
                "UniProtKB": f"UniProtKB-{primary_id}",
                "GeneSymbol": gene_symbols[0] if gene_symbols else None,
                "GeneID": self._extract_gene_id(target_data)
            }

            # 过滤次要登录号
            secondary_accessions = target_data.get("secondaryAccessions", [])
            if secondary_accessions:
                identifiers["SecondaryAccessions"] = secondary_accessions

            # 构建属性字典
            properties = {
                "name": protein_name or primary_id,
                "gene_symbol": gene_symbols[0] if gene_symbols else None,
                "gene_symbols": gene_symbols,
                "gene_synonyms": gene_names,
                "protein_name": protein_name,
                "organism": target_data.get("organism", {}) \
                                       .get("scientificName", ""),
                "organism_tax_id": target_data.get("organism", {}) \
                                            .get("taxonId", ""),
                "cellular_location": subcellular_locations,
                "go_annotations": go_annotations,
                "druggability_classification": druggability,
                "sequence": target_data.get("sequence", {}) \
                                     .get("value", ""),
                "sequence_length": target_data.get("sequence", {}) \
                                           .get("length", 0),
                "sequence_mass": target_data.get("sequence", {}) \
                                         .get("mass", 0),
                "protein_existence": target_data.get("proteinExistence", ""),
                "entry_info": {
                    "entry_type": target_data.get("entryType", ""),
                    "flag": target_data.get("flag", [])
                },
                "source": "UniProt",
                "version": "2024.01"
            }

            return {
                "primary_id": primary_id,
                "identifiers": identifiers,
                "properties": properties,
                "entity_type": "rd:Target"
            }

        except Exception as e:
            logger.warning(f"转换靶点失败 {primary_id if 'primary_id' in locals() else 'unknown'}: {e}")
            return None

    def _extract_druggability(self, target_data: Dict) -> Dict:
        """
        提取药物靶向信息

        Args:
            target_data: UniProt 数据

        Returns:
            药物靶向分类信息
        """
        druggability = {
            "is_drug_target": False,
            "target_class": None,
            "confidence": "unknown",
            "evidence": []
        }

        # 检查是否有 SmallMolecule 交互
        for db_ref in target_data.get("uniProtKBCrossReferences", []):
            if db_ref.get("database") == "DrugBank":
                druggability["is_drug_target"] = True
                druggability["target_class"] = "DrugBank target"
                druggability["evidence"].append("DrugBank annotation")

        # 检查注释
        for comment in target_data.get("comments", []):
            if comment.get("commentType") == "CATALYTIC_ACTIVITY":
                druggability["target_class"] = "Enzyme"
                druggability["evidence"].append("Catalytic activity")

            elif comment.get("commentType") == "BINDING":
                druggability["target_class"] = "Binding protein"
                druggability["evidence"].append("Ligand binding")

        # 检查关键词
        keywords = [kw.get("name") for kw in target_data.get("keywords", [])]
        if "Drug target" in keywords:
            druggability["is_drug_target"] = True
            druggability["evidence"].append("Drug target keyword")

        return druggability

    def _extract_gene_id(self, target_data: Dict) -> Optional[str]:
        """
        提取 Gene ID

        Args:
            target_data: UniProt 数据

        Returns:
            Gene ID 或 None
        """
        for db_ref in target_data.get("uniProtKBCrossReferences", []):
            if db_ref.get("database") == "GeneID":
                return db_ref.get("id")
        return None

    def _transform_disease(self, disease_data: Dict) -> Optional[Dict]:
        """
        转换疾病数据为知识图谱实体格式

        Args:
            disease_data: 原始疾病数据

        Returns:
            转换后的实体数据
        """
        try:
            # 生成主标识符
            disease_id = disease_data.get("diseaseId")
            disease_name = disease_data.get("diseaseName", "")

            if not disease_id:
                # 使用名称作为备用
                disease_id = f"DISEASE-{hashlib.md5(disease_name.encode()).hexdigest()[:8]}"

            identifiers = {
                "MIM": disease_data.get("diseaseId") if disease_data.get("diseaseId", "").startswith("MIM") else None,
                "OMIM": disease_data.get("diseaseId") if disease_data.get("diseaseId", "").startswith("OMIM") else None,
                "DOID": disease_data.get("diseaseId") if disease_data.get("diseaseId", "").startswith("DOID") else None,
                "MeSH": disease_data.get("diseaseId") if disease_data.get("diseaseId", "").startswith("D") else None
            }

            # 移除 None 值
            identifiers = {k: v for k, v in identifiers.items() if v}

            properties = {
                "name": disease_name,
                "acronym": disease_data.get("acronym"),
                "description": disease_data.get("description"),
                "disease_type": disease_data.get("diseaseType"),
                "source": "UniProt",
                "version": "2024.01"
            }

            return {
                "primary_id": disease_id,
                "identifiers": identifiers,
                "properties": properties,
                "entity_type": "rd:Disease"
            }

        except Exception as e:
            logger.warning(f"转换疾病失败: {e}")
            return None

    def _extract_disease_relationships(self, target_data: Dict) -> List[Dict]:
        """
        提取疾病关联关系

        Args:
            target_data: UniProt 靶点数据

        Returns:
            关系列表
        """
        relationships = []

        primary_id = target_data.get("primaryAccession")

        for comment in target_data.get("comments", []):
            if comment.get("commentType") == "DISEASE":
                disease_data = comment.get("disease", {})
                disease_id = disease_data.get("diseaseId")

                if not disease_id:
                    continue

                # 确定关系类型
                rel_type = "ASSOCIATED_WITH_DISEASE"

                # 检查是否是生物标志物
                note = comment.get("note", [])
                if any("biomarker" in str(n).lower() for n in (note if isinstance(note, list) else [note])):
                    rel_type = "BIOMARKER_FOR"

                relationships.append({
                    "relationship_type": rel_type,
                    "source_entity_id": f"Target-{primary_id}",
                    "target_entity_id": f"Disease-{disease_id}",
                    "target_entity_data": disease_data,
                    "properties": {
                        "association_type": comment.get("diseaseAssociationType"),
                        "note": comment.get("note"),
                        "evidence": comment.get("evidence")
                    },
                    "source": "UniProt-DISEASE"
                })

        self.stats.relationships_created += len(relationships)

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
        if "primary_id" not in entity:
            return False

        if "properties" not in entity:
            return False

        # 检查实体类型
        entity_type = entity.get("entity_type")
        if entity_type not in ["rd:Target", "rd:Disease"]:
            return False

        return True

    #===========================================================
    # 结果保存方法
    #===========================================================

    def _save_uniprot_results(
        self,
        all_entities: List[Dict],
        all_relationships: List[Dict],
        output_to: Optional[str] = None
    ) -> Path:
        """
        保存 UniProt 处理结果

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
        targets = [e for e in all_entities if e.get("entity_type") == "rd:Target"]
        diseases = [e for e in all_entities if e.get("entity_type") == "rd:Disease"]

        if targets:
            targets_file = output_dir / f"uniprot_targets_{timestamp}.json"
            with open(targets_file, "w", encoding="utf-8") as f:
                json.dump(targets, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(targets)} 个靶点到: {targets_file}")

        if diseases:
            diseases_file = output_dir / f"uniprot_diseases_{timestamp}.json"
            with open(diseases_file, "w", encoding="utf-8") as f:
                json.dump(diseases, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(diseases)} 个疾病到: {diseases_file}")

        # 保存关系
        if all_relationships:
            relationships_file = output_dir / f"uniprot_disease_associations_{timestamp}.json"
            with open(relationships_file, "w", encoding="utf-8") as f:
                json.dump(all_relationships, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(all_relationships)} 个关系到: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "UniProt REST API",
            "timestamp": timestamp,
            "extraction_config": {
                "batch_size": self.extraction_config.batch_size,
                "rate_limit": self.extraction_config.rate_limit,
                "cache_enabled": self.extraction_config.cache_enabled,
                "include_go_annotations": self.extraction_config.include_go_annotations,
                "include_diseases": self.extraction_config.include_diseases,
                "min_quality": self.extraction_config.min_quality
            },
            "statistics": {
                "targets_processed": self.stats.targets_processed,
                "targets_enhanced": self.stats.targets_enhanced,
                "diseases_extracted": self.stats.diseases_extracted,
                "go_annotations_extracted": self.stats.go_annotations_extracted,
                "relationships_created": self.stats.relationships_created,
                "api_requests_made": self.stats.api_requests_made,
                "cache_hits": self.stats.cache_hits,
                "processing_time_seconds": self.stats.processing_time_seconds
            },
            "entities_by_type": {
                "rd:Target": len(targets),
                "rd:Disease": len(diseases)
            },
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "errors": self.stats.errors,
            "warnings": self.stats.warnings
        }

        summary_file = output_dir / f"uniprot_summary_{timestamp}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
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
        description="UniProt REST API 处理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 从 UniProt ID 文件处理
  python -m processors.uniprot_processor /path/to/uniprot_ids.txt

  # 按生物体搜索并处理
  python -m processors.uniprot_processor --organism human --limit 100

  # 自定义输出目录
  python -m processors.uniprot_processor /path/to/uniprot_ids.txt --output /custom/output/path

  # 包含未审核条目
  python -m processors.uniprot_processor --organism human --min-quality all --limit 500

  # 禁用缓存
  python -m processors.uniprot_processor /path/to/uniprot_ids.txt --no-cache
        """
    )

    parser.add_argument(
        "source_path",
        nargs="?",
        help="UniProt ID 文件路径（如果使用 --organism 则可选）"
    )

    parser.add_argument(
        "--output",
        help="输出目录（默认为 data/processed/documents/uniprot/）"
    )

    parser.add_argument(
        "--organism",
        choices=["human", "mouse", "rat", "all"],
        default="human",
        help="生物体过滤器（默认: human）"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="提取数量限制"
    )

    parser.add_argument(
        "--query",
        help="额外的查询条件（例如: 'kinase'）"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="批处理大小（默认: 100）"
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        default=10.0,
        help="API 请求速率限制（请求/秒，默认: 10）"
    )

    parser.add_argument(
        "--min-quality",
        choices=["reviewed", "unreviewed", "all"],
        default="reviewed",
        help="最小质量标准（默认: reviewed）"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="禁用缓存"
    )

    parser.add_argument(
        "--no-go",
        action="store_true",
        help="不包含 GO 注释"
    )

    parser.add_argument(
        "--no-diseases",
        action="store_true",
        help="不包含疾病关联"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 构建配置
    config = {
        "extraction": {
            "batch_size": args.batch_size,
            "rate_limit": args.rate_limit,
            "cache_enabled": not args.no_cache,
            "include_go_annotations": not args.no_go,
            "include_diseases": not args.no_diseases,
            "min_quality": args.min_quality
        }
    }

    # 创建处理器
    processor = UniProtProcessor(config)

    # 确定数据源
    if args.organism != "all" or args.limit:
        # 使用生物体搜索
        logger.info(f"使用生物体搜索模式: {args.organism}")

        organism_filter = OrganismFilter(args.organism)
        uniprot_data = processor.fetch_by_organism(
            organism=organism_filter,
            limit=args.limit,
            query=args.query
        )

        # 创建临时数据结构
        raw_data = {
            "targets": uniprot_data,
            "source_file": f"organism_search_{args.organism}",
            "extraction_timestamp": datetime.now().isoformat(),
            "uniprot_ids": [entry.get("primaryAccession") for entry in uniprot_data]
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

        entities_dict = transformed_data.get("entities", {})
        relationships = transformed_data.get("relationships", [])

        for entity_type, entity_list in entities_dict.items():
            for entity in entity_list:
                all_entities.append({
                    **entity,
                    "entity_type": entity_type
                })

        all_relationships.extend(relationships)

        # 保存结果
        output_path = processor._save_uniprot_results(
            all_entities,
            all_relationships,
            args.output
        )

        # 创建处理结果
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            processor_name=processor.PROCESSOR_NAME,
            source_path=f"organism_search_{args.organism}",
            metrics=ProcessingMetrics(
                files_processed=1,
                entities_extracted=len(all_entities),
                relationships_extracted=len(all_relationships),
                processing_time_seconds=processor.stats.processing_time_seconds
            ),
            entities=all_entities,
            relationships=all_relationships,
            metadata={
                "processor": processor.PROCESSOR_NAME,
                "source": "UniProt REST API",
                "stats": {
                    "targets_processed": processor.stats.targets_processed,
                    "targets_enhanced": processor.stats.targets_enhanced,
                    "diseases_extracted": processor.stats.diseases_extracted,
                    "api_requests_made": processor.stats.api_requests_made,
                    "cache_hits": processor.stats.cache_hits
                }
            },
            output_path=str(output_path)
        )

    else:
        # 使用文件模式
        if not args.source_path:
            parser.error("必须指定 source_path 或使用 --organism")

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
        stats = result.metadata.get("stats", {})
        print(f"\n详细统计:")
        print(f"  靶点处理: {stats.get('targets_processed', 0)}")
        print(f"  靶点增强: {stats.get('targets_enhanced', 0)}")
        print(f"  疾病提取: {stats.get('diseases_extracted', 0)}")
        print(f"  GO注释提取: {stats.get('go_annotations_extracted', 0)}")
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


if __name__ == "__main__":
    exit(main())
