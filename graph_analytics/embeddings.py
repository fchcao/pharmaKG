#===========================================================
# PharmaKG - 图嵌入
# Pharmaceutical Knowledge Graph - Graph Embeddings
#===========================================================
# 版本: v1.0
# 描述: 图嵌入和相似度引擎
#===========================================================

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)


class EmbeddingType(str, Enum):
    """嵌入类型"""
    NODE2VEC = "node2vec"
    GRAPH_SAGE = "graphsage"
    TRANSE = "transe"
    DISTMULT = "distmult"
    COMPLEX = "complex"
    RANDOM_WALK = "random_walk"
    SHALLOW = "shallow"


@dataclass
class EmbeddingResult:
    """嵌入结果"""
    node_id: str
    embedding: np.ndarray
    node_type: str
    metadata: Dict[str, Any]


class NodeEmbeddingModel:
    """
    节点嵌入模型

    支持多种图嵌入算法
    """

    def __init__(
        self,
        neo4j_driver,
        embedding_dim: int = 128,
        model_type: EmbeddingType = EmbeddingType.RANDOM_WALK
    ):
        """
        初始化嵌入模型

        Args:
            neo4j_driver: Neo4j 数据库驱动
            embedding_dim: 嵌入维度
            model_type: 模型类型
        """
        self.driver = neo4j_driver
        self.embedding_dim = embedding_dim
        self.model_type = model_type
        self.embeddings: Dict[str, np.ndarray] = {}
        self.node_types: Dict[str, str] = {}

    def train(
        self,
        labels: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        walk_length: int = 80,
        num_walks: int = 10,
        window_size: int = 5,
        min_count: int = 1
    ) -> Dict[str, Any]:
        """
        训练嵌入模型

        Args:
            labels: 节点标签列表
            relationship_types: 关系类型列表
            walk_length: 随机游走长度
            num_walks: 每个节点的游走次数
            window_size: Word2Vec 窗口大小
            min_count: 最小词频

        Returns:
            训练统计信息
        """
        import time
        start_time = time.time()

        try:
            # 收集随机游走数据
            walks = self._generate_random_walks(
                labels=labels,
                relationship_types=relationship_types,
                walk_length=walk_length,
                num_walks=num_walks
            )

            # 训练 Word2Vec 模型
            model = self._train_word2vec(walks, window_size=window_size, min_count=min_count)

            # 提取嵌入向量
            for node_id in model.wv.key_to_index:
                self.embeddings[node_id] = model.wv[node_id]

            # 获取节点类型
            self._fetch_node_types(labels)

            training_time = time.time() - start_time

            return {
                "success": True,
                "training_time_seconds": training_time,
                "num_nodes": len(self.embeddings),
                "embedding_dim": self.embedding_dim,
                "num_walks": len(walks),
                "walk_length": walk_length
            }

        except Exception as e:
            logger.error(f"Embedding training failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_random_walks(
        self,
        labels: Optional[List[str]],
        relationship_types: Optional[List[str]],
        walk_length: int,
        num_walks: int
    ) -> List[List[str]]:
        """生成随机游走序列"""
        label_filter = ""
        if labels:
            label_filter = ":" + "|".join(labels)

        rel_pattern = ""
        if relationship_types:
            rel_pattern = ":" + "|".join(relationship_types)

        # 获取所有节点
        query = f"""
        MATCH (n{label_filter})
        RETURN n.primary_id as node_id
        """

        with self.driver.session() as session:
            result = session.run(query)
            nodes = [record["node_id"] for record in result]

        walks = []

        for _ in range(num_walks):
            import random
            random.shuffle(nodes)

            for node_id in nodes:
                walk = self._random_walk(node_id, walk_length, label_filter, rel_pattern)
                if walk:
                    walks.append(walk)

        return walks

    def _random_walk(
        self,
        start_node: str,
        length: int,
        label_filter: str,
        rel_pattern: str
    ) -> List[str]:
        """执行单次随机游走"""
        walk = [start_node]
        current = start_node

        for _ in range(length - 1):
            query = f"""
            MATCH (n {{primary_id: $current_id}})-[{rel_pattern}]->(neighbor{label_filter})
            RETURN neighbor.primary_id as neighbor_id
            """

            with self.driver.session() as session:
                result = session.run(query, current_id=current)
                neighbors = [record["neighbor_id"] for record in result]

            if not neighbors:
                break

            import random
            current = random.choice(neighbors)
            walk.append(current)

        return walk

    def _train_word2vec(
        self,
        walks: List[List[str]],
        window_size: int,
        min_count: int
    ):
        """训练 Word2Vec 模型"""
        try:
            from gensim.models import Word2Vec
        except ImportError:
            logger.error("gensim not installed. Install with: pip install gensim")
            raise

        model = Word2Vec(
            sentences=walks,
            vector_size=self.embedding_dim,
            window=window_size,
            min_count=min_count,
            workers=4,
            sg=1,  # Skip-gram
            epochs=10
        )

        return model

    def _fetch_node_types(self, labels: Optional[List[str]]):
        """获取节点类型"""
        label_filter = ""
        if labels:
            label_filter = ":" + "|".join(labels)

        query = f"""
        MATCH (n{label_filter})
        RETURN n.primary_id as node_id, head(labels(n)) as node_type
        """

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                self.node_types[record["node_id"]] = record["node_type"]

    def get_embedding(self, node_id: str) -> Optional[np.ndarray]:
        """获取节点嵌入向量"""
        return self.embeddings.get(node_id)

    def get_embeddings_batch(self, node_ids: List[str]) -> Dict[str, np.ndarray]:
        """批量获取节点嵌入向量"""
        return {nid: self.embeddings.get(nid) for nid in node_ids if nid in self.embeddings}

    def save(self, filepath: str):
        """保存嵌入模型"""
        data = {
            "embeddings": self.embeddings,
            "node_types": self.node_types,
            "embedding_dim": self.embedding_dim,
            "model_type": self.model_type
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Saved embeddings to {filepath}")

    def load(self, filepath: str):
        """加载嵌入模型"""
        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.embeddings = data["embeddings"]
        self.node_types = data["node_types"]
        self.embedding_dim = data["embedding_dim"]
        self.model_type = data["model_type"]

        logger.info(f"Loaded embeddings from {filepath}: {len(self.embeddings)} nodes")


class SimilarityEngine:
    """
    相似度引擎

    基于嵌入向量计算相似度
    """

    def __init__(
        self,
        neo4j_driver,
        embedding_model: Optional[NodeEmbeddingModel] = None
    ):
        """
        初始化相似度引擎

        Args:
            neo4j_driver: Neo4j 数据库驱动
            embedding_model: 嵌入模型
        """
        self.driver = neo4j_driver
        self.model = embedding_model or NodeEmbeddingModel(neo4j_driver)

    def find_similar_nodes(
        self,
        node_id: str,
        node_type: Optional[str] = None,
        top_k: int = 10,
        method: str = "cosine"
    ) -> List[Dict[str, Any]]:
        """
        查找相似节点

        Args:
            node_id: 查询节点 ID
            node_type: 目标节点类型
            top_k: 返回前 K 个结果
            method: 相似度计算方法 (cosine, euclidean, dot)

        Returns:
            相似节点列表
        """
        if node_id not in self.model.embeddings:
            logger.warning(f"Node {node_id} not in embeddings")
            return []

        query_embedding = self.model.embeddings[node_id]
        similarities = []

        for other_id, other_embedding in self.model.embeddings.items():
            if other_id == node_id:
                continue

            # 按节点类型过滤
            if node_type:
                if self.model.node_types.get(other_id) != node_type:
                    continue

            similarity = self._compute_similarity(query_embedding, other_embedding, method)
            similarities.append({
                "node_id": other_id,
                "similarity": similarity,
                "node_type": self.model.node_types.get(other_id)
            })

        # 排序并返回 top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        # 获取节点详细信息
        results = []
        for sim in similarities[:top_k]:
            details = self._get_node_details(sim["node_id"])
            results.append({**sim, **details})

        return results

    def _compute_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray,
        method: str
    ) -> float:
        """计算向量相似度"""
        if method == "cosine":
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        elif method == "euclidean":
            return float(-np.linalg.norm(vec1 - vec2))  # 负值，因为越大越相似
        elif method == "dot":
            return float(np.dot(vec1, vec2))
        else:
            raise ValueError(f"Unknown similarity method: {method}")

    def _get_node_details(self, node_id: str) -> Dict[str, Any]:
        """获取节点详细信息"""
        query = """
        MATCH (n {primary_id: $node_id})
        RETURN n.name as name,
               labels(n) as labels,
               properties(n) as props
        """

        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                return {
                    "name": record["name"],
                    "labels": record["labels"]
                }
        return {}

    def batch_similarity(
        self,
        node_pairs: List[Tuple[str, str]],
        method: str = "cosine"
    ) -> List[Dict[str, Any]]:
        """
        批量计算节点对相似度

        Args:
            node_pairs: 节点对列表 [(node1, node2), ...]
            method: 相似度计算方法

        Returns:
            相似度结果列表
        """
        results = []

        for node1_id, node2_id in node_pairs:
            emb1 = self.model.embeddings.get(node1_id)
            emb2 = self.model.embeddings.get(node2_id)

            if emb1 is None or emb2 is None:
                results.append({
                    "node1": node1_id,
                    "node2": node2_id,
                    "similarity": None,
                    "error": "embedding_not_found"
                })
                continue

            similarity = self._compute_similarity(emb1, emb2, method)

            results.append({
                "node1": node1_id,
                "node2": node2_id,
                "similarity": similarity,
                "node1_type": self.model.node_types.get(node1_id),
                "node2_type": self.model.node_types.get(node2_id)
            })

        return results

    def most_similar_to_vector(
        self,
        vector: np.ndarray,
        node_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找与给定向量最相似的节点

        Args:
            vector: 查询向量
            node_type: 节点类型过滤
            top_k: 返回前 K 个结果

        Returns:
            相似节点列表
        """
        similarities = []

        for node_id, embedding in self.model.embeddings.items():
            # 按节点类型过滤
            if node_type:
                if self.model.node_types.get(node_id) != node_type:
                    continue

            similarity = self._compute_similarity(vector, embedding, "cosine")
            similarities.append({
                "node_id": node_id,
                "similarity": similarity,
                "node_type": self.model.node_types.get(node_id)
            })

        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        results = []
        for sim in similarities[:top_k]:
            details = self._get_node_details(sim["node_id"])
            results.append({**sim, **details})

        return results


class GraphEmbeddings:
    """
    图嵌入统一接口

    整合所有图嵌入功能
    """

    def __init__(self, neo4j_driver):
        """
        初始化图嵌入实例

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver
        self.models: Dict[str, NodeEmbeddingModel] = {}
        self.similarity_engine = SimilarityEngine(neo4j_driver)

    def create_model(
        self,
        model_name: str,
        embedding_dim: int = 128,
        model_type: EmbeddingType = EmbeddingType.RANDOM_WALK
    ) -> NodeEmbeddingModel:
        """
        创建新的嵌入模型

        Args:
            model_name: 模型名称
            embedding_dim: 嵌入维度
            model_type: 模型类型

        Returns:
            嵌入模型实例
        """
        model = NodeEmbeddingModel(
            neo4j_driver=self.driver,
            embedding_dim=embedding_dim,
            model_type=model_type
        )
        self.models[model_name] = model
        return model

    def train_model(
        self,
        model_name: str,
        labels: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        训练指定模型

        Args:
            model_name: 模型名称
            labels: 节点标签列表
            relationship_types: 关系类型列表
            **kwargs: 训练参数

        Returns:
            训练统计信息
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        return self.models[model_name].train(
            labels=labels,
            relationship_types=relationship_types,
            **kwargs
        )

    def save_model(self, model_name: str, filepath: str):
        """保存模型"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        self.models[model_name].save(filepath)

    def load_model(self, model_name: str, filepath: str) -> NodeEmbeddingModel:
        """加载模型"""
        model = NodeEmbeddingModel(neo4j_driver=self.driver)
        model.load(filepath)
        self.models[model_name] = model
        return model

    def get_model(self, model_name: str) -> Optional[NodeEmbeddingModel]:
        """获取模型"""
        return self.models.get(model_name)

    def set_active_model(self, model_name: str):
        """设置活跃模型用于相似度计算"""
        model = self.get_model(model_name)
        if model:
            self.similarity_engine.model = model
        else:
            raise ValueError(f"Model {model_name} not found")

    def find_similar(
        self,
        node_id: str,
        node_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找相似节点

        Args:
            node_id: 查询节点 ID
            node_type: 目标节点类型
            top_k: 返回前 K 个结果

        Returns:
            相似节点列表
        """
        return self.similarity_engine.find_similar_nodes(node_id, node_type, top_k)

    def compute_similarity_matrix(
        self,
        node_ids: List[str],
        method: str = "cosine"
    ) -> np.ndarray:
        """
        计算节点间的相似度矩阵

        Args:
            node_ids: 节点 ID 列表
            method: 相似度计算方法

        Returns:
            相似度矩阵
        """
        model = self.similarity_engine.model
        n = len(node_ids)
        matrix = np.zeros((n, n))

        embeddings = [model.get_embedding(nid) for nid in node_ids]

        for i in range(n):
            for j in range(i, n):
                if embeddings[i] is not None and embeddings[j] is not None:
                    sim = self.similarity_engine._compute_similarity(
                        embeddings[i], embeddings[j], method
                    )
                    matrix[i, j] = sim
                    matrix[j, i] = sim

        return matrix

    def cluster_nodes(
        self,
        node_ids: List[str],
        n_clusters: int = 5,
        method: str = "kmeans"
    ) -> Dict[str, int]:
        """
        对节点进行聚类

        Args:
            node_ids: 节点 ID 列表
            n_clusters: 聚类数量
            method: 聚类方法 (kmeans, hierarchical)

        Returns:
            节点到簇的映射
        """
        model = self.similarity_engine.model
        embeddings = []

        valid_ids = []
        for nid in node_ids:
            emb = model.get_embedding(nid)
            if emb is not None:
                embeddings.append(emb)
                valid_ids.append(nid)

        embeddings = np.array(embeddings)

        if method == "kmeans":
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings)
        else:
            from sklearn.cluster import AgglomerativeClustering
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
            clusters = clustering.fit_predict(embeddings)

        return {nid: int(cluster) for nid, cluster in zip(valid_ids, clusters)}
