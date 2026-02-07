#===========================================================
# PharmaKG ETL - 基础抽取器类
# Pharmaceutical Knowledge Graph - Base Extractor
#===========================================================
# 版本: v1.0
# 描述: 通用数据抽取基类，提供错误处理、重试、进度跟踪
#===========================================================

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExtractorStatus(Enum):
    """抽取器状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ExtractionMetrics:
    """抽取指标"""
    source_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    api_calls: int = 0
    errors: List[Dict] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def duration(self) -> Optional[float]:
        """获取抽取持续时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """获取成功率"""
        if self.total_records > 0:
            return self.successful_records / self.total_records
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "source_name": self.source_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "total_records": self.total_records,
            "successful_records": self.successful_records,
            "failed_records": self.failed_records,
            "skipped_records": self.skipped_records,
            "api_calls": self.api_calls,
            "success_rate": f"{self.success_rate:.2%}",
            "error_count": len(self.errors)
        }


class BaseExtractor(ABC):
    """
    数据抽取器基类

    提供通用功能：
    - HTTP 会话管理（重试、超时）
    - 错误处理和重试
    - 进度跟踪
    - 速率限制
    - 日志记录
    """

    def __init__(
        self,
        name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        rate_limit: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        初始化抽取器

        Args:
            name: 数据源名称
            base_url: API 基础 URL
            api_key: API 密钥
            rate_limit: 请求速率限制（秒/请求）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries

        # 状态管理
        self._status = ExtractorStatus.IDLE
        self._metrics = ExtractionMetrics(source_name=name)
        self._last_request_time = 0.0

        # 创建 HTTP 会话
        self.session = self._create_session()

        logger.info(f"Initialized extractor: {name}")

    def _create_session(self) -> requests.Session:
        """
        创建配置好的 HTTP 会话

        Returns:
            配置了重试策略的 Session 对象
        """
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置默认超时
        session.timeout = self.timeout

        return session

    def _rate_limit_wait(self):
        """等待以满足速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.rate_limit:
            wait_time = self.rate_limit - time_since_last_request
            logger.debug(f"Rate limit wait: {wait_time:.2f}s")
            time.sleep(wait_time)

        self._last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> requests.Response:
        """
        发送 HTTP 请求

        Args:
            endpoint: API 端点
            method: HTTP 方法
            params: 查询参数
            data: 请求体数据
            headers: 请求头

        Returns:
            HTTP 响应对象

        Raises:
            requests.RequestException: 请求失败
        """
        # 速率限制等待
        self._rate_limit_wait()

        # 构建完整 URL
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint

        # 添加认证头
        request_headers = headers or {}
        if self.api_key:
            request_headers["Authorization"] = f"Bearer {self.api_key}"

        # 记录 API 调用
        self._metrics.api_calls += 1

        try:
            logger.debug(f"Request: {method} {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response

        except requests.RequestException as e:
            self._metrics.errors.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "endpoint": endpoint,
                "method": method
            })
            logger.error(f"Request failed: {e}")
            raise

    def fetch_all(
        self,
        limit: Optional[int] = None,
        batch_size: int = 100
    ) -> Generator[List[Dict], None, None]:
        """
        抽取所有数据（生成器）

        Args:
            limit: 最大记录数限制
            batch_size: 每批处理的记录数

        Yields:
            数据批次列表
        """
        self._status = ExtractorStatus.RUNNING
        self._metrics.start_time = datetime.now()

        logger.info(f"Starting extraction from {self.name}")

        try:
            batch = []
            total_fetched = 0

            for record in self._fetch_records():
                # 检查限制
                if limit and total_fetched >= limit:
                    logger.info(f"Reached limit of {limit} records")
                    break

                batch.append(record)
                total_fetched += 1

                # 当批次满时 yield
                if len(batch) >= batch_size:
                    self._metrics.total_records += len(batch)
                    self._metrics.successful_records += len(batch)
                    yield batch
                    batch = []
                    logger.info(f"Fetched {total_fetched} records so far...")

            # yield 最后一批
            if batch:
                self._metrics.total_records += len(batch)
                self._metrics.successful_records += len(batch)
                yield batch

            self._metrics.end_time = datetime.now()
            self._status = ExtractorStatus.COMPLETED

            logger.info(
                f"Extraction completed from {self.name}: "
                f"{self._metrics.total_records} records in "
                f"{self._metrics.duration:.2f}s"
            )

        except Exception as e:
            self._status = ExtractorStatus.FAILED
            self._metrics.end_time = datetime.now()
            logger.error(f"Extraction failed from {self.name}: {e}")
            raise

    @abstractmethod
    def _fetch_records(self) -> Generator[Dict, None, None]:
        """
        抽取记录的抽象方法

        由子类实现具体的抽取逻辑

        Yields:
            单条数据记录
        """
        pass

    @abstractmethod
    def get_total_count(self) -> Optional[int]:
        """
        获取总记录数的抽象方法

        Returns:
            总记录数，如果无法获取则返回 None
        """
        pass

    def get_metrics(self) -> ExtractionMetrics:
        """
        获取抽取指标

        Returns:
            抽取指标对象
        """
        return self._metrics

    def get_status(self) -> ExtractorStatus:
        """
        获取抽取器状态

        Returns:
            当前状态
        """
        return self._status

    def close(self):
        """关闭抽取器，释放资源"""
        if self.session:
            self.session.close()
        logger.info(f"Closed extractor: {self.name}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


class PaginatedExtractor(BaseExtractor):
    """
    支持分页的抽取器基类

    用于处理支持分页的 API
    """

    @abstractmethod
    def _fetch_page(self, page: int, page_size: int) -> List[Dict]:
        """
        抽取单页数据的抽象方法

        Args:
            page: 页码（从 1 开始）
            page_size: 每页大小

        Returns:
            该页的数据记录列表
        """
        pass

    @abstractmethod
    def get_total_pages(self, page_size: int) -> Optional[int]:
        """
        获取总页数的抽象方法

        Args:
            page_size: 每页大小

        Returns:
            总页数，如果无法获取则返回 None
        """
        pass

    def _fetch_records(
        self,
        start_page: int = 1,
        page_size: int = 100
    ) -> Generator[Dict, None, None]:
        """
        从所有页面抽取记录

        Args:
            start_page: 起始页码
            page_size: 每页大小

        Yields:
            单条数据记录
        """
        page = start_page

        while True:
            logger.debug(f"Fetching page {page} (size: {page_size})")

            try:
                records = self._fetch_page(page, page_size)

                if not records:
                    logger.info(f"No more records at page {page}")
                    break

                for record in records:
                    yield record

                # 如果返回的记录少于页面大小，说明是最后一页
                if len(records) < page_size:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                raise


class FileBasedExtractor(BaseExtractor):
    """
    基于文件的抽取器基类

    用于处理本地文件或下载的数据文件
    """

    @abstractmethod
    def _parse_file(self, file_path: str) -> Generator[Dict, None, None]:
        """
        解析文件的抽象方法

        Args:
            file_path: 文件路径

        Yields:
            单条数据记录
        """
        pass

    @abstractmethod
    def get_file_paths(self) -> List[str]:
        """
        获取要处理的文件路径列表

        Returns:
            文件路径列表
        """
        pass

    def _fetch_records(self) -> Generator[Dict, None, None]:
        """
        从所有文件抽取记录

        Yields:
            单条数据记录
        """
        file_paths = self.get_file_paths()
        logger.info(f"Found {len(file_paths)} files to process")

        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")

            try:
                for record in self._parse_file(file_path):
                    yield record

            except Exception as e:
                logger.error(f"Failed to parse file {file_path}: {e}")
                self._metrics.errors.append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "file_path": file_path
                })
