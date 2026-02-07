#===========================================================
# PharmaKG ETL - 配置管理
# Pharmaceutical Knowledge Graph - ETL Configuration
#===========================================================
# 版本: v1.0
# 描述: ETL 管道的配置管理
#===========================================================

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ETLConfig(BaseModel):
    """
    ETL 基础配置

    通过环境变量或直接传递设置
    """

    # Neo4j 配置
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j 连接 URI",
        env="NEO4J_URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j 用户名",
        env="NEO4J_USER"
    )
    neo4j_password: str = Field(
        default="pharmaKG2024!",
        description="Neo4j 密码",
        env="NEO4J_PASSWORD"
    )
    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j 数据库名称",
        env="NEO4J_DATABASE"
    )

    # ETL 行为配置
    batch_size: int = Field(
        default=500,
        description="批量处理大小",
        ge=1,
        le=10000
    )
    dry_run: bool = Field(
        default=False,
        description="试运行模式（不写入数据）"
    )
    timeout: int = Field(
        default=300,
        description="操作超时时间（秒）",
        ge=1
    )

    # 重试配置
    max_retries: int = Field(
        default=3,
        description="最大重试次数",
        ge=0,
        le=10
    )
    retry_backoff: float = Field(
        default=1.0,
        description="重试退避时间（秒）",
        ge=0.1
    )

    # API 限流配置
    api_rate_limit: float = Field(
        default=10.0,
        description="API 请求速率限制（请求/秒）",
        ge=0.1
    )
    api_timeout: int = Field(
        default=30,
        description="API 请求超时（秒）",
        ge=1
    )

    # 数据源配置
    chembl_api_url: str = Field(
        default="https://www.ebi.ac.uk/chembl/api/data",
        description="ChEMBL API URL",
        env="CHEMBL_API_URL"
    )
    chembl_api_key: Optional[str] = Field(
        default=None,
        description="ChEMBL API Key",
        env="CHEMBL_API_KEY"
    )

    clinicaltrials_api_url: str = Field(
        default="https://clinicaltrials.gov/api/v2/studies",
        description="ClinicalTrials.gov API URL",
        env="CLINICALTRIALS_API_URL"
    )
    clinicaltrials_api_key: Optional[str] = Field(
        default=None,
        description="ClinicalTrials.gov API Key",
        env="CLINICALTRIALS_API_KEY"
    )
    clinicaltrials_rate_limit: float = Field(
        default=10.0,
        description="ClinicalTrials.gov 请求速率限制",
        ge=0.1
    )

    fda_api_url: str = Field(
        default="https://api.fda.gov",
        description="FDA API URL",
        env="FDA_API_URL"
    )
    fda_api_key: Optional[str] = Field(
        default=None,
        description="FDA API Key",
        env="FDA_API_KEY"
    )

    # 日志配置
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="日志级别",
        env="LOG_LEVEL"
    )
    log_file: str = Field(
        default="etl.log",
        description="日志文件路径",
        env="LOG_FILE"
    )

    # 数据质量配置
    strict_validation: bool = Field(
        default=False,
        description="严格验证模式（验证失败时拒绝记录）"
    )
    skip_invalid_records: bool = Field(
        default=True,
        description="跳过无效记录"
    )

    # 进度跟踪配置
    enable_progress_tracking: bool = Field(
        default=True,
        description="启用进度跟踪"
    )
    progress_report_interval: int = Field(
        default=10,
        description="进度报告间隔（秒）",
        ge=1
    )

    # 并发配置
    max_workers: int = Field(
        default=4,
        description="最大并发工作线程数",
        ge=1,
        le=16
    )

    class Config:
        env_prefix = ""
        case_sensitive = False


@dataclass
class ExtractionTask:
    """抽取任务配置"""
    name: str
    extractor_class: str
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    timeout: int = 300
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TransformationTask:
    """转换任务配置"""
    name: str
    transformer_class: str
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    timeout: int = 300
    dependencies: List[str] = field(default_factory=list)


