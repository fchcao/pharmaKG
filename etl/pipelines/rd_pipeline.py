#===========================================================
# PharmaKG ETL - R&D 领域管道
# Pharmaceutical Knowledge Graph - R&D Domain Pipeline
#===========================================================
# 版本: v1.0
# 描述: R&D 领域的完整 ETL 管道
#===========================================================

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import get_etl_config
from ..extractors.chembl import ChEMBLExtractor
from ..transformers.compound import CompoundTransformer
from ..transformers.target_disease import TargetTransformer
from ..loaders.neo4j_batch import Neo4jBatchLoader


logger = logging.getLogger(__name__)


class RDPipeline:
    """
    R&D 领域 ETL 管道

    处理流程:
    1. 从 ChEMBL 抽取化合物和靶点数据
    2. 转换和标准化
    3. 验证数据完整性
    4. 加载到 Neo4j
    """

    def __init__(self, config=None):
        """
        初始化 R&D 管道

        Args:
            config: ETL 配置
        """
        self.config = config or get_etl_config()

        # 初始化组件
        self.extractor = ChEMBLExtractor(
            api_key=self.config.chembl_api_key,
            rate_limit=self.config.api_rate_limit
        )

        self.compound_transformer = CompoundTransformer()
        self.target_transformer = TargetTransformer()

        self.stats = {
            "extracted_compounds": 0,
            "extracted_targets": 0,
            "extracted_activities": 0,
            "transformed_compounds": 0,
            "transformed_targets": 0,
            "loaded_compounds": 0,
            "loaded_targets": 0,
            "loaded_relationships": 0
        }

    def run(
        self,
        limit_compounds: int = 1000,
        limit_targets: int = 500,
        load_to_neo4j: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        运行 R&D ETL 管道

        Args:
            limit_compounds: 化合物数量限制
            limit_targets: 靶点数量限制
            load_to_neo4j: 是否加载到 Neo4j
            dry_run: 试运行模式

        Returns:
            执行结果统计
        """
        logger.info("=" * 60)
        logger.info("Starting R&D Domain ETL Pipeline")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # 1. 抽取阶段
            logger.info("\n[1/4] Extraction Phase")
            extracted_data = self._extract_phase(
                limit_compounds=limit_compounds,
                limit_targets=limit_targets
            )

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
                "pipeline": "R&D",
                "status": "success",
                "duration_seconds": duration,
                "extraction": {
                    "compounds": self.stats["extracted_compounds"],
                    "targets": self.stats["extracted_targets"],
                    "activities": self.stats["extracted_activities"]
                },
                "transformation": {
                    "compounds": self.stats["transformed_compounds"],
                    "targets": self.stats["transformed_targets"]
                },
                "validation": validation_results,
                "loading": load_results
            }

            logger.info("\n" + "=" * 60)
            logger.info(f"R&D ETL Pipeline completed in {duration:.2f}s")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"R&D ETL Pipeline failed: {e}", exc_info=True)
            return {
                "pipeline": "R&D",
                "status": "failed",
                "error": str(e),
                "extraction": {
                    "compounds": self.stats["extracted_compounds"],
                    "targets": self.stats["extracted_targets"]
                }
            }

    def _extract_phase(
        self,
        limit_compounds: int,
        limit_targets: int
    ) -> Dict[str, List[Dict]]:
        """抽取阶段"""
        logger.info("Extracting from ChEMBL...")

        # 抽取化合物
        compounds = list(self.extractor.extract_compounds(
            limit=limit_compounds,
            properties=["molecule_structures", "molecule_properties"]
        ))
        self.stats["extracted_compounds"] = len(compounds)
        logger.info(f"Extracted {len(compounds)} compounds")

        # 抽取靶点
        targets = list(self.extractor.extract_targets(
            limit=limit_targets
        ))
        self.stats["extracted_targets"] = len(targets)
        logger.info(f"Extracted {len(targets)} targets")

        # 抽取活性数据（可选，基于化合物）
        activities = []
        if compounds and targets:
            # 限制活性数据抽取
            activities = list(self.extractor.extract_activities(
                compound_id=None,  # 从所有化合物抽取
                target_id=None,
                limit=min(limit_compounds, 500)  # 限制活性数据数量
            ))
            self.stats["extracted_activities"] = len(activities)
            logger.info(f"Extracted {len(activities)} activity records")

        return {
            "compounds": compounds,
            "targets": targets,
            "activities": activities
        }

    def _transform_phase(self, extracted_data: Dict) -> Dict[str, List[Dict]]:
        """转换阶段"""
        logger.info("Transforming R&D data...")

        # 转换化合物
        compound_results = self.compound_transformer.transform_batch(
            extracted_data["compounds"]
        )
        transformed_compounds = [
            r.output_record for r in compound_results
            if r.status.name == "SUCCESS"
        ]
        self.stats["transformed_compounds"] = len(transformed_compounds)
        logger.info(
            f"Transformed {len(transformed_compounds)}/{len(compound_results)} compounds"
        )

        # 转换靶点
        target_results = self.target_transformer.transform_batch(
            extracted_data["targets"]
        )
        transformed_targets = [
            r.output_record for r in target_results
            if r.status.name == "SUCCESS"
        ]
        self.stats["transformed_targets"] = len(transformed_targets)
        logger.info(
            f"Transformed {len(transformed_targets)}/{len(target_results)} targets"
        )

        return {
            "compounds": transformed_compounds,
            "targets": transformed_targets,
            "activities": extracted_data["activities"]
        }

    def _validate_phase(self, data: Dict) -> Dict:
        """验证阶段"""
        from ..quality.validators import validate_batch

        validation_results = {
            "compounds": {},
            "targets": {}
        }

        # 验证化合物
        if data["compounds"]:
            compound_results = validate_batch(data["compounds"], "compound")
            valid_compounds = sum(1 for r in compound_results if r.is_valid)
            validation_results["compounds"] = {
                "total": len(data["compounds"]),
                "valid": valid_compounds,
                "invalid": len(data["compounds"]) - valid_compounds
            }

        # 验证靶点
        if data["targets"]:
            target_results = validate_batch(data["targets"], "target")
            valid_targets = sum(1 for r in target_results if r.is_valid)
            validation_results["targets"] = {
                "total": len(data["targets"]),
                "valid": valid_targets,
                "invalid": len(data["targets"]) - valid_targets
            }

        logger.info(
            f"Validation: {validation_results['compounds'].get('valid', 0)}/"
            f"{validation_results['compounds'].get('total', 0)} compounds, "
            f"{validation_results['targets'].get('valid', 0)}/"
            f"{validation_results['targets'].get('total', 0)} targets valid"
        )

        return validation_results

    def _load_phase(self, data: Dict) -> Dict:
        """加载阶段"""
        if self.config.dry_run:
            logger.info("[DRY RUN] Would load data to Neo4j")
            return {"dry_run": True}

        loader = Neo4jBatchLoader(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
            batch_size=self.config.batch_size,
            dry_run=self.config.dry_run
        )

        try:
            # 加载化合物节点
            compounds = data.get("compounds", [])
            if compounds:
                loader.load_nodes(
                    label="Compound",
                    records=compounds,
                    merge_key="primary_id",
                    additional_props={
                        "created_at": datetime.now().isoformat(),
                        "data_source": "chembl"
                    }
                )
                self.stats["loaded_compounds"] = len(compounds)
                logger.info(f"Loaded {len(compounds)} Compound nodes")

            # 加载靶点节点
            targets = data.get("targets", [])
            if targets:
                loader.load_nodes(
                    label="Target",
                    records=targets,
                    merge_key="primary_id",
                    additional_props={
                        "created_at": datetime.now().isoformat(),
                        "data_source": "chembl"
                    }
                )
                self.stats["loaded_targets"] = len(targets)
                logger.info(f"Loaded {len(targets)} Target nodes")

            # 加载化合物-靶点关系（基于活性数据）
            self._load_compound_target_relationships(loader, data)

            return loader.get_stats()

        finally:
            loader.close()

    def _load_compound_target_relationships(
        self,
        loader: Neo4jBatchLoader,
        data: Dict
    ):
        """加载化合物-靶点关系"""
        activities = data.get("activities", [])

        if not activities:
            return

        # 构建关系记录
        relationships = []
        for activity in activities:
            compound_chembl_id = activity.get("molecule_chembl_id")
            target_chembl_id = activity.get("target_chembl_id")

            if compound_chembl_id and target_chembl_id:
                relationships.append({
                    "from_id": f"chembl:{compound_chembl_id}",
                    "to_id": f"chembl.target:{target_chembl_id}",
                    "props": {
                        "activity_type": activity.get("standard_type"),
                        "activity_value": activity.get("standard_value"),
                        "activity_unit": activity.get("units"),
                        "assay_type": activity.get("assay_type"),
                        "confidence": activity.get("confidence", 9)  # ChEMBL confidence score
                    }
                })

        if relationships:
            # 加载关系
            loader.load_relationships(
                from_label="Compound",
                from_key="primary_id",
                to_label="Target",
                to_key="primary_id",
                rel_type="TARGETS",
                records=relationships,
                rel_properties={"props": "props"},
                merge=False
            )
            self.stats["loaded_relationships"] = len(relationships)
            logger.info(f"Loaded {len(relationships)} TARGETS relationships")


def run_rd_pipeline(
    limit_compounds: int = 1000,
    limit_targets: int = 500,
    load_to_neo4j: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：运行 R&D 管道

    Args:
        limit_compounds: 化合物数量限制
        limit_targets: 靶点数量限制
        load_to_neo4j: 是否加载到 Neo4j
        dry_run: 试运行模式

    Returns:
        执行结果
    """
    pipeline = RDPipeline()
    return pipeline.run(
        limit_compounds=limit_compounds,
        limit_targets=limit_targets,
        load_to_neo4j=load_to_neo4j,
        dry_run=dry_run
    )
