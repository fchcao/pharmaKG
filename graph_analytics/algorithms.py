#===========================================================
# PharmaKG - 图算法
# Pharmaceutical Knowledge Graph - Graph Algorithms
#===========================================================
# 版本: v1.0
# 描述: 图分析算法实现
#===========================================================

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlgorithmType(str, Enum):
    """算法类型"""
    CENTRALITY = "centrality"
    COMMUNITY = "community"
    PATH = "path"
    SIMILARITY = "similarity"
    EMBEDDING = "embedding"


@dataclass
class AlgorithmResult:
    """算法结果"""
    algorithm_type: AlgorithmType
    algorithm_name: str
    success: bool
    execution_time_ms: float
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class CentralityMeasures:
    """
    中心性度量计算

    支持：
    - 度中心性 (Degree Centrality)
    - PageRank
    - 接近中心性 (Closeness Centrality)
    - 中介中心性 (Betweenness Centrality)
    - 特征向量中心性 (Eigenvector Centrality)
    """

    def __init__(self, neo4j_driver):
        """
        初始化中心性计算器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def degree_centrality(
        self,
        label: Optional[str] = None,
        relationship_type: Optional[str] = None,
        direction: str = "both",
        top_n: int = 100
    ) -> AlgorithmResult:
        """
        计算度中心性

        Args:
            label: 节点标签过滤
            relationship_type: 关系类型过滤
            direction: 方向 (in, out, both)
            top_n: 返回前N个节点

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            # 构建查询
            direction_pattern = {
                "in": "<-",
                "out": "-",
                "both": "-"
            }[direction]

            rel_pattern = ""
            if relationship_type:
                rel_pattern = f":[{relationship_type}]"
            else:
                rel_pattern = ""

            label_filter = f":{label}" if label else ""

            query = f"""
            MATCH (n{label_filter})
            OPTIONAL MATCH {direction_pattern}[r{rel_pattern}]{direction_pattern}(n)
            WITH n, count(r) as degree
            RETURN n.primary_id as node_id, n.name as name, labels(n) as labels, degree
            ORDER BY degree DESC
            LIMIT {top_n}
            """

            with self.driver.session() as session:
                result = session.run(query)
                nodes = [record.data() for record in result]

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.CENTRALITY,
                algorithm_name="degree_centrality",
                success=True,
                execution_time_ms=execution_time,
                result={"nodes": nodes, "total": len(nodes)},
                metadata={"top_n": top_n, "direction": direction}
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Degree centrality calculation failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.CENTRALITY,
                algorithm_name="degree_centrality",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def pagerank(
        self,
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        iterations: int = 20,
        damping_factor: float = 0.85,
        top_n: int = 100
    ) -> AlgorithmResult:
        """
        计算 PageRank

        Args:
            label: 节点标签过滤
            relationship_types: 关系类型列表
            iterations: 迭代次数
            damping_factor: 阻尼系数
            top_n: 返回前N个节点

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            # 使用 Neo4j Graph Data Science 库或手动实现
            label_filter = f":{label}" if label else ""

            # 构建关系模式
            if relationship_types:
                rel_pattern = "|".join(relationship_types)
            else:
                rel_pattern = None

            # 尝试使用 GDS 库
            query = f"""
            CALL algo.pageRank.stream(
                '{label or '*'}',
                '{rel_pattern or ''}',
                {{iterations: {iterations}, dampingFactor: {damping_factor}}}
            )
            YIELD nodeId, score
            RETURN algo.getNodeById(nodeId).primary_id as node_id,
                   algo.getNodeById(nodeId).name as name,
                   score
            ORDER BY score DESC
            LIMIT {top_n}
            """

            with self.driver.session() as session:
                try:
                    result = session.run(query)
                    nodes = [record.data() for record in result]
                except Exception:
                    # GDS 不可用，使用简单实现
                    nodes = self._simple_pagerank(
                        label, rel_pattern, iterations, damping_factor, top_n
                    )

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.CENTRALITY,
                algorithm_name="pagerank",
                success=True,
                execution_time_ms=execution_time,
                result={"nodes": nodes, "total": len(nodes)},
                metadata={
                    "iterations": iterations,
                    "damping_factor": damping_factor,
                    "top_n": top_n
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"PageRank calculation failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.CENTRALITY,
                algorithm_name="pagerank",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def _simple_pagerank(
        self,
        label: Optional[str],
        rel_pattern: Optional[str],
        iterations: int,
        damping_factor: float,
        top_n: int
    ) -> List[Dict]:
        """简单的 PageRank 实现（当 GDS 不可用时）"""
        label_filter = f":{label}" if label else ""

        # 获取所有节点
        query = f"""
        MATCH (n{label_filter})
        RETURN n.primary_id as node_id, n.name as name
        """

        with self.driver.session() as session:
            result = session.run(query)
            nodes = {record["node_id"]: record for record in result}

        # 获取边
        query = f"""
        MATCH (a{label_filter})-[r]->(b{label_filter})
        RETURN a.primary_id as source, b.primary_id as target
        """

        with self.driver.session() as session:
            result = session.run(query)
            edges = [(record["source"], record["target"]) for record in result]

        # 计算 PageRank
        scores = {node_id: 1.0 for node_id in nodes}
        out_links = defaultdict(list)
        in_links = defaultdict(set)

        for src, tgt in edges:
            out_links[src].append(tgt)
            in_links[tgt].add(src)

        for _ in range(iterations):
            new_scores = {}
            for node_id in nodes:
                rank_sum = 0
                for neighbor in in_links[node_id]:
                    out_degree = len(out_links[neighbor])
                    if out_degree > 0:
                        rank_sum += scores[neighbor] / out_degree

                new_scores[node_id] = (1 - damping_factor) + damping_factor * rank_sum

            scores = new_scores

        # 排序并返回
        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [
            {
                "node_id": node_id,
                "name": nodes[node_id]["name"],
                "score": score
            }
            for node_id, score in sorted_nodes
        ]

    def betweenness_centrality(
        self,
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        sample_size: int = 1000
    ) -> AlgorithmResult:
        """
        计算中介中心性（采样版本）

        Args:
            label: 节点标签过滤
            relationship_types: 关系类型列表
            sample_size: 采样大小

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            # 简化实现：使用最短路径计数
            label_filter = f":{label}" if label else ""

            query = f"""
            MATCH (a{label_filter}), (b{label_filter})
            WHERE id(a) < id(b)
            MATCH path = shortestPath((a)-[*..5]-(b))
            WITH path, nodes(path) as path_nodes
            UNWIND path_nodes[1..-2] as intermediate
            RETURN intermediate.primary_id as node_id,
                   intermediate.name as name,
                   count(*) as betweenness
            ORDER BY betweenness DESC
            LIMIT {sample_size}
            """

            with self.driver.session() as session:
                result = session.run(query)
                nodes = [record.data() for record in result]

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.CENTRALITY,
                algorithm_name="betweenness_centrality",
                success=True,
                execution_time_ms=execution_time,
                result={"nodes": nodes, "total": len(nodes)},
                metadata={"sample_size": sample_size}
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Betweenness centrality calculation failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.CENTRALITY,
                algorithm_name="betweenness_centrality",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )


