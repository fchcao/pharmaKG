#!/usr/bin/env python3
#===========================================================
# PharmaKG ETL - CLI 工具
# Pharmaceutical Knowledge Graph - ETL Command Line Interface
#===========================================================
# 版本: v1.0
# 描述: ETL 管道的命令行工具
#===========================================================

import argparse
import logging
import sys
from typing import Optional, List
from datetime import datetime
import json

from .config import get_etl_config, PipelineConfig
from .scheduler import ETLScheduler


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('etl.log')
    ]
)

logger = logging.getLogger(__name__)


# 导入各个管道
def _import_pipelines():
    """延迟导入管道模块"""
    from .pipelines.rd_pipeline import RDPipeline, run_rd_pipeline
    from .pipelines.clinical_pipeline import ClinicalPipeline, run_clinical_pipeline
    from .pipelines.sc_pipeline import SupplyChainPipeline, run_supply_chain_pipeline
    from .pipelines.regulatory_pipeline import RegulatoryPipeline, run_regulatory_pipeline
    return {
        "rd": (RDPipeline, run_rd_pipeline),
        "clinical": (ClinicalPipeline, run_clinical_pipeline),
        "sc": (SupplyChainPipeline, run_supply_chain_pipeline),
        "regulatory": (RegulatoryPipeline, run_regulatory_pipeline)
    }


