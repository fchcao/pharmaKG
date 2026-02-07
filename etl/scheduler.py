#===========================================================
# PharmaKG ETL - 任务调度器
# Pharmaceutical Knowledge Graph - ETL Task Scheduler
#===========================================================
# 版本: v1.0
# 描述: ETL 管道的任务调度和执行管理
#===========================================================

import logging
import threading
import time
from typing import Dict, Callable, Optional, List, Any
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .config import PipelineConfig, ExtractionTask, TransformationTask, LoadTask


logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    name: str
    func: Callable
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    enabled: bool = True
    timeout: int = 300
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class ETLScheduler:
    """
    ETL 任务调度器

    功能：
    - 任务注册和管理
    - 依赖关系解析
    - 并发执行控制
    - 进度跟踪
    - 错误处理和重试
    """

    def __init__(self, max_workers: int = 4):
        """
        初始化调度器

        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_order: List[str] = []
        self._lock = threading.Lock()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[str, Future] = {}
        self._progress_callbacks: List[Callable] = []

        # 统计信息
        self._stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }

    def register_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        priority: int = 0,
        dependencies: Optional[List[str]] = None,
        enabled: bool = True,
        timeout: int = 300,
        max_retries: int = 3
    ) -> None:
        """
        注册任务

        Args:
            task_id: 任务唯一标识
            name: 任务名称
            func: 任务执行函数
            priority: 优先级（数字越大越优先）
            dependencies: 依赖的任务 ID 列表
            enabled: 是否启用
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
        """
        with self._lock:
            if task_id in self.tasks:
                logger.warning(f"Task {task_id} already registered, overwriting")

            self.tasks[task_id] = TaskInfo(
                task_id=task_id,
                name=name,
                func=func,
                priority=priority,
                dependencies=dependencies or [],
                enabled=enabled,
                timeout=timeout,
                max_retries=max_retries
            )

            # 更新任务顺序（按优先级排序）
            self._update_task_order()

            logger.debug(f"Registered task: {task_id} (priority={priority})")

    def register_pipeline(
        self,
        pipeline_name: str,
        config: PipelineConfig
    ) -> None:
        """
        注册管道配置

        Args:
            pipeline_name: 管道名称
            config: 管道配置
        """
        logger.info(f"Registering pipeline: {pipeline_name}")

        # 注册抽取任务
        for task in config.extraction_tasks:
            if task.enabled:
                self.register_task(
                    task_id=f"{pipeline_name}.{task.name}",
                    name=task.name,
                    func=lambda: None,  # 实际函数由管道提供
                    priority=task.priority,
                    dependencies=task.dependencies,
                    enabled=task.enabled,
                    timeout=task.timeout
                )

        # 注册转换任务
        for task in config.transformation_tasks:
            if task.enabled:
                deps = [f"{pipeline_name}.{d}" for d in task.dependencies]
                self.register_task(
                    task_id=f"{pipeline_name}.{task.name}",
                    name=task.name,
                    func=lambda: None,
                    priority=task.priority,
                    dependencies=deps,
                    enabled=task.enabled,
                    timeout=task.timeout
                )

        # 注册加载任务
        for task in config.load_tasks:
            if task.enabled:
                deps = [f"{pipeline_name}.{d}" for d in task.dependencies]
                self.register_task(
                    task_id=f"{pipeline_name}.{task.name}",
                    name=task.name,
                    func=lambda: None,
                    priority=task.priority,
                    dependencies=deps,
                    enabled=task.enabled,
                    timeout=task.timeout
                )

    def _update_task_order(self) -> None:
        """更新任务执行顺序（按优先级排序）"""
        enabled_tasks = [
            (task_id, task.priority)
            for task_id, task in self.tasks.items()
            if task.enabled
        ]
        # 按优先级降序排序
        self.task_order = [
            task_id for task_id, _ in
            sorted(enabled_tasks, key=lambda x: x[1], reverse=True)
        ]

    def _resolve_dependencies(self, task_id: str) -> bool:
        """
        检查任务依赖是否都已满足

        Args:
            task_id: 任务 ID

        Returns:
            依赖是否已满足
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task:
                logger.error(f"Dependency {dep_id} not found for task {task_id}")
                return False

            if dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    def _execute_task(self, task_info: TaskInfo) -> Any:
        """
        执行单个任务

        Args:
            task_info: 任务信息

        Returns:
            任务执行结果
        """
        task_id = task_info.task_id
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.now()

        logger.info(f"Executing task: {task_id}")

        try:
            # 执行任务函数
            result = task_info.func()
            task_info.result = result
            task_info.status = TaskStatus.COMPLETED

            logger.info(f"Task completed: {task_id}")
            self._notify_progress(task_id, TaskStatus.COMPLETED)

            return result

        except Exception as e:
            logger.error(f"Task failed: {task_id} - {e}")

            task_info.error = str(e)

            # 检查是否需要重试
            if task_info.retry_count < task_info.max_retries:
                task_info.retry_count += 1
                task_info.status = TaskStatus.PENDING

                logger.info(f"Retrying task {task_id} (attempt {task_info.retry_count}/{task_info.max_retries})")
                time.sleep(1)  # 重试前等待

                return self._execute_task(task_info)
            else:
                task_info.status = TaskStatus.FAILED
                self._notify_progress(task_id, TaskStatus.FAILED)
                raise

        finally:
            task_info.completed_at = datetime.now()

    def execute_task(
        self,
        task_id: str,
        retry_count: int = 0
    ) -> Any:
        """
        执行指定任务

        Args:
            task_id: 任务 ID
            retry_count: 重试次数

        Returns:
            任务执行结果
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if not task.enabled:
            logger.info(f"Task {task_id} is disabled, skipping")
            task.status = TaskStatus.SKIPPED
            return None

        # 检查依赖
        if not self._resolve_dependencies(task_id):
            logger.warning(f"Dependencies not satisfied for task {task_id}")
            return None

        # 执行任务
        return self._execute_task(task)

    def execute_pipeline(
        self,
        pipeline_name: str,
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """
        执行管道

        Args:
            pipeline_name: 管道名称
            config: 管道配置

        Returns:
            执行结果
        """
        logger.info(f"Executing pipeline: {pipeline_name}")
        start_time = datetime.now()

        try:
            # 导入管道类
            if pipeline_name == "rd":
                from .pipelines.rd_pipeline import RDPipeline
                pipeline = RDPipeline()
                result = pipeline.run(
                    limit_compounds=config.params.get("limit_compounds", 1000),
                    limit_targets=config.params.get("limit_targets", 500),
                    dry_run=config.params.get("dry_run", False)
                )
            elif pipeline_name == "clinical":
                from .pipelines.clinical_pipeline import ClinicalPipeline
                pipeline = ClinicalPipeline()
                result = pipeline.run(
                    query=config.params.get("query"),
                    phase=config.params.get("phase"),
                    limit=config.params.get("limit", 500),
                    dry_run=config.params.get("dry_run", False)
                )
            elif pipeline_name == "sc":
                from .pipelines.sc_pipeline import SupplyChainPipeline
                pipeline = SupplyChainPipeline()
                result = pipeline.run(
                    data_file=config.params.get("data_file"),
                    limit=config.params.get("limit", 500),
                    dry_run=config.params.get("dry_run", False)
                )
            elif pipeline_name == "regulatory":
                from .pipelines.regulatory_pipeline import RegulatoryPipeline
                pipeline = RegulatoryPipeline()
                result = pipeline.run(
                    data_file=config.params.get("data_file"),
                    limit=config.params.get("limit", 1000),
                    dry_run=config.params.get("dry_run", False)
                )
            else:
                raise ValueError(f"Unknown pipeline: {pipeline_name}")

            duration = (datetime.now() - start_time).total_seconds()
            result["duration_seconds"] = duration

            return result

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return {
                "pipeline": pipeline_name,
                "status": "failed",
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }

    def execute_all(
        self,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        执行所有已注册的任务

        Args:
            parallel: 是否并行执行

        Returns:
            执行结果汇总
        """
        logger.info("Executing all tasks...")
        start_time = datetime.now()

        results = {}

        if parallel:
            # 并行执行
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

            for task_id in self.task_order:
                task = self.tasks[task_id]
                if task.enabled and self._resolve_dependencies(task_id):
                    future = self._executor.submit(self.execute_task, task_id)
                    self._futures[task_id] = future

            # 等待所有任务完成
            for task_id, future in self._futures.items():
                try:
                    results[task_id] = future.result()
                except Exception as e:
                    results[task_id] = {"error": str(e)}

            if self._executor:
                self._executor.shutdown(wait=True)
        else:
            # 串行执行
            for task_id in self.task_order:
                task = self.tasks[task_id]
                if task.enabled:
                    try:
                        results[task_id] = self.execute_task(task_id)
                    except Exception as e:
                        results[task_id] = {"error": str(e)}

        duration = (datetime.now() - start_time).total_seconds()

        # 统计结果
        completed = sum(1 for r in results.values() if "error" not in r)
        failed = len(results) - completed

        return {
            "status": "completed",
            "total_tasks": len(results),
            "completed": completed,
            "failed": failed,
            "duration_seconds": duration,
            "results": results
        }

    def get_progress(self) -> Dict[str, Any]:
        """
        获取执行进度

        Returns:
            进度信息
        """
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

        task_details = {}
        for task_id, task in self.tasks.items():
            task_details[task_id] = {
                "name": task.name,
                "status": task.status.value,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error
            }

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "pending_tasks": pending,
            "running_tasks": running,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "task_details": task_details
        }

    def add_progress_callback(self, callback: Callable) -> None:
        """
        添加进度回调函数

        Args:
            callback: 回调函数，接收 (task_id, status) 参数
        """
        self._progress_callbacks.append(callback)

    def _notify_progress(self, task_id: str, status: TaskStatus) -> None:
        """通知进度更新"""
        for callback in self._progress_callbacks:
            try:
                callback(task_id, status)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.RUNNING:
            # 取消 Future
            future = self._futures.get(task_id)
            if future:
                future.cancel()

        task.status = TaskStatus.CANCELLED
        logger.info(f"Task cancelled: {task_id}")
        return True

    def reset(self) -> None:
        """重置调度器状态"""
        with self._lock:
            self.tasks.clear()
            self.task_order.clear()
            self._futures.clear()
            self._stats = {"total": 0, "completed": 0, "failed": 0, "skipped": 0}

        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None

        logger.info("Scheduler reset")