class CommunityDetection:
    """
    社区检测算法

    支持：
    - Louvain 算法
    - 标签传播算法
    - 弱连通分量
    """

    def __init__(self, neo4j_driver):
        """
        初始化社区检测器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def louvain(
        self,
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        include_intermediate_communities: bool = False
    ) -> AlgorithmResult:
        """
        Louvain 社区检测

        Args:
            label: 节点标签过滤
            relationship_types: 关系类型列表
            include_intermediate_communities: 是否包含中间社区

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            label_filter = f":{label}" if label else ""
            rel_pattern = "|".join(relationship_types) if relationship_types else ""

            # 尝试使用 GDS 库
            query = f"""
            CALL algo.louvain.stream(
                '{label or '*'}',
                '{rel_pattern or ''}',
                {{includeIntermediateCommunities: {str(include_intermediate_communities).lower()}}}
            )
            YIELD nodeId, community
            RETURN community, count(*) as size
            ORDER BY size DESC
            """

            with self.driver.session() as session:
                try:
                    result = session.run(query)
                    communities = [record.data() for record in result]
                except Exception:
                    # GDS 不可用，使用标签传播作为替代
                    return self.label_propagation(label, relationship_types)

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.COMMUNITY,
                algorithm_name="louvain",
                success=True,
                execution_time_ms=execution_time,
                result={"communities": communities, "total": len(communities)},
                metadata={"include_intermediate": include_intermediate_communities}
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Louvain community detection failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.COMMUNITY,
                algorithm_name="louvain",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def label_propagation(
        self,
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        iterations: int = 10
    ) -> AlgorithmResult:
        """
        标签传播算法

        Args:
            label: 节点标签过滤
            relationship_types: 关系类型列表
            iterations: 迭代次数

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            label_filter = f":{label}" if label else ""
            rel_pattern = "|".join(relationship_types) if relationship_types else ""

            query = f"""
            CALL algo.labelPropagation.stream(
                '{label or '*'}',
                '{rel_pattern or ''}',
                {{iterations: {iterations}}}
            )
            YIELD nodeId, community
            RETURN community, count(*) as size
            ORDER BY size DESC
            """

            with self.driver.session() as session:
                try:
                    result = session.run(query)
                    communities = [record.data() for record in result]
                except Exception:
                    # GDS 不可用，使用简单实现
                    communities = self._simple_label_propagation(
                        label, rel_pattern, iterations
                    )

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.COMMUNITY,
                algorithm_name="label_propagation",
                success=True,
                execution_time_ms=execution_time,
                result={"communities": communities, "total": len(communities)},
                metadata={"iterations": iterations}
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Label propagation failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.COMMUNITY,
                algorithm_name="label_propagation",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def _simple_label_propagation(
        self,
        label: Optional[str],
        rel_pattern: Optional[str],
        iterations: int
    ) -> List[Dict]:
        """简单的标签传播实现"""
        # 获取节点和边
        label_filter = f":{label}" if label else ""

        query = f"""
        MATCH (n{label_filter})
        RETURN n.primary_id as node_id
        """

        with self.driver.session() as session:
            result = session.run(query)
            nodes = [record["node_id"] for record in result]

        # 初始化：每个节点自己的社区
        labels = {node: i for i, node in enumerate(nodes)}
        neighbors = defaultdict(set)

        # 获取邻居
        query = f"""
        MATCH (a{label_filter})-[r]-(b{label_filter})
        RETURN a.primary_id as node_id, b.primary_id as neighbor
        """

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                neighbors[record["node_id"]].add(record["neighbor"])

        # 迭代传播
        for _ in range(iterations):
            new_labels = {}
            for node in nodes:
                # 统计邻居的标签
                label_counts = defaultdict(int)
                for neighbor in neighbors[node]:
                    label_counts[labels[neighbor]] += 1

                # 选择最常见的标签
                if label_counts:
                    new_labels[node] = max(label_counts.items(), key=lambda x: x[1])[0]
                else:
                    new_labels[node] = labels[node]

            labels = new_labels

        # 统计社区大小
        community_sizes = defaultdict(int)
        for node, community in labels.items():
            community_sizes[community] += 1

        return [
            {"community": str(comm), "size": size}
            for comm, size in sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)
        ]

    def weakly_connected_components(
        self,
        label: Optional[str] = None,
        relationship_types: Optional[List[str]] = None
    ) -> AlgorithmResult:
        """
        弱连通分量检测

        Args:
            label: 节点标签过滤
            relationship_types: 关系类型列表

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            label_filter = f":{label}" if label else ""
            rel_pattern = "|".join(relationship_types) if relationship_types else ""

            query = f"""
            CALL algo.unionFind.stream(
                '{label or '*'}',
                '{rel_pattern or ''}'
            )
            YIELD nodeId, setId
            RETURN setId as component, count(*) as size
            ORDER BY size DESC
            """

            with self.driver.session() as session:
                try:
                    result = session.run(query)
                    components = [record.data() for record in result]
                except Exception:
                    # GDS 不可用，使用 Cypher 实现
                    components = self._cypher_connected_components(label, rel_pattern)

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.COMMUNITY,
                algorithm_name="weakly_connected_components",
                success=True,
                execution_time_ms=execution_time,
                result={"components": components, "total": len(components)},
                metadata={}
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Connected components detection failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.COMMUNITY,
                algorithm_name="weakly_connected_components",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def _cypher_connected_components(
        self,
        label: Optional[str],
        rel_pattern: Optional[str]
    ) -> List[Dict]:
        """使用 Cypher 实现连通分量检测"""
        label_filter = f":{label}" if label else ""

        # 简化实现：使用遍历
        query = f"""
        MATCH (n{label_filter})
        WHERE NOT (n)-[]->()
        WITH n
        CALL apoc.path.subgraphAll(n, {{
            maxLevel: 100,
            relationshipFilter: '{rel_pattern or ''}'
        }})
        YIELD nodes
        RETURN min([node in nodes | node.primary_id]) as component, count(*) as size
        ORDER BY size DESC
        LIMIT 100
        """

        with self.driver.session() as session:
            try:
                result = session.run(query)
                return [record.data() for record in result]
            except Exception:
                # APOC 也不可用，返回空结果
                return []


