#===========================================================
# PharmaKG - 图分析 API
# Pharmaceutical Knowledge Graph - Graph Analytics API
#===========================================================
# 版本: v1.0
# 描述: 图分析和推理 API 端点
#===========================================================

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from .algorithms import GraphAlgorithms
from .inference import (
    DrugDrugInteractionPredictor,
    DrugDiseasePredictor,
    TargetDiseasePredictor
)
from .embeddings import GraphEmbeddings, SimilarityEngine
from .visualization import GraphVisualizer, LayoutType


logger = logging.getLogger(__name__)


# ============================================
# 请求/响应模型
# ============================================

class CentralityRequest(BaseModel):
    """中心性计算请求"""
    label: Optional[str] = None
    relationship_type: Optional[str] = None
    direction: str = "both"
    top_n: int = Field(default=100, ge=1, le=1000)


class PathFindingRequest(BaseModel):
    """路径查找请求"""
    source_id: str
    target_id: str
    relationship_types: Optional[List[str]] = None
    max_depth: int = Field(default=5, ge=1, le=10)


class SimilarityRequest(BaseModel):
    """相似度计算请求"""
    node1_id: str
    node2_id: str
    method: str = "jaccard"


class InferenceRequest(BaseModel):
    """关系推断请求"""
    entity1_id: str
    entity2_id: str
    methods: Optional[List[str]] = None


class EmbeddingTrainRequest(BaseModel):
    """嵌入训练请求"""
    model_name: str
    labels: Optional[List[str]] = None
    relationship_types: Optional[List[str]] = None
    walk_length: int = Field(default=80, ge=10, le=200)
    num_walks: int = Field(default=10, ge=1, le=100)


class VisualizationRequest(BaseModel):
    """可视化请求"""
    node_id: Optional[str] = None
    node_ids: Optional[List[str]] = None
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    hops: int = Field(default=1, ge=1, le=3)
    layout: LayoutType = LayoutType.FORCE_DIRECTED


# ============================================
# API 路由
# ============================================

