#===========================================================
# PharmaKG ETL - 管道模块
# Pharmaceutical Knowledge Graph - ETL Pipelines Module
#===========================================================
# 版本: v1.0
# 描述: 导出所有 ETL 管道
#===========================================================

from .rd_pipeline import RDPipeline, run_rd_pipeline
from .clinical_pipeline import ClinicalPipeline, run_clinical_pipeline
from .sc_pipeline import SupplyChainPipeline, run_supply_chain_pipeline
from .regulatory_pipeline import RegulatoryPipeline, run_regulatory_pipeline


__all__ = [
    "RDPipeline",
    "run_rd_pipeline",
    "ClinicalPipeline",
    "run_clinical_pipeline",
    "SupplyChainPipeline",
    "run_supply_chain_pipeline",
    "RegulatoryPipeline",
    "run_regulatory_pipeline"
]


# 管道名称映射
PIPELINES = {
    "rd": ("R&D Domain", RDPipeline, run_rd_pipeline),
    "clinical": ("Clinical Domain", ClinicalPipeline, run_clinical_pipeline),
    "sc": ("Supply Chain Domain", SupplyChainPipeline, run_supply_chain_pipeline),
    "regulatory": ("Regulatory Domain", RegulatoryPipeline, run_regulatory_pipeline)
}


def get_pipeline(name: str):
    """
    获取管道类

    Args:
        name: 管道名称

    Returns:
        (描述, 管道类, 运行函数)
    """
    return PIPELINES.get(name)


def list_pipelines() -> list:
    """
    列出所有可用管道

    Returns:
        管道名称列表
    """
    return list(PIPELINES.keys())


def get_pipeline_descriptions() -> dict:
    """
    获取所有管道的描述

    Returns:
        {管道名称: 描述} 字典
    """
    return {name: info[0] for name, info in PIPELINES.items()}