class PathFinding:
    """
    路径查找算法

    支持：
    - 最短路径
    - 所有路径
    - K 最短路径
    - 权重最短路径
    """

    def __init__(self, neo4j_driver):
        """
        初始化路径查找器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 5,
        label: Optional[str] = None
    ) -> AlgorithmResult:
        """
        查找最短路径

        Args:
            source_id: 起始节点 ID
            target_id: 目标节点 ID
            relationship_types: 关系类型列表
            max_depth: 最大深度
            label: 节点标签过滤

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            rel_pattern = ""
            if relationship_types:
                rel_pattern = ":" + "|".join(relationship_types)

            label_filter = f":{label}" if label else ""

            query = f"""
            MATCH path = shortestPath(
                (a{label_filter} {{primary_id: $source_id}})-[*1..{max_depth}]-(b{label_filter} {{primary_id: $target_id}})
            )
            RETURN [node in nodes(path) | {{
                id: node.primary_id,
                name: node.name,
                labels: labels(node)
            }}] as nodes,
            [rel in relationships(path) | type(rel)] as relationships,
            length(path) as path_length
            """

            with self.driver.session() as session:
                result = session.run(query, source_id=source_id, target_id=target_id)
                paths = [record.data() for record in result]

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.PATH,
                algorithm_name="shortest_path",
                success=True,
                execution_time_ms=execution_time,
                result={"paths": paths, "total": len(paths)},
                metadata={
                    "source_id": source_id,
                    "target_id": target_id,
                    "max_depth": max_depth
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Shortest path finding failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.PATH,
                algorithm_name="shortest_path",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def all_paths(
        self,
        source_id: str,
        target_id: str,
        relationship_types: Optional[List[str]] = None,
        min_depth: int = 1,
        max_depth: int = 3,
        limit: int = 100
    ) -> AlgorithmResult:
        """
        查找所有路径

        Args:
            source_id: 起始节点 ID
            target_id: 目标节点 ID
            relationship_types: 关系类型列表
            min_depth: 最小深度
            max_depth: 最大深度
            limit: 结果数量限制

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            label_filter = f":{label}" if label else ""

            query = f"""
            MATCH path = (a{{primary_id: $source_id}})-[*{min_depth}..{max_depth}]-(b{{primary_id: $target_id}})
            RETURN [node in nodes(path) | {{
                id: node.primary_id,
                name: node.name,
                labels: labels(node)
            }}] as nodes,
            [rel in relationships(path) | type(rel)] as relationships,
            length(path) as path_length
            LIMIT {limit}
            """

            with self.driver.session() as session:
                result = session.run(query, source_id=source_id, target_id=target_id)
                paths = [record.data() for record in result]

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.PATH,
                algorithm_name="all_paths",
                success=True,
                execution_time_ms=execution_time,
                result={"paths": paths, "total": len(paths)},
                metadata={
                    "source_id": source_id,
                    "target_id": target_id,
                    "min_depth": min_depth,
                    "max_depth": max_depth
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"All paths finding failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.PATH,
                algorithm_name="all_paths",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def k_shortest_paths(
        self,
        source_id: str,
        target_id: str,
        k: int = 5,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> AlgorithmResult:
        """
        查找 K 条最短路径

        Args:
            source_id: 起始节点 ID
            target_id: 目标节点 ID
            k: 返回路径数量
            relationship_types: 关系类型列表
            max_depth: 最大深度

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            label_filter = f":{label}" if label else ""

            # 使用 Yen's 算法或简化实现
            query = f"""
            MATCH (a{{primary_id: $source_id}}), (b{{primary_id: $target_id}})
            CALL algo.kShortestPaths.stream(a, b, {k}, {{
                relationshipQuery: '{relationship_types[0] if relationship_types else ""}',
                direction: 'OUTGOING',
                maxDepth: {max_depth}
            }})
            YIELD index, nodeIds, costs
            RETURN index, nodeIds, costs
            """

            with self.driver.session() as session:
                try:
                    result = session.run(query, source_id=source_id, target_id=target_id)
                    paths = [record.data() for record in result]
                except Exception:
                    # GDS 不可用，使用简单排序
                    query = f"""
                    MATCH path = (a{{primary_id: $source_id}})-[*1..{max_depth}]-(b{{primary_id: $target_id}})
                    RETURN [node in nodes(path) | node.primary_id] as node_ids,
                           length(path) as cost
                    ORDER BY cost ASC
                    LIMIT {k}
                    """

                    result = session.run(query, source_id=source_id, target_id=target_id)
                    paths = [{"index": i, "nodeIds": r["node_ids"], "costs": r["cost"]}
                             for i, r in enumerate(result)]

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.PATH,
                algorithm_name="k_shortest_paths",
                success=True,
                execution_time_ms=execution_time,
                result={"paths": paths, "total": len(paths)},
                metadata={
                    "source_id": source_id,
                    "target_id": target_id,
                    "k": k
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"K shortest paths finding failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.PATH,
                algorithm_name="k_shortest_paths",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )


class SimilarityMeasures:
    """
    相似度计算

    支持：
    - Jaccard 相似度
    - 余弦相似度
    - 重叠系数
    - 图结构相似度
    """

    def __init__(self, neo4j_driver):
        """
        初始化相似度计算器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def jaccard_similarity(
        self,
        node1_id: str,
        node2_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "outgoing"
    ) -> AlgorithmResult:
        """
        计算 Jaccard 相似度

        基于两个节点的共同邻居比例

        Args:
            node1_id: 第一个节点 ID
            node2_id: 第二个节点 ID
            relationship_type: 关系类型
            direction: 方向 (incoming, outgoing, both)

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            direction_pattern = {
                "incoming": "<-",
                "outgoing": "-",
                "both": "-"
            }[direction]

            rel_pattern = f"[:{relationship_type}]" if relationship_type else ""

            query = f"""
            MATCH (a {{primary_id: $node1_id}}){direction_pattern}{rel_pattern}(neighbor)
            WITH a, collect(DISTINCT neighbor.primary_id) as neighbors_a
            MATCH (b {{primary_id: $node2_id}}){direction_pattern}{rel_pattern}(neighbor)
            WITH neighbors_a, collect(DISTINCT neighbor.primary_id) as neighbors_b
            WITH neighbors_a, neighbors_b,
                 size([n in neighbors_a WHERE n in neighbors_b]) as intersection,
                 size(neighbors_a) + size(neighbors_b) - size([n in neighbors_a WHERE n in neighbors_b]) as union
            RETURN intersection, union,
                   (intersection * 1.0 / union) as jaccard_similarity
            """

            with self.driver.session() as session:
                result = session.run(query, node1_id=node1_id, node2_id=node2_id)
                similarity_data = result.single()

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.SIMILARITY,
                algorithm_name="jaccard_similarity",
                success=True,
                execution_time_ms=execution_time,
                result=similarity_data,
                metadata={
                    "node1_id": node1_id,
                    "node2_id": node2_id,
                    "direction": direction
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Jaccard similarity calculation failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.SIMILARITY,
                algorithm_name="jaccard_similarity",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def cosine_similarity(
        self,
        node1_id: str,
        node2_id: str,
        relationship_type: Optional[str] = None
    ) -> AlgorithmResult:
        """
        计算余弦相似度

        Args:
            node1_id: 第一个节点 ID
            node2_id: 第二个节点 ID
            relationship_type: 关系类型

        Returns:
            算法结果
        """
        import time
        start_time = time.time()

        try:
            rel_pattern = f"[:{relationship_type}]" if relationship_type else ""

            query = f"""
            MATCH (a {{primary_id: $node1_id}})-{rel_pattern}]->(neighbor)
            WITH a, count(neighbor) as degree_a
            MATCH (b {{primary_id: $node2_id}})-{rel_pattern}]->(neighbor)
            WITH degree_a, count(neighbor) as degree_b
            MATCH (a {{primary_id: $node1_id}})-{rel_pattern}]->(common)
            MATCH (b {{primary_id: $node2_id}})-{rel_pattern}]->(common)
            WITH degree_a, degree_b, count(common) as common_neighbors
            RETURN common_neighbors * 1.0 / sqrt(degree_a * degree_b) as cosine_similarity
            """

            with self.driver.session() as session:
                result = session.run(query, node1_id=node1_id, node2_id=node2_id)
                similarity_data = result.single()

            execution_time = (time.time() - start_time) * 1000

            return AlgorithmResult(
                algorithm_type=AlgorithmType.SIMILARITY,
                algorithm_name="cosine_similarity",
                success=True,
                execution_time_ms=execution_time,
                result=similarity_data,
                metadata={
                    "node1_id": node1_id,
                    "node2_id": node2_id
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Cosine similarity calculation failed: {e}")
            return AlgorithmResult(
                algorithm_type=AlgorithmType.SIMILARITY,
                algorithm_name="cosine_similarity",
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )


class GraphAlgorithms:
    """
    图算法统一接口

    整合所有图算法功能
    """

    def __init__(self, neo4j_driver):
        """
        初始化图算法实例

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver
        self.centrality = CentralityMeasures(neo4j_driver)
        self.community = CommunityDetection(neo4j_driver)
        self.pathfinding = PathFinding(neo4j_driver)
        self.similarity = SimilarityMeasures(neo4j_driver)

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图统计信息

        Returns:
            图统计信息
        """
        query = """
        CALL db.stats.retrieve('GRAPH COUNTS')
        YIELD graphCount
        RETURN graphCount
        """

        with self.driver.session() as session:
            result = session.run(query)
            stats = result.single()

        # 获取更详细的统计
        queries = {
            "node_count": "MATCH (n) RETURN count(n) as count",
            "relationship_count": "MATCH ()-[r]->() RETURN count(r) as count",
            "node_labels": "CALL db.labels() YIELD label RETURN collect(label) as labels",
            "relationship_types": "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types"
        }

        detailed_stats = {}
        with self.driver.session() as session:
            for key, q in queries.items():
                result = session.run(q)
                detailed_stats[key] = result.single()[0]

        return {
            "overview": stats["graphCount"] if stats else {},
            **detailed_stats
        }
