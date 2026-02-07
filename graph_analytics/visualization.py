#===========================================================
# PharmaKG - 图可视化
# Pharmaceutical Knowledge Graph - Graph Visualization
#===========================================================
# 版本: v1.0
# 描述: 知识图谱可视化支持
#===========================================================

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class LayoutType(str, Enum):
    """布局类型"""
    FORCE_DIRECTED = "force_directed"
    CIRCULAR = "circular"
    HIERARCHICAL = "hierarchical"
    RADIAL = "radial"
    GRID = "grid"
    CONCENTRIC = "concentric"


@dataclass
class GraphNode:
    """图节点"""
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any]
    x: Optional[float] = None
    y: Optional[float] = None
    size: float = 1.0
    color: Optional[str] = None


@dataclass
class GraphEdge:
    """图边"""
    id: str
    source: str
    target: str
    relationship_type: str
    properties: Dict[str, Any]
    weight: float = 1.0
    color: Optional[str] = None


@dataclass
class Subgraph:
    """子图"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any]


class SubgraphExtractor:
    """
    子图提取器

    从知识图谱中提取感兴趣的子图
    """

    def __init__(self, neo4j_driver):
        """
        初始化子图提取器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver

    def extract_by_node_ids(
        self,
        node_ids: List[str],
        include_neighbors: bool = False,
        neighbor_depth: int = 1
    ) -> Subgraph:
        """
        根据节点 ID 提取子图

        Args:
            node_ids: 节点 ID 列表
            include_neighbors: 是否包含邻居节点
            neighbor_depth: 邻居深度

        Returns:
            子图
        """
        nodes = {}
        edges = []

        # 获取主要节点
        for node_id in node_ids:
            node_data = self._get_node(node_id)
            if node_data:
                nodes[node_id] = GraphNode(
                    id=node_id,
                    label=node_data.get("name", ""),
                    node_type=node_data.get("node_type", ""),
                    properties=node_data
                )

        # 获取邻居节点
        if include_neighbors:
            for node_id in node_ids:
                neighbors = self._get_neighbors(node_id, neighbor_depth)
                for neighbor_id, neighbor_data in neighbors.items():
                    if neighbor_id not in nodes:
                        nodes[neighbor_id] = GraphNode(
                            id=neighbor_id,
                            label=neighbor_data.get("name", ""),
                            node_type=neighbor_data.get("node_type", ""),
                            properties=neighbor_data
                        )

        # 获取边
        for node_id in nodes.keys():
            node_edges = self._get_edges(node_id)
            edges.extend(node_edges)

        return Subgraph(
            nodes=list(nodes.values()),
            edges=edges,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        )

    def extract_by_relationship_type(
        self,
        relationship_type: str,
        node_labels: Optional[List[str]] = None,
        limit: int = 1000
    ) -> Subgraph:
        """
        根据关系类型提取子图

        Args:
            relationship_type: 关系类型
            node_labels: 节点标签过滤
            limit: 结果数量限制

        Returns:
            子图
        """
        label_filter = ""
        if node_labels:
            label_filter = ":" + "|".join(node_labels)

        query = f"""
        MATCH (a{label_filter})-[r:{relationship_type}]->(b{label_filter})
        RETURN a.primary_id as source_id, a.name as source_name, head(labels(a)) as source_type,
               b.primary_id as target_id, b.name as target_name, head(labels(b)) as target_type,
               properties(r) as rel_props
        LIMIT {limit}
        """

        with self.driver.session() as session:
            result = session.run(query)
            records = [record.data() for record in result]

        nodes = {}
        edges = []

        for record in records:
            source_id = record["source_id"]
            target_id = record["target_id"]

            # 添加节点
            if source_id not in nodes:
                nodes[source_id] = GraphNode(
                    id=source_id,
                    label=record["source_name"],
                    node_type=record["source_type"],
                    properties={}
                )

            if target_id not in nodes:
                nodes[target_id] = GraphNode(
                    id=target_id,
                    label=record["target_name"],
                    node_type=record["target_type"],
                    properties={}
                )

            # 添加边
            edge_id = f"{source_id}-{target_id}"
            edges.append(GraphEdge(
                id=edge_id,
                source=source_id,
                target=target_id,
                relationship_type=relationship_type,
                properties=record["rel_props"]
            ))

        return Subgraph(
            nodes=list(nodes.values()),
            edges=edges,
            metadata={
                "relationship_type": relationship_type,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        )

    def extract_path_subgraph(
        self,
        source_id: str,
        target_id: str,
        max_paths: int = 10,
        max_depth: int = 3
    ) -> Subgraph:
        """
        提取路径子图

        Args:
            source_id: 起始节点 ID
            target_id: 目标节点 ID
            max_paths: 最大路径数
            max_depth: 最大深度

        Returns:
            子图
        """
        query = """
        MATCH path = (a {primary_id: $source_id})-[*1..$max_depth]-(b {primary_id: $target_id})
        RETURN path
        LIMIT $max_paths
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                max_paths=max_paths,
                max_depth=max_depth
            )

        nodes = {}
        edges = []

        for record in result:
            path = record["path"]

            # 提取节点
            for node in path.nodes:
                node_id = node["primary_id"]
                if node_id not in nodes:
                    nodes[node_id] = GraphNode(
                        id=node_id,
                        label=node.get("name", ""),
                        node_type=labels(node)[0] if labels(node) else "",
                        properties=dict(node)
                    )

            # 提取边
            for rel in path.relationships:
                edge_id = f"{rel.start_node.element_id}-{rel.end_node.element_id}"
                edges.append(GraphEdge(
                    id=edge_id,
                    source=rel.start_node["primary_id"],
                    target=rel.end_node["primary_id"],
                    relationship_type=type(rel).__name__,
                    properties=dict(rel)
                ))

        return Subgraph(
            nodes=list(nodes.values()),
            edges=edges,
            metadata={
                "source_id": source_id,
                "target_id": target_id,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        )

    def extract_community_subgraph(
        self,
        node_id: str,
        max_hops: int = 2
    ) -> Subgraph:
        """
        提取社区子图（节点周围的局部结构）

        Args:
            node_id: 中心节点 ID
            max_hops: 最大跳数

        Returns:
            子图
        """
        query = f"""
        MATCH (center {{primary_id: $node_id}})
        CALL apoc.path.subgraphAll(center, {{
            maxLevel: {max_hops},
            relationshipFilter: ""
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        with self.driver.session() as session:
            try:
                result = session.run(query, node_id=node_id)
                record = result.single()

                if record:
                    nodes_data = record["nodes"]
                    rels_data = record["relationships"]
                else:
                    # APOC 不可用，使用基本查询
                    return self._extract_community_fallback(node_id, max_hops)

            except Exception:
                return self._extract_community_fallback(node_id, max_hops)

        nodes = {}
        edges = []

        for node in nodes_data:
            node_id = node["primary_id"]
            nodes[node_id] = GraphNode(
                id=node_id,
                label=node.get("name", ""),
                node_type=labels(node)[0] if labels(node) else "",
                properties=dict(node)
            )

        for rel in rels_data:
            edge_id = f"{rel.start_node.element_id}-{rel.end_node.element_id}"
            edges.append(GraphEdge(
                id=edge_id,
                source=rel.start_node["primary_id"],
                target=rel.end_node["primary_id"],
                relationship_type=type(rel).__name__,
                properties=dict(rel)
            ))

        return Subgraph(
            nodes=list(nodes.values()),
            edges=edges,
            metadata={
                "center_node": node_id,
                "max_hops": max_hops,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        )

    def _extract_community_fallback(
        self,
        node_id: str,
        max_hops: int
    ) -> Subgraph:
        """社区提取的回退实现"""
        nodes = {}
        edges = []

        # 获取中心节点
        center_data = self._get_node(node_id)
        if center_data:
            nodes[node_id] = GraphNode(
                id=node_id,
                label=center_data.get("name", ""),
                node_type=center_data.get("node_type", ""),
                properties=center_data
            )

        # 扩展获取邻居
        current_nodes = {node_id}
        for hop in range(max_hops):
            next_nodes = set()
            for current_id in current_nodes:
                neighbors = self._get_neighbors(current_id, 1)
                for neighbor_id, neighbor_data in neighbors.items():
                    if neighbor_id not in nodes:
                        nodes[neighbor_id] = GraphNode(
                            id=neighbor_id,
                            label=neighbor_data.get("name", ""),
                            node_type=neighbor_data.get("node_type", ""),
                            properties=neighbor_data
                        )
                        next_nodes.add(neighbor_id)

                # 获取边
                for current_id in current_nodes:
                    node_edges = self._get_edges(current_id)
                    edges.extend(node_edges)

            current_nodes = next_nodes
            if not current_nodes:
                break

        return Subgraph(
            nodes=list(nodes.values()),
            edges=edges,
            metadata={
                "center_node": node_id,
                "max_hops": max_hops,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        )

    def _get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点数据"""
        query = """
        MATCH (n {primary_id: $node_id})
        RETURN n.name as name,
               head(labels(n)) as node_type,
               properties(n) as props
        """

        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                return {
                    "name": record["name"],
                    "node_type": record["node_type"],
                    **record["props"]
                }
        return None

    def _get_neighbors(
        self,
        node_id: str,
        depth: int
    ) -> Dict[str, Dict[str, Any]]:
        """获取邻居节点"""
        query = f"""
        MATCH (n {{primary_id: $node_id}})-[*1..{depth}]-(neighbor)
        RETURN DISTINCT neighbor.primary_id as neighbor_id,
               neighbor.name as name,
               head(labels(neighbor)) as node_type
        """

        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            return {
                record["neighbor_id"]: {
                    "name": record["name"],
                    "node_type": record["node_type"]
                }
                for record in result
            }

    def _get_edges(self, node_id: str) -> List[GraphEdge]:
        """获取节点的边"""
        query = """
        MATCH (n {primary_id: $node_id})-[r]-(other)
        RETURN n.primary_id as source_id,
               other.primary_id as target_id,
               type(r) as rel_type,
               properties(r) as props
        """

        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            edges = []

            for record in result:
                edge_id = f"{record['source_id']}-{record['target_id']}"
                edges.append(GraphEdge(
                    id=edge_id,
                    source=record["source_id"],
                    target=record["target_id"],
                    relationship_type=record["rel_type"],
                    properties=record["props"]
                ))

            return edges


class LayoutEngine:
    """
    布局引擎

    计算节点在图中的位置
    """

    def compute_layout(
        self,
        subgraph: Subgraph,
        layout_type: LayoutType = LayoutType.FORCE_DIRECTED,
        **kwargs
    ) -> Subgraph:
        """
        计算布局

        Args:
            subgraph: 子图
            layout_type: 布局类型
            **kwargs: 布局参数

        Returns:
            带位置信息的子图
        """
        if layout_type == LayoutType.FORCE_DIRECTED:
            return self._force_directed_layout(subgraph, **kwargs)
        elif layout_type == LayoutType.CIRCULAR:
            return self._circular_layout(subgraph, **kwargs)
        elif layout_type == LayoutType.HIERARCHICAL:
            return self._hierarchical_layout(subgraph, **kwargs)
        elif layout_type == LayoutType.RADIAL:
            return self._radial_layout(subgraph, **kwargs)
        elif layout_type == LayoutType.GRID:
            return self._grid_layout(subgraph, **kwargs)
        else:
            return subgraph

    def _force_directed_layout(
        self,
        subgraph: Subgraph,
        iterations: int = 100,
        repulsion: float = 100,
        attraction: float = 0.1,
        damping: float = 0.9
    ) -> Subgraph:
        """力导向布局"""
        import random
        import math

        # 初始化位置
        node_positions = {}
        for node in subgraph.nodes:
            node_positions[node.id] = {
                "x": random.uniform(-100, 100),
                "y": random.uniform(-100, 100)
            }

        # 构建邻接表
        adjacency = defaultdict(list)
        for edge in subgraph.edges:
            adjacency[edge.source].append(edge.target)
            adjacency[edge.target].append(edge.source)

        # 迭代优化
        for iteration in range(iterations):
            forces = {nid: [0.0, 0.0] for nid in node_positions}

            # 计算斥力
            for n1 in node_positions:
                for n2 in node_positions:
                    if n1 == n2:
                        continue

                    dx = node_positions[n1]["x"] - node_positions[n2]["x"]
                    dy = node_positions[n1]["y"] - node_positions[n2]["y"]
                    dist = math.sqrt(dx * dx + dy * dy) + 0.1

                    force = repulsion / (dist * dist)
                    forces[n1][0] += (dx / dist) * force
                    forces[n1][1] += (dy / dist) * force

            # 计算引力
            for edge in subgraph.edges:
                source_pos = node_positions[edge.source]
                target_pos = node_positions[edge.target]

                dx = target_pos["x"] - source_pos["x"]
                dy = target_pos["y"] - source_pos["y"]
                dist = math.sqrt(dx * dx + dy * dy) + 0.1

                force = dist * attraction
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                forces[edge.source][0] += fx
                forces[edge.source][1] += fy
                forces[edge.target][0] -= fx
                forces[edge.target][1] -= fy

            # 应用力并阻尼
            for nid in node_positions:
                node_positions[nid]["x"] += forces[nid][0] * damping
                node_positions[nid]["y"] += forces[nid][1] * damping

        # 更新节点位置
        for node in subgraph.nodes:
            if node.id in node_positions:
                node.x = node_positions[node.id]["x"]
                node.y = node_positions[node.id]["y"]

        return subgraph

    def _circular_layout(
        self,
        subgraph: Subgraph,
        radius: float = 100
    ) -> Subgraph:
        """圆形布局"""
        import math

        nodes = subgraph.nodes
        n = len(nodes)

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            node.x = radius * math.cos(angle)
            node.y = radius * math.sin(angle)

        return subgraph

    def _hierarchical_layout(
        self,
        subgraph: Subgraph,
        node_rank: Optional[Dict[str, int]] = None,
        level_height: float = 50
    ) -> Subgraph:
        """层次布局"""
        import math

        # 如果没有指定层次，使用度数
        if node_rank is None:
            degree = defaultdict(int)
            for edge in subgraph.edges:
                degree[edge.source] += 1
                degree[edge.target] += 1

            # 按度数分组
            max_degree = max(degree.values()) if degree else 1
            node_rank = {
                nid: (max_degree - deg) for nid, deg in degree.items()
            }

        # 按层次分组
        levels = defaultdict(list)
        for node in subgraph.nodes:
            rank = node_rank.get(node.id, 0)
            levels[rank].append(node)

        # 布局
        for rank, nodes_in_level in sorted(levels.items()):
            y = rank * level_height
            n = len(nodes_in_level)
            width = n * 30

            for i, node in enumerate(nodes_in_level):
                x = -width / 2 + (width / (n + 1)) * (i + 1)
                node.x = x
                node.y = y

        return subgraph

    def _radial_layout(
        self,
        subgraph: Subgraph,
        center_node: Optional[str] = None
    ) -> Subgraph:
        """径向布局"""
        import math

        if center_node and center_node in [n.id for n in subgraph.nodes]:
            # 找到中心节点
            center = next(n for n in subgraph.nodes if n.id == center_node)
            center.x = 0
            center.y = 0

            # 其他节点按距离排列
            other_nodes = [n for n in subgraph.nodes if n.id != center_node]
            n = len(other_nodes)

            for i, node in enumerate(other_nodes):
                angle = 2 * math.pi * i / n
                radius = 100
                node.x = radius * math.cos(angle)
                node.y = radius * math.sin(angle)
        else:
            # 使用圆形布局
            return self._circular_layout(subgraph)

        return subgraph

    def _grid_layout(
        self,
        subgraph: Subgraph,
        cols: int = 5,
        spacing: float = 50
    ) -> Subgraph:
        """网格布局"""
        for i, node in enumerate(subgraph.nodes):
            row = i // cols
            col = i % cols
            node.x = col * spacing
            node.y = row * spacing

        return subgraph


class GraphVisualizer:
    """
    图可视化器

    整合子图提取和布局计算
    """

    def __init__(self, neo4j_driver):
        """
        初始化可视化器

        Args:
            neo4j_driver: Neo4j 数据库驱动
        """
        self.driver = neo4j_driver
        self.extractor = SubgraphExtractor(neo4j_driver)
        self.layout_engine = LayoutEngine()

    def visualize_node_neighborhood(
        self,
        node_id: str,
        hops: int = 1,
        layout: LayoutType = LayoutType.FORCE_DIRECTED
    ) -> Dict[str, Any]:
        """
        可视化节点邻域

        Args:
            node_id: 节点 ID
            hops: 跳数
            layout: 布局类型

        Returns:
            可视化数据
        """
        subgraph = self.extractor.extract_community_subgraph(node_id, hops)
        subgraph = self.layout_engine.compute_layout(subgraph, layout)

        return self._serialize_subgraph(subgraph)

    def visualize_path(
        self,
        source_id: str,
        target_id: str,
        max_paths: int = 5,
        layout: LayoutType = LayoutType.HIERARCHICAL
    ) -> Dict[str, Any]:
        """
        可视化路径

        Args:
            source_id: 起始节点 ID
            target_id: 目标节点 ID
            max_paths: 最大路径数
            layout: 布局类型

        Returns:
            可视化数据
        """
        subgraph = self.extractor.extract_path_subgraph(
            source_id, target_id, max_paths
        )
        subgraph = self.layout_engine.compute_layout(subgraph, layout)

        return self._serialize_subgraph(subgraph)

    def visualize_community(
        self,
        node_ids: List[str],
        layout: LayoutType = LayoutType.FORCE_DIRECTED
    ) -> Dict[str, Any]:
        """
        可视化社区

        Args:
            node_ids: 节点 ID 列表
            layout: 布局类型

        Returns:
            可视化数据
        """
        subgraph = self.extractor.extract_by_node_ids(
            node_ids, include_neighbors=True, neighbor_depth=2
        )
        subgraph = self.layout_engine.compute_layout(subgraph, layout)

        return self._serialize_subgraph(subgraph)

    def _serialize_subgraph(self, subgraph: Subgraph) -> Dict[str, Any]:
        """序列化子图为可视化数据格式"""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "x": node.x,
                    "y": node.y,
                    "size": node.size,
                    "color": node.color
                }
                for node in subgraph.nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.relationship_type,
                    "weight": edge.weight,
                    "color": edge.color
                }
                for edge in subgraph.edges
            ],
            "metadata": subgraph.metadata
        }

    def get_node_color_map(self) -> Dict[str, str]:
        """获取节点类型颜色映射"""
        return {
            "Compound": "#4CAF50",
            "Target": "#2196F3",
            "Disease": "#F44336",
            "ClinicalTrial": "#FF9800",
            "Pathway": "#9C27B0",
            "Gene": "#00BCD4",
            "default": "#9E9E9E"
        }

    def get_relationship_color_map(self) -> Dict[str, str]:
        """获取关系类型颜色映射"""
        return {
            "TARGETS": "#2196F3",
            "TREATS": "#4CAF50",
            "ASSOCIATED_WITH": "#FF9800",
            "PARTICIPATES_IN": "#9C27B0",
            "INTERACTS_WITH": "#F44336",
            "default": "#BDBDBD"
        }
