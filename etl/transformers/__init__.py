#===========================================================
# PharmaKG ETL - 数据转换模块
# Pharmaceutical Knowledge Graph - Data Transformers Module
#===========================================================
# 版本: v1.0
# 描述: 数据转换器模块
#===========================================================

from .base import (
    TransformationStatus,
    TransformationResult,
    BaseTransformer,
    FieldMapping
)

from .compound import (
    CompoundTransformer,
    CompoundTransformerChEMBL,
    CompoundTransformerDrugBank,
    transform_compounds
)

from .target_disease import (
    TargetTransformer,
    DiseaseTransformer
)

from .trial import (
    ClinicalTrialTransformer,
    transform_trials
)

from .document_transformer import DocumentTransformer


__all__ = [
    # Base
    "TransformationStatus",
    "TransformationResult",
    "BaseTransformer",
    "FieldMapping",

    # Compound
    "CompoundTransformer",
    "CompoundTransformerChEMBL",
    "CompoundTransformerDrugBank",
    "transform_compounds",

    # Target/Disease
    "TargetTransformer",
    "DiseaseTransformer",

    # Clinical Trial
    "ClinicalTrialTransformer",
    "transform_trials",

    # Document
    "DocumentTransformer"
]