@dataclass
class LoadTask:
    """加载任务配置"""
    name: str
    loader_class: str
    node_label: str
    merge_key: str
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    timeout: int = 600
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    """管道配置"""
    name: str
    description: str = ""
    enabled: bool = True
    extraction_tasks: List[ExtractionTask] = field(default_factory=list)
    transformation_tasks: List[TransformationTask] = field(default_factory=list)
    load_tasks: List[LoadTask] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)

    def get_all_tasks(self) -> List[Any]:
        """获取所有任务"""
        return (
            self.extraction_tasks +
            self.transformation_tasks +
            self.load_tasks
        )


# ============================================
# 预定义管道配置
# ============================================

# R&D 管道配置
RD_PIPELINE_CONFIG = PipelineConfig(
    name="rd",
    description="R&D Domain ETL Pipeline - Compounds and Targets from ChEMBL",
    enabled=True,
    extraction_tasks=[
        ExtractionTask(
            name="extract_compounds",
            extractor_class="ChEMBLExtractor",
            params={"limit": 1000},
            priority=10
        ),
        ExtractionTask(
            name="extract_targets",
            extractor_class="ChEMBLExtractor",
            params={"limit": 500},
            priority=9
        )
    ],
    transformation_tasks=[
        TransformationTask(
            name="transform_compounds",
            transformer_class="CompoundTransformer",
            params={},
            dependencies=["extract_compounds"],
            priority=10
        ),
        TransformationTask(
            name="transform_targets",
            transformer_class="TargetTransformer",
            params={},
            dependencies=["extract_targets"],
            priority=9
        )
    ],
    load_tasks=[
        LoadTask(
            name="load_compounds",
            loader_class="Neo4jBatchLoader",
            node_label="Compound",
            merge_key="primary_id",
            dependencies=["transform_compounds"],
            priority=10
        ),
        LoadTask(
            name="load_targets",
            loader_class="Neo4jBatchLoader",
            node_label="Target",
            merge_key="primary_id",
            dependencies=["transform_targets"],
            priority=9
        )
    ],
    params={
        "limit_compounds": 1000,
        "limit_targets": 500
    }
)

# 临床管道配置
CLINICAL_PIPELINE_CONFIG = PipelineConfig(
    name="clinical",
    description="Clinical Domain ETL Pipeline - Clinical Trials from ClinicalTrials.gov",
    enabled=True,
    extraction_tasks=[
        ExtractionTask(
            name="extract_studies",
            extractor_class="ClinicalTrialsGovExtractor",
            params={"query": "cancer", "limit": 500},
            priority=10
        )
    ],
    transformation_tasks=[
        TransformationTask(
            name="transform_studies",
            transformer_class="ClinicalTrialTransformer",
            params={},
            dependencies=["extract_studies"],
            priority=10
        )
    ],
    load_tasks=[
        LoadTask(
            name="load_studies",
            loader_class="Neo4jBatchLoader",
            node_label="ClinicalTrial",
            merge_key="primary_id",
            dependencies=["transform_studies"],
            priority=10
        )
    ],
    params={
        "query": None,
        "phase": None,
        "limit": 500
    }
)

# 供应链管道配置
SC_PIPELINE_CONFIG = PipelineConfig(
    name="sc",
    description="Supply Chain Domain ETL Pipeline - Manufacturers and Shortages",
    enabled=True,
    extraction_tasks=[
        ExtractionTask(
            name="extract_manufacturers",
            extractor_class="SupplyChainExtractor",
            params={"limit": 500},
            priority=10
        ),
        ExtractionTask(
            name="extract_shortages",
            extractor_class="SupplyChainExtractor",
            params={"limit": 500},
            priority=9
        )
    ],
    transformation_tasks=[
        TransformationTask(
            name="transform_manufacturers",
            transformer_class="BaseTransformer",
            params={},
            dependencies=["extract_manufacturers"],
            priority=10
        ),
        TransformationTask(
            name="transform_shortages",
            transformer_class="BaseTransformer",
            params={},
            dependencies=["extract_shortages"],
            priority=9
        )
    ],
    load_tasks=[
        LoadTask(
            name="load_manufacturers",
            loader_class="Neo4jBatchLoader",
            node_label="Manufacturer",
            merge_key="primary_id",
            dependencies=["transform_manufacturers"],
            priority=10
        ),
        LoadTask(
            name="load_shortages",
            loader_class="Neo4jBatchLoader",
            node_label="DrugShortage",
            merge_key="primary_id",
            dependencies=["transform_shortages"],
            priority=9
        )
    ],
    params={
        "limit": 500
    }
)

