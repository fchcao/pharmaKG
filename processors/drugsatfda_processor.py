#!/usr/bin/env python3
#===========================================================
# PharmaKG FDA Drugs@FDA API 处理器
# Pharmaceutical Knowledge Graph - FDA Drugs@FDA API Processor
#===========================================================
# 版本: v1.0
# 描述: 从 FDA Drugs@FDA API 提取药物批准数据
#===========================================================

import logging
import json
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Generator
from enum import Enum
from urllib.parse import urlencode, quote

import requests

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


#===========================================================
# 枚举类型 / Enumeration Types
#===========================================================

class ApprovalType(str, Enum):
    """批准类型枚举 / Approval Type Enumeration"""
    NDA = "NDA"  # New Drug Application
    ANDA = "ANDA"  # Abbreviated New Drug Application
    BLA = "BLA"  # Biologics License Application


class SubmissionType(str, Enum):
    """提交类型枚举 / Submission Type Enumeration"""
    ORIGINAL = "Original"
    SUPPLEMENT = "Supplement"
    EFFICACY_SUPPLEMENT = "Efficacy Supplement"
    MANUFACTURING_SUPPLEMENT = "Manufacturing Supplement"
    LABELING_SUPPLEMENT = "Labeling Supplement"


class SubmissionStatus(str, Enum):
    """提交状态枚举 / Submission Status Enumeration"""
    APPROVED = "Approved"
    WITHDRAWN = "Withdrawn"
    PENDING = "Pending"
    APPROVED_WITHDRAWN = "Approved/Withdrawn"
    APPROVED_PENDING = "Approved/Pending"
    INACTIVE = "Inactive"


class ReviewPriority(str, Enum):
    """审查优先级枚举 / Review Priority Enumeration"""
    STANDARD = "Standard"
    PRIORITY = "Priority"


class MarketingStatus(str, Enum):
    """营销状态枚举 / Marketing Status Enumeration"""
    PRESCRIPTION = "Prescription"
    OTC = "OTC"
    DISCONTINUED = "Discontinued"
    NONE = "None"


#===========================================================
# 配置类 / Configuration Classes
#===========================================================

@dataclass
class DrugsAtFDAExtractionConfig:
    """Drugs@FDA 提取配置 / Extraction Configuration"""
    # API 配置 / API Configuration
    api_base_url: str = "https://api.fda.gov/drug/drugsfda.json"
    api_version: str = "v1"
    request_timeout: int = 30  # 请求超时时间（秒）/ Request timeout (seconds)

    # 速率限制配置 / Rate Limit Configuration
    # FDA openFDA 通常限制为 240 请求/分钟 = 4 请求/秒
    # 为了安全起见，我们使用更保守的速率
    rate_limit_per_second: float = 1.0  # 每秒请求数 / Requests per second
    rate_limit_delay: float = 1.0  # 请求间延迟（秒）/ Delay between requests (seconds)

    # 分页配置 / Pagination Configuration
    page_size: int = 100  # 每页结果数 / Results per page (max: 100)
    max_pages: Optional[int] = None  # 最大页数限制 / Maximum pages limit
    max_applications: Optional[int] = None  # 最大申请数量限制 / Maximum applications limit

    # 重试配置 / Retry Configuration
    max_retries: int = 3  # 最大重试次数 / Maximum retry attempts
    retry_backoff_factor: float = 2.0  # 重试退避因子 / Retry backoff factor
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])

    # 查询配置 / Query Configuration
    query_brand_name: Optional[str] = None  # 按品牌名查询 / Query by brand name
    query_generic_name: Optional[str] = None  # 按通用名查询 / Query by generic name
    query_application_number: Optional[str] = None  # 按申请号查询 / Query by application number
    query_sponsor_name: Optional[str] = None  # 按赞助商查询 / Query by sponsor name

    # 交叉域映射配置 / Cross-Domain Mapping Configuration
    map_unii_to_chembl: bool = True  # 映射 UNII 到 ChEMBL / Map UNII to ChEMBL
    map_to_clinical_trials: bool = True  # 映射到临床试验 / Map to clinical trials
    use_mychem_api: bool = True  # 使用 MyChem.info API / Use MyChem.info API

    # 输出配置 / Output Configuration
    save_raw_response: bool = False  # 保存原始 API 响应 / Save raw API response
    save_intermediate_batches: bool = True  # 保存中间批次 / Save intermediate batches

    # 去重配置 / Deduplication Configuration
    deduplicate_by_application_number: bool = True  # 按申请号去重 / Deduplicate by application number


@dataclass
class DrugsAtFDAStats:
    """Drugs@FDA 提取统计信息 / Extraction Statistics"""
    # API 请求统计 / API Request Statistics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0

    # 数据提取统计 / Data Extraction Statistics
    applications_extracted: int = 0
    products_extracted: int = 0
    submissions_extracted: int = 0
    approvals_extracted: int = 0
    compounds_extracted: int = 0
    sponsors_extracted: int = 0
    agencies_extracted: int = 0

    # 关系统计 / Relationship Statistics
    relationships_created: int = 0
    cross_domain_relationships: int = 0

    # 去重统计 / Deduplication Statistics
    applications_deduplicated: int = 0

    # 处理时间 / Processing Time
    processing_time_seconds: float = 0.0
    api_request_time_seconds: float = 0.0

    # 错误和警告 / Errors and Warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


#===========================================================
# 主处理器类 / Main Processor Class
#===========================================================

