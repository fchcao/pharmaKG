#!/usr/bin/env python3
#===========================================================
# PharmaKG ClinicalTrials.gov API v2 处理器
# Pharmaceutical Knowledge Graph - ClinicalTrials.gov API v2 Processor
#===========================================================
# 版本: v1.0
# 描述: 从 ClinicalTrials.gov API v2 提取临床试验数据
#===========================================================

import logging
import json
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Generator
from enum import Enum
from urllib.parse import urlencode, quote

import requests

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


#===========================================================
# 枚举类型
#===========================================================

class ProcessingMode(str, Enum):
    """处理模式枚举 / Processing Mode Enumeration"""
    FULL_DOWNLOAD = "full_download"  # 全量下载所有试验
    QUERY_BY_DISEASE = "query_by_disease"  # 按疾病查询
    QUERY_BY_PHASE = "query_by_phase"  # 按阶段查询
    QUERY_BY_STATUS = "query_by_status"  # 按状态查询
    INCREMENTAL = "incremental"  # 增量更新


class StudyPhase(str, Enum):
    """临床试验阶段枚举 / Clinical Trial Phase Enumeration"""
    PHASE1 = "Phase 1"
    PHASE2 = "Phase 2"
    PHASE3 = "Phase 3"
    PHASE4 = "Phase 4"
    N_A = "N/A"  # 不适用
    EARLY_PHASE1 = "Early Phase 1"


class StudyStatus(str, Enum):
    """研究状态枚举 / Study Status Enumeration"""
    RECRUITING = "Recruiting"
    NOT_YET_RECRUITING = "Not yet recruiting"
    ACTIVE_NOT_RECRUITING = "Active, not recruiting"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"
    SUSPENDED = "Suspended"
    WITHDRAWN = "Withdrawn"
    ENROLLING_BY_INVITATION = "Enrolling by invitation"
    AVAILABLE = "Available"
    NO_LONGER_AVAILABLE = "No longer available"
    APPROVED_FOR_MARKETING = "Approved for marketing"
    TEMPORARILY_NOT_AVAILABLE = "Temporarily not available"
    UNKNOWN = "Unknown"


#===========================================================
# 配置类
#===========================================================

@dataclass
class ClinicalTrialsExtractionConfig:
    """ClinicalTrials.gov 提取配置 / Extraction Configuration"""
    # API 配置
    api_base_url: str = "https://clinicaltrials.gov/api/v2/studies"
    api_version: str = "v2"
    request_timeout: int = 30  # 请求超时时间（秒）

    # 速率限制配置（ClinicalTrials.gov 限制：1 请求 / 0.5 秒 = 2 请求/秒）
    rate_limit_per_second: float = 2.0  # 每秒请求数
    rate_limit_delay: float = 0.5  # 请求间延迟（秒）

    # 分页配置
    page_size: int = 100  # 每页结果数（最大：100）
    max_pages: Optional[int] = None  # 最大页数限制（用于测试）
    max_studies: Optional[int] = None  # 最大研究数量限制

    # 重试配置
    max_retries: int = 3  # 最大重试次数
    retry_backoff_factor: float = 2.0  # 重试退避因子
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])

    # 查询配置
    query_term: Optional[str] = None  # 搜索词
    query_filters: Dict[str, Any] = field(default_factory=dict)  # 查询过滤器
    fields_to_return: Optional[List[str]] = None  # 返回字段列表

    # 增量更新配置
    incremental_mode: bool = False  # 增量模式
    last_update_date: Optional[str] = None  # 最后更新日期（YYYY-MM-DD）

    # 去重配置
    deduplicate_by_nct_id: bool = True  # 按 NCT ID 去重

    # 交叉域映射配置
    map_to_chembl: bool = True  # 映射干预到 ChEMBL 化合物
    map_to_mondo: bool = True  # 映射条件到 MONDO 疾病

    # 输出配置
    save_raw_response: bool = False  # 保存原始 API 响应
    save_intermediate_batches: bool = True  # 保存中间批次

    # 处理配置
    process_in_batches: bool = True  # 批处理模式
    batch_size: int = 1000  # 批处理大小


@dataclass
class ClinicalTrialsStats:
    """ClinicalTrials.gov 提取统计信息 / Extraction Statistics"""
    # API 请求统计
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0

    # 数据提取统计
    trials_extracted: int = 0
    interventions_extracted: int = 0
    conditions_extracted: int = 0
    sites_extracted: int = 0
    investigators_extracted: int = 0
    sponsors_extracted: int = 0
    outcomes_extracted: int = 0
    eligibility_criteria_extracted: int = 0

    # 关系统计
    relationships_created: int = 0
    cross_domain_relationships: int = 0

    # 去重统计
    trials_deduplicated: int = 0

    # 处理时间
    processing_time_seconds: float = 0.0
    api_request_time_seconds: float = 0.0

    # 错误和警告
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 状态跟踪
    last_processed_nct_id: Optional[str] = None
    last_page_token: Optional[str] = None
    total_studies_available: Optional[int] = None


#===========================================================
# 主处理器类
#===========================================================