# 监管管道配置
REGULATORY_PIPELINE_CONFIG = PipelineConfig(
    name="regulatory",
    description="Regulatory Domain ETL Pipeline - FDA Products and Applications",
    enabled=True,
    extraction_tasks=[
        ExtractionTask(
            name="extract_products",
            extractor_class="FDAExtractor",
            params={"limit": 1000},
            priority=10
        ),
        ExtractionTask(
            name="extract_applications",
            extractor_class="FDAExtractor",
            params={"limit": 1000},
            priority=9
        ),
        ExtractionTask(
            name="extract_tecodes",
            extractor_class="FDAExtractor",
            params={"limit": 500},
            priority=8
        )
    ],
    transformation_tasks=[
        TransformationTask(
            name="transform_products",
            transformer_class="BaseTransformer",
            params={},
            dependencies=["extract_products"],
            priority=10
        ),
        TransformationTask(
            name="transform_applications",
            transformer_class="BaseTransformer",
            params={},
            dependencies=["extract_applications"],
            priority=9
        ),
        TransformationTask(
            name="transform_tecodes",
            transformer_class="BaseTransformer",
            params={},
            dependencies=["extract_tecodes"],
            priority=8
        )
    ],
    load_tasks=[
        LoadTask(
            name="load_products",
            loader_class="Neo4jBatchLoader",
            node_label="FDAProduct",
            merge_key="primary_id",
            dependencies=["transform_products"],
            priority=10
        ),
        LoadTask(
            name="load_applications",
            loader_class="Neo4jBatchLoader",
            node_label="FDAApplication",
            merge_key="primary_id",
            dependencies=["transform_applications"],
            priority=9
        ),
        LoadTask(
            name="load_tecodes",
            loader_class="Neo4jBatchLoader",
            node_label="TECode",
            merge_key="primary_id",
            dependencies=["transform_tecodes"],
            priority=8
        )
    ],
    params={
        "data_file": None,
        "limit": 1000
    }
)


# ============================================
# 配置获取函数
# ============================================

_config_cache: Optional[ETLConfig] = None


def get_etl_config(**kwargs) -> ETLConfig:
    """
    获取 ETL 配置（单例模式）

    Args:
        **kwargs: 覆盖默认配置的参数

    Returns:
        ETL 配置实例
    """
    global _config_cache

    if _config_cache is None:
        _config_cache = ETLConfig()

    # 应用覆盖参数
    if kwargs:
        return _config_cache.copy(update=kwargs)

    return _config_cache


def reset_etl_config():
    """重置 ETL 配置缓存"""
    global _config_cache
    _config_cache = None


def load_config_from_file(file_path: str) -> ETLConfig:
    """
    从 YAML 文件加载配置

    Args:
        file_path: 配置文件路径

    Returns:
        ETL 配置实例
    """
    import yaml

    with open(file_path, 'r') as f:
        config_data = yaml.safe_load(f)

    return ETLConfig(**config_data)


def load_pipeline_config_from_file(file_path: str) -> Dict[str, PipelineConfig]:
    """
    从 YAML 文件加载管道配置

    Args:
        file_path: 配置文件路径

    Returns:
        管道配置字典
    """
    import yaml

    with open(file_path, 'r') as f:
        config_data = yaml.safe_load(f)

    pipeline_configs = {}

    for name, params in config_data.get("pipelines", {}).items():
        extraction_tasks = [
            ExtractionTask(**t) for t in params.get("extraction_tasks", [])
        ]
        transformation_tasks = [
            TransformationTask(**t) for t in params.get("transformation_tasks", [])
        ]
        load_tasks = [
            LoadTask(**t) for t in params.get("load_tasks", [])
        ]

        pipeline_configs[name] = PipelineConfig(
            name=name,
            description=params.get("description", ""),
            enabled=params.get("enabled", True),
            extraction_tasks=extraction_tasks,
            transformation_tasks=transformation_tasks,
            load_tasks=load_tasks,
            params=params.get("params", {})
        )

    return pipeline_configs
