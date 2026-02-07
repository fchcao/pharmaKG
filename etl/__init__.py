#===========================================================
# PharmaKG ETL - 模块入口
# Pharmaceutical Knowledge Graph - ETL Module
#===========================================================
# 版本: v1.0
# 描述: ETL 管道的模块入口
#===========================================================

"""
PharmaKG ETL 模块

完整的 ETL (Extract, Transform, Load) 管道系统，支持：
- 多数据源抽取 (ChEMBL, ClinicalTrials.gov, FDA, DrugBank)
- 数据转换和标准化
- Neo4j 图数据库批量加载
- 数据质量验证
"""

__version__ = "1.0.0"
__author__ = "PharmaKG Team"

# 配置
from .config import (
    ETLConfig,
    get_etl_config,
    PipelineConfig,
    ExtractionTask,
    TransformationTask,
    LoadTask,
    RD_PIPELINE_CONFIG,
    CLINICAL_PIPELINE_CONFIG,
    SC_PIPELINE_CONFIG,
    REGULATORY_PIPELINE_CONFIG,
    load_config_from_file,
    load_pipeline_config_from_file
)

# 调度器
from .scheduler import (
    ETLScheduler,
    TaskStatus,
    TaskInfo
)

# 管道
from .pipelines import (
    RDPipeline,
    run_rd_pipeline,
    ClinicalPipeline,
    run_clinical_pipeline,
    SupplyChainPipeline,
    run_supply_chain_pipeline,
    RegulatoryPipeline,
    run_regulatory_pipeline,
    PIPELINES,
    list_pipelines,
    get_pipeline
)

# 数据质量
from .quality import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    BaseValidator,
    CompoundValidator,
    TargetValidator,
    DiseaseValidator,
    ClinicalTrialValidator,
    SupplyChainValidator,
    RegulatoryValidator,
    ValidatorFactory,
    validate_batch,
    QualityDimension,
    QualityMetric,
    QualityReport,
    DataQualityChecker,
    check_data_quality
)

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Config
    "ETLConfig",
    "get_etl_config",
    "PipelineConfig",
    "ExtractionTask",
    "TransformationTask",
    "LoadTask",
    "RD_PIPELINE_CONFIG",
    "CLINICAL_PIPELINE_CONFIG",
    "SC_PIPELINE_CONFIG",
    "REGULATORY_PIPELINE_CONFIG",
    "load_config_from_file",
    "load_pipeline_config_from_file",

    # Scheduler
    "ETLScheduler",
    "TaskStatus",
    "TaskInfo",

    # Pipelines
    "RDPipeline",
    "run_rd_pipeline",
    "ClinicalPipeline",
    "run_clinical_pipeline",
    "SupplyChainPipeline",
    "run_supply_chain_pipeline",
    "RegulatoryPipeline",
    "run_regulatory_pipeline",
    "PIPELINES",
    "list_pipelines",
    "get_pipeline",

    # Quality
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "BaseValidator",
    "CompoundValidator",
    "TargetValidator",
    "DiseaseValidator",
    "ClinicalTrialValidator",
    "SupplyChainValidator",
    "RegulatoryValidator",
    "ValidatorFactory",
    "validate_batch",
    "QualityDimension",
    "QualityMetric",
    "QualityReport",
    "DataQualityChecker",
    "check_data_quality"
]


# 便捷函数
def run_etl(
    pipeline_name: str,
    dry_run: bool = False,
    **kwargs
) -> dict:
    """
    运行 ETL 管道

    Args:
        pipeline_name: 管道名称 (rd, clinical, sc, regulatory)
        dry_run: 试运行模式
        **kwargs: 管道特定参数

    Returns:
        执行结果

    Examples:
        >>> run_etl("rd", limit_compounds=1000)
        >>> run_etl("clinical", query="cancer", limit=500)
        >>> run_etl("regulatory", data_file="/path/to/fda.zip", dry_run=True)
    """
    pipelines = {
        "rd": run_rd_pipeline,
        "clinical": run_clinical_pipeline,
        "sc": run_supply_chain_pipeline,
        "regulatory": run_regulatory_pipeline
    }

    pipeline_func = pipelines.get(pipeline_name)
    if not pipeline_func:
        raise ValueError(
            f"Unknown pipeline: {pipeline_name}. "
            f"Available: {', '.join(pipelines.keys())}"
        )

    kwargs["dry_run"] = dry_run
    return pipeline_func(**kwargs)


def run_all_etl(
    dry_run: bool = False,
    load_to_neo4j: bool = True
) -> dict:
    """
    运行所有 ETL 管道

    Args:
        dry_run: 试运行模式
        load_to_neo4j: 是否加载到 Neo4j

    Returns:
        所有管道的执行结果
    """
    scheduler = ETLScheduler()

    results = {}

    for pipeline_name in list_pipelines():
        config = get_etl_config()

        # 更新参数
        if dry_run:
            config.dry_run = True

        result = scheduler.execute_pipeline(
            pipeline_name,
            getattr(config, f"{pipeline_name}_pipeline_config", None)
        )

        results[pipeline_name] = result

    return results


def validate_etl_results(
    records: list,
    record_type: str,
    print_report: bool = True
) -> QualityReport:
    """
    验证 ETL 结果

    Args:
        records: 记录列表
        record_type: 记录类型
        print_report: 是否打印报告

    Returns:
        数据质量报告
    """
    from .quality import DataQualityChecker, DEFAULT_CONSISTENCY_RULES

    checker = DataQualityChecker()

    consistency_rules = DEFAULT_CONSISTENCY_RULES.get(record_type, [])

    report = checker.generate_report(
        records=records,
        record_type=record_type,
        consistency_rules=consistency_rules
    )

    if print_report:
        checker.print_report(report)

    return report
