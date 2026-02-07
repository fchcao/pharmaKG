#===========================================================
# PharmaKG ETL - ChEMBL 数据抽取器
# Pharmaceutical Knowledge Graph - ChEMBL Extractor
#===========================================================
# 版本: v1.0
# 描述: 从 ChEMBL 数据库抽取化合物、靶点、活性数据
#===========================================================

import logging
from typing import Generator, Dict, Optional, List
from datetime import datetime
from .base import PaginatedExtractor


logger = logging.getLogger(__name__)


class ChEMBLExtractor(PaginatedExtractor):
    """
    ChEMBL 数据抽取器

    抽取内容：
    - 化合物（分子）
    - 靶点（蛋白质）
    - 生物活性数据
    - 机制 of action
    - 化合物-靶点关系
    """

    # ChEMBL API v2 端点
    API_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 0.5  # ChEMBL 建议不超过 2 req/sec
    ):
        """
        初始化 ChEMBL 抽取器

        Args:
            api_key: ChEMBL API 密钥（可选，高频访问需要）
            rate_limit: 速率限制（秒/请求）
        """
        super().__init__(
            name="ChEMBL",
            base_url=self.API_BASE_URL,
            api_key=api_key,
            rate_limit=rate_limit
        )

    #===========================================================
    # 分页抽取实现
    #===========================================================

    def _fetch_page(self, page: int, page_size: int) -> List[Dict]:
        """
        抽取单页分子数据

        Args:
            page: 页码（从 0 开始）
            page_size: 每页大小

        Returns:
            该页的分子数据记录
        """
        response = self._make_request(
            endpoint="/molecule",
            params={
                "format": "json",
                "offset": page * page_size,
                "limit": page_size
            }
        )

        data = response.json()
        return data.get("molecules", {})

    def get_total_pages(self, page_size: int) -> Optional[int]:
        """
        获取总页数

        Args:
            page_size: 每页大小

        Returns:
            总页数
        """
        response = self._make_request(
            endpoint="/molecule",
            params={"format": "json", "limit": 1}
        )

        data = response.json()
        page_meta = data.get("page_meta", {})
        total_count = page_meta.get("total_count", 0)

        return (total_count + page_size - 1) // page_size if total_count > 0 else None

    def get_total_count(self) -> Optional[int]:
        """
        获取分子总数

        Returns:
            分子总数
        """
        response = self._make_request(
            endpoint="/molecule",
            params={"format": "json", "limit": 1}
        )

        data = response.json()
        page_meta = data.get("page_meta", {})
        return page_meta.get("total_count")

    #===========================================================
    # 具体数据抽取方法
    #===========================================================

    def extract_compounds(
        self,
        limit: Optional[int] = None,
        properties: Optional[List[str]] = None
    ) -> Generator[Dict, None, None]:
        """
        抽取化合物数据

        Args:
            limit: 记录数限制
            properties: 要获取的属性列表

        Yields:
            化合物数据记录
        """
        # 默认获取的属性
        default_properties = [
            "molecule_chembl_id",
            "molecule_type",
            "pref_name",
            "molecule_structures",
            "max_phase",
            "therapeutic_flag",
            "is_parent",
            "num_ro5_violations",
            "molecule_properties"
        ]

        props = properties or default_properties

        endpoint = "/molecule"
        offset = 0
        batch_size = 100

        while True:
            # 检查限制
            if limit and offset >= limit:
                break

            response = self._make_request(
                endpoint=endpoint,
                params={
                    "format": "json",
                    "offset": offset,
                    "limit": batch_size
                }
            )

            data = response.json()
            molecules = data.get("molecules", {})

            if not molecules:
                break

            for molecule in molecules:
                # 过滤只获取父分子
                if molecule.get("is_parent"):
                    yield {
                        "chembl_id": molecule.get("molecule_chembl_id"),
                        "name": molecule.get("pref_name"),
                        "type": molecule.get("molecule_type"),
                        "max_phase": molecule.get("max_phase"),
                        "therapeutic_flag": molecule.get("therapeutic_flag"),
                        "ro5_violations": molecule.get("num_ro5_violations"),
                        "smiles": self._extract_smiles(molecule),
                        "inchikey": self._extract_inchikey(molecule),
                        "molecular_properties": molecule.get("molecule_properties", {}),
                        "structures": molecule.get("molecule_structures", {})
                    }

            offset += batch_size

    def _extract_smiles(self, molecule: Dict) -> Optional[str]:
        """从分子数据中提取 SMILES"""
        structures = molecule.get("molecule_structures", [])
        if structures:
            return structures[0].get("canonical_smiles")
        return None

    def _extract_inchikey(self, molecule: Dict) -> Optional[str]:
        """从分子数据中提取 InChIKey"""
        structures = molecule.get("molecule_structures", [])
        if structures:
            return structures[0].get("standard_inchi_key")
        return None

    def extract_targets(
        self,
        limit: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        抽取靶点数据

        Args:
            limit: 记录数限制

        Yields:
            靶点数据记录
        """
        endpoint = "/target"
        offset = 0
        batch_size = 100

        while True:
            if limit and offset >= limit:
                break

            response = self._make_request(
                endpoint=endpoint,
                params={
                    "format": "json",
                    "offset": offset,
                    "limit": batch_size
                }
            )

            data = response.json()
            targets = data.get("targets", {})

            if not targets:
                break

            for target in targets:
                yield {
                    "chembl_id": target.get("target_chembl_id"),
                    "name": target.get("target_pref_name"),
                    "target_type": target.get("target_type"),
                    "organism": target.get("organism"),
                    "species": target.get("species"),
                    "protein_class": target.get("protein_class"),
                    "components": target.get("target_components", [])
                }

            offset += batch_size

    def extract_activities(
        self,
        compound_id: Optional[str] = None,
        target_id: Optional[str] = None,
        assay_type: Optional[str] = None,
        min_confidence: int = 8
    ) -> Generator[Dict, None, None]:
        """
        抽取生物活性数据

        Args:
            compound_id: 化合物 ID 筛选
            target_id: 靶点 ID 筛选
            assay_type: 实验类型筛选
            min_confidence: 最小置信度评分 (0-9)

        Yields:
            活性数据记录
        """
        endpoint = "/activity"
        offset = 0
        batch_size = 100

        # 构建查询参数
        params = {
            "format": "json",
            "offset": offset,
            "limit": batch_size
        }

        filters = []
        if compound_id:
            filters.append(f"molecule_chembl_id={compound_id}")
        if target_id:
            filters.append(f"target_chembl_id={target_id}")
        if assay_type:
            filters.append(f"assay_type={assay_type}")
        if min_confidence:
            filters.append(f"pchembl_value>={min_confidence}")

        if filters:
            params["where"] = " and ".join(filters)

        while True:
            response = self._make_request(
                endpoint=endpoint,
                params=params
            )

            data = response.json()
            activities = data.get("activities", {})

            if not activities:
                break

            for activity in activities:
                yield {
                    "activity_id": activity.get("activity_id"),
                    "compound_chembl_id": activity.get("molecule_chembl_id"),
                    "target_chembl_id": activity.get("target_chembl_id"),
                    "assay_chembl_id": activity.get("assay_chembl_id"),
                    "assay_type": activity.get("assay_type"),
                    "assay_description": activity.get("assay_description"),
                    "activity_type": activity.get("standard_type"),
                    "activity_value": activity.get("standard_value"),
                    "activity_units": activity.get("standard_units"),
                    "pchembl_value": activity.get("pchembl_value"),
                    "confidence_score": activity.get("confidence_score"),
                    "document_chembl_id": activity.get("document_chembl_id")
                }

            offset += batch_size
            params["offset"] = offset

    def extract_mechanisms(
        self,
        limit: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        抽取作用机制数据

        Args:
            limit: 记录数限制

        Yields:
            机制数据记录
        """
        endpoint = "/mechanism"
        offset = 0
        batch_size = 100

        while True:
            if limit and offset >= limit:
                break

            response = self._make_request(
                endpoint=endpoint,
                params={
                    "format": "json",
                    "offset": offset,
                    "limit": batch_size
                }
            )

            data = response.json()
            mechanisms = data.get("mechanisms", {})

            if not mechanisms:
                break

            for mechanism in mechanisms:
                yield {
                    "mechanism_id": mechanism.get("mec_id"),
                    "compound_chembl_id": mechanism.get("molecule_chembl_id"),
                    "target_chembl_id": mechanism.get("target_chembl_id"),
                    "mechanism_of_action": mechanism.get("mechanism_of_action"),
                    "action_type": mechanism.get("action_type"),
                    "selectivity": mechanism.get("selectivity"),
                    "binding_site": mechanism.get("site_id"),
                    "references": mechanism.get("site_refs", [])
                }

            offset += batch_size

    def extract_drug_indications(
        self,
        limit: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        抽取药物适应症数据

        Args:
            limit: 记录数限制

        Yields:
            适应症数据记录
        """
        endpoint = "/drug_indication"
        offset = 0
        batch_size = 100

        while True:
            if limit and offset >= limit:
                break

            response = self._make_request(
                endpoint=endpoint,
                params={
                    "format": "json",
                    "offset": offset,
                    "limit": batch_size
                }
            )

            data = response.json()
            indications = data.get("drug_indications", {})

            if not indications:
                break

            for indication in indications:
                yield {
                    "indication_id": indication.get("drug_indication_id"),
                    "compound_chembl_id": indication.get("molecule_chembl_id"),
                    "max_phase_for_ind": indication.get("max_phase_for_ind"),
                    "indication_refs": indication.get("indication_refs"),
                    "phase": indication.get("phase")
                }

            offset += batch_size

    #===========================================================
    # 数据更新检测
    #===========================================================

    def get_last_update_date(self) -> Optional[datetime]:
        """
        获取 ChEMBL 数据库最后更新日期

        Returns:
            最后更新日期
        """
        try:
            # 获取最新记录的更新时间
            response = self._make_request(
                endpoint="/molecule",
                params={"format": "json", "limit": 1}
            )

            data = response.json()
            molecules = data.get("molecules", {})

            if molecules:
                # ChEMBL 数据集的发布日期
                # 实际项目中应使用专门的数据版本 API
                return datetime.now()

        except Exception as e:
            logger.error(f"Failed to get last update date: {e}")

        return None

    #===========================================================
    # 批量抽取方法
    #===========================================================

    def extract_all_rd_data(
        self,
        limit_compounds: Optional[int] = 1000,
        limit_targets: Optional[int] = None,
        limit_activities: Optional[int] = 5000
    ) -> Dict[str, List[Dict]]:
        """
        抽取所有 R&D 相关数据

        Args:
            limit_compounds: 化合物数量限制
            limit_targets: 靶点数量限制
            limit_activities: 活性数据数量限制

        Returns:
            包含所有抽取数据的字典
        """
        logger.info("Starting comprehensive ChEMBL data extraction")

        result = {
            "compounds": [],
            "targets": [],
            "activities": [],
            "mechanisms": [],
            "indications": []
        }

        # 抽取化合物
        logger.info("Extracting compounds...")
        result["compounds"] = list(self.extract_compounds(limit=limit_compounds))

        # 抽取靶点
        logger.info("Extracting targets...")
        result["targets"] = list(self.extract_targets(limit=limit_targets))

        # 抽取活性数据
        logger.info("Extracting activities...")
        result["activities"] = list(self.extract_activities(limit=limit_activities))

        # 抽取作用机制
        logger.info("Extracting mechanisms...")
        result["mechanisms"] = list(self.extract_mechanisms())

        # 抽取适应症
        logger.info("Extracting indications...")
        result["indications"] = list(self.extract_drug_indications())

        logger.info(f"ChEMBL extraction completed: "
                   f"{len(result['compounds'])} compounds, "
                   f"{len(result['targets'])} targets, "
                   f"{len(result['activities'])} activities")

        return result


# 便捷函数
def extract_chembl_data(
    api_key: Optional[str] = None,
    limits: Optional[Dict] = None
) -> Dict[str, List[Dict]]:
    """
    便捷函数：抽取 ChEMBL 数据

    Args:
        api_key: ChEMBL API 密钥
        limits: 各类型数据的限制

    Returns:
        抽取的数据字典
    """
    extractor = ChEMBLExtractor(api_key=api_key)

    try:
        return extractor.extract_all_rd_data(
            limit_compounds=(limits or {}).get("compounds", 1000),
            limit_targets=(limits or {}).get("targets"),
            limit_activities=(limits or {}).get("activities", 5000)
        )
    finally:
        extractor.close()
