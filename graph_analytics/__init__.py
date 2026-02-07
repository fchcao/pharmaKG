#===========================================================
# PharmaKG - 图分析模块
# Pharmaceutical Knowledge Graph - Graph Analytics Module
#===========================================================
# 版本: v1.0
# 描述: 知识图谱分析和算法
#===========================================================

"""
PharmaKG 图分析模块

提供：
- 图中心性算法（度中心性、PageRank、接近中心性）
- 社区检测（Louvain、标签传播）
- 路径查找（最短路径、所有路径、权重路径）
- 相似度计算（Jaccard、Cosine、图谱嵌入）
- 推荐算法（协同过滤、基于图谱的推荐）
"""

__version__ = "1.0.0"

from .algorithms import (
    GraphAlgorithms,
    CentralityMeasures,
    CommunityDetection,
    PathFinding,
    SimilarityMeasures
)

from .inference import (
    RelationshipInference,
    DrugDrugInteractionPredictor,
    DrugDiseasePredictor,
    TargetDiseasePredictor
)

from .embeddings import (
    GraphEmbeddings,
    NodeEmbeddingModel,
    SimilarityEngine
)

from .visualization import (
    GraphVisualizer,
    SubgraphExtractor,
    LayoutEngine
)

from .api import (
    AnalyticsAPI,
    SimilarityAPI,
    PathAPI,
    RecommendationAPI
)

__all__ = [
    # Algorithms
    "GraphAlgorithms",
    "CentralityMeasures",
    "CommunityDetection",
    "PathFinding",
    "SimilarityMeasures",

    # Inference
    "RelationshipInference",
    "DrugDrugInteractionPredictor",
    "DrugDiseasePredictor",
    "TargetDiseasePredictor",

    # Embeddings
    "GraphEmbeddings",
    "NodeEmbeddingModel",
    "SimilarityEngine",

    # Visualization
    "GraphVisualizer",
    "SubgraphExtractor",
    "LayoutEngine",

    # API
    "AnalyticsAPI",
    "SimilarityAPI",
    "PathAPI",
    "RecommendationAPI"
]
