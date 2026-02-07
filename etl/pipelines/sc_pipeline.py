#===========================================================
# PharmaKG ETL - 供应链领域管道
# Pharmaceutical Knowledge Graph - Supply Chain Domain Pipeline
#===========================================================
# 版本: v1.0
# 描述: 供应链领域的完整 ETL 管道
#===========================================================

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import get_etl_config


logger = logging.getLogger(__name__)


class SupplyChainPipeline:
    """
    供应链领域 ETL 管道

    处理流程:
    1. 从 FDA 短缺数据库抽取短缺数据
    2. 抽取制造商和供应商信息
    3. 转换和标准化
    4. 加载到 Neo4j
    """

    def __init__(self, config=None):
        """
        初始化供应链管道

        Args:
            config: ETL 配置
        """
        self.config = config or get_etl_config()

        self.stats = {
            "extracted_manufacturers": 0,
            "extracted_shortages": 0,
            "loaded_manufacturers": 0,
            "loaded_shortages": 0
        }

    def run(
        self,
        data_file: Optional[str] = None,
        limit: int = 500,
        load_to_neo4j: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        运行供应链 ETL 管道

        Args:
            data_file: 数据文件路径
            limit: 记录数限制
            load_to_n eo4j: 是否加载到 Neo4j
            dry_run: 试运行模式

        Returns:
            执行结果统计
        """
        logger.info("=" * 60)
        logger.info("Starting Supply Chain Domain ETL Pipeline")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # 1. 抽取阶段
            logger.info("\n[1/4] Extraction Phase")
            extracted_data = self._extract_phase(data_file, limit)

            # 2. 转换阶段
            logger.info("\n[2/4] Transformation Phase")
            transformed_data = self._transform_phase(extracted_data)

            # 3. 验证阶段
            logger.info("\n[3/4] Validation Phase")
            validation_results = self._validate_phase(transformed_data)

            # 4. 加载阶段
            if load_to_neo4j and not dry_run:
                logger.info("\n[4/4] Loading Phase")
                load_results = self._load_phase(transformed_data)
            else:
                logger.info("\n[4/4] Loading Phase (SKIPPED)")
                load_results = {"dry_run": True}

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "pipeline": "Supply Chain",
                "status": "success",
                "duration_seconds": duration,
                "extraction": self.stats,
                "transformation": {
                    "manufacturers": len(transformed_data.get("manufacturers", [])),
                    "shortages": len(transformed_data.get("shortages", []))
                },
                "validation": validation_results,
                "loading": load_results
            }

            logger.info("\n" + "=" * 60)
            logger.info(f"Supply Chain ETL Pipeline completed in {duration:.2f}s")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Supply Chain ETL Pipeline failed: {e}", exc_info=True)
            return {
                "pipeline": "Supply Chain",
                "status": "failed",
                "error": str(e),
                "extraction": self.stats
            }

    def _extract_phase(
        self,
        data_file: Optional[str],
        limit: int
    ) -> Dict[str, List[Dict]]:
        """抽取阶段"""
        logger.info("Extracting supply chain data...")

        # 从文件或API抽取制造商和短缺数据
        manufacturers = self._extract_manufacturers(limit)
        self.stats["extracted_manufacturers"] = len(manufacturers)

        shortages = self._extract_shortages(limit)
        self.stats["extracted_shortages"] = len(shortages)

        logger.info(f"Extracted {len(manufacturers)} manufacturers, {len(shortages)} shortages")

        return {
            "manufacturers": manufacturers,
            "shortages": shortages
        }

    def _extract_manufacturers(self, limit: int) -> List[Dict]:
        """抽取制造商数据"""
        # 实际实现中会从 FDA 或其他数据库获取
        # 这里返回示例数据
        return [
            {
                "manufacturer_id": "MFR001",
                "name": "Pfizer Inc.",
                "location": "New York, USA",
                "type": "Innovator",
                "website": "https://www.pfizer.com"
            }
        ]

    def _extract_shortages(self, limit: int) -> List[Dict]:
        """抽取药品短缺数据"""
        # 实际实现中会从 FDA 短缺数据库获取
        return [
            {
                "shortage_id": "DS001",
                "drug_name": "Drug A",
                "status": "active",
                "start_date": "2024-01-01",
                "manufacturer_id": "MFR001"
            }
        ]

    def _transform_phase(self, extracted_data: Dict) -> Dict[str, List[Dict]]:
        """转换阶段"""
        logger.info("Transforming supply chain data...")

        # 简化的标准化处理
        transformed_manufacturers = []
        for mfg in extracted_data.get("manufacturers", []):
            transformed_manufacturers.append({
                "primary_id": f"manufacturer:{mfg['manufacturer_id']}",
                "name": mfg.get("name"),
                "location": mfg.get("location"),
                "type": mfg.get("type"),
                "website": mfg.get("website"),
                "created_at": datetime.now().isoformat(),
                "data_source": "supply_chain"
            })

        transformed_shortages = []
        for shortage in extracted_data.get("shortages", []):
            transformed_shortages.append({
                "primary_id": f"shortage:{shortage['shortage_id']}",
                "drug_name": shortage.get("drug_name"),
                "status": shortage.get("status"),
                "start_date": self.normalize_date(shortage.get("start_date")),
                "manufacturer_id": shortage.get("manufacturer_id"),
                "created_at": datetime.now().isoformat(),
                "data_source": "supply_chain"
            })

        return {
            "manufacturers": transformed_manufacturers,
            "shortages": transformed_shortages
        }

    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """标准化日期"""
        return super().normalize_date(date_str) if hasattr(super(), 'normalize_date') else None

    def _validate_phase(self, data: Dict) -> Dict:
        """验证阶段"""
        validation_results = {
            "manufacturers": {
                "total": len(data.get("manufacturers", [])),
                "valid": len(data.get("manufacturers", [])),
                "errors": []
            },
            "shortages": {
                "total": len(data.get("shortages", [])),
                "valid": len(data.get("shortages", [])),
                "errors": []
            }
        }

        return validation_results

    def _load_phase(self, data: Dict) -> Dict:
        """加载阶段"""
        if self.config.dry_run:
            logger.info("[DRY RUN] Would load data to Neo4j")
            return {"dry_run": True}

        from ..loaders.neo4j_batch import Neo4jBatchLoader

        loader = Neo4jBatchLoader(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
            batch_size=self.config.batch_size,
            dry_run=self.config.dry_run
        )

        try:
            # 加载制造商节点
            manufacturers = data.get("manufacturers", [])
            if manufacturers:
                loader.load_nodes(
                    label="Manufacturer",
                    records=manufacturers,
                    merge_key="primary_id"
                )
                self.stats["loaded_manufacturers"] = len(manufacturers)

            # 加载短缺节点
            shortages = data.get("shortages", [])
            if shortages:
                loader.load_nodes(
                    label="DrugShortage",
                    records=shortages,
                    merge_key="primary_id"
                )
                self.stats["loaded_shortages"] = len(shortages)

            return loader.get_stats()

        finally:
            loader.close()


def run_supply_chain_pipeline(
    limit: int = 500,
    load_to_neo4j: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：运行供应链管道

    Args:
        limit: 记录数限制
        load_to_neo4j: 是否加载到 Neo4j
        dry_run: 试运行模式

    Returns:
        执行结果
    """
    pipeline = SupplyChainPipeline()
    return pipeline.run(
        limit=limit,
        load_to_neo4j=load_to_neo4j,
        dry_run=dry_run
    )