class ClinicalTrialsProcessor(BaseProcessor):
    """
    ClinicalTrials.gov API v2 处理器

    提取内容 / Extracted Content:
    - 临床试验（ClinicalTrial）- NCT ID, 标题, 阶段, 状态, 日期等
    - 干预措施（Intervention）- 药物, 程序, 行为等
    - 疾病条件（Condition）- 研究的疾病/状况
    - 研究站点（StudySite）- 设施, 位置, 联系信息
    - 研究者（Investigator）- 主要研究者, 合作研究者
    - 赞助商（Sponsor）- 赞助商, 合作机构
    - 结果（Outcome）- 主要, 次要结果指标
    - 入排标准（EligibilityCriteria）- 纳入/排除标准

    关系类型 / Relationship Types:
    - TESTS_INTERVENTION - ClinicalTrial → Intervention
    - ENROLLS - ClinicalTrial → Subject (aggregate)
    - HAS_PRINCIPAL_INVESTIGATOR - ClinicalTrial → Investigator
    - CONDUCTED_AT_SITE - ClinicalTrial → StudySite
    - SPONSORED_BY - ClinicalTrial → Sponsor
    - TRIAL_FOR_DISEASE - ClinicalTrial → Condition
    - HAS_ARM - ClinicalTrial → Arm
    - HAS_OUTCOME - ClinicalTrial → Outcome
    - HAS_ELIGIBILITY - ClinicalTrial → EligibilityCriteria

    交叉域关系 / Cross-Domain Relationships:
    - TESTED_IN_CLINICAL_TRIAL - Compound → ClinicalTrial (via ChEMBL)
    """

    PROCESSOR_NAME = "ClinicalTrialsProcessor"
    SUPPORTED_FORMATS = []  # API 处理器不需要文件格式
    OUTPUT_SUBDIR = "clinicaltrials"

    # 注意：ClinicalTrials.gov API v2 不支持 fields 参数
    # API 会自动返回所有可用的数据
    # 以下列出的是我们使用的主要字段（供参考）
    API_FIELDS_REFERENCE = [
        # 协议部分字段 / Protocol Section Fields
        "protocolSection.identificationModule.nctId",
        "protocolSection.identificationModule.briefTitle",
        "protocolSection.identificationModule.officialTitle",
        "protocolSection.identificationModule.organization",
        "protocolSection.statusModule.overallStatus",
        "protocolSection.statusModule.startDateStruct",
        "protocolSection.statusModule.completionDateStruct",
        "protocolSection.statusModule.primaryCompletionDateStruct",
        "protocolSection.designModule.phase",
        "protocolSection.designModule.studyType",
        "protocolSection.designModule.enrollmentInfo",
        "protocolSection.armsInterventionsModule.interventions",
        "protocolSection.conditionsModule.conditions",
        "protocolSection.eligibilityModule",
        "protocolSection.contactsLocationsModule.locations",
        "protocolSection.sponsorCollaboratorsModule.leadSponsor",
        "protocolSection.sponsorCollaboratorsModule.responsibleParty",
        "protocolSection.outcomesModule.primaryOutcomes",
        "protocolSection.outcomesModule.secondaryOutcomes",
        "protocolSection.descriptionModule.briefSummary",
        "protocolSection.descriptionModule.detailedDescription"
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 ClinicalTrials.gov 处理器

        Args:
            config: 处理器配置字典
        """
        super().__init__(config)

        # 初始化提取配置
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = ClinicalTrialsExtractionConfig(**extraction_config)

        # 统计信息
        self.stats = ClinicalTrialsStats()

        # 去重集合
        self.seen_nct_ids: Set[str] = set()

        # 交叉域映射缓存
        self.chembl_cache: Dict[str, Optional[str]] = {}  # 干预名 → ChEMBL ID
        self.mondo_cache: Dict[str, Optional[str]] = {}  # 条件名 → MONDO ID

        # 进度跟踪
        self._progress_file = self.data_root / "cache" / f"{self.OUTPUT_SUBDIR}_progress.json"
        self._progress_file.parent.mkdir(parents=True, exist_ok=True)

        # 输出文件路径
        timestamp = datetime.now().strftime("%Y%m%d")
        self.output_trials = self.entities_output_dir / f"clinicaltrials_trials_{timestamp}.json"
        self.output_interventions = self.entities_output_dir / f"clinicaltrials_interventions_{timestamp}.json"
        self.output_conditions = self.entities_output_dir / f"clinicaltrials_conditions_{timestamp}.json"
        self.output_sites = self.entities_output_dir / f"clinicaltrials_sites_{timestamp}.json"
        self.output_investigators = self.entities_output_dir / f"clinicaltrials_investigators_{timestamp}.json"
        self.output_sponsors = self.entities_output_dir / f"clinicaltrials_sponsors_{timestamp}.json"
        self.output_outcomes = self.entities_output_dir / f"clinicaltrials_outcomes_{timestamp}.json"
        self.output_eligibility = self.entities_output_dir / f"clinicaltrials_eligibility_{timestamp}.json"
        self.output_relationships = self.relationships_output_dir / f"clinicaltrials_relationships_{timestamp}.json"
        self.output_summary = self.documents_output_dir / f"clinicaltrials_summary_{timestamp}.json"

        # 原始响应输出目录
        if self.extraction_config.save_raw_response:
            self.raw_output_dir = self.data_root / "sources" / "clinicaltrials" / "raw_responses"
            self.raw_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    #===========================================================
    # BaseProcessor 抽象方法实现
    #===========================================================

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录（API 处理器不需要扫描文件）

        Args:
            source_path: 源目录路径（忽略）

        Returns:
            空列表（API 处理器不处理文件）
        """
        logger.info("API processor does not scan files")
        return []

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        提取数据（API 处理器不处理文件，使用 fetch_all_studies）

        Args:
            file_path: 文件路径（忽略）

        Returns:
            空字典
        """
        logger.warning("Use fetch_all_studies() or fetch_by_query() for API extraction")
        return {}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据为知识图谱格式

        Args:
            raw_data: 原始提取数据（API 响应）

        Returns:
            转换后的实体和关系数据
        """
        if 'error' in raw_data:
            return raw_data

        logger.info("Transforming extracted data")

        transformed = {
            'entities': {
                'clinical:ClinicalTrial': [],
                'clinical:Intervention': [],
                'clinical:Condition': [],
                'clinical:StudySite': [],
                'clinical:Investigator': [],
                'clinical:Sponsor': [],
                'clinical:Outcome': [],
                'clinical:EligibilityCriteria': []
            },
            'relationships': []
        }

        # 转换试验数据
        for study_data in raw_data.get('studies', []):
            entities, relationships = self._transform_study(study_data)

            # 添加实体到对应类型
            for entity in entities:
                entity_type = entity.get('entity_type')
                if entity_type in transformed['entities']:
                    transformed['entities'][entity_type].append(entity)

            # 添加关系
            transformed['relationships'].extend(relationships)

        logger.info(f"Transformed {len(raw_data.get('studies', []))} studies into "
                   f"{sum(len(v) for v in transformed['entities'].values())} entities "
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

    #===========================================================
    # API 数据获取方法
    #===========================================================

    def fetch_all_studies(
        self,
        query_term: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_studies: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取所有研究（全量下载）

        Args:
            query_term: 搜索词（可选）
            filters: 查询过滤器（可选）
            max_studies: 最大研究数量（可选）

        Returns:
            提取的研究数据
        """
        logger.info("Starting full download of ClinicalTrials.gov data")

        # 使用配置或参数
        query_term = query_term or self.extraction_config.query_term
        filters = filters or self.extraction_config.query_filters
        max_studies = max_studies or self.extraction_config.max_studies

        # 构建查询参数
        params = self._build_query_params(query_term, filters)

        # 分页获取数据
        all_studies = []
        next_page_token = None
        page_count = 0

        # 加载进度
        progress = self._load_progress()
        if progress and progress.get('next_page_token'):
            next_page_token = progress['next_page_token']
            logger.info(f"Resuming from page token: {next_page_token}")

        start_time = datetime.now()

        while True:
            # 检查限制
            if max_studies and len(all_studies) >= max_studies:
                logger.info(f"Reached maximum studies limit: {max_studies}")
                break

            if self.extraction_config.max_pages and page_count >= self.extraction_config.max_pages:
                logger.info(f"Reached maximum pages limit: {self.extraction_config.max_pages}")
                break

            # 获取一页数据
            page_data = self._fetch_page(params, next_page_token)

            if not page_data or 'studies' not in page_data:
                logger.warning("No more studies or error occurred")
                break

            studies = page_data.get('studies', [])
            all_studies.extend(studies)

            page_count += 1
            self.stats.trials_extracted = len(all_studies)

            # 更新统计
            if 'totalStudies' in page_data:
                self.stats.total_studies_available = page_data['totalStudies']

            logger.info(f"Fetched page {page_count}: {len(studies)} studies, "
                       f"total: {len(all_studies)}")

            # 保存进度
            self._save_progress({
                'next_page_token': next_page_token,
                'studies_fetched': len(all_studies),
                'last_update': datetime.now().isoformat()
            })

            # 检查是否有下一页
            next_page_token = page_data.get('nextPageToken')
            if not next_page_token:
                logger.info("No more pages to fetch")
                break

        # 计算处理时间
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.stats.processing_time_seconds = elapsed_time

        logger.info(f"Completed full download: {len(all_studies)} studies in {elapsed_time:.2f} seconds")

        return {
            'studies': all_studies,
            'total_studies': len(all_studies),
            'extraction_timestamp': datetime.now().isoformat(),
            'processing_time_seconds': elapsed_time
        }

    def fetch_by_query(
        self,
        query_term: str,
        filters: Optional[Dict[str, Any]] = None,
        max_studies: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        按查询获取研究

        Args:
            query_term: 搜索词
            filters: 查询过滤器（可选）
            max_studies: 最大研究数量（可选）

        Returns:
            提取的研究数据
        """
        logger.info(f"Fetching studies by query: {query_term}")

        return self.fetch_all_studies(query_term, filters, max_studies)

    def fetch_by_nct_id(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        按 NCT ID 获取单个研究

        Args:
            nct_id: NCT ID（如：NCT00001234）

        Returns:
            研究数据或 None
        """
        logger.info(f"Fetching study by NCT ID: {nct_id}")

        # 构建 URL
        url = f"{self.extraction_config.api_base_url}/{nct_id}"

        # 构建查询参数
        params = {
            'format': 'json',
            'fields': ','.join(self.API_FIELDS)
        }

        # 发送请求
        response = self._make_request(url, params)

        if response and 'study' in response:
            return response['study']

        return None

    def fetch_incremental(
        self,
        last_update_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        增量获取更新的研究

        Args:
            last_update_date: 最后更新日期（YYYY-MM-DD 格式）

        Returns:
            提取的研究数据
        """
        last_update_date = last_update_date or self.extraction_config.last_update_date

        if not last_update_date:
            logger.warning("No last update date provided for incremental update")
            return {}

        logger.info(f"Fetching incremental updates since: {last_update_date}")

        # 构建过滤器：只获取在该日期之后更新的研究
        filters = {
            'filter': {
                'value': {
                    'expr': {
                        'date': {
                            'minDate': last_update_date,
                            'maxDate': datetime.now().strftime('%Y-%m-%d')
                        }
                    }
                },
                'field': 'LastUpdatePostDate',
                'type': 'date'
            }
        }

        return self.fetch_all_studies(filters=filters)

    #===========================================================
    # API 请求处理方法
    #===========================================================

    def _build_query_params(
        self,
        query_term: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        构建查询参数

        Args:
            query_term: 搜索词
            filters: 过滤器

        Returns:
            查询参数字典
        """
        params = {
            'pageSize': str(self.extraction_config.page_size)
        }

        # 注意：API v2 不支持 fields 参数，API 会返回所有数据
        # 如果需要过滤字段，应该在本地处理

        # 添加搜索词
        if query_term:
            params['query.term'] = query_term

        # 添加过滤器
        if filters:
            for key, value in filters.items():
                if key == 'filter':
                    # 处理复杂过滤器
                    params[key] = json.dumps(value)
                else:
                    params[key] = str(value)

        return params

    def _fetch_page(
        self,
        params: Dict[str, str],
        page_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取单页数据

        Args:
            params: 查询参数
            page_token: 分页令牌

        Returns:
            页面数据或 None
        """
        # 添加分页令牌
        if page_token:
            params['pageToken'] = page_token

        # 构建 URL
        url = f"{self.extraction_config.api_base_url}?{urlencode(params, doseq=True)}"

        # 发送请求
        response = self._make_request(url)

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
        发送 API 请求（带重试和速率限制）

        Args:
            url: 请求 URL
            params: 查询参数（可选，如果已包含在 URL 中则为 None）

        Returns:
            响应数据或 None
        """
        max_retries = self.extraction_config.max_retries
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            # 速率限制：在请求之间延迟
            if self.stats.total_requests > 0:
                time.sleep(self.extraction_config.rate_limit_delay)

            try:
                # 记录请求时间
                request_start = time.time()

                # 发送请求
                if params:
                    response = requests.get(
                        url,
                        params=params,
                        timeout=self.extraction_config.request_timeout
                    )
                else:
                    response = requests.get(
                        url,
                        timeout=self.extraction_config.request_timeout
                    )

                # 记录请求时间
                request_time = time.time() - request_start
                self.stats.api_request_time_seconds += request_time
                self.stats.total_requests += 1

                # 检查响应状态
                if response.status_code == 200:
                    # 保存原始响应（如果配置）
                    if self.extraction_config.save_raw_response:
                        self._save_raw_response(response)

                    return response.json()

                # 处理错误状态码
                if response.status_code in self.extraction_config.retry_status_codes:
                    retry_count += 1
                    self.stats.retried_requests += 1

                    # 计算退避延迟
                    backoff_delay = self.extraction_config.retry_backoff_factor ** retry_count
                    logger.warning(f"Request failed with status {response.status_code}, "
                                 f"retrying in {backoff_delay}s (attempt {retry_count}/{max_retries})")
                    time.sleep(backoff_delay)
                    continue

                # 其他错误
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

        # 所有重试都失败
        error_msg = f"Request failed after {max_retries} retries: {last_error}"
        logger.error(error_msg)
        self.stats.errors.append(error_msg)
        return None

    #===========================================================
    # 数据转换方法
    #===========================================================

    def _transform_study(self, study_data: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """
        转换单个研究数据

        Args:
            study_data: 原始研究数据

        Returns:
            (实体列表, 关系列表)
        """
        entities = []
        relationships = []

        protocol_section = study_data.get('protocolSection', {})
        identification_module = protocol_section.get('identificationModule', {})
        status_module = protocol_section.get('statusModule', '')
        design_module = protocol_section.get('designModule', '')
        arms_interventions_module = protocol_section.get('armsInterventionsModule', '')
        conditions_module = protocol_section.get('conditionsModule', '')
        eligibility_module = protocol_section.get('eligibilityModule', '')
        contacts_locations_module = protocol_section.get('contactsLocationsModule', '')

        # 提取 NCT ID
        nct_id = identification_module.get('nctId')

        # 去重检查
        if self.extraction_config.deduplicate_by_nct_id and nct_id in self.seen_nct_ids:
            self.stats.trials_deduplicated += 1
            return [], []

        if nct_id:
            self.seen_nct_ids.add(nct_id)
            self.stats.last_processed_nct_id = nct_id

        # 1. 创建 ClinicalTrial 实体
        trial_entity = self._create_trial_entity(study_data)
        if trial_entity:
            entities.append(trial_entity)

        # 2. 创建 Intervention 实体和关系
        intervention_entities, intervention_rels = self._create_interventions(study_data, nct_id)
        entities.extend(intervention_entities)
        relationships.extend(intervention_rels)

        # 3. 创建 Condition 实体和关系
        condition_entities, condition_rels = self._create_conditions(study_data, nct_id)
        entities.extend(condition_entities)
        relationships.extend(condition_rels)

        # 4. 创建 StudySite 实体和关系
        site_entities, site_rels = self._create_sites(study_data, nct_id)
        entities.extend(site_entities)
        relationships.extend(site_rels)

        # 5. 创建 Investigator 实体和关系
        investigator_entities, investigator_rels = self._create_investigators(study_data, nct_id)
        entities.extend(investigator_entities)
        relationships.extend(investigator_rels)

        # 6. 创建 Sponsor 实体和关系
        sponsor_entities, sponsor_rels = self._create_sponsors(study_data, nct_id)
        entities.extend(sponsor_entities)
        relationships.extend(sponsor_rels)

        # 7. 创建 Outcome 实体和关系
        outcome_entities, outcome_rels = self._create_outcomes(study_data, nct_id)
        entities.extend(outcome_entities)
        relationships.extend(outcome_rels)

        # 8. 创建 EligibilityCriteria 实体和关系
        eligibility_entity, eligibility_rels = self._create_eligibility(study_data, nct_id)
        if eligibility_entity:
            entities.append(eligibility_entity)
        relationships.extend(eligibility_rels)

        # 9. 创建交叉域关系
        cross_domain_rels = self._create_cross_domain_relationships(study_data, nct_id)
        relationships.extend(cross_domain_rels)

        return entities, relationships

    def _create_trial_entity(self, study_data: Dict[str, Any]) -> Optional[Dict]:
        """创建临床试验实体"""
        try:
            protocol_section = study_data.get('protocolSection', {})
            identification_module = protocol_section.get('identificationModule', {})
            status_module = protocol_section.get('statusModule', {})
            design_module = protocol_section.get('designModule', {})

            nct_id = identification_module.get('nctId')

            # 生成主标识符
            primary_id = f"ClinicalTrial-{nct_id}" if nct_id else f"ClinicalTrial-{id(study_data)}"

            # 构建标识符字典
            identifiers = {
                'NCT': nct_id,
                'org_study_id': identification_module.get('orgStudyId'),
                'secondary_ids': [id.get('id') for id in identification_module.get('secondaryIdList', [])]
            }

            # 解析日期
            start_date = self._parse_date(status_module.get('startDateStruct'))
            completion_date = self._parse_date(status_module.get('completionDateStruct'))
            primary_completion_date = self._parse_date(status_module.get('primaryCompletionDateStruct'))

            # 构建属性字典
            properties = {
                'nct_id': nct_id,
                'brief_title': identification_module.get('briefTitle'),
                'official_title': identification_module.get('officialTitle'),
                'organization': identification_module.get('organization', {}).get('fullName'),
                'org_study_id': identification_module.get('orgStudyIdInfo', {}).get('id'),
                'study_phase': self._parse_study_phase(design_module.get('phase')),
                'study_status': status_module.get('overallStatus'),
                'start_date': start_date,
                'completion_date': completion_date,
                'primary_completion_date': primary_completion_date,
                'enrollment': design_module.get('enrollmentInfo', {}).get('count'),
                'study_type': design_module.get('studyType'),
                'study_design': self._parse_study_design(design_module.get('designInfo')),
                'brief_summary': protocol_section.get('descriptionModule', {}).get('briefSummary'),
                'detailed_description': protocol_section.get('descriptionModule', {}).get('detailedDescription'),
                'source': identification_module.get('organization', {}).get('fullName'),
                'last_update_posted': self._parse_date(status_module.get('lastUpdatePostDateStruct')),
                'first_posted': self._parse_date(status_module.get('studyFirstPostDateStruct')),
                'has_results': study_data.get('derivedSection', {}).get('hasResults', False),
                'data_source': 'ClinicalTrials.gov',
                'api_version': self.extraction_config.api_version
            }

            self.stats.trials_extracted += 1

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'clinical:ClinicalTrial'
            }

        except Exception as e:
            logger.warning(f"Failed to create trial entity: {e}")
            return None

    def _create_interventions(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建干预措施实体和关系"""
        entities = []
        relationships = []

        try:
            arms_interventions = study_data.get('protocolSection', {}).get('armsInterventionsModule', {})
            interventions_list = arms_interventions.get('interventions', [])

            for intervention_data in interventions_list:
                # 创建干预实体
                intervention_name = intervention_data.get('name', 'Unknown')
                intervention_type = intervention_data.get('type', 'Unknown')

                primary_id = f"Intervention-{trial_nct_id}-{intervention_name}-{intervention_type}"

                # 清理 ID（移除特殊字符）
                primary_id = primary_id.replace(' ', '_').replace('/', '_')

                entity = {
                    'primary_id': primary_id,
                    'identifiers': {
                        'name': intervention_name,
                        'type': intervention_type,
                        'trial_nct_id': trial_nct_id
                    },
                    'properties': {
                        'intervention_name': intervention_name,
                        'intervention_type': intervention_type,
                        'description': intervention_data.get('description'),
                        'arm_group_labels': intervention_data.get('armGroupLabels', []),
                        'other_names': intervention_data.get('otherNames', [])
                    },
                    'entity_type': 'clinical:Intervention'
                }

                entities.append(entity)
                self.stats.interventions_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'TESTS_INTERVENTION',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': primary_id,
                    'properties': {
                        'intervention_type': intervention_type,
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create interventions: {e}")

        return entities, relationships

    def _create_conditions(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建疾病条件实体和关系"""
        entities = []
        relationships = []

        try:
            conditions_module = study_data.get('protocolSection', {}).get('conditionsModule', {})
            conditions_list = conditions_module.get('conditions', [])

            for condition_data in conditions_list:
                condition_name = condition_data.get('name', 'Unknown')

                primary_id = f"Condition-{condition_name}".replace(' ', '_')

                entity = {
                    'primary_id': primary_id,
                    'identifiers': {
                        'name': condition_name
                    },
                    'properties': {
                        'condition_name': condition_name,
                        'mesh_terms': condition_data.get('meshTerms', [])
                    },
                    'entity_type': 'clinical:Condition'
                }

                entities.append(entity)
                self.stats.conditions_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'TRIAL_FOR_DISEASE',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': primary_id,
                    'properties': {
                        'condition_name': condition_name,
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create conditions: {e}")

        return entities, relationships

    def _create_sites(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建研究站点实体和关系"""
        entities = []
        relationships = []

        try:
            contacts_locations = study_data.get('protocolSection', {}).get('contactsLocationsModule', {})
            locations_list = contacts_locations.get('locations', [])

            for idx, location_data in enumerate(locations_list):
                facility = location_data.get('facility', {})
                geo_point = location_data.get('geoPoint', {})

                facility_name = facility.get('name', 'Unknown Facility')
                location_id = f"Site-{trial_nct_id}-{idx}".replace(' ', '_')

                entity = {
                    'primary_id': location_id,
                    'identifiers': {
                        'name': facility_name,
                        'trial_nct_id': trial_nct_id
                    },
                    'properties': {
                        'facility_name': facility_name,
                        'city': location_data.get('city'),
                        'state': location_data.get('state'),
                        'country': location_data.get('country'),
                        'latitude': geo_point.get('lat'),
                        'longitude': geo_point.get('lon'),
                        'status': location_data.get('status'),
                        'investigator_name': location_data.get('centralContact', {}).get('name'),
                        'investigator_email': location_data.get('centralContact', {}).get('email'),
                        'investigator_phone': location_data.get('centralContact', {}).get('phone')
                    },
                    'entity_type': 'clinical:StudySite'
                }

                entities.append(entity)
                self.stats.sites_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'CONDUCTED_AT_SITE',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': location_id,
                    'properties': {
                        'facility_name': facility_name,
                        'location': f"{location_data.get('city', '')}, {location_data.get('state', '')}, {location_data.get('country', '')}",
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create sites: {e}")

        return entities, relationships

    def _create_investigators(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建研究者实体和关系"""
        entities = []
        relationships = []

        try:
            responsible_party = study_data.get('protocolSection', {}).get('sponsorCollaboratorsModule', {}).get('responsibleParty', {})
            contacts_locations = study_data.get('protocolSection', {}).get('contactsLocationsModule', {})

            # 提取主要研究者
            # 负责人信息
            responsible_party_type = responsible_party.get('type')
            pi_name = None
            pi_title = None
            pi_organization = None

            if responsible_party_type == 'SPONSOR_INVESTIGATOR':
                pi_name = responsible_party.get('investigatorFullName')
                pi_title = responsible_party.get('investigatorTitle')
                pi_organization = responsible_party.get('investigatorAffiliation')
            elif responsible_party_type == 'PRINCIPAL_INVESTIGATOR':
                pi_name = responsible_party.get('name')
                pi_title = responsible_party.get('title')
                pi_organization = responsible_party.get('affiliation')

            if pi_name:
                investigator_id = f"Investigator-{pi_name}".replace(' ', '_')

                entity = {
                    'primary_id': investigator_id,
                    'identifiers': {
                        'name': pi_name
                    },
                    'properties': {
                        'name': pi_name,
                        'role': 'Principal Investigator',
                        'title': pi_title,
                        'organization': pi_organization
                    },
                    'entity_type': 'clinical:Investigator'
                }

                entities.append(entity)
                self.stats.investigators_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'HAS_PRINCIPAL_INVESTIGATOR',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': investigator_id,
                    'properties': {
                        'role': 'Principal Investigator',
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

            # 提取中心联系人（通常是主要研究者或研究协调员）
            central_contacts = contacts_locations.get('centralContacts', [])
            for idx, contact in enumerate(central_contacts):
                contact_name = contact.get('name')
                if contact_name and contact_name != pi_name:  # 避免重复
                    investigator_id = f"Investigator-{trial_nct_id}-{idx}".replace(' ', '_')

                    entity = {
                        'primary_id': investigator_id,
                        'identifiers': {
                            'name': contact_name
                        },
                        'properties': {
                            'name': contact_name,
                            'role': contact.get('role', 'Sub-Investigator'),
                            'email': contact.get('email'),
                            'phone': contact.get('phone')
                        },
                        'entity_type': 'clinical:Investigator'
                    }

                    entities.append(entity)
                    self.stats.investigators_extracted += 1

        except Exception as e:
            logger.warning(f"Failed to create investigators: {e}")

        return entities, relationships

    def _create_sponsors(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建赞助商实体和关系"""
        entities = []
        relationships = []

        try:
            sponsor_collaborators = study_data.get('protocolSection', {}).get('sponsorCollaboratorsModule', {})

            # 提取主要赞助商
            lead_sponsor = sponsor_collaborators.get('leadSponsor', {})
            sponsor_name = lead_sponsor.get('name')
            sponsor_class = lead_sponsor.get('class')  # API v2 使用 'class' 而不是 'agencyClass'

            if sponsor_name:
                sponsor_id = f"Sponsor-{sponsor_name}".replace(' ', '_')

                entity = {
                    'primary_id': sponsor_id,
                    'identifiers': {
                        'name': sponsor_name
                    },
                    'properties': {
                        'sponsor_name': sponsor_name,
                        'agency_class': sponsor_class,
                        'sponsor_type': 'Lead Sponsor'
                    },
                    'entity_type': 'clinical:Sponsor'
                }

                entities.append(entity)
                self.stats.sponsors_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'SPONSORED_BY',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': sponsor_id,
                    'properties': {
                        'sponsor_type': 'Lead Sponsor',
                        'agency_class': sponsor_class,
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

            # 提取合作机构
            collaborators = sponsor_collaborators.get('collaborators', [])
            for collaborator in collaborators:
                collaborator_name = collaborator.get('name')
                collaborator_class = collaborator.get('class')  # API v2 使用 'class' 而不是 'agencyClass'

                if collaborator_name:
                    collaborator_id = f"Sponsor-{collaborator_name}".replace(' ', '_')

                    entity = {
                        'primary_id': collaborator_id,
                        'identifiers': {
                            'name': collaborator_name
                        },
                        'properties': {
                            'sponsor_name': collaborator_name,
                            'agency_class': collaborator_class,
                            'sponsor_type': 'Collaborator'
                        },
                        'entity_type': 'clinical:Sponsor'
                    }

                    entities.append(entity)
                    self.stats.sponsors_extracted += 1

                    # 创建关系
                    relationship = {
                        'relationship_type': 'SPONSORED_BY',
                        'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                        'target_entity_id': collaborator_id,
                        'properties': {
                            'sponsor_type': 'Collaborator',
                            'agency_class': collaborator_class,
                            'data_source': 'ClinicalTrials.gov'
                        },
                        'source': 'ClinicalTrials.gov'
                    }

                    relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create sponsors: {e}")

        return entities, relationships

    def _create_outcomes(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建结果实体和关系"""
        entities = []
        relationships = []

        try:
            outcomes_module = study_data.get('protocolSection', {}).get('outcomesModule', {})

            # 提取主要结果
            primary_outcomes = outcomes_module.get('primaryOutcomes', [])
            for idx, outcome in enumerate(primary_outcomes):
                outcome_id = f"Outcome-{trial_nct_id}-primary-{idx}".replace(' ', '_')

                entity = {
                    'primary_id': outcome_id,
                    'identifiers': {
                        'measure': outcome.get('measure', 'Unknown')
                    },
                    'properties': {
                        'outcome_type': 'Primary',
                        'measure': outcome.get('measure'),
                        'description': outcome.get('description'),
                        'time_frame': outcome.get('timeFrame')
                    },
                    'entity_type': 'clinical:Outcome'
                }

                entities.append(entity)
                self.stats.outcomes_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'HAS_OUTCOME',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': outcome_id,
                    'properties': {
                        'outcome_type': 'Primary',
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

            # 提取次要结果
            secondary_outcomes = outcomes_module.get('secondaryOutcomes', [])
            for idx, outcome in enumerate(secondary_outcomes):
                outcome_id = f"Outcome-{trial_nct_id}-secondary-{idx}".replace(' ', '_')

                entity = {
                    'primary_id': outcome_id,
                    'identifiers': {
                        'measure': outcome.get('measure', 'Unknown')
                    },
                    'properties': {
                        'outcome_type': 'Secondary',
                        'measure': outcome.get('measure'),
                        'description': outcome.get('description'),
                        'time_frame': outcome.get('timeFrame')
                    },
                    'entity_type': 'clinical:Outcome'
                }

                entities.append(entity)
                self.stats.outcomes_extracted += 1

                # 创建关系
                relationship = {
                    'relationship_type': 'HAS_OUTCOME',
                    'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                    'target_entity_id': outcome_id,
                    'properties': {
                        'outcome_type': 'Secondary',
                        'data_source': 'ClinicalTrials.gov'
                    },
                    'source': 'ClinicalTrials.gov'
                }

                relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create outcomes: {e}")

        return entities, relationships

    def _create_eligibility(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """创建入排标准实体和关系"""
        entity = None
        relationships = []

        try:
            eligibility_module = study_data.get('protocolSection', {}).get('eligibilityModule', {})

            eligibility_id = f"EligibilityCriteria-{trial_nct_id}".replace(' ', '_')

            # 解析入排标准
            eligibility_text = eligibility_module.get('eligibilityCriteria', '')
            inclusion_criteria = []
            exclusion_criteria = []

            if eligibility_text:
                # 简单解析（实际应用中可能需要更复杂的解析）
                criteria_lines = eligibility_text.split('\n')
                current_section = None

                for line in criteria_lines:
                    line = line.strip()
                    if not line:
                        continue

                    if 'inclusion' in line.lower() or 'include' in line.lower():
                        current_section = 'inclusion'
                        continue
                    elif 'exclusion' in line.lower() or 'exclude' in line.lower():
                        current_section = 'exclusion'
                        continue

                    if current_section == 'inclusion':
                        inclusion_criteria.append(line)
                    elif current_section == 'exclusion':
                        exclusion_criteria.append(line)

            entity = {
                'primary_id': eligibility_id,
                'identifiers': {
                    'trial_nct_id': trial_nct_id
                },
                'properties': {
                    'inclusion_criteria': inclusion_criteria,
                    'exclusion_criteria': exclusion_criteria,
                    'eligibility_criteria_text': eligibility_text,
                    'gender': eligibility_module.get('sex'),
                    'minimum_age': eligibility_module.get('minimumAge'),
                    'maximum_age': eligibility_module.get('maximumAge'),
                    'healthy_volunteers': eligibility_module.get('healthyVolunteers'),
                    'population': eligibility_module.get('population'),
                    'study_population': eligibility_module.get('studyPopulation')
                },
                'entity_type': 'clinical:EligibilityCriteria'
            }

            self.stats.eligibility_criteria_extracted += 1

            # 创建关系
            relationship = {
                'relationship_type': 'HAS_ELIGIBILITY',
                'source_entity_id': f"ClinicalTrial-{trial_nct_id}",
                'target_entity_id': eligibility_id,
                'properties': {
                    'data_source': 'ClinicalTrials.gov'
                },
                'source': 'ClinicalTrials.gov'
            }

            relationships.append(relationship)

        except Exception as e:
            logger.warning(f"Failed to create eligibility criteria: {e}")

        return entity, relationships

    def _create_cross_domain_relationships(
        self,
        study_data: Dict[str, Any],
        trial_nct_id: str
    ) -> List[Dict]:
        """创建交叉域关系"""
        relationships = []

        try:
            # 映射干预到 ChEMBL 化合物
            if self.extraction_config.map_to_chembl:
                arms_interventions = study_data.get('protocolSection', {}).get('armsInterventionsModule', {})
                interventions_list = arms_interventions.get('interventions', [])

                for intervention in interventions_list:
                    if intervention.get('type') == 'Drug':
                        intervention_name = intervention.get('name')
                        if intervention_name:
                            # 查找 ChEMBL ID
                            chembl_id = self._map_intervention_to_chembl(intervention_name)
                            if chembl_id:
                                # 创建交叉域关系
                                relationship = {
                                    'relationship_type': 'TESTED_IN_CLINICAL_TRIAL',
                                    'source_entity_id': f"Compound-{chembl_id}",
                                    'target_entity_id': f"ClinicalTrial-{trial_nct_id}",
                                    'properties': {
                                        'intervention_name': intervention_name,
                                        'mapping_confidence': 'high',
                                        'data_source': 'ClinicalTrials.gov',
                                        'mapped_via': 'intervention_name'
                                    },
                                    'source': 'ClinicalTrials.gov-ChEMBL-Mapping'
                                }
                                relationships.append(relationship)
                                self.stats.cross_domain_relationships += 1

            # 映射条件到 MONDO 疾病
            if self.extraction_config.map_to_mondo:
                conditions_module = study_data.get('protocolSection', {}).get('conditionsModule', {})
                conditions_list = conditions_module.get('conditions', [])

                for condition in conditions_list:
                    condition_name = condition.get('name')
                    if condition_name:
                        # 查找 MONDO ID
                        mondo_id = self._map_condition_to_mondo(condition_name)
                        if mondo_id:
                            # 可以在这里创建关系，如果需要的话
                            pass

        except Exception as e:
            logger.warning(f"Failed to create cross-domain relationships: {e}")

        return relationships

    #===========================================================
    # 交叉域映射方法
    #===========================================================

    def _map_intervention_to_chembl(self, intervention_name: str) -> Optional[str]:
        """
        将干预名称映射到 ChEMBL 化合物 ID

        Args:
            intervention_name: 干预名称

        Returns:
            ChEMBL ID 或 None
        """
        # 检查缓存
        if intervention_name in self.chembl_cache:
            return self.chembl_cache[intervention_name]

        # 这里应该实现实际的映射逻辑
        # 例如：通过本地 ChEMBL 数据库查询或 API 调用
        # 目前返回 None 作为占位符

        chembl_id = None

        # 缓存结果
        self.chembl_cache[intervention_name] = chembl_id

        return chembl_id

    def _map_condition_to_mondo(self, condition_name: str) -> Optional[str]:
        """
        将条件名称映射到 MONDO 疾病 ID

        Args:
            condition_name: 条件名称

        Returns:
            MONDO ID 或 None
        """
        # 检查缓存
        if condition_name in self.mondo_cache:
            return self.mondo_cache[condition_name]

        # 这里应该实现实际的映射逻辑
        # 例如：通过 MONDO API 或本地映射文件
        # 目前返回 None 作为占位符

        mondo_id = None

        # 缓存结果
        self.mondo_cache[condition_name] = mondo_id

        return mondo_id

    #===========================================================
    # 辅助方法
    #===========================================================

    def _parse_date(self, date_struct: Optional[Dict]) -> Optional[str]:
        """
        解析日期结构

        Args:
            date_struct: 日期结构字典

        Returns:
            ISO 格式日期字符串或 None
        """
        if not date_struct:
            return None

        date_str = date_struct.get('date')
        if date_str:
            return date_str

        return None

    def _parse_study_phase(self, phase_str: Optional[str]) -> str:
        """
        解析研究阶段

        Args:
            phase_str: 阶段字符串

        Returns:
            标准化的阶段字符串
        """
        if not phase_str:
            return StudyPhase.N_A.value

        # 标准化阶段名称
        phase_mapping = {
            'PHASE1': StudyPhase.PHASE1.value,
            'PHASE2': StudyPhase.PHASE2.value,
            'PHASE3': StudyPhase.PHASE3.value,
            'PHASE4': StudyPhase.PHASE4.value,
            'EARLY_PHASE1': StudyPhase.EARLY_PHASE1.value,
            'N/A': StudyPhase.N_A.value
        }

        phase_upper = phase_str.upper().replace(' ', '')
        return phase_mapping.get(phase_upper, phase_str)

    def _parse_study_design(self, design_info: Optional[Dict]) -> Optional[Dict]:
        """
        解析研究设计信息

        Args:
            design_info: 设计信息字典

        Returns:
            标准化的设计信息字典
        """
        if not design_info:
            return None

        return {
            'primary_purpose': design_info.get('primaryPurpose'),
            'observational_model': design_info.get('observationalModel'),
            'time_perspective': design_info.get('timePerspective'),
            'masking': design_info.get('masking'),
            'masking_description': design_info.get('maskingDescription'),
            'allocation': design_info.get('allocation'),
            'subject_masked': design_info.get('subjectMasked'),
            'caregiver_masked': design_info.get('caregiverMasked'),
            'investigator_masked': design_info.get('investigatorMasked'),
            'outcome_assessor_masked': design_info.get('outcomeAssessorMasked')
        }

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
        valid_types = [
            'clinical:ClinicalTrial',
            'clinical:Intervention',
            'clinical:Condition',
            'clinical:StudySite',
            'clinical:Investigator',
            'clinical:Sponsor',
            'clinical:Outcome',
            'clinical:EligibilityCriteria'
        ]

        if entity_type not in valid_types:
            return False

        return True

    def _save_raw_response(self, response: requests.Response):
        """
        保存原始 API 响应

        Args:
            response: 响应对象
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

    def _load_progress(self) -> Optional[Dict]:
        """
        加载进度信息

        Returns:
            进度信息字典或 None
        """
        try:
            if self._progress_file.exists():
                with open(self._progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load progress: {e}")

        return None

    def _save_progress(self, progress: Dict):
        """
        保存进度信息

        Args:
            progress: 进度信息字典
        """
        try:
            with open(self._progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save progress: {e}")

    #===========================================================
    # 结果保存方法
    #===========================================================

    def save_results(
        self,
        entities: Dict[str, List[Dict]],
        relationships: List[Dict],
        output_to: Optional[str] = None
    ) -> Path:
        """
        保存 ClinicalTrials.gov 处理结果

        Args:
            entities: 按类型分组的实体字典
            relationships: 关系列表
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
        for entity_type, entity_list in entities.items():
            if not entity_list:
                continue

            type_name = entity_type.replace('clinical:', '').lower()
            entities_file = output_dir / f"clinicaltrials_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entity_list, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(entity_list)} {entity_type} entities to: {entities_file}")

        # 保存关系
        if relationships:
            relationships_file = output_dir / f"clinicaltrials_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(relationships)} relationships to: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "ClinicalTrials.gov API v2",
            "timestamp": timestamp,
            "extraction_config": {
                'api_version': self.extraction_config.api_version,
                'page_size': self.extraction_config.page_size,
                'rate_limit': self.extraction_config.rate_limit_per_second,
                'max_studies': self.extraction_config.max_studies,
                'map_to_chembl': self.extraction_config.map_to_chembl,
                'map_to_mondo': self.extraction_config.map_to_mondo
            },
            "statistics": {
                "trials_extracted": self.stats.trials_extracted,
                "interventions_extracted": self.stats.interventions_extracted,
                "conditions_extracted": self.stats.conditions_extracted,
                "sites_extracted": self.stats.sites_extracted,
                "investigators_extracted": self.stats.investigators_extracted,
                "sponsors_extracted": self.stats.sponsors_extracted,
                "outcomes_extracted": self.stats.outcomes_extracted,
                "eligibility_criteria_extracted": self.stats.eligibility_criteria_extracted,
                "relationships_created": self.stats.relationships_created,
                "cross_domain_relationships": self.stats.cross_domain_relationships,
                "trials_deduplicated": self.stats.trials_deduplicated,
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
            "last_processed_nct_id": self.stats.last_processed_nct_id,
            "total_studies_available": self.stats.total_studies_available,
            "errors": self.stats.errors,
            "warnings": self.stats.warnings
        }

        summary_file = output_dir / f"clinicaltrials_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved processing summary to: {summary_file}")

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
        description='ClinicalTrials.gov API v2 处理器 / ClinicalTrials.gov API v2 Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:

  # 全量下载所有试验（前 1000 个）
  python -m processors.clinicaltrials_processor --mode full_download --max-studies 1000

  # 按疾病查询
  python -m processors.clinicaltrials_processor --mode query_by_disease --query-term "cancer"

  # 按阶段查询
  python -m processors.clinicaltrials_processor --mode query_by_phase --phase "Phase 3"

  # 增量更新
  python -m processors.clinicaltrials_processor --mode incremental --last-update-date "2024-01-01"

  # 按 NCT ID 获取单个研究
  python -m processors.clinicaltrials_processor --nct-id "NCT00001234"

  # 自定义输出目录
  python -m processors.clinicaltrials_processor --mode full_download --output /custom/output/path
        """
    )

    parser.add_argument(
        '--mode',
        choices=['full_download', 'query_by_disease', 'query_by_phase', 'query_by_status', 'incremental', 'nct_id'],
        default='full_download',
        help='处理模式（默认: full_download）'
    )

    parser.add_argument(
        '--query-term',
        help='搜索词'
    )

    parser.add_argument(
        '--phase',
        help='研究阶段（如：Phase 2, Phase 3）'
    )

    parser.add_argument(
        '--status',
        help='研究状态（如：Recruiting, Completed）'
    )

    parser.add_argument(
        '--nct-id',
        help='NCT ID（用于获取单个研究）'
    )

    parser.add_argument(
        '--last-update-date',
        help='最后更新日期（YYYY-MM-DD 格式，用于增量更新）'
    )

    parser.add_argument(
        '--max-studies',
        type=int,
        help='最大研究数量'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        help='最大页数'
    )

    parser.add_argument(
        '--page-size',
        type=int,
        default=100,
        help='每页结果数（默认: 100, 最大: 100）'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=2.0,
        help='每秒请求数（默认: 2.0）'
    )

    parser.add_argument(
        '--output',
        help='输出目录（默认为 data/processed/documents/clinicaltrials/）'
    )

    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='禁用去重'
    )

    parser.add_argument(
        '--no-cross-domain',
        action='store_true',
        help='禁用交叉域映射'
    )

    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='保存原始 API 响应'
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

    logger = logging.getLogger(__name__)

    # 构建配置
    config = {
        'extraction': {
            'api_base_url': 'https://clinicaltrials.gov/api/v2/studies',
            'page_size': args.page_size,
            'rate_limit_per_second': args.rate_limit,
            'max_studies': args.max_studies,
            'max_pages': args.max_pages,
            'deduplicate_by_nct_id': not args.no_dedup,
            'map_to_chembl': not args.no_cross_domain,
            'map_to_mondo': not args.no_cross_domain,
            'save_raw_response': args.save_raw
        }
    }

    # 创建处理器
    processor = ClinicalTrialsProcessor(config)

    # 根据模式获取数据
    start_time = datetime.now()

    if args.mode == 'nct_id' and args.nct_id:
        # 获取单个研究
        study_data = processor.fetch_by_nct_id(args.nct_id)
        if study_data:
            raw_data = {'studies': [study_data]}
        else:
            logger.error(f"Failed to fetch study: {args.nct_id}")
            return 1
    elif args.mode == 'incremental':
        # 增量更新
        raw_data = processor.fetch_incremental(args.last_update_date)
    elif args.mode == 'query_by_disease':
        # 按疾病查询
        raw_data = processor.fetch_by_query(args.query_term)
    elif args.mode == 'query_by_phase':
        # 按阶段查询
        filters = {'filter': {'value': {'expr': {'phase': args.phase}}, 'field': 'Phase', 'type': 'exact'}}
        raw_data = processor.fetch_by_query(None, filters)
    elif args.mode == 'query_by_status':
        # 按状态查询
        filters = {'filter': {'value': {'expr': {'status': args.status}}, 'field': 'Status', 'type': 'exact'}}
        raw_data = processor.fetch_by_query(None, filters)
    else:
        # 全量下载
        raw_data = processor.fetch_all_studies(args.query_term)

    if not raw_data or 'studies' not in raw_data:
        logger.error("No data fetched")
        return 1

    # 转换数据
    transformed_data = processor.transform(raw_data)

    # 验证数据
    if not processor.validate(transformed_data):
        logger.warning("Data validation failed")

    # 保存结果
    entities = transformed_data.get('entities', {})
    relationships = transformed_data.get('relationships', [])

    output_path = processor.save_results(entities, relationships, args.output)

    # 输出结果摘要
    elapsed_time = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*60}")
    print(f"ClinicalTrials.gov 处理完成 / Processing Complete")
    print(f"{'='*60}")
    print(f"提取的研究 / Trials extracted: {processor.stats.trials_extracted}")
    print(f"处理的文件 / Files processed: N/A (API)")
    print(f"提取的实体 / Entities extracted: {sum(len(v) for v in entities.values())}")
    print(f"提取的关系 / Relationships extracted: {len(relationships)}")
    print(f"处理时间 / Processing time: {elapsed_time:.2f} 秒 / seconds")
    print(f"API 请求时间 / API request time: {processor.stats.api_request_time_seconds:.2f} 秒 / seconds")
    print(f"\n详细统计 / Detailed Statistics:")
    print(f"  干预措施 / Interventions: {processor.stats.interventions_extracted}")
    print(f"  疾病条件 / Conditions: {processor.stats.conditions_extracted}")
    print(f"  研究站点 / Sites: {processor.stats.sites_extracted}")
    print(f"  研究者 / Investigators: {processor.stats.investigators_extracted}")
    print(f"  赞助商 / Sponsors: {processor.stats.sponsors_extracted}")
    print(f"  结果 / Outcomes: {processor.stats.outcomes_extracted}")
    print(f"  入排标准 / Eligibility Criteria: {processor.stats.eligibility_criteria_extracted}")
    print(f"  交叉域关系 / Cross-domain relationships: {processor.stats.cross_domain_relationships}")
    print(f"  去重试验 / Deduplicated trials: {processor.stats.trials_deduplicated}")
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
