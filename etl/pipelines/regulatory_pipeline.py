#===========================================================
# PharmaKG ETL - 监管领域管道
# Pharmaceutical Knowledge Graph - Regulatory Domain Pipeline
#===========================================================
# 版本: v1.0
# 描述: 监管领域的完整 ETL 管道
#===========================================================

import logging
import zipfile
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..config import get_etl_config
from ..loaders import Neo4jBatchLoader


logger = logging.getLogger(__name__)


class RegulatoryPipeline:
    """
    监管领域 ETL 管道

    处理流程:
    1. 从 FDA 抽取产品和应用数据
    2. 转换和标准化
    3. 验证数据完整性
    4. 加载到 Neo4j
    """

    def __init__(self, config=None):
        """
        初始化监管管道

        Args:
            config: ETL 配置
        """
        self.config = config or get_etl_config()

        self.stats = {
            "extracted_products": 0,
            "extracted_applications": 0,
            "extracted_tecodes": 0,
            "loaded_products": 0,
            "loaded_applications": 0,
            "loaded_tecodes": 0
        }

    def run(
        self,
        data_file: Optional[str] = None,
        limit: int = 1000,
        load_to_neo4j: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        运行监管 ETL 管道

        Args:
            data_file: 数据文件路径（ZIP 格式）
            limit: 记录数限制
            load_to_neo4j: 是否加载到 Neo4j
            dry_run: 试运行模式

        Returns:
            执行结果统计
        """
        logger.info("=" * 60)
        logger.info("Starting Regulatory Domain ETL Pipeline")
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
                "pipeline": "Regulatory",
                "status": "success",
                "duration_seconds": duration,
                "extraction": self.stats,
                "transformation": {
                    "products": len(transformed_data.get("products", [])),
                    "applications": len(transformed_data.get("applications", [])),
                    "tecodes": len(transformed_data.get("tecodes", []))
                },
                "validation": validation_results,
                "loading": load_results
            }

            logger.info("\n" + "=" * 60)
            logger.info(f"Regulatory ETL Pipeline completed in {duration:.2f}s")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Regulatory ETL Pipeline failed: {e}", exc_info=True)
            return {
                "pipeline": "Regulatory",
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
        logger.info("Extracting regulatory data...")

        if data_file:
            # 从文件抽取
            products = self._extract_products_from_file(data_file, limit)
            applications = self._extract_applications_from_file(data_file, limit)
            tecodes = self._extract_tecodes_from_file(data_file, limit)
        else:
            # 从示例数据抽取（实际应从 FDA API 获取）
            products = self._extract_products(limit)
            applications = self._extract_applications(limit)
            tecodes = self._extract_tecodes(limit)

        self.stats["extracted_products"] = len(products)
        self.stats["extracted_applications"] = len(applications)
        self.stats["extracted_tecodes"] = len(tecodes)

        logger.info(
            f"Extracted {len(products)} products, "
            f"{len(applications)} applications, "
            f"{len(tecodes)} TE codes"
        )

        return {
            "products": products,
            "applications": applications,
            "tecodes": tecodes
        }

    def _extract_products_from_file(self, file_path: str, limit: int) -> List[Dict]:
        """从文件抽取产品数据"""
        from ..extractors.fda import FDAExtractors

        extractor = FDAExtractors(
            name="FDA Products",
            base_url=None,
            api_key=None,
            rate_limit=0,
            timeout=300,
            max_retries=3
        )

        # 检查是否为 ZIP 文件
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 查找 XML 文件
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                if xml_files:
                    # 解压到临时目录
                    import tempfile
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_ref.extractall(tmpdir)
                        xml_path = Path(tmpdir) / xml_files[0]
                        return list(extractor.extract_products(
                            file_path=str(xml_path),
                            limit=limit
                        ))

        return list(extractor.extract_products(file_path=file_path, limit=limit))

    def _extract_applications_from_file(self, file_path: str, limit: int) -> List[Dict]:
        """从文件抽取应用数据"""
        from ..extractors.fda import FDAExtractors

        extractor = FDAExtractors(
            name="FDA Applications",
            base_url=None,
            api_key=None,
            rate_limit=0,
            timeout=300,
            max_retries=3
        )

        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                if xml_files:
                    import tempfile
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_ref.extractall(tmpdir)
                        xml_path = Path(tmpdir) / xml_files[0]
                        return list(extractor.extract_applications(
                            file_path=str(xml_path),
                            limit=limit
                        ))

        return list(extractor.extract_applications(file_path=file_path, limit=limit))

    def _extract_tecodes_from_file(self, file_path: str, limit: int) -> List[Dict]:
        """从文件抽取 TE 代码数据"""
        from ..extractors.fda import FDAExtractors

        extractor = FDAExtractors(
            name="FDA TE Codes",
            base_url=None,
            api_key=None,
            rate_limit=0,
            timeout=300,
            max_retries=3
        )

        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                if xml_files:
                    import tempfile
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_ref.extractall(tmpdir)
                        xml_path = Path(tmpdir) / xml_files[0]
                        return list(extractor.extract_tecodes(
                            file_path=str(xml_path),
                            limit=limit
                        ))

        return list(extractor.extract_tecodes(file_path=file_path, limit=limit))

    def _extract_products(self, limit: int) -> List[Dict]:
        """抽取产品数据（示例）"""
        return [
            {
                "product_id": "P001",
                "product_number": "001",
                "form": "TABLET",
                "strength": "10mg",
                "applicant": "Pfizer Inc.",
                "brand_name": "Drug A",
                "active_ingredient": "Ingredient A"
            }
        ]

    def _extract_applications(self, limit: int) -> List[Dict]:
        """抽取应用数据（示例）"""
        return [
            {
                "appl_no": "NDA012345",
                "appl_type": "NDA",
                "sponsor_name": "Pfizer Inc.",
                "submission_date": "2020-01-01",
                "approval_date": "2021-06-15"
            }
        ]

    def _extract_tecodes(self, limit: int) -> List[Dict]:
        """抽取 TE 代码数据（示例）"""
        return [
            {
                "te_code": "AB",
                "te_code_description": "Reference Listed Drug",
                "product_code": "ABC123"
            }
        ]

    def _transform_phase(self, extracted_data: Dict) -> Dict[str, List[Dict]]:
        """转换阶段"""
        logger.info("Transforming regulatory data...")

        # 转换产品
        transformed_products = []
        for product in extracted_data.get("products", [])[:self.config.batch_size]:
            transformed_products.append({
                "primary_id": f"fda.product:{product.get('product_id', product.get('product_number'))}",
                "product_number": product.get("product_number"),
                "form": self._normalize_form(product.get("form")),
                "strength": self._normalize_strength(product.get("strength")),
                "applicant": product.get("applicant"),
                "brand_name": product.get("brand_name"),
                "active_ingredient": product.get("active_ingredient"),
                "route": product.get("route"),
                "marketing_status": self._normalize_marketing_status(product.get("marketing_status")),
                "created_at": datetime.now().isoformat(),
                "data_source": "fda"
            })

        # 转换应用
        transformed_applications = []
        for app in extracted_data.get("applications", [])[:self.config.batch_size]:
            transformed_applications.append({
                "primary_id": f"fda.appl:{app.get('appl_no')}",
                "appl_no": app.get("appl_no"),
                "appl_type": app.get("appl_type"),
                "sponsor_name": app.get("sponsor_name"),
                "submission_date": self._normalize_date(app.get("submission_date")),
                "approval_date": self._normalize_date(app.get("approval_date")),
                "created_at": datetime.now().isoformat(),
                "data_source": "fda"
            })

        # 转换 TE 代码
        transformed_tecodes = []
        for tecode in extracted_data.get("tecodes", [])[:self.config.batch_size]:
            transformed_tecodes.append({
                "primary_id": f"fda.tecode:{tecode.get('te_code')}",
                "te_code": tecode.get("te_code"),
                "description": tecode.get("te_code_description"),
                "product_code": tecode.get("product_code"),
                "created_at": datetime.now().isoformat(),
                "data_source": "fda"
            })

        return {
            "products": transformed_products,
            "applications": transformed_applications,
            "tecodes": transformed_tecodes
        }

    def _normalize_form(self, form: Optional[str]) -> Optional[str]:
        """标准化剂型"""
        if not form:
            return None
        return form.strip().title()

    def _normalize_strength(self, strength: Optional[str]) -> Optional[str]:
        """标准化规格"""
        if not strength:
            return None
        return strength.strip().upper()

    def _normalize_marketing_status(self, status: Optional[str]) -> Optional[str]:
        """标准化上市状态"""
        if not status:
            return None

        status_map = {
            "Prescription": "RX",
            "Over-the-counter": "OTC",
            "Discontinued": "DISCONTINUED"
        }

        return status_map.get(status, status.upper())

    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """标准化日期"""
        if not date_str:
            return None

        # 尝试解析各种日期格式
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue

        logger.warning(f"Failed to parse date: {date_str}")
        return None

    def _validate_phase(self, data: Dict) -> Dict:
        """验证阶段"""
        validation_results = {
            "products": {
                "total": len(data.get("products", [])),
                "valid": len(data.get("products", [])),
                "errors": []
            },
            "applications": {
                "total": len(data.get("applications", [])),
                "valid": len(data.get("applications", [])),
                "errors": []
            },
            "tecodes": {
                "total": len(data.get("tecodes", [])),
                "valid": len(data.get("tecodes", [])),
                "errors": []
            }
        }

        logger.info(
            f"Validation: {validation_results['products']['valid']}/{validation_results['products']['total']} products, "
            f"{validation_results['applications']['valid']}/{validation_results['applications']['total']} applications, "
            f"{validation_results['tecodes']['valid']}/{validation_results['tecodes']['total']} TE codes"
        )

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
            # 加载产品节点
            products = data.get("products", [])
            if products:
                loader.load_nodes(
                    label="FDAProduct",
                    records=products,
                    merge_key="primary_id"
                )
                self.stats["loaded_products"] = len(products)
                logger.info(f"Loaded {len(products)} FDAProduct nodes")

            # 加载应用节点
            applications = data.get("applications", [])
            if applications:
                loader.load_nodes(
                    label="FDAApplication",
                    records=applications,
                    merge_key="primary_id"
                )
                self.stats["loaded_applications"] = len(applications)
                logger.info(f"Loaded {len(applications)} FDAApplication nodes")

            # 加载 TE 代码节点
            tecodes = data.get("tecodes", [])
            if tecodes:
                loader.load_nodes(
                    label="TECode",
                    records=tecodes,
                    merge_key="primary_id"
                )
                self.stats["loaded_tecodes"] = len(tecodes)
                logger.info(f"Loaded {len(tecodes)} TECode nodes")

            # 加载关系
            self._load_regulatory_relationships(loader, data)

            return loader.get_stats()

        finally:
            loader.close()

    def _load_regulatory_relationships(self, loader: Neo4jBatchLoader, data: Dict):
        """加载监管关系"""
        # 产品-应用关系
        products = data.get("products", [])
        if products:
            # 假设产品有 appl_no 字段
            relationships = []
            for product in products:
                if product.get("appl_no"):
                    relationships.append({
                        "from_id": product["primary_id"],
                        "to_id": f"fda.appl:{product['appl_no']}"
                    })

            if relationships:
                loader.load_relationships(
                    from_label="FDAProduct",
                    from_key="primary_id",
                    to_label="FDAApplication",
                    to_key="primary_id",
                    rel_type="PART_OF_APPLICATION",
                    records=relationships,
                    rel_properties={},
                    merge=False
                )
                logger.info(f"Loaded {len(relationships)} PART_OF_APPLICATION relationships")

        # TE 代码-产品关系
        tecodes = data.get("tecodes", [])
        if tecodes:
            relationships = []
            for tecode in tecodes:
                if tecode.get("product_code"):
                    relationships.append({
                        "from_id": tecode["primary_id"],
                        "to_id": f"fda.product:{tecode['product_code']}"
                    })

            if relationships:
                loader.load_relationships(
                    from_label="TECode",
                    from_key="primary_id",
                    to_label="FDAProduct",
                    to_key="primary_id",
                    rel_type="APPLIES_TO_PRODUCT",
                    records=relationships,
                    rel_properties={},
                    merge=False
                )
                logger.info(f"Loaded {len(relationships)} APPLIES_TO_PRODUCT relationships")


def run_regulatory_pipeline(
    data_file: str = None,
    limit: int = 1000,
    load_to_neo4j: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    便捷函数：运行监管管道

    Args:
        data_file: 数据文件路径
        limit: 记录数限制
        load_to_neo4j: 是否加载到 Neo4j
        dry_run: 试运行模式

    Returns:
        执行结果
    """
    pipeline = RegulatoryPipeline()
    return pipeline.run(
        data_file=data_file,
        limit=limit,
        load_to_neo4j=load_to_neo4j,
        dry_run=dry_run
    )
