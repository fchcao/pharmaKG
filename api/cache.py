#===========================================================
# PharmaKG API - 查询缓存管理
# Pharmaceutical Knowledge Graph - Query Cache Management
#===========================================================
# 版本: v1.0
# 描述: 实现查询结果缓存，提升常用跨域查询性能
#===========================================================

import hashlib
import json
import time
from typing import Optional, Any, Dict
from functools import wraps
from datetime import datetime, timedelta


class QueryCache:
    """查询结果缓存管理器"""

    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存管理器

        Args:
            default_ttl: 默认缓存过期时间（秒），默认5分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def _generate_key(self, query: str, params: Optional[dict] = None) -> str:
        """
        生成缓存键

        Args:
            query: Cypher查询语句
            params: 查询参数

        Returns:
            缓存键
        """
        # 标准化查询（移除多余空格）
        normalized_query = " ".join(query.split())

        # 组合查询和参数
        cache_input = {
            "query": normalized_query,
            "params": params or {}
        }

        # 生成哈希
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(self, query: str, params: Optional[dict] = None) -> Optional[Any]:
        """
        从缓存获取查询结果

        Args:
            query: Cypher查询语句
            params: 查询参数

        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        key = self._generate_key(query, params)

        if key in self._cache:
            entry = self._cache[key]

            # 检查是否过期
            if time.time() - entry["timestamp"] < entry["ttl"]:
                self._stats["hits"] += 1
                return entry["data"]
            else:
                # 过期，删除
                del self._cache[key]
                self._stats["evictions"] += 1

        self._stats["misses"] += 1
        return None

    def set(
        self,
        query: str,
        data: Any,
        params: Optional[dict] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        设置查询结果到缓存

        Args:
            query: Cypher查询语句
            data: 查询结果
            params: 查询参数
            ttl: 缓存过期时间（秒），None表示使用默认值
        """
        key = self._generate_key(query, params)

        self._cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl if ttl is not None else self._default_ttl,
            "query": query,
            "params": params
        }

    def invalidate(self, query: str = None, params: Optional[dict] = None) -> None:
        """
        使缓存失效

        Args:
            query: 要失效的查询，None表示清空所有缓存
            params: 查询参数
        """
        if query is None:
            # 清空所有缓存
            count = len(self._cache)
            self._cache.clear()
            self._stats["evictions"] += count
        else:
            # 使特定查询失效
            key = self._generate_key(query, params)
            if key in self._cache:
                del self._cache[key]
                self._stats["evictions"] += 1

    def invalidate_pattern(self, pattern: str) -> int:
        """
        使匹配模式的缓存失效

        Args:
            pattern: 查询模式字符串

        Returns:
            失效的缓存条目数
        """
        keys_to_delete = []
        pattern_lower = pattern.lower()

        for key, entry in self._cache.items():
            if pattern_lower in entry["query"].lower():
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._cache[key]

        self._stats["evictions"] += len(keys_to_delete)
        return len(keys_to_delete)

    def cleanup_expired(self) -> int:
        """
        清理过期缓存条目

        Returns:
            清理的条目数
        """
        keys_to_delete = []
        current_time = time.time()

        for key, entry in self._cache.items():
            if current_time - entry["timestamp"] >= entry["ttl"]:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._cache[key]

        self._stats["evictions"] += len(keys_to_delete)
        return len(keys_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

    def clear_stats(self) -> None:
        """清空统计信息"""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }


# 全局缓存实例
_global_cache = QueryCache(default_ttl=300)


def get_cache() -> QueryCache:
    """获取全局缓存实例"""
    return _global_cache