def create_analytics_router(neo4j_driver) -> APIRouter:
    """
    创建分析 API 路由

    Args:
        neo4j_driver: Neo4j 数据库驱动

    Returns:
        FastAPI 路由
    """
    router = APIRouter(prefix="/graph/analytics", tags=["Analytics"])

    # 初始化组件
    algorithms = GraphAlgorithms(neo4j_driver)

    @router.get("/statistics")
    async def get_graph_statistics():
        """
        获取图统计信息

        返回节点数、边数、标签等统计信息
        """
        try:
            stats = algorithms.get_graph_statistics()
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/centrality/degree")
    async def calculate_degree_centrality(request: CentralityRequest):
        """
        计算度中心性

        返回指定标签/关系类型下度中心性最高的节点
        """
        try:
            result = algorithms.centrality.degree_centrality(
                label=request.label,
                relationship_type=request.relationship_type,
                direction=request.direction,
                top_n=request.top_n
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "degree_centrality",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Degree centrality calculation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/centrality/pagerank")
    async def calculate_pagerank(
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        top_n: int = Query(default=100, ge=1, le=1000)
    ):
        """
        计算 PageRank

        返回 PageRank 分数最高的节点
        """
        try:
            result = algorithms.centrality.pagerank(
                label=label,
                relationship_types=relationship_types,
                top_n=top_n
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "pagerank",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PageRank calculation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/centrality/betweenness")
    async def calculate_betweenness(
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        sample_size: int = Query(default=1000, ge=100, le=10000)
    ):
        """
        计算中介中心性

        返回经过最短路径次数最多的节点
        """
        try:
            result = algorithms.centrality.betweenness_centrality(
                label=label,
                relationship_types=relationship_types,
                sample_size=sample_size
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "betweenness_centrality",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Betweenness centrality calculation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/community/louvain")
    async def detect_louvain_communities(
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None
    ):
        """
        Louvain 社区检测

        使用 Louvain 算法检测图中的社区结构
        """
        try:
            result = algorithms.community.louvain(
                label=label,
                relationship_types=relationship_types
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "louvain",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Louvain community detection failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/community/connected-components")
    async def find_connected_components(
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None
    ):
        """
        弱连通分量检测

        找出图中的所有连通分量
        """
        try:
            result = algorithms.community.weakly_connected_components(
                label=label,
                relationship_types=relationship_types
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "connected_components",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Connected components detection failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


def create_similarity_router(neo4j_driver) -> APIRouter:
    """
    创建相似度 API 路由

    Args:
        neo4j_driver: Neo4j 数据库驱动

    Returns:
        FastAPI 路由
    """
    router = APIRouter(prefix="/graph/similarity", tags=["Similarity"])

    algorithms = GraphAlgorithms(neo4j_driver)

    @router.post("/jaccard")
    async def jaccard_similarity(request: SimilarityRequest):
        """
        计算 Jaccard 相似度

        基于共同邻居比例计算两个节点的相似度
        """
        try:
            result = algorithms.similarity.jaccard_similarity(
                node1_id=request.node1_id,
                node2_id=request.node2_id
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "method": "jaccard",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Jaccard similarity calculation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/cosine")
    async def cosine_similarity(request: SimilarityRequest):
        """
        计算余弦相似度

        基于向量相似度计算两个节点的相似度
        """
        try:
            result = algorithms.similarity.cosine_similarity(
                node1_id=request.node1_id,
                node2_id=request.node2_id
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "method": "cosine",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


def create_path_router(neo4j_driver) -> APIRouter:
    """
    创建路径查找 API 路由

    Args:
        neo4j_driver: Neo4j 数据库驱动

    Returns:
        FastAPI 路由
    """
    router = APIRouter(prefix="/graph/path", tags=["Path Finding"])

    algorithms = GraphAlgorithms(neo4j_driver)

    @router.post("/shortest")
    async def find_shortest_path(request: PathFindingRequest):
        """
        查找最短路径

        在两个节点之间查找最短路径
        """
        try:
            result = algorithms.pathfinding.shortest_path(
                source_id=request.source_id,
                target_id=request.target_id,
                relationship_types=request.relationship_types,
                max_depth=request.max_depth
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "shortest_path",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Shortest path finding failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/all")
    async def find_all_paths(request: PathFindingRequest):
        """
        查找所有路径

        在两个节点之间查找所有路径
        """
        try:
            result = algorithms.pathfinding.all_paths(
                source_id=request.source_id,
                target_id=request.target_id,
                relationship_types=request.relationship_types,
                max_depth=request.max_depth
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "all_paths",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"All paths finding failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/k-shortest")
    async def find_k_shortest_paths(
        request: PathFindingRequest,
        k: int = Query(default=5, ge=1, le=20)
    ):
        """
        查找 K 条最短路径

        返回两个节点之间的 K 条最短路径
        """
        try:
            result = algorithms.pathfinding.k_shortest_paths(
                source_id=request.source_id,
                target_id=request.target_id,
                k=k,
                relationship_types=request.relationship_types,
                max_depth=request.max_depth
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            return {
                "success": True,
                "algorithm": "k_shortest_paths",
                "execution_time_ms": result.execution_time_ms,
                "data": result.result
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"K shortest paths finding failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


def create_inference_router(neo4j_driver) -> APIRouter:
    """
    创建关系推断 API 路由

    Args:
        neo4j_driver: Neo4j 数据库驱动

    Returns:
        FastAPI 路由
    """
    router = APIRouter(prefix="/graph/inference", tags=["Inference"])

    ddi_predictor = DrugDrugInteractionPredictor(neo4j_driver)
    dd_predictor = DrugDiseasePredictor(neo4j_driver)
    td_predictor = TargetDiseasePredictor(neo4j_driver)

    @router.post("/drug-drug-interaction")
    async def predict_ddi(
        drug1_id: str = Query(..., description="First drug ID"),
        drug2_id: str = Query(..., description="Second drug ID"),
        methods: Optional[List[str]] = Query(default=None)
    ):
        """
        预测药物-药物相互作用

        基于共享靶点、通路重叠、结构相似性预测 DDI
        """
        try:
            result = ddi_predictor.predict_interaction(drug1_id, drug2_id, methods)

            return {
                "success": True,
                "data": {
                    "drug1_id": result.entities[0],
                    "drug2_id": result.entities[1],
                    "predicted_relationship": result.predicted_relationship,
                    "confidence": result.confidence,
                    "evidence": result.evidence,
                    "explanation": result.explanation
                }
            }

        except Exception as e:
            logger.error(f"DDI prediction failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/drug-disease")
    async def predict_drug_disease(
        drug_id: str = Query(..., description="Drug ID"),
        disease_id: str = Query(..., description="Disease ID")
    ):
        """
        预测药物-疾病适应症

        基于靶点-疾病关联、相似药物、通路等预测适应症
        """
        try:
            result = dd_predictor.predict_indication(drug_id, disease_id)

            return {
                "success": True,
                "data": {
                    "drug_id": result.entities[0],
                    "disease_id": result.entities[1],
                    "predicted_relationship": result.predicted_relationship,
                    "confidence": result.confidence,
                    "evidence": result.evidence,
                    "explanation": result.explanation
                }
            }

        except Exception as e:
            logger.error(f"Drug-disease prediction failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/target-disease")
    async def predict_target_disease(
        target_id: str = Query(..., description="Target ID"),
        disease_id: str = Query(..., description="Disease ID")
    ):
        """
        预测靶点-疾病关联

        基于药物介导、通路关联、基因本体等预测关联
        """
        try:
            result = td_predictor.predict_association(target_id, disease_id)

            return {
                "success": True,
                "data": {
                    "target_id": result.entities[0],
                    "disease_id": result.entities[1],
                    "predicted_relationship": result.predicted_relationship,
                    "confidence": result.confidence,
                    "evidence": result.evidence,
                    "explanation": result.explanation
                }
            }

        except Exception as e:
            logger.error(f"Target-disease prediction failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


def create_visualization_router(neo4j_driver) -> APIRouter:
    """
    创建可视化 API 路由

    Args:
        neo4j_driver: Neo4j 数据库驱动

    Returns:
        FastAPI 路由
    """
    router = APIRouter(prefix="/graph/visualization", tags=["Visualization"])

    visualizer = GraphVisualizer(neo4j_driver)

    @router.post("/neighborhood")
    async def visualize_neighborhood(
        node_id: str = Query(..., description="Center node ID"),
        hops: int = Query(default=1, ge=1, le=3),
        layout: LayoutType = LayoutType.FORCE_DIRECTED
    ):
        """
        可视化节点邻域

        返回节点周围指定跳数的子图用于可视化
        """
        try:
            data = visualizer.visualize_node_neighborhood(node_id, hops, layout)

            return {
                "success": True,
                "data": data
            }

        except Exception as e:
            logger.error(f"Neighborhood visualization failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/path")
    async def visualize_path(
        source_id: str = Query(..., description="Source node ID"),
        target_id: str = Query(..., description="Target node ID"),
        max_paths: int = Query(default=5, ge=1, le=20),
        layout: LayoutType = LayoutType.HIERARCHICAL
    ):
        """
        可视化路径

        返回两个节点之间的路径子图
        """
        try:
            data = visualizer.visualize_path(source_id, target_id, max_paths, layout)

            return {
                "success": True,
                "data": data
            }

        except Exception as e:
            logger.error(f"Path visualization failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/community")
    async def visualize_community(
        node_ids: List[str] = Query(..., description="List of node IDs"),
        layout: LayoutType = LayoutType.FORCE_DIRECTED
    ):
        """
        可视化社区

        返回指定节点及其邻域的子图
        """
        try:
            data = visualizer.visualize_community(node_ids, layout)

            return {
                "success": True,
                "data": data
            }

        except Exception as e:
            logger.error(f"Community visualization failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/colors/node-types")
    async def get_node_colors():
        """获取节点类型颜色映射"""
        return {
            "success": True,
            "data": visualizer.get_node_color_map()
        }

    @router.get("/colors/relationship-types")
    async def get_relationship_colors():
        """获取关系类型颜色映射"""
        return {
            "success": True,
            "data": visualizer.get_relationship_color_map()
        }

    return router


# ============================================
# 统一 API 类
# ============================================

class AnalyticsAPI:
    """
    分析 API 统一接口

    整合所有图分析 API 端点
    """

    def __init__(self, neo4j_driver):
        """
        初始化分析 API

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def register_routers(self, app):
        """
        注册所有路由到 FastAPI 应用

        Args:
            app: FastAPI 应用实例
        """
        app.include_router(create_analytics_router(self.driver))
        app.include_router(create_similarity_router(self.driver))
        app.include_router(create_path_router(self.driver))
        app.include_router(create_inference_router(self.driver))
        app.include_router(create_visualization_router(self.driver))

        logger.info("Registered graph analytics API routers")


# 独立的路由实例（用于单独使用）
class SimilarityAPI:
    """相似度 API"""

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    def get_router(self) -> APIRouter:
        return create_similarity_router(self.driver)


class PathAPI:
    """路径查找 API"""

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    def get_router(self) -> APIRouter:
        return create_path_router(self.driver)


class RecommendationAPI:
    """推荐 API"""

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.embeddings = GraphEmbeddings(neo4j_driver)

    def recommend_similar_drugs(
        self,
        drug_id: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        推荐相似药物

        Args:
            drug_id: 药物 ID
            top_k: 返回数量

        Returns:
            相似药物列表
        """
        return self.embeddings.find_similar(drug_id, "Compound", top_k)

    def recommend_drug_repurposing(
        self,
        disease_id: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        药物重定位推荐

        为指定疾病推荐可能有效的药物

        Args:
            disease_id: 疾病 ID
            top_k: 返回数量

        Returns:
            推荐药物列表
        """
        # 获取疾病相关的靶点
        query = """
        MATCH (d:Disease {primary_id: $disease_id})<-[:ASSOCIATED_WITH]-(t:Target)
        RETURN t.primary_id as target_id
        """

        with self.driver.session() as session:
            result = session.run(query, disease_id=disease_id)
            target_ids = [record["target_id"] for record in result]

        # 获取靶向这些靶点的药物
        recommendations = []
        for target_id in target_ids:
            query = """
            MATCH (c:Compound)-[:TARGETS]->(:Target {primary_id: $target_id})
            WHERE NOT (c)-[:TREATS]->(:Disease {primary_id: $disease_id})
            RETURN DISTINCT c.primary_id as drug_id, c.name as drug_name
            LIMIT 5
            """

            with self.driver.session() as session:
                result = session.run(query, target_id=target_id, disease_id=disease_id)
                for record in result:
                    if len(recommendations) < top_k:
                        recommendations.append({
                            "drug_id": record["drug_id"],
                            "drug_name": record["drug_name"],
                            "target_id": target_id
                        })

        return recommendations
