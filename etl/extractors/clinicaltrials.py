#===========================================================
# PharmaKG ETL - ClinicalTrials.gov 数据抽取器
# Pharmaceutical Knowledge Graph - ClinicalTrials Extractor
#===========================================================
# 版本: v1.0
# 描述: 从 ClinicalTrials.gov API v2 抽取临床试验数据
#===========================================================

import logging
from typing import Generator, Dict, Optional, List
from datetime import datetime
from .base import PaginatedExtractor


logger = logging.getLogger(__name__)


class ClinicalTrialsGovExtractor(PaginatedExtractor):
    """
    ClinicalTrials.gov 数据抽取器

    抽取内容：
    - 临床试验基本信息
    - 试验设计细节
    - 受试者招募信息
    - 干预措施
    - 结果测量
    - 不良事件
    """

    # ClinicalTrials.gov API v2 端点
    API_BASE_URL = "https://clinicaltrials.gov/api/v2"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 0.5  # API 建议延迟
    ):
        """
        初始化 ClinicalTrials.gov 抽取器

        Args:
            api_key: NIH API 密钥（可选，提高速率限制）
            rate_limit: 速率限制（秒/请求）
        """
        super().__init__(
            name="ClinicalTrials.gov",
            base_url=self.API_BASE_URL,
            api_key=api_key,
            rate_limit=rate_limit
        )

    #===========================================================
    # 分页抽取实现
    #===========================================================

    def _fetch_page(self, page: int, page_size: int) -> List[Dict]:
        """
        抽取单页试验数据

        Args:
            page: 页码（从 1 开始，API token 从 1 开始）
            page_size: 每页大小 (1-100)

        Returns:
            该页的试验数据记录
        """
        # API v2 使用 token 分页
        params = {
            "pageSize": min(page_size, 100)  # API 限制最大 100
        }

        # 对于后续页，使用从上一页获取的 token
        if page > 1:
            params["pageToken"] = str(page)  # 实际应使用真实的 next_page_token

        response = self._make_request(
            endpoint="/studies",
            params=params
        )

        data = response.json()
        return data.get("studies", [])

    def get_total_pages(self, page_size: int) -> Optional[int]:
        """
        获取总页数（估算）

        Args:
            page_size: 每页大小

        Returns:
            总页数
        """
        total_count = self.get_total_count()
        if total_count:
            return (total_count + page_size - 1) // page_size
        return None

    def get_total_count(self) -> Optional[int]:
        """
        获取试验总数

        Returns:
            试验总数
        """
        response = self._make_request(
            endpoint="/studies",
            params={"pageSize": 1}
        )

        data = response.json()
        return data.get("totalCount")

    #===========================================================
    # 具体数据抽取方法
    #===========================================================

    def extract_studies(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        抽取研究/试验数据

        Args:
            query: 搜索查询（例如：癌症、糖尿病）
            status: 试验状态筛选
            phase: 试验阶段筛选
            limit: 记录数限制

        Yields:
            试验数据记录
        """
        params = {"pageSize": 100}

        # 构建查询过滤器
        filters = []
        if query:
            filters.append(f"query.term={query}")
        if status:
            filters.append(f"filter.structs=({status})")
        if phase:
            filters.append(f"filter.phases={phase}")

        if filters:
            params["query"] = " AND ".join(filters)

        next_page_token = None
        total_fetched = 0

        while True:
            # 检查限制
            if limit and total_fetched >= limit:
                break

            if next_page_token:
                params["pageToken"] = next_page_token

            response = self._make_request(
                endpoint="/studies",
                params=params
            )

            data = response.json()
            studies = data.get("studies", [])

            if not studies:
                break

            for study in studies:
                yield self._parse_study(study)
                total_fetched += 1

            # 获取下一页 token
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

    def _parse_study(self, study: Dict) -> Dict:
        """
        解析单个研究数据

        Args:
            study: API 返回的研究数据

        Returns:
            标准化的研究数据
        """
        protocol = study.get("protocolSection", {})
        identification = study.get("identificationModule", {})
        status = study.get("statusModule", {})
        contacts = study.get("contactsLocationsModule", {})
        description = study.get("descriptionModule", {})
        arms_interventions = study.get("armsInterventionsModule", {})
        outcomes = study.get("outcomesModule", {})
        eligibility = study.get("eligibilityModule", {})

        return {
            # 基本信息
            "nct_id": identification.get("nctId"),
            "brief_title": protocol.get("briefTitle"),
            "official_title": protocol.get("officialTitle"),
            "acronym": protocol.get("acronym"),

            # 状态信息
            "status": status.get("overallStatus"),
            "start_date": self._parse_date(status.get("startDateStruct")),
            "completion_date": self._parse_date(status.get("primaryCompletionDateStruct")),
            "last_update_posted": self._parse_date(status.get("lastUpdatePostDateStruct")),

            # 研究设计
            "study_type": protocol.get("studyType"),
            "phase": self._extract_phase(protocol),
            "allocation": protocol.get("designInfo", {}).get("allocation"),
            "masking": protocol.get("designInfo", {}).get("masking"),
            "masking_description": protocol.get("designInfo", {}).get("maskingDescription"),
            "primary_purpose": protocol.get("designInfo", {}).get("primaryPurpose"),

            # 疾病状况
            "conditions": protocol.get("conditionsModule", {}).get("conditions", []),
            "keywords": protocol.get("conditionsModule", {}).get("keywords", []),

            # 干预措施
            "interventions": self._parse_interventions(arms_interventions),

            # 研究终点
            "primary_outcomes": self._parse_outcomes(outcomes, "primary"),
            "secondary_outcomes": self._parse_outcomes(outcomes, "secondary"),

            # 招募信息
            "enrollment": status.get("enrollmentInfo", {}).get("count"),
            "enrollment_type": status.get("enrollmentInfo", {}).get("type"),
            "eligibility_criteria": eligibility.get("eligibilityCriteria", ""),

            # 研究地点
            "locations": self._parse_locations(contacts),

            # 赞助方
            "sponsors": self._parse_sponsors(protocol),

            # 参考文献
            "references": protocol.get("referencesModule", {}).get("references", []),

            # 原始数据（用于后续处理）
            "raw_data": study
        }

    def _parse_date(self, date_struct: Optional[Dict]) -> Optional[str]:
        """解析日期结构"""
        if date_struct:
            return date_struct.get("date")
        return None

    def _extract_phase(self, protocol: Dict) -> Optional[str]:
        """提取试验阶段"""
        phase = protocol.get("phase")
        if phase and phase.upper() != "N/A":
            return phase.upper()
        return None

    def _parse_interventions(self, arms_interventions: Dict) -> List[Dict]:
        """解析干预措施"""
        interventions = []
        arms = arms_interventions.get("arms", [])

        for arm in arms:
            arm_info = {
                "arm_group_label": arm.get("name"),
                "arm_group_type": arm.get("type"),
                "description": arm.get("description"),
                "interventions": []
            }

            for intervention in arm.get("interventions", []):
                intervention_info = {
                    "intervention_type": intervention.get("type"),
                    "intervention_name": intervention.get("name"),
                    "description": intervention.get("description"),
                    "arm_group_label": arm.get("name"),
                    "other_names": intervention.get("otherNames", [])
                }
                arm_info["interventions"].append(intervention_info)

            interventions.append(arm_info)

        return interventions

    def _parse_outcomes(self, outcomes: Dict, outcome_type: str) -> List[Dict]:
        """解析研究终点"""
        parsed_outcomes = []

        if outcome_type == "primary":
            outcome_list = outcomes.get("primaryOutcomes", [])
        else:
            outcome_list = outcomes.get("secondaryOutcomes", [])

        for outcome in outcome_list:
            outcome_info = {
                "outcome_type": outcome_type,
                "measure": outcome.get("measure"),
                "title": outcome.get("title"),
                "description": outcome.get("description"),
                "time_frame": outcome.get("timeFrame"),
                "units": outcome.get("units"),
                "param": outcome.get("param", {}).get("value")
            }
            parsed_outcomes.append(outcome_info)

        return parsed_outcomes

    def _parse_locations(self, contacts: Dict) -> List[Dict]:
        """解析研究地点"""
        locations = []
        location_items = contacts.get("locations", [])

        for item in location_items:
            location_info = {
                "facility": item.get("facility"),
                "name": item.get("name"),
                "city": item.get("city"),
                "state": item.get("state"),
                "country": item.get("country"),
                "lat": item.get("geoPoint", {}).get("lat"),
                "lon": item.get("geoPoint", {}).get("lon"),
                "status": item.get("status")
            }
            locations.append(location_info)

        return locations

    def _parse_sponsors(self, protocol: Dict) -> Dict:
        """解析赞助方信息"""
        sponsors_module = protocol.get("sponsorsModule", {})

        return {
            "lead_sponsor": sponsors_module.get("leadSponsor", {}).get("name"),
            "collaborators": [
                collab.get("name") for collab in
                sponsors_module.get("collaborators", [])
            ]
        }

    def extract_adverse_events(
        self,
        nct_id: str
    ) -> Generator[Dict, None, None]:
        """
        抽取特定试验的不良事件

        Args:
            nct_id: 试验 NCT 编号

        Yields:
            不良事件数据
        """
        # 不良事件通常在结果数据中
        response = self._make_request(
            endpoint=f"/studies/{nct_id}"
        )

        study = response.json()

        # 解析结果部分的不良事件
        results_section = study.get("resultsSection", {})
        adverse_events = results_section.get("adverseEventsEventsModule", {}).get("events", [])

        for event_category in adverse_events:
            category = event_category.get("category", "Uncategorized")
            for event in event_category.get("events", []):
                yield {
                    "nct_id": nct_id,
                    "category": category,
                    "event_type": event.get("name"),
                    "description": event.get("description"),
                    "frequency": event.get("counts", []),
                    "severity": event.get("severity"),
                    "related_to_intervention": event.get("assessments", [])
                }

    def extract_by_condition(self, condition: str, limit: int = 100) -> List[Dict]:
        """
        按疾病/状况抽取试验

        Args:
            condition: 疾病/状况名称
            limit: 最大返回数量

        Returns:
            试验列表
        """
        return list(self.extract_studies(query=condition, limit=limit))

    def extract_by_phase(self, phase: str, limit: int = 100) -> List[Dict]:
        """
        按试验阶段抽取试验

        Args:
            phase: 试验阶段 (Phase 1, Phase 2, etc.)
            limit: 最大返回数量

        Returns:
            试验列表
        """
        return list(self.extract_studies(phase=phase, limit=limit))

    #===========================================================
    # 数据更新检测
    #===========================================================

    def get_studies_updated_since(
        self,
        date: datetime,
        limit: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        获取指定日期后更新的试验

        Args:
            date: 起始日期
            limit: 记录数限制

        Yields:
            试验数据记录
        """
        date_str = date.strftime("%Y-%m-%d")
        query = f"lastUpdatePosted[{date_str}+"

        yield from self.extract_studies(query=query, limit=limit)

    #===========================================================
    # 批量抽取方法
    #===========================================================

    def extract_all_clinical_data(
        self,
        conditions: Optional[List[str]] = None,
        phases: Optional[List[str]] = None,
        limit_per_query: int = 500
    ) -> Dict[str, List[Dict]]:
        """
        抽取所有临床相关数据

        Args:
            conditions: 疾病列表
            phases: 试验阶段列表
            limit_per_query: 每个查询的记录数限制

        Returns:
            包含所有抽取数据的字典
        """
        logger.info("Starting ClinicalTrials.gov data extraction")

        result = {
            "studies": [],
            "interventions": [],
            "locations": [],
            "outcomes": []
        }

        # 默认抽取的重点疾病
        default_conditions = conditions or [
            "Diabetes",
            "Hypertension",
            "Cancer",
            "COVID-19",
            "Alzheimer's Disease"
        ]

        # 默认关注的阶段
        default_phases = phases or ["Phase 1", "Phase 2", "Phase 3"]

        # 按疾病和阶段抽取
        for condition in default_conditions:
            for phase in default_phases:
                logger.info(f"Extracting {condition} - {phase}")

                studies = list(self.extract_studies(
                    query=condition,
                    phase=phase,
                    limit=limit_per_query
                ))

                for study in studies:
                    result["studies"].append(study)
                    result["interventions"].extend(study.get("interventions", []))
                    result["locations"].extend(study.get("locations", []))
                    result["outcomes"].extend(
                        study.get("primary_outcomes", []) +
                        study.get("secondary_outcomes", [])
                    )

        logger.info(f"ClinicalTrials.gov extraction completed: "
                   f"{len(result['studies'])} studies, "
                   f"{len(result['interventions'])} interventions, "
                   f"{len(result['locations'])} locations")

        return result


# 便捷函数
def extract_clinical_trials_data(
    api_key: Optional[str] = None,
    conditions: Optional[List[str]] = None,
    limits: Optional[Dict] = None
) -> Dict[str, List[Dict]]:
    """
    便捷函数：抽取临床试验数据

    Args:
        api_key: NIH API 密钥
        conditions: 疾病列表
        limits: 各类型数据的限制

    Returns:
        抽取的数据字典
    """
    extractor = ClinicalTrialsGovExtractor(api_key=api_key)

    try:
        return extractor.extract_all_clinical_data(
            conditions=conditions,
            limit_per_query=(limits or {}).get("per_query", 500)
        )
    finally:
        extractor.close()