class DrugsAtFDAProcessor(BaseProcessor):
    """
    FDA Drugs@FDA API 处理器 / FDA Drugs@FDA API Processor

    提取内容 / Extracted Content:
    - 批准（Approval）- 申请号、批准日期、批准类型等 / Application number, approval date, approval type, etc.
    - 提交（Submission）- 提交号、提交类型、提交状态等 / Submission number, submission type, submission status, etc.
    - 化合物（Compound）- UNII、药物名称、化学类型等 / UNII, drug name, chemical type, etc.
    - 药物产品（DrugProduct）- 产品号、品牌名、营销状态等 / Product number, brand name, marketing status, etc.
    - 监管机构（RegulatoryAgency）- 机构名称、部门、办公室等 / Agency name, division, office, etc.

    关系类型 / Relationship Types:
    - SUBMITTED_FOR_APPROVAL - Submission → Approval
    - APPROVED_PRODUCT - RegulatoryAgency → Compound (via approval)
    - APPROVAL_FOR - Approval → Compound
    - HAS_MARKETING_AUTHORIZATION - Compound → DrugProduct
    - MANUFACTURED_BY - DrugProduct → Sponsor/Manufacturer
    - HAS_SUBMISSION - Approval → Submission

    交叉域关系 / Cross-Domain Relationships:
    - TESTED_IN_CLINICAL_TRIAL - Compound → ClinicalTrial (via NCT mapping)
    - APPROVED_FOR_DISEASE - Compound → Condition (via indication)
    """

    PROCESSOR_NAME = "DrugsAtFDAProcessor"
    SUPPORTED_FORMATS = []  # API 处理器不需要文件格式 / API processor doesn't need file formats
    OUTPUT_SUBDIR = "drugsatfda"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Drugs@FDA 处理器 / Initialize Drugs@FDA Processor

        Args:
            config: 处理器配置字典 / Processor configuration dictionary
        """
        super().__init__(config)

        # 初始化提取配置 / Initialize extraction configuration
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = DrugsAtFDAExtractionConfig(**extraction_config)

        # 统计信息 / Statistics
        self.stats = DrugsAtFDAStats()

        # 去重集合 / Deduplication sets
        self.seen_application_numbers: Set[str] = set()
        self.seen_uniis: Set[str] = set()

        # 交叉域映射缓存 / Cross-domain mapping cache
        self.chembl_cache: Dict[str, Optional[str]] = {}  # UNII → ChEMBL ID
        self.clinical_trials_cache: Dict[str, List[str]] = {}  # UNII → NCT IDs

        # 进度跟踪 / Progress tracking
        self._progress_file = self.data_root / "cache" / f"{self.OUTPUT_SUBDIR}_progress.json"
        self._progress_file.parent.mkdir(parents=True, exist_ok=True)

        # 输出文件路径 / Output file paths
        timestamp = datetime.now().strftime("%Y%m%d")
        self.output_approvals = self.entities_output_dir / f"drugsatfda_approvals_{timestamp}.json"
        self.output_submissions = self.entities_output_dir / f"drugsatfda_submissions_{timestamp}.json"
        self.output_compounds = self.entities_output_dir / f"drugsatfda_compounds_{timestamp}.json"
        self.output_products = self.entities_output_dir / f"drugsatfda_products_{timestamp}.json"
        self.output_agencies = self.entities_output_dir / f"drugsatfda_agencies_{timestamp}.json"
        self.output_relationships = self.relationships_output_dir / f"drugsatfda_relationships_{timestamp}.json"
        self.output_summary = self.documents_output_dir / f"drugsatfda_summary_{timestamp}.json"

        # 原始响应输出目录 / Raw response output directory
        if self.extraction_config.save_raw_response:
            self.raw_output_dir = self.data_root / "sources" / "drugsatfda" / "raw_responses"
            self.raw_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    #===========================================================
    # BaseProcessor 抽象方法实现 / BaseProcessor Abstract Method Implementation
    #===========================================================

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录（API 处理器不需要扫描文件）/ Scan source directory (API processor doesn't scan files)

        Args:
            source_path: 源目录路径（忽略）/ Source directory path (ignored)

        Returns:
            空列表（API 处理器不处理文件）/ Empty list (API processor doesn't process files)
        """
        logger.info("API processor does not scan files")
        return []

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        提取数据（API 处理器不处理文件，使用 fetch_all_applications）/ Extract data (API processor doesn't process files)

        Args:
            file_path: 文件路径（忽略）/ File path (ignored)

        Returns:
            空字典 / Empty dictionary
        """
        logger.warning("Use fetch_all_applications() or fetch_by_query() for API extraction")
        return {}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据为知识图谱格式 / Transform extracted data to knowledge graph format

        Args:
            raw_data: 原始提取数据（API 响应）/ Raw extracted data (API response)

        Returns:
            转换后的实体和关系数据 / Transformed entity and relationship data
        """
        if 'error' in raw_data:
            return raw_data

        logger.info("Transforming extracted data")

        transformed = {
            'entities': {
                'regulatory:Approval': [],
                'regulatory:Submission': [],
                'rd:Compound': [],
                'rd:DrugProduct': [],
                'regulatory:RegulatoryAgency': []
            },
            'relationships': []
        }

        # 转换申请数据 / Transform application data
        for application_data in raw_data.get('results', []):
            entities, relationships = self._transform_application(application_data)

            # 添加实体到对应类型 / Add entities to corresponding types
            for entity in entities:
                entity_type = entity.get('entity_type')
                if entity_type in transformed['entities']:
                    transformed['entities'][entity_type].append(entity)

            # 添加关系 / Add relationships
            transformed['relationships'].extend(relationships)

        total_entities = sum(len(v) for v in transformed['entities'].values())
        logger.info(f"Transformed {len(raw_data.get('results', []))} applications into "
                   f"{total_entities} entities and {len(transformed['relationships'])} relationships")

        return transformed

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证转换后的数据 / Validate transformed data

        Args:
            data: 待验证数据 / Data to validate

        Returns:
            是否验证通过 / Whether validation passed
        """
        if 'error' in data:
            return False

        entities = data.get('entities', {})
        relationships = data.get('relationships', [])

        # 检查实体 / Check entities
        total_entities = sum(len(v) for v in entities.values())
        if total_entities == 0:
            self.stats.warnings.append("No entities extracted")
            return False

        # 检查关系 / Check relationships
        if len(relationships) == 0:
            self.stats.warnings.append("No relationships created")

        # 验证必需字段 / Validate required fields
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if not self._validate_entity(entity):
                    self.stats.warnings.append(f"Invalid entity in {entity_type}")
                    return False

        logger.info(f"Validation passed: {total_entities} entities, {len(relationships)} relationships")
        return True

    #===========================================================
    # API 数据获取方法 / API Data Fetching Methods
    #===========================================================

    def fetch_all_applications(
        self,
        max_applications: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取所有申请（全量下载）/ Fetch all applications (full download)

        Args:
            max_applications: 最大申请数量（可选）/ Maximum applications (optional)

        Returns:
            提取的申请数据 / Extracted application data
        """
        logger.info("Starting full download of Drugs@FDA data")

        # 使用配置或参数 / Use configuration or parameter
        max_applications = max_applications or self.extraction_config.max_applications

        # 构建查询参数 / Build query parameters
        params = self._build_query_params()

        # 分页获取数据 / Fetch data with pagination
        all_results = []
        skip = 0
        page_count = 0

        start_time = datetime.now()

        while True:
            # 检查限制 / Check limits
            if max_applications and len(all_results) >= max_applications:
                logger.info(f"Reached maximum applications limit: {max_applications}")
                break

            if self.extraction_config.max_pages and page_count >= self.extraction_config.max_pages:
                logger.info(f"Reached maximum pages limit: {self.extraction_config.max_pages}")
                break

            # 获取一页数据 / Fetch one page of data
            page_data = self._fetch_page(params, skip)

            if not page_data or 'results' not in page_data:
                logger.warning("No more results or error occurred")
                break

            results = page_data.get('results', [])
            if not results:
                logger.info("No more results")
                break

            all_results.extend(results)

            page_count += 1
            self.stats.applications_extracted = len(all_results)

            # 更新统计 / Update statistics
            total_results = page_data.get('meta', {}).get('results', {}).get('total')

            logger.info(f"Fetched page {page_count}: {len(results)} applications, "
                       f"total: {len(all_results)}")

            # 检查是否还有更多结果 / Check if there are more results
            if total_results and len(all_results) >= total_results:
                logger.info(f"Fetched all {total_results} applications")
                break

            # 更新 skip / Update skip
            skip += self.extraction_config.page_size

        # 计算处理时间 / Calculate processing time
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.stats.processing_time_seconds = elapsed_time

        logger.info(f"Completed full download: {len(all_results)} applications in {elapsed_time:.2f} seconds")

        return {
            'results': all_results,
            'total_applications': len(all_results),
            'extraction_timestamp': datetime.now().isoformat(),
            'processing_time_seconds': elapsed_time
        }

    def fetch_by_query(
        self,
        query_params: Dict[str, str],
        max_applications: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        按查询获取申请 / Fetch applications by query

        Args:
            query_params: 查询参数字典 / Query parameters dictionary
            max_applications: 最大申请数量（可选）/ Maximum applications (optional)

        Returns:
            提取的申请数据 / Extracted application data
        """
        logger.info(f"Fetching applications by query: {query_params}")

        # 更新配置 / Update configuration
        if 'brand_name' in query_params:
            self.extraction_config.query_brand_name = query_params['brand_name']
        if 'generic_name' in query_params:
            self.extraction_config.query_generic_name = query_params['generic_name']
        if 'application_number' in query_params:
            self.extraction_config.query_application_number = query_params['application_number']
        if 'sponsor_name' in query_params:
            self.extraction_config.query_sponsor_name = query_params['sponsor_name']

        return self.fetch_all_applications(max_applications)

    def fetch_by_brand_name(
        self,
        brand_name: str,
        max_applications: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        按品牌名获取申请 / Fetch applications by brand name

        Args:
            brand_name: 品牌名称 / Brand name
            max_applications: 最大申请数量（可选）/ Maximum applications (optional)

        Returns:
            提取的申请数据 / Extracted application data
        """
        logger.info(f"Fetching applications by brand name: {brand_name}")
        return self.fetch_by_query({'brand_name': brand_name}, max_applications)

    def fetch_by_application_number(
        self,
        application_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        按申请号获取单个申请 / Fetch single application by application number

        Args:
            application_number: 申请号（如：NDA020709）/ Application number (e.g., NDA020709)

        Returns:
            申请数据或 None / Application data or None
        """
        logger.info(f"Fetching application by number: {application_number}")

        # 构建查询参数 / Build query parameters
        params = {
            'search': f'application_number:"{application_number}"',
            'limit': '1'
        }

        # 发送请求 / Send request
        response = self._make_request(self.extraction_config.api_base_url, params)

        if response and 'results' in response and len(response['results']) > 0:
            return response['results'][0]

        return None

    def fetch_by_sponsor_name(
        self,
        sponsor_name: str,
        max_applications: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        按赞助商名称获取申请 / Fetch applications by sponsor name

        Args:
            sponsor_name: 赞助商名称 / Sponsor name
            max_applications: 最大申请数量（可选）/ Maximum applications (optional)

        Returns:
            提取的申请数据 / Extracted application data
        """
        logger.info(f"Fetching applications by sponsor name: {sponsor_name}")
        return self.fetch_by_query({'sponsor_name': sponsor_name}, max_applications)

    #===========================================================
    # API 请求处理方法 / API Request Handling Methods
    #===========================================================

    def _build_query_params(self) -> Dict[str, str]:
        """
        构建查询参数 / Build query parameters

        Returns:
            查询参数字典 / Query parameters dictionary
        """
        params = {
            'limit': str(self.extraction_config.page_size)
        }

        # 添加搜索条件 / Add search conditions
        search_conditions = []

        if self.extraction_config.query_brand_name:
            search_conditions.append(f'openfda.brand_name:"{self.extraction_config.query_brand_name}"')

        if self.extraction_config.query_generic_name:
            search_conditions.append(f'openfda.generic_name:"{self.extraction_config.query_generic_name}"')

        if self.extraction_config.query_application_number:
            search_conditions.append(f'application_number:"{self.extraction_config.query_application_number}"')

        if self.extraction_config.query_sponsor_name:
            search_conditions.append(f'sponsor_name:"{self.extraction_config.query_sponsor_name}"')

        if search_conditions:
            params['search'] = ' AND '.join(search_conditions)

        return params

    def _fetch_page(
        self,
        params: Dict[str, str],
        skip: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        获取单页数据 / Fetch single page of data

        Args:
            params: 查询参数 / Query parameters
            skip: 跳过记录数 / Number of records to skip

        Returns:
            页面数据或 None / Page data or None
        """
        # 添加 skip 参数 / Add skip parameter
        params['skip'] = str(skip)

        # 发送请求 / Send request
        response = self._make_request(self.extraction_config.api_base_url, params)

        if response:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1

        return response

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        发送 API 请求（带重试和速率限制）/ Send API request (with retry and rate limiting)

        Args:
            url: 请求 URL / Request URL
            params: 查询参数（可选）/ Query parameters (optional)

        Returns:
            响应数据或 None / Response data or None
        """
        max_retries = self.extraction_config.max_retries
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            # 速率限制：在请求之间延迟 / Rate limiting: delay between requests
            if self.stats.total_requests > 0:
                time.sleep(self.extraction_config.rate_limit_delay)

            try:
                # 记录请求时间 / Record request time
                request_start = time.time()

                # 发送请求 / Send request
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.extraction_config.request_timeout
                )

                # 记录请求时间 / Record request time
                request_time = time.time() - request_start
                self.stats.api_request_time_seconds += request_time
                self.stats.total_requests += 1

                # 检查响应状态 / Check response status
                if response.status_code == 200:
                    # 保存原始响应（如果配置）/ Save raw response (if configured)
                    if self.extraction_config.save_raw_response:
                        self._save_raw_response(response)

                    return response.json()

                # 处理错误状态码 / Handle error status codes
                if response.status_code in self.extraction_config.retry_status_codes:
                    retry_count += 1
                    self.stats.retried_requests += 1

                    # 计算退避延迟 / Calculate backoff delay
                    backoff_delay = self.extraction_config.retry_backoff_factor ** retry_count
                    logger.warning(f"Request failed with status {response.status_code}, "
                                 f"retrying in {backoff_delay}s (attempt {retry_count}/{max_retries})")
                    time.sleep(backoff_delay)
                    continue

                # 其他错误 / Other errors
                error_msg = f"Request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
                return None

            except requests.exceptions.Timeout:
                last_error = "Request timed out"
                retry_count += 1
                self.stats.retried_requests += 1
                logger.warning(f"{last_error}, retrying (attempt {retry_count}/{max_retries})")
                time.sleep(self.extraction_config.retry_backoff_factor ** retry_count)
                continue

            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {str(e)}"
                retry_count += 1
                self.stats.retried_requests += 1
                logger.warning(f"{last_error}, retrying (attempt {retry_count}/{max_retries})")
                time.sleep(self.extraction_config.retry_backoff_factor ** retry_count)
                continue

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(last_error)
                self.stats.errors.append(last_error)
                return None

        # 所有重试都失败 / All retries failed
        error_msg = f"Request failed after {max_retries} retries: {last_error}"
        logger.error(error_msg)
        self.stats.errors.append(error_msg)
        return None

    #===========================================================
    # 数据转换方法 / Data Transformation Methods
    #===========================================================

    def _transform_application(
        self,
        application_data: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        转换单个申请数据 / Transform single application data

        Args:
            application_data: 原始申请数据 / Raw application data

        Returns:
            (实体列表, 关系列表) / (Entity list, Relationship list)
        """
        entities = []
        relationships = []

        try:
            # 提取申请号 / Extract application number
            application_number = application_data.get('application_number', '')

            # 去重检查 / Deduplication check
            if (self.extraction_config.deduplicate_by_application_number and
                application_number in self.seen_application_numbers):
                self.stats.applications_deduplicated += 1
                return [], []

            if application_number:
                self.seen_application_numbers.add(application_number)

            # 1. 创建 Approval 实体 / Create Approval entity
            approval_entity = self._create_approval_entity(application_data)
            if approval_entity:
                entities.append(approval_entity)

            # 2. 创建 Submission 实体和关系 / Create Submission entities and relationships
            submission_entities, submission_rels = self._create_submissions(application_data, application_number)
            entities.extend(submission_entities)
            relationships.extend(submission_rels)

            # 3. 创建 Compound 实体 / Create Compound entities
            compound_entities, compound_rels = self._create_compounds(application_data, application_number)
            entities.extend(compound_entities)
            relationships.extend(compound_rels)

            # 4. 创建 DrugProduct 实体和关系 / Create DrugProduct entities and relationships
            product_entities, product_rels = self._create_products(application_data, application_number)
            entities.extend(product_entities)
            relationships.extend(product_rels)

            # 5. 创建 RegulatoryAgency 实体和关系 / Create RegulatoryAgency entities and relationships
            agency_entities, agency_rels = self._create_agencies(application_data, application_number)
            entities.extend(agency_entities)
            relationships.extend(agency_rels)

            # 6. 创建交叉域关系 / Create cross-domain relationships
            cross_domain_rels = self._create_cross_domain_relationships(application_data, application_number)
            relationships.extend(cross_domain_rels)

        except Exception as e:
            logger.warning(f"Failed to transform application {application_data.get('application_number')}: {e}")
            self.stats.errors.append(f"Transform error for {application_data.get('application_number')}: {str(e)}")

        return entities, relationships

    def _create_approval_entity(self, application_data: Dict[str, Any]) -> Optional[Dict]:
        """创建批准实体 / Create Approval entity"""
        try:
            application_number = application_data.get('application_number', '')

            # 确定批准类型 / Determine approval type
            approval_type_str = application_number[:3].upper() if application_number else 'NDA'
            try:
                approval_type = ApprovalType(approval_type_str)
            except ValueError:
                approval_type = ApprovalType.NDA

            # 提取产品信息以获取批准日期 / Extract product info for approval date
            products = application_data.get('products', [])
            approval_date = None
            tentative_approval_date = None

            if products:
                # 从第一个产品获取批准日期 / Get approval date from first product
                approval_date = products[0].get('approval_date')

                # 检查是否有临时批准 / Check for tentative approval
                for product in products:
                    if product.get('tentative_approval_date'):
                        tentative_approval_date = product.get('tentative_approval_date')
                        break

            # 生成主标识符 / Generate primary identifier
            primary_id = f"Approval-{application_number}" if application_number else f"Approval-{id(application_data)}"

            # 构建标识符字典 / Build identifiers dictionary
            identifiers = {
                'application_number': application_number,
                'approval_type': approval_type.value
            }

            # 构建属性字典 / Build properties dictionary
            properties = {
                'application_number': application_number,
                'approval_type': approval_type.value,
                'approval_date': approval_date,
                'tentative_approval_date': tentative_approval_date,
                'approval_status': self._determine_approval_status(application_data),
                'supplement_numbers': self._extract_supplement_numbers(application_data),
                'submission_count': len(application_data.get('submissions', [])),
                'product_count': len(products),
                'source': 'Drugs@FDA',
                'api_version': self.extraction_config.api_version
            }

            self.stats.approvals_extracted += 1

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'regulatory:Approval'
            }

        except Exception as e:
            logger.warning(f"Failed to create approval entity: {e}")
            return None

    def _create_submissions(
        self,
        application_data: Dict[str, Any],
        application_number: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建提交实体和关系 / Create Submission entities and relationships"""
        entities = []
        relationships = []

        try:
            submissions = application_data.get('submissions', [])

            for submission_data in submissions:
                submission_number = submission_data.get('submission_number', '')
                submission_type_str = submission_data.get('submission_type', 'Original')
                submission_status_str = submission_data.get('submission_status', 'Pending')

                # 标准化提交类型 / Standardize submission type
                try:
                    submission_type = SubmissionType(submission_type_str)
                except ValueError:
                    submission_type = SubmissionType.ORIGINAL

                # 标准化提交状态 / Standardize submission status
                try:
                    submission_status = SubmissionStatus(submission_status_str)
                except ValueError:
                    submission_status = SubmissionStatus.PENDING

                # 提取审查优先级 / Extract review priority
                review_priority_str = submission_data.get('review_priority', 'Standard')
                try:
                    review_priority = ReviewPriority(review_priority_str)
                except ValueError:
                    review_priority = ReviewPriority.STANDARD

                primary_id = f"Submission-{submission_number}" if submission_number else f"Submission-{id(submission_data)}"

                entity = {
                    'primary_id': primary_id,
                    'identifiers': {
                        'submission_number': submission_number,
                        'application_number': application_number
                    },
                    'properties': {
                        'submission_number': submission_number,
                        'submission_type': submission_type.value,
                        'submission_status': submission_status.value,
                        'submission_date': submission_data.get('submission_date'),
                        'review_priority': review_priority.value,
                        'submission_class_code': submission_data.get('submission_class_code'),
                        'submission_category': submission_data.get('submission_category'),
                        'application_number': application_number,
                        'source': 'Drugs@FDA'
                    },
                    'entity_type': 'regulatory:Submission'
                }

                entities.append(entity)
                self.stats.submissions_extracted += 1

                # 创建关系 / Create relationship
                relationship = {
                    'relationship_type': 'SUBMITTED_FOR_APPROVAL',
                    'source_entity_id': primary_id,
                    'target_entity_id': f"Approval-{application_number}",
                    'properties': {
                        'submission_type': submission_type.value,
                        'submission_status': submission_status.value,
                        'data_source': 'Drugs@FDA'
                    },
                    'source': 'Drugs@FDA'
                }

                relationships.append(relationship)

                # 创建 HAS_SUBMISSION 关系（反向）/ Create HAS_SUBMISSION relationship (reverse)
                reverse_relationship = {
                    'relationship_type': 'HAS_SUBMISSION',
                    'source_entity_id': f"Approval-{application_number}",
                    'target_entity_id': primary_id,
                    'properties': {
                        'submission_type': submission_type.value,
                        'data_source': 'Drugs@FDA'
                    },
                    'source': 'Drugs@FDA'
                }

                relationships.append(reverse_relationship)

        except Exception as e:
            logger.warning(f"Failed to create submissions: {e}")

        return entities, relationships

    def _create_compounds(
        self,
        application_data: Dict[str, Any],
        application_number: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建化合物实体和关系 / Create Compound entities and relationships"""
        entities = []
        relationships = []

        try:
            products = application_data.get('products', [])

            for product in products:
                active_ingredients = product.get('active_ingredients', [])

                for ingredient in active_ingredients:
                    unii = ingredient.get('unii', '')
                    drug_name = ingredient.get('name', '')

                    if not unii:
                        continue

                    # 去重检查 / Deduplication check
                    if unii in self.seen_uniis:
                        continue

                    self.seen_uniis.add(unii)

                    primary_id = f"Compound-{unii}"

                    entity = {
                        'primary_id': primary_id,
                        'identifiers': {
                            'UNII': unii,
                            'drug_name': drug_name
                        },
                        'properties': {
                            'unirot_id': unii,
                            'drug_name': drug_name,
                            'generic_name': product.get('generic_name', ''),
                            'chemical_type': ingredient.get('strength', ''),
                            'route_of_administration': product.get('route', ''),
                            'dosage_form': product.get('dosage_form', ''),
                            'strength': ingredient.get('strength', ''),
                            'source': 'Drugs@FDA'
                        },
                        'entity_type': 'rd:Compound'
                    }

                    entities.append(entity)
                    self.stats.compounds_extracted += 1

                    # 创建关系 / Create relationship
                    relationship = {
                        'relationship_type': 'APPROVAL_FOR',
                        'source_entity_id': f"Approval-{application_number}",
                        'target_entity_id': primary_id,
                        'properties': {
                            'approval_date': product.get('approval_date'),
                            'drug_name': drug_name,
                            'data_source': 'Drugs@FDA'
                        },
                        'source': 'Drugs@FDA'
                    }

                    relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create compounds: {e}")

        return entities, relationships

    def _create_products(
        self,
        application_data: Dict[str, Any],
        application_number: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建药物产品实体和关系 / Create DrugProduct entities and relationships"""
        entities = []
        relationships = []

        try:
            products = application_data.get('products', [])

            for product in products:
                product_number = product.get('product_number', '')
                brand_name = product.get('brand_name', '')
                generic_name = product.get('generic_name', '')

                primary_id = f"DrugProduct-{application_number}-{product_number}" if product_number else f"DrugProduct-{id(product)}"

                # 提取营销状态 / Extract marketing status
                marketing_status_str = product.get('marketing_status', 'Prescription')
                try:
                    marketing_status = MarketingStatus(marketing_status_str)
                except ValueError:
                    marketing_status = MarketingStatus.PRESCRIPTION

                entity = {
                    'primary_id': primary_id,
                    'identifiers': {
                        'product_number': product_number,
                        'application_number': application_number,
                        'brand_name': brand_name
                    },
                    'properties': {
                        'product_number': product_number,
                        'product_type': product.get('product_type', ''),
                        'brand_name': brand_name,
                        'generic_name': generic_name,
                        'trade_names': [brand_name] if brand_name else [],
                        'marketing_status': marketing_status.value,
                        'sponsor_name': product.get('sponsor_name', ''),
                        'dosage_form': product.get('dosage_form', ''),
                        'route_of_administration': product.get('route', ''),
                        'approval_date': product.get('approval_date'),
                        'tentative_approval_date': product.get('tentative_approval_date'),
                        'application_number': application_number,
                        'source': 'Drugs@FDA'
                    },
                    'entity_type': 'rd:DrugProduct'
                }

                entities.append(entity)
                self.stats.products_extracted += 1

                # 创建 HAS_MARKETING_AUTHORIZATION 关系 / Create HAS_MARKETING_AUTHORIZATION relationship
                active_ingredients = product.get('active_ingredients', [])
                for ingredient in active_ingredients:
                    unii = ingredient.get('unii', '')
                    if unii:
                        relationship = {
                            'relationship_type': 'HAS_MARKETING_AUTHORIZATION',
                            'source_entity_id': f"Compound-{unii}",
                            'target_entity_id': primary_id,
                            'properties': {
                                'brand_name': brand_name,
                                'marketing_status': marketing_status.value,
                                'approval_date': product.get('approval_date'),
                                'data_source': 'Drugs@FDA'
                            },
                            'source': 'Drugs@FDA'
                        }

                        relationships.append(relationship)

                # 创建 MANUFACTURED_BY 关系 / Create MANUFACTURED_BY relationship
                sponsor_name = product.get('sponsor_name', '')
                if sponsor_name:
                    sponsor_id = f"Sponsor-{sponsor_name}".replace(' ', '_')

                    relationship = {
                        'relationship_type': 'MANUFACTURED_BY',
                        'source_entity_id': primary_id,
                        'target_entity_id': sponsor_id,
                        'properties': {
                            'sponsor_name': sponsor_name,
                            'data_source': 'Drugs@FDA'
                        },
                        'source': 'Drugs@FDA'
                    }

                    relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create products: {e}")

        return entities, relationships

    def _create_agencies(
        self,
        application_data: Dict[str, Any],
        application_number: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建监管机构实体和关系 / Create RegulatoryAgency entities and relationships"""
        entities = []
        relationships = []

        try:
            # Drugs@FDA 数据通常不包含详细的机构信息
            # 我们创建一个通用的 FDA 机构实体
            # Drugs@FDA data usually doesn't contain detailed agency information
            # We create a generic FDA agency entity

            agency_id = "RegulatoryAgency-FDA"

            # 只创建一次 / Only create once
            if self.stats.agencies_extracted == 0:
                entity = {
                    'primary_id': agency_id,
                    'identifiers': {
                        'agency_name': 'FDA',
                        'agency_id': 'FDA'
                    },
                    'properties': {
                        'agency_name': 'FDA',
                        'full_name': 'U.S. Food and Drug Administration',
                        'division': 'CDER',  # Center for Drug Evaluation and Research
                        'office': 'Office of New Drugs',
                        'review_class': 'Pharmaceutical',
                        'country': 'United States',
                        'source': 'Drugs@FDA'
                    },
                    'entity_type': 'regulatory:RegulatoryAgency'
                }

                entities.append(entity)
                self.stats.agencies_extracted += 1

            # 创建关系 / Create relationship
            relationship = {
                'relationship_type': 'APPROVED_PRODUCT',
                'source_entity_id': agency_id,
                'target_entity_id': f"Approval-{application_number}",
                'properties': {
                    'approval_date': application_data.get('products', [{}])[0].get('approval_date'),
                    'data_source': 'Drugs@FDA'
                },
                'source': 'Drugs@FDA'
            }

            relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create agencies: {e}")

        return entities, relationships

    def _create_cross_domain_relationships(
        self,
        application_data: Dict[str, Any],
        application_number: str
    ) -> List[Dict]:
        """创建交叉域关系 / Create cross-domain relationships"""
        relationships = []

        try:
            products = application_data.get('products', [])

            for product in products:
                active_ingredients = product.get('active_ingredients', [])

                for ingredient in active_ingredients:
                    unii = ingredient.get('unii', '')
                    drug_name = ingredient.get('name', '')

                    if not unii:
                        continue

                    # 映射 UNII 到 ChEMBL / Map UNII to ChEMBL
                    if self.extraction_config.map_unii_to_chembl:
                        chembl_id = self._map_unii_to_chembl(unii, drug_name)
                        if chembl_id:
                            # 创建关系 / Create relationship
                            # 这个关系将在图谱中创建化合物间的链接
                            # This relationship will create links between compounds in the graph
                            pass

                    # 映射到临床试验 / Map to clinical trials
                    if self.extraction_config.map_to_clinical_trials:
                        nct_ids = self._map_to_clinical_trials(unii, drug_name, application_number)
                        for nct_id in nct_ids:
                            relationship = {
                                'relationship_type': 'TESTED_IN_CLINICAL_TRIAL',
                                'source_entity_id': f'Compound-{unii}',
                                'target_entity_id': f'ClinicalTrial-{nct_id}',
                                'properties': {
                                    'drug_name': drug_name,
                                    'nct_id': nct_id,
                                    'mapping_confidence': 'medium',
                                    'data_source': 'Drugs@FDA-ClinicalTrials.gov-Mapping',
                                    'mapped_via': 'application_number'
                                },
                                'source': 'Drugs@FDA-CrossDomain'
                            }

                            relationships.append(relationship)
                            self.stats.cross_domain_relationships += 1

        except Exception as e:
            logger.warning(f"Failed to create cross-domain relationships: {e}")

        return relationships

    #===========================================================
    # 交叉域映射方法 / Cross-Domain Mapping Methods
    #===========================================================

    def _map_unii_to_chembl(self, unii: str, drug_name: str) -> Optional[str]:
        """
        将 UNII 映射到 ChEMBL ID / Map UNII to ChEMBL ID

        Args:
            unii: UNII 标识符 / UNII identifier
            drug_name: 药物名称 / Drug name

        Returns:
            ChEMBL ID 或 None / ChEMBL ID or None
        """
        # 检查缓存 / Check cache
        if unii in self.chembl_cache:
            return self.chembl_cache[unii]

        # 使用 MyChem.info API / Use MyChem.info API
        if self.extraction_config.use_mychem_api:
            try:
                url = f"https://mychem.info/v1/query/{unii}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    chembl_id = data.get('chembl', {}).get('id')

                    if chembl_id:
                        self.chembl_cache[unii] = chembl_id
                        logger.debug(f"Mapped UNII {unii} to ChEMBL {chembl_id}")
                        return chembl_id
            except Exception as e:
                logger.warning(f"Failed to map UNII {unii} via MyChem.info: {e}")

        # 缓存结果（即使为 None）/ Cache result (even if None)
        self.chembl_cache[unii] = None

        return None

    def _map_to_clinical_trials(
        self,
        unii: str,
        drug_name: str,
        application_number: str
    ) -> List[str]:
        """
        映射到临床试验 NCT IDs / Map to clinical trial NCT IDs

        Args:
            unii: UNII 标识符 / UNII identifier
            drug_name: 药物名称 / Drug name
            application_number: 申请号 / Application number

        Returns:
            NCT ID 列表 / List of NCT IDs
        """
        # 检查缓存 / Check cache
        cache_key = f"{unii}_{application_number}"
        if cache_key in self.clinical_trials_cache:
            return self.clinical_trials_cache[cache_key]

        # 这里应该实现实际的映射逻辑
        # 例如：通过 ClinicalTrials.gov API 查询相关试验
        # 目前返回空列表作为占位符 / Return empty list as placeholder for now

        nct_ids = []

        # 缓存结果 / Cache result
        self.clinical_trials_cache[cache_key] = nct_ids

        return nct_ids

    #===========================================================
    # 辅助方法 / Helper Methods
    #===========================================================

    def _determine_approval_status(self, application_data: Dict[str, Any]) -> str:
        """确定批准状态 / Determine approval status"""
        products = application_data.get('products', [])

        if not products:
            return "Unknown"

        # 检查是否有已批准的产品 / Check if there are approved products
        for product in products:
            if product.get('approval_date'):
                return "Approved"

        # 检查是否有临时批准 / Check for tentative approval
        for product in products:
            if product.get('tentative_approval_date'):
                return "Tentatively Approved"

        return "Pending"

    def _extract_supplement_numbers(self, application_data: Dict[str, Any]) -> List[str]:
        """提取补充申请号 / Extract supplement numbers"""
        submissions = application_data.get('submissions', [])
        supplement_numbers = []

        for submission in submissions:
            submission_type = submission.get('submission_type', '')
            if 'supplement' in submission_type.lower():
                submission_number = submission.get('submission_number', '')
                if submission_number:
                    supplement_numbers.append(submission_number)

        return supplement_numbers

    def _validate_entity(self, entity: Dict) -> bool:
        """
        验证实体数据 / Validate entity data

        Args:
            entity: 实体数据 / Entity data

        Returns:
            是否有效 / Whether valid
        """
        # 检查必需字段 / Check required fields
        if 'primary_id' not in entity:
            return False

        if 'properties' not in entity:
            return False

        # 检查实体类型 / Check entity type
        entity_type = entity.get('entity_type')
        valid_types = [
            'regulatory:Approval',
            'regulatory:Submission',
            'rd:Compound',
            'rd:DrugProduct',
            'regulatory:RegulatoryAgency'
        ]

        if entity_type not in valid_types:
            return False

        return True

    def _save_raw_response(self, response: requests.Response):
        """
        保存原始 API 响应 / Save raw API response

        Args:
            response: 响应对象 / Response object
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"response_{timestamp}.json"
            filepath = self.raw_output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved raw response to: {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save raw response: {e}")

    #===========================================================
    # 结果保存方法 / Result Saving Methods
    #===========================================================

    def save_results(
        self,
        entities: Dict[str, List[Dict]],
        relationships: List[Dict],
        output_to: Optional[str] = None
    ) -> Path:
        """
        保存 Drugs@FDA 处理结果 / Save Drugs@FDA processing results

        Args:
            entities: 按类型分组的实体字典 / Entity dictionary grouped by type
            relationships: 关系列表 / Relationship list
            output_to: 自定义输出目录 / Custom output directory

        Returns:
            输出文件路径 / Output file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定输出目录 / Determine output directory
        if output_to:
            output_dir = Path(output_to)
        else:
            output_dir = self.documents_output_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # 按类型保存实体 / Save entities by type
        for entity_type, entity_list in entities.items():
            if not entity_list:
                continue

            type_name = entity_type.replace(':', '_').lower()
            entities_file = output_dir / f"drugsatfda_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entity_list, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(entity_list)} {entity_type} entities to: {entities_file}")

        # 保存关系 / Save relationships
        if relationships:
            relationships_file = output_dir / f"drugsatfda_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(relationships)} relationships to: {relationships_file}")

        # 保存处理摘要 / Save processing summary
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "FDA Drugs@FDA API",
            "timestamp": timestamp,
            "extraction_config": {
                'api_version': self.extraction_config.api_version,
                'page_size': self.extraction_config.page_size,
                'rate_limit': self.extraction_config.rate_limit_per_second,
                'max_applications': self.extraction_config.max_applications,
                'map_unii_to_chembl': self.extraction_config.map_unii_to_chembl,
                'map_to_clinical_trials': self.extraction_config.map_to_clinical_trials
            },
            "statistics": {
                "applications_extracted": self.stats.applications_extracted,
                "products_extracted": self.stats.products_extracted,
                "submissions_extracted": self.stats.submissions_extracted,
                "approvals_extracted": self.stats.approvals_extracted,
                "compounds_extracted": self.stats.compounds_extracted,
                "sponsors_extracted": self.stats.sponsors_extracted,
                "agencies_extracted": self.stats.agencies_extracted,
                "relationships_created": self.stats.relationships_created,
                "cross_domain_relationships": self.stats.cross_domain_relationships,
                "applications_deduplicated": self.stats.applications_deduplicated,
                "processing_time_seconds": self.stats.processing_time_seconds,
                "api_request_time_seconds": self.stats.api_request_time_seconds,
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "retried_requests": self.stats.retried_requests
            },
            "entities_by_type": {
                entity_type: len(entity_list)
                for entity_type, entity_list in entities.items()
            },
            "total_entities": sum(len(entity_list) for entity_list in entities.values()),
            "total_relationships": len(relationships),
            "errors": self.stats.errors,
            "warnings": self.stats.warnings
        }

        summary_file = output_dir / f"drugsatfda_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved processing summary to: {summary_file}")

        return summary_file


#===========================================================
# 命令行接口 / Command Line Interface
#===========================================================

def main():
    """
    命令行主函数 / Command line main function
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='FDA Drugs@FDA API 处理器 / FDA Drugs@FDA API Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:

  # 获取所有申请（前 100 个）
  python -m processors.drugsatfda_processor --mode all --max-applications 100

  # 按品牌名查询
  python -m processors.drugsatfda_processor --mode brand-name --brand-name "Lipitor"

  # 按申请号查询
  python -m processors.drugsatfda_processor --mode application-number --application-number "NDA020709"

  # 按赞助商查询
  python -m processors.drugsatfda_processor --mode sponsor-name --sponsor-name "Pfizer"

  # 自定义输出目录
  python -m processors.drugsatfda_processor --mode all --output /custom/output/path
        """
    )

    parser.add_argument(
        '--mode',
        choices=['all', 'brand-name', 'generic-name', 'application-number', 'sponsor-name'],
        default='all',
        help='处理模式（默认: all）/ Processing mode (default: all)'
    )

    parser.add_argument(
        '--brand-name',
        help='品牌名称 / Brand name'
    )

    parser.add_argument(
        '--generic-name',
        help='通用名称 / Generic name'
    )

    parser.add_argument(
        '--application-number',
        help='申请号 / Application number (e.g., NDA020709)'
    )

    parser.add_argument(
        '--sponsor-name',
        help='赞助商名称 / Sponsor name'
    )

    parser.add_argument(
        '--max-applications',
        type=int,
        help='最大申请数量 / Maximum applications'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        help='最大页数 / Maximum pages'
    )

    parser.add_argument(
        '--page-size',
        type=int,
        default=100,
        help='每页结果数（默认: 100）/ Results per page (default: 100)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='每秒请求数（默认: 1.0）/ Requests per second (default: 1.0)'
    )

    parser.add_argument(
        '--output',
        help='输出目录（默认为 data/processed/documents/drugsatfda/）/ Output directory (default: data/processed/documents/drugsatfda/)'
    )

    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='禁用去重 / Disable deduplication'
    )

    parser.add_argument(
        '--no-cross-domain',
        action='store_true',
        help='禁用交叉域映射 / Disable cross-domain mapping'
    )

    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='保存原始 API 响应 / Save raw API response'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出 / Verbose output'
    )

    args = parser.parse_args()

    # 配置日志 / Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # 构建配置 / Build configuration
    config = {
        'extraction': {
            'api_base_url': 'https://api.fda.gov/drug/drugsfda.json',
            'page_size': args.page_size,
            'rate_limit_per_second': args.rate_limit,
            'max_applications': args.max_applications,
            'max_pages': args.max_pages,
            'deduplicate_by_application_number': not args.no_dedup,
            'map_unii_to_chembl': not args.no_cross_domain,
            'map_to_clinical_trials': not args.no_cross_domain,
            'save_raw_response': args.save_raw
        }
    }

    # 创建处理器 / Create processor
    processor = DrugsAtFDAProcessor(config)

    # 根据模式获取数据 / Fetch data based on mode
    start_time = datetime.now()

    if args.mode == 'brand-name' and args.brand_name:
        # 按品牌名查询 / Query by brand name
        raw_data = processor.fetch_by_brand_name(args.brand_name)
    elif args.mode == 'generic-name' and args.generic_name:
        # 按通用名查询 / Query by generic name
        raw_data = processor.fetch_by_query({'generic_name': args.generic_name})
    elif args.mode == 'application-number' and args.application_number:
        # 按申请号查询 / Query by application number
        application_data = processor.fetch_by_application_number(args.application_number)
        if application_data:
            raw_data = {'results': [application_data]}
        else:
            logger.error(f"Failed to fetch application: {args.application_number}")
            return 1
    elif args.mode == 'sponsor-name' and args.sponsor_name:
        # 按赞助商查询 / Query by sponsor name
        raw_data = processor.fetch_by_sponsor_name(args.sponsor_name)
    else:
        # 获取所有申请 / Fetch all applications
        raw_data = processor.fetch_all_applications()

    if not raw_data or 'results' not in raw_data:
        logger.error("No data fetched")
        return 1

    # 转换数据 / Transform data
    transformed_data = processor.transform(raw_data)

    # 验证数据 / Validate data
    if not processor.validate(transformed_data):
        logger.warning("Data validation failed")

    # 保存结果 / Save results
    entities = transformed_data.get('entities', {})
    relationships = transformed_data.get('relationships', [])

    output_path = processor.save_results(entities, relationships, args.output)

    # 输出结果摘要 / Output result summary
    elapsed_time = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*60}")
    print(f"Drugs@FDA 处理完成 / Processing Complete")
    print(f"{'='*60}")
    print(f"提取的申请 / Applications extracted: {processor.stats.applications_extracted}")
    print(f"提取的产品 / Products extracted: {processor.stats.products_extracted}")
    print(f"提取的提交 / Submissions extracted: {processor.stats.submissions_extracted}")
    print(f"提取的化合物 / Compounds extracted: {processor.stats.compounds_extracted}")
    print(f"提取的实体 / Entities extracted: {sum(len(v) for v in entities.values())}")
    print(f"提取的关系 / Relationships extracted: {len(relationships)}")
    print(f"处理时间 / Processing time: {elapsed_time:.2f} 秒 / seconds")
    print(f"API 请求时间 / API request time: {processor.stats.api_request_time_seconds:.2f} 秒 / seconds")

    print(f"\n详细统计 / Detailed Statistics:")
    print(f"  批准 / Approvals: {processor.stats.approvals_extracted}")
    print(f"  提交 / Submissions: {processor.stats.submissions_extracted}")
    print(f"  化合物 / Compounds: {processor.stats.compounds_extracted}")
    print(f"  产品 / Products: {processor.stats.products_extracted}")
    print(f"  机构 / Agencies: {processor.stats.agencies_extracted}")
    print(f"  交叉域关系 / Cross-domain relationships: {processor.stats.cross_domain_relationships}")
    print(f"  去重申请 / Deduplicated applications: {processor.stats.applications_deduplicated}")

    print(f"\nAPI 请求统计 / API Request Statistics:")
    print(f"  总请求数 / Total requests: {processor.stats.total_requests}")
    print(f"  成功请求 / Successful: {processor.stats.successful_requests}")
    print(f"  失败请求 / Failed: {processor.stats.failed_requests}")
    print(f"  重试请求 / Retries: {processor.stats.retried_requests}")

    if processor.stats.errors:
        print(f"\n错误 / Errors ({len(processor.stats.errors)}):")
        for error in processor.stats.errors[:5]:
            print(f"  - {error}")
        if len(processor.stats.errors) > 5:
            print(f"  ... 还有 {len(processor.stats.errors) - 5} 个错误")

    if processor.stats.warnings:
        print(f"\n警告 / Warnings ({len(processor.stats.warnings)}):")
        for warning in processor.stats.warnings[:5]:
            print(f"  - {warning}")
        if len(processor.stats.warnings) > 5:
            print(f"  ... 还有 {len(processor.stats.warnings) - 5} 个警告")

    print(f"\n输出文件 / Output files: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
