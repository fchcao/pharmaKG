#===========================================================
# PharmaKG 数据处理器模块
# Pharmaceutical Knowledge Graph - Data Processors Module
#===========================================================
# 版本: v1.0
# 描述: 按数据类型组织的处理器模块
#===========================================================

from .base import BaseProcessor, ProcessingResult, ProcessingStatus

# Only import processors that don't have missing dependencies
try:
    from .chembl_processor import ChEMBLProcessor
    _chembl_available = True
except ImportError:
    _chembl_available = False

try:
    from .uniprot_processor import UniProtProcessor
    _uniprot_available = True
except ImportError:
    _uniprot_available = False

try:
    from .kegg_processor import KEGGProcessor
    _kegg_available = True
except ImportError:
    _kegg_available = False

try:
    from .clinicaltrials_processor import ClinicalTrialsProcessor
    _clinicaltrials_available = True
except ImportError:
    _clinicaltrials_available = False

__all__ = [
    "BaseProcessor",
    "ProcessingResult",
    "ProcessingStatus",
]

if _chembl_available:
    __all__.append("ChEMBLProcessor")
if _uniprot_available:
    __all__.append("UniProtProcessor")
if _kegg_available:
    __all__.append("KEGGProcessor")
if _clinicaltrials_available:
    __all__.append("ClinicalTrialsProcessor")