def cached_query(ttl: int = 300, key_params: bool = True):
    """
    查询缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_params: 是否将参数包含在缓存键中

    Returns:
        装饰器函数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, query: str, params: Optional[dict] = None, **kwargs):
            cache = get_cache()

            # 检查缓存
            cache_params = params if key_params else None
            cached_result = cache.get(query, cache_params)

            if cached_result is not None:
                return cached_result

            # 执行查询
            result = func(self, query, params, **kwargs)

            # 存入缓存
            cache.set(query, result, cache_params, ttl=ttl)

            return result

        return wrapper

    return decorator


class CacheAwareQueryExecutor:
    """支持缓存的查询执行器"""

    def __init__(self, cache_ttl: int = 300):
        """
        初始化查询执行器

        Args:
            cache_ttl: 默认缓存过期时间（秒）
        """
        self.cache = get_cache()
        self.cache_ttl = cache_ttl

    def execute(
        self,
        query: str,
        params: Optional[dict] = None,
        use_cache: bool = True,
        ttl: Optional[int] = None
    ):
        """
        执行查询（带缓存）

        Args:
            query: Cypher查询语句
            params: 查询参数
            use_cache: 是否使用缓存
            ttl: 缓存过期时间，None表示使用默认值

        Returns:
            查询结果
        """
        if use_cache:
            # 尝试从缓存获取
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                return cached_result

        # 执行查询
        from .database import get_db
        db = get_db()
        result = db.execute_query(query, params)

        # 存入缓存
        if use_cache and result.success:
            self.cache.set(query, result, params, ttl=ttl or self.cache_ttl)

        return result

    def invalidate_related(self, entity_type: str, entity_id: str) -> None:
        """
        使相关实体的缓存失效

        Args:
            entity_type: 实体类型（如Compound, ClinicalTrial等）
            entity_id: 实体ID
        """
        # 使包含该实体的所有查询缓存失效
        patterns = [
            f"MATCH (:{entity_type} {{primary_id: '{entity_id}'}})",
            f"MATCH (:{entity_type})",
            f"WHERE .* '{entity_id}'"
        ]

        for pattern in patterns:
            self.cache.invalidate_pattern(pattern)


# 常用跨域查询的缓存配置
COMMON_QUERY_CACHE_CONFIG = {
    # 统计查询 - 长TTL（15分钟）
    "statistics": {
        "ttl": 900,
        "patterns": ["MATCH", "count(", "RETURN count"]
    },

    # 药物重定位查询 - 中等TTL（10分钟）
    "repurposing": {
        "ttl": 600,
        "patterns": ["POTENTIALLY_TREATS", "drug_repurposing"]
    },

    # 竞争分析 - 中等TTL（10分钟）
    "competitive": {
        "ttl": 600,
        "patterns": ["competitive_landscape", "pipeline_analysis"]
    },

    # 安全性查询 - 短TTL（5分钟）
    "safety": {
        "ttl": 300,
        "patterns": ["safety_profile", "adverse_event", "safety_signal"]
    },

    # 地理分布 - 长TTL（15分钟）
    "geographic": {
        "ttl": 900,
        "patterns": ["geographic_distribution", "country"]
    },

    # 时序分析 - 中等TTL（10分钟）
    "temporal": {
        "ttl": 600,
        "patterns": ["timeline", "year(", "start_date"]
    }
}


def get_cache_ttl_for_query(query: str) -> int:
    """
    根据查询类型自动确定缓存TTL

    Args:
        query: Cypher查询语句

    Returns:
        推荐的TTL（秒）
    """
    query_lower = query.lower()

    for category, config in COMMON_QUERY_CACHE_CONFIG.items():
        for pattern in config["patterns"]:
            if pattern.lower() in query_lower:
                return config["ttl"]

    # 默认TTL
    return 300


def setup_cache_monitoring(app):
    """
    设置缓存监控端点

    Args:
        app: FastAPI应用实例
    """

    @app.get("/cache/stats", tags=["System"])
    async def get_cache_stats():
        """获取缓存统计信息"""
        cache = get_cache()
        return cache.get_stats()

    @app.post("/cache/clear", tags=["System"])
    async def clear_cache(
        pattern: str = None,
        expired_only: bool = False
    ):
        """清空缓存"""
        cache = get_cache()

        if expired_only:
            count = cache.cleanup_expired()
            return {"message": f"Cleared {count} expired cache entries"}
        elif pattern:
            count = cache.invalidate_pattern(pattern)
            return {"message": f"Cleared {count} cache entries matching pattern"}
        else:
            cache.invalidate()
            return {"message": "Cleared all cache"}

    @app.post("/cache/reset-stats", tags=["System"])
    async def reset_cache_stats():
        """重置缓存统计"""
        cache = get_cache()
        cache.clear_stats()
        return {"message": "Cache statistics reset"}
