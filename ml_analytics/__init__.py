#===========================================================
# PharmaKG - 机器学习分析模块
# Pharmaceutical Knowledge Graph - ML Analytics Module
#===========================================================
# 版本: v1.0
# 描述: 机器学习与知识图谱集成
#===========================================================

"""
PharmaKG ML 分析模块

提供：
- 图神经网络 (GNN) 模型
- 链接预测模型
- 节点分类模型
- 知识图谱嵌入
- 药物重定位预测
- 不良反应预测
"""

__version__ = "1.0.0"

from .models import (
    GraphNeuralNetwork,
    LinkPredictionModel,
    NodeClassificationModel,
    KGEmbeddingModel
)

from .predictors import (
    DrugRepurposingPredictor,
    AdverseReactionPredictor,
    ClinicalTrialOutcomePredictor,
    DrugEfficacyPredictor
)

from .features import (
    GraphFeatureExtractor,
    NodeFeatureBuilder,
    PathFeatureExtractor
)

from .training import (
    ModelTrainer,
    EvaluationMetrics,
    CrossValidator
)

from .pipeline import (
    MLPipeline,
    ExperimentTracker,
    ModelRegistry
)

from .reasoning import (
    KnowledgeGraphReasoner,
    PathBasedReasoner,
    RuleEngine,
    ExplainabilityEngine
)

__all__ = [
    # Models
    "GraphNeuralNetwork",
    "LinkPredictionModel",
    "NodeClassificationModel",
    "KGEmbeddingModel",

    # Predictors
    "DrugRepurposingPredictor",
    "AdverseReactionPredictor",
    "ClinicalTrialOutcomePredictor",
    "DrugEfficacyPredictor",

    # Features
    "GraphFeatureExtractor",
    "NodeFeatureBuilder",
    "PathFeatureExtractor",

    # Training
    "ModelTrainer",
    "EvaluationMetrics",
    "CrossValidator",

    # Pipeline
    "MLPipeline",
    "ExperimentTracker",
    "ModelRegistry",

    # Reasoning
    "KnowledgeGraphReasoner",
    "PathBasedReasoner",
    "RuleEngine",
    "ExplainabilityEngine"
]