def run_pipeline(
    pipeline_name: str,
    **kwargs
) -> dict:
    """
    运行指定管道

    Args:
        pipeline_name: 管道名称 (rd, clinical, sc, regulatory)
        **kwargs: 管道参数

    Returns:
        执行结果
    """
    pipelines = _import_pipelines()

    if pipeline_name not in pipelines:
        logger.error(f"Unknown pipeline: {pipeline_name}")
        logger.info(f"Available pipelines: {', '.join(pipelines.keys())}")
        return {"status": "error", "message": f"Unknown pipeline: {pipeline_name}"}

    pipeline_class, run_func = pipelines[pipeline_name]

    logger.info(f"Running {pipeline_name.upper()} pipeline...")

    try:
        result = run_func(**kwargs)
        return result
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def run_all_pipelines(
    config_file: Optional[str] = None,
    dry_run: bool = False,
    load_to_neo4j: bool = True
) -> dict:
    """
    运行所有配置的管道

    Args:
        config_file: 管道配置文件路径
        dry_run: 试运行模式
        load_to_neo4j: 是否加载到 Neo4j

    Returns:
        执行结果
    """
    scheduler = ETLScheduler()

    # 加载管道配置
    if config_file:
        import yaml
        with open(config_file, 'r') as f:
            pipeline_configs = yaml.safe_load(f)
    else:
        # 使用默认配置
        from .config import (
            RD_PIPELINE_CONFIG,
            CLINICAL_PIPELINE_CONFIG,
            SC_PIPELINE_CONFIG,
            REGULATORY_PIPELINE_CONFIG
        )
        pipeline_configs = {
            "rd": RD_PIPELINE_CONFIG,
            "clinical": CLINICAL_PIPELINE_CONFIG,
            "sc": SC_PIPELINE_CONFIG,
            "regulatory": REGULATORY_PIPELINE_CONFIG
        }

    results = {}

    for name, config in pipeline_configs.items():
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Running {name.upper()} pipeline")
        logger.info(f"{'=' * 60}\n")

        # 注册管道
        scheduler.register_pipeline(name, config)

        # 执行管道
        result = scheduler.execute_pipeline(name, config)
        results[name] = result

        if result.get("status") == "failed":
            logger.error(f"Pipeline {name} failed: {result.get('error')}")

    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 60)

    for name, result in results.items():
        status = result.get("status", "unknown")
        duration = result.get("duration_seconds", 0)
        logger.info(f"{name.upper()}: {status} ({duration:.2f}s)")

    return {
        "status": "completed",
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


def show_pipeline_status():
    """显示管道状态"""
    scheduler = ETLScheduler()
    progress = scheduler.get_progress()

    print("\n" + "=" * 60)
    print("PIPELINE STATUS")
    print("=" * 60)

    print(f"\nTotal tasks: {progress['total_tasks']}")
    print(f"Completed: {progress['completed_tasks']}")
    print(f"Failed: {progress['failed_tasks']}")
    print(f"Pending: {progress['pending_tasks']}")
    print(f"Running: {progress['running_tasks']}")

    if progress['task_details']:
        print("\nTask Details:")
        for task_id, details in progress['task_details'].items():
            status = details.get('status', 'UNKNOWN')
            print(f"  {task_id}: {status}")


def validate_config(config_file: str) -> bool:
    """
    验证配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        是否有效
    """
    import yaml

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # 验证必需字段
        required_fields = ["neo4j_uri", "neo4j_user", "neo4j_password"]
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field: {field}")
                return False

        # 验证管道配置
        if "pipelines" in config:
            for pipeline_name, pipeline_config in config["pipelines"].items():
                if "extraction_tasks" not in pipeline_config:
                    logger.error(f"Pipeline {pipeline_name} missing extraction_tasks")
                    return False
                if "transformation_tasks" not in pipeline_config:
                    logger.error(f"Pipeline {pipeline_name} missing transformation_tasks")
                    return False
                if "load_tasks" not in pipeline_config:
                    logger.error(f"Pipeline {pipeline_name} missing load_tasks")
                    return False

        logger.info("Configuration file is valid")
        return True

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def create_sample_config(output_file: str = "etl_config.yaml"):
    """
    创建示例配置文件

    Args:
        output_file: 输出文件路径
    """
    import yaml

    sample_config = {
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password",
        "batch_size": 500,
        "dry_run": False,
        "pipelines": {
            "rd": {
                "enabled": True,
                "limit_compounds": 1000,
                "limit_targets": 500,
                "load_to_neo4j": True
            },
            "clinical": {
                "enabled": True,
                "query": "cancer",
                "phase": "Phase 2",
                "limit": 500,
                "load_to_neo4j": True
            },
            "sc": {
                "enabled": True,
                "limit": 500,
                "load_to_neo4j": True
            },
            "regulatory": {
                "enabled": True,
                "data_file": "/path/to/fda_data.zip",
                "limit": 1000,
                "load_to_neo4j": True
            }
        }
    }

    with open(output_file, 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False)

    logger.info(f"Sample configuration written to {output_file}")


def main():
    """主 CLI 入口"""
    parser = argparse.ArgumentParser(
        description="PharmaKG ETL Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 运行 R&D 管道
  etl-cli run rd --limit-compounds 1000 --dry-run

  # 运行临床管道
  etl-cli run clinical --query cancer --phase "Phase 2" --limit 500

  # 运行所有管道
  etl-cli run-all --config etl_config.yaml

  # 查看管道状态
  etl-cli status

  # 创建示例配置
  etl-cli init-config --output etl_config.yaml
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run 命令
    run_parser = subparsers.add_parser("run", help="Run a specific pipeline")
    run_parser.add_argument(
        "pipeline",
        choices=["rd", "clinical", "sc", "regulatory"],
        help="Pipeline to run"
    )

    # R&D 管道参数
    run_parser.add_argument("--limit-compounds", type=int, default=1000,
                           help="Limit number of compounds to extract")
    run_parser.add_argument("--limit-targets", type=int, default=500,
                           help="Limit number of targets to extract")

    # 临床管道参数
    run_parser.add_argument("--query", type=str, help="Search query for clinical trials")
    run_parser.add_argument("--phase", type=str, help="Clinical trial phase filter")

    # 供应链管道参数
    run_parser.add_argument("--data-file", type=str, help="Data file path for supply chain")

    # 监管管道参数
    run_parser.add_argument("--fda-file", type=str, help="FDA data file path (ZIP format)")

    # 通用参数
    run_parser.add_argument("--limit", type=int, default=500,
                           help="General record limit")
    run_parser.add_argument("--dry-run", action="store_true",
                           help="Dry run mode (no data loading)")
    run_parser.add_argument("--no-load", action="store_true",
                           help="Skip loading to Neo4j")

    # run-all 命令
    run_all_parser = subparsers.add_parser("run-all", help="Run all configured pipelines")
    run_all_parser.add_argument("--config", type=str,
                               help="Pipeline configuration file (YAML)")
    run_all_parser.add_argument("--dry-run", action="store_true",
                               help="Dry run mode")
    run_all_parser.add_argument("--no-load", action="store_true",
                               help="Skip loading to Neo4j")

    # status 命令
    status_parser = subparsers.add_parser("status", help="Show pipeline status")

    # init-config 命令
    init_parser = subparsers.add_parser("init-config", help="Create sample configuration file")
    init_parser.add_argument("--output", type=str, default="etl_config.yaml",
                            help="Output file path")

    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="Validate configuration file")
    validate_parser.add_argument("config_file", type=str,
                                help="Configuration file to validate")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 执行命令
    if args.command == "run":
        # 准备参数
        kwargs = {"dry_run": args.dry_run, "load_to_neo4j": not args.no_load}

        if args.pipeline == "rd":
            kwargs["limit_compounds"] = args.limit_compounds
            kwargs["limit_targets"] = args.limit_targets
        elif args.pipeline == "clinical":
            kwargs["query"] = args.query
            kwargs["phase"] = args.phase
            kwargs["limit"] = args.limit
        elif args.pipeline == "sc":
            kwargs["data_file"] = args.data_file
            kwargs["limit"] = args.limit
        elif args.pipeline == "regulatory":
            kwargs["data_file"] = args.fda_file
            kwargs["limit"] = args.limit

        result = run_pipeline(args.pipeline, **kwargs)

        # 输出结果
        print("\n" + "=" * 60)
        print("EXECUTION RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))

        return 0 if result.get("status") == "success" else 1

    elif args.command == "run-all":
        result = run_all_pipelines(
            config_file=args.config,
            dry_run=args.dry_run,
            load_to_neo4j=not args.no_load
        )

        print("\n" + "=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))

        return 0 if result.get("status") == "completed" else 1

    elif args.command == "status":
        show_pipeline_status()
        return 0

    elif args.command == "init-config":
        create_sample_config(args.output)
        return 0

    elif args.command == "validate":
        is_valid = validate_config(args.config_file)
        return 0 if is_valid else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
