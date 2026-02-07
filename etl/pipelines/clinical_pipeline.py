#===========================================================
# PharmaKG ETL - 临床领域管道
# Pharmaceutical Knowledge Graph - Clinical Domain Pipeline
#===========================================================
# 版本: v1.0
# 描述: 临床领域的完整 ETL 管道
#===========================================================

import logging
from typing import Dict, List, Any
from datetime import datetime

from ..extractors.clinicaltrials import ClinicalTrialsGovExtractor
from ..transformers.trial import ClinicalTrialTransformer
from ..loaders.neo4j_batch import Neo4jBatchLoader
from ..config import get_etl_config


logger = logging.getLogger(__name__)


class ClinicalPipeline:
    """
    临床领域 ETL 管道

    处理流程:
    1. 从 ClinicalTrials.gov 抽取试验数据
    2. 转换和标准化试验数据
    3. 验证数据完整性
    4. 加载到 Neo4j
    """

    def __init__(self, config=None):
        """
        初始化临床管道

        Args:
            config: ETL 配置（可选，默认从环境变量读取）
        """
        self.config = config or get_etl_config()

        # 初始化组件
        self.extractor = ClinicalTrialsGovExtractor(
            api_key=self.config.clinicaltrials_api_key,
            rate_limit=self.config.clinicaltrials_rate_limit
        )
        self.transformer = ClinicalTrialTransformer()

        self.stats = {
            "extracted_studies": 0,
            "extracted_ae": 0,
            "transformed_studies": 0,
            "loaded_nodes": 0,
            "loaded_relationships": 0
        }

    def run(
        self,
        query: str = None,
        phase: str = None,
        limit: int = 1000,
        load_to_neo4j: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        运行临床 ETL 管道

        Args:
            query: 搜索查询（疾病、药物等）
            phase: 试验阶段筛选
            limit: 记录数限制
            load_to_neo4j: 是否加载到 Neo4j
            dry_run: 试运行模式

        Returns:
            执行结果统计
        """
        logger.info("=" * 60)
        logger.info("Starting Clinical Domain ETL Pipeline")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # 1. 抽取阶段
            logger.info("\n[1/4] Extraction Phase")
            extracted_data = self._extract_phase(
                query=query,
                phase=phase,
                limit=limit
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
                "pipeline": "Clinical",
                "status": "success",
                "duration_seconds": duration,
                "extraction": self.stats,
                "transformation": {
                    "studies": len(transformed_data.get("studies", [])),
                    "interventions": sum(len(s.get("interventions", [])) for s in transformed_data.get("studies", [])),
                    "locations": sum(len(s.get("locations", [])) for s in transformed_data.get("studies", []))
                },
                "validation": validation_results,
                "loading": load_results
            }

            logger.info("\n" + "=" * 60)
            logger.info(f"Clinical ETL Pipeline completed in {duration:.2f}s")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Clinical ETL Pipeline failed: {e}", exc_info=True)
            return {
                "pipeline": "Clinical",
                "status": "failed",
                "error": str(e),
                "extraction": self.stats
            }

    def _extract_phase(
        self,
        query: str,
        phase: str,
        limit: int
    ) -> Dict[str, List[Dict]]:
        """抽取阶段"""
        logger.info(f"Extracting from ClinicalTrials.gov (query={query}, phase={phase})...")

        # 抽取试验
        studies = list(self.extractor.extract_studies(
            query=query,
            phase=phase,
            limit=limit
        ))
        self.stats["extracted_studies"] = len(studies)
        logger.info(f"Extracted {len(studies)} clinical trial records")

        # 抽取不良事件（简化版本，实际应按试验抽取）
        adverse_events = []
        if studies:
            # 可选：抽取不良事件
            pass

        return {
            "studies": studies,
            "adverse_events": adverse_events
        }

    def _transform_phase(self, extracted_data: Dict) -> Dict[str, List[Dict]]:
        """转换阶段"""
        logger.info("Transforming clinical trial data...")
        trial_results = self.transformer.transform_batch(
            extracted_data["studies"]
        )

        successful = [
            r.output_record
            for r in trial_results
            if r.status.name == "SUCCESS"
        ]

        self.stats["transformed_studies"] = len(successful)
        logger.info(f"Transformed {len(successful)}/{len(trial_results)} clinical trials")

        return {
            "studies": successful
        }

    def _validate_phase(self, data: Dict) -> Dict:
        """验证阶段"""
        validation_results = {
            "studies": {
                "total": len(data.get("studies", [])),
                "valid": sum(
                    1 for r in self.transformer.transform_batch(
                        data.get("studies", [])
                    ) if r.status.name == "SUCCESS"
                ),
                "errors": []
            }
        }

        logger.info(
            f"Validation: {validation_results['studies']['valid']}/{validation_results['studies']['total']} studies valid"
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
            # 加载临床试验节点
            studies = data.get("studies", [])
            if studies:
                loader.load_nodes(
                    label="ClinicalTrial",
                    records=studies,
                    merge_key="primary_id",
                    additional_props={
                        "created_at": datetime.now().isoformat(),
                        "data_source": "clinicaltrials.gov"
                    }
                )
                self.stats["loaded_nodes"] += len(studies)
                logger.info(f"Loaded {len(studies)} ClinicalTrial nodes")

            # 加载干预措施节点和关系
            self._load_interventions(loader, studies)
            self._load_locations(loader, studies)

            return loader.get_stats()

        finally:
            loader.close()

    def _load_interventions(self, loader: Neo4jBatchLoader, studies: List[Dict]):
        """加载干预措施节点和关系"""
        interventions = []

        for study in studies:
            study_id = study.get("primary_id")
            for intervention in study.get("interventions", []):
                interventions.append({
                    "study_id": study_id,
                    "intervention_name": intervention.get("name"),
                    "intervention_type": intervention.get("intervention_type"),
                    "arm_group_label": intervention.get("arm_group_label"),
                    "props": {
                        "description": intervention.get("description"),
                        "created_at": datetime.now().isoformat()
                    }
                })

        if interventions:
            # 加载干预措施节点
            loader.load_nodes(
                label="Intervention",
                records=interventions,
                merge_key="intervention_name",
                additional_props={
                    "created_at": datetime.now().isoformat(),
                    "data_source": "clinicaltrials.gov"
                }
            )

            # 加载试验-干预措施关系
            loader.load_relationships(
                from_label="ClinicalTrial",
                from_key="primary_id",
                to_label="Intervention",
                to_key="intervention_name",
                rel_type="TESTS_INTERVENTION",
                records=interventions,
                rel_properties={},
                merge=False
            )

            logger.info(f"Loaded {len(interventions)} Intervention nodes")

    def _load_locations(self, loader: Neo4jBatchLoader, studies: List[Dict]):
        """加载研究地点节点和关系"""
        locations = []

        for study in studies:
            study_id = study.get("primary_id")
            for location in study.get("locations", []):
                # 唯一地点标识
                facility = location.get("facility")
                city = location.get("city")
                country = location.get("country")

                if facility or city or country:
                    # 创建唯一地点标识
                    location_id = f"{facility or city or country}".replace(" ", "-")
                    if country:
                        location_id = f"{location_id}-{country}"

                    locations.append({
                        "study_id": study_id,
                        "location_id": location_id,
                        "props": {
                            "facility": facility,
                            "name": location.get("name"),
                            "city": city,
                            "state": location.get("state"),
                            "country": country,
                            "lat": location.get("lat"),
                            "lon": location.get("lon"),
                            "status": location.get("status"),
                            "created_at": datetime.now().isoformat()
                        }
                    })

        if locations:
            # 加载地点节点
            loader.load_nodes(
                label="StudySite",
                records=locations,
                merge_key="location_id",
                additional_props={
                    "created_at": datetime.now().isoformat(),
                    "data_source": "clinicaltrials.gov"
                }
            )

            # 加载试验-地点关系
            loader.load_relationships(
                from_label="ClinicalTrial",
                from_key="primary_id",
                to_label="StudySite",
                to_key="location_id",
                rel_type="CONDUCTED_AT_SITE",
                records=locations,
                rel_properties={},
                merge=True
            )

            logger.info(f"Loaded {len(locations)} StudySite nodes")


def run_clinical_pipeline(
    query: str = None,
    phase: str = None,
    limit: int = 1000,
    load_to_neo4j: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：运行临床管道

    Args:
        query: 搜索查询
        phase: 试验阶段
        limit: 记录数限制
        load_to_neo4j: 是否加载到 Neo4j
        dry_run: 试运行模式

    Returns:
        执行结果
    """
    pipeline = ClinicalPipeline()
    return pipeline.run(
        query=query,
        phase=phase,
        limit=limit,
        load_to_neo4j=load_to_neo4j,
        dry_run=dry_run
    )
