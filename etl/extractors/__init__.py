#===========================================================
# PharmaKG ETL - 数据抽取器模块
# Pharmaceutical Knowledge Graph - Data Extractors Module
#===========================================================
# 版本: v1.0
# 描述: 数据抽取器模块
#===========================================================

from .base import (
    BaseExtractor,
    PaginatedExtractor,
    FileBasedExtractor,
    ExtractionResult,
    ExtractorStatus
)

from .chembl import ChEMBLExtractor
from .clinicaltrials import ClinicalTrialsGovExtractor
from .drugbank import DrugBankExtractor
from .fda import FDAExtractors
from .document_extractor import DocumentExtractor


__all__ = [
    # Base
    "BaseExtractor",
    "PaginatedExtractor",
    "FileBasedExtractor",
    "ExtractionResult",
    "ExtractorStatus",

    # Data Source Extractors
    "ChEMBLExtractor",
    "ClinicalTrialsGovExtractor",
    "DrugBankExtractor",
    "FDAExtractors",

    # Document Extractor
    "DocumentExtractor"
]
