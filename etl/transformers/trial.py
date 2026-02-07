#===========================================================
# PharmaKG ETL - 临床试验数据转换器
# Pharmaceutical Knowledge Graph - Clinical Trial Transformer
#===========================================================
# 版本: v1.0
# 描述: 标准化临床试验数据，阶段分类，状态映射
#===========================================================

import logging
from typing import Dict, Optional, List
from datetime import datetime
from .base import BaseTransformer, TransformationResult, FieldMapping


logger = logging.getLogger(__name__)


class ClinicalTrialTransformer(BaseTransformer):
    """
    临床试验数据转换器

    功能：
    - 试验阶段标准化
    - 状态码映射
    - 日期格式统一
    - 干预措施分类
    """

    # 试验阶段映射
    PHASE_MAPPING = {
        "Phase 0": "Early Phase 1",
        "Phase I": "Phase 1",
        "Phase 1": "Phase 1",
        "Phase II": "Phase 2",
        "Phase 2": "Phase 2",
        "Phase III": "Phase 3",
        "Phase 3": "Phase 3",
        "Phase IV": "Phase 4",
        "Phase 4": "Phase 4",
        "N/A": "Not Applicable"
    }

    # 状态映射
    STATUS_MAPPING = {
        "Recruiting": "RECRUITING",
        "Not yet recruiting": "NOT_YET_RECRUITING",
        "Active, not recruiting": "ACTIVE_NOT_RECRUITING",
        "Completed": "COMPLETED",
        "Terminated": "TERMINATED",
        "Withdrawn": "WITHDRAWN",
        "Suspended": "SUSPENDED"
    }

    def __init__(self, strict_mode: bool = False):
        """初始化试验转换器"""
        super().__init__(name="ClinicalTrialTransformer", strict_mode=strict_mode)

    def transform(self, record: Dict) -> TransformationResult:
        """转换试验记录"""
        errors = self.validate(record)

        try:
            normalized = self._normalize_trial(record)

            validation_errors = self._validate_normalized(normalized)
            if validation_errors:
                return TransformationResult(
                    status=TransformationStatus.VALIDATION_ERROR,
                    input_record=record,
                    output_record=None,
                    errors=validation_errors,
                    warnings=[],
                    metadata={"transformer": self.name}
                )

            return TransformationResult(
                status=TransformationStatus.SUCCESS,
                input_record=record,
                output_record=normalized,
                errors=errors,
                warnings=[],
                metadata={"transformer": self.name}
            )

        except Exception as e:
            logger.error(f"Failed to transform trial: {e}")
            return TransformationResult(
                status=TransformationStatus.FAILED,
                input_record=record,
                output_record=None,
                errors=[str(e)] + errors,
                warnings=[],
                metadata={"transformer": self.name}
            )

    def get_required_fields(self) -> List[str]:
        return ["nct_id"]

    def _normalize_trial(self, record: Dict) -> Dict:
        """标准化试验数据"""
        return {
            "primary_id": self._get_primary_id(record),
            "trial_id": record.get("nct_id"),
            "title": self.normalize_string(record.get("brief_title")),
            "official_title": self.normalize_string(record.get("official_title")),
            "phase": self._normalize_phase(record.get("phase")),
            "status": self._normalize_status(record.get("status")),
            "study_type": record.get("study_type"),
            "allocation": record.get("allocation"),
            "masking": record.get("masking"),
            "primary_purpose": record.get("primary_purpose"),
            "conditions": self._normalize_conditions(record.get("conditions", [])),
            "interventions": self._normalize_interventions(record.get("interventions", [])),
            "primary_outcomes": self._normalize_outcomes(record.get("primary_outcomes", [])),
            "secondary_outcomes": self._normalize_outcomes(record.get("secondary_outcomes", [])),
            "enrollment": self._normalize_enrollment(record),
            "eligibility_criteria": record.get("eligibility_criteria"),
            "locations": self._normalize_locations(record.get("locations", [])),
            "sponsors": self._normalize_sponsors(record.get("sponsors")),
            "start_date": self.normalize_date(record.get("start_date")),
            "completion_date": self.normalize_date(record.get("completion_date")),
            "last_update_posted": self.normalize_date(record.get("last_update_posted")),
            "data_source": "clinicaltrials.gov"
        }

    def _get_primary_id(self, record: Dict) -> str:
        """获取主键（NCT Number）"""
        nct_id = record.get("nct_id")
        if nct_id:
            return f"nct:{nct_id}"
        raise ValueError("Missing NCT ID")

    def _normalize_phase(self, phase: Optional[str]) -> Optional[str]:
        """标准化试验阶段"""
        if not phase:
            return None

        phase = self.normalize_string(phase)
        return self.PHASE_MAPPING.get(phase, phase)

    def _normalize_status(self, status: Optional[str]) -> Optional[str]:
        """标准化状态"""
        if not status:
            return None

        status = self.normalize_string(status)
        return self.STATUS_MAPPING.get(status, status.upper())

    def _normalize_conditions(self, conditions: List) -> List[Dict]:
        """标准化疾病状况"""
        normalized = []

        for condition in conditions:
            if isinstance(condition, str):
                normalized.append({
                    "name": self.normalize_string(condition),
                    "mesh_id": None
                })
            elif isinstance(condition, dict):
                normalized.append({
                    "name": self.normalize_string(condition.get("name")),
                    "mesh_id": condition.get("mesh_id")
                })

        return normalized

    def _normalize_interventions(self, interventions: List) -> List[Dict]:
        """标准化干预措施"""
        normalized = []

        for intervention in interventions:
            if isinstance(intervention, dict):
                normalized.append({
                    "intervention_type": intervention.get("intervention_type"),
                    "name": self.normalize_string(intervention.get("intervention_name")),
                    "description": intervention.get("description"),
                    "arm_group_label": intervention.get("arm_group_label"),
                    "other_names": intervention.get("other_names", [])
                })

        return normalized

    def _normalize_outcomes(self, outcomes: List) -> List[Dict]:
        """标准化研究终点"""
        normalized = []

        for outcome in outcomes:
            if isinstance(outcome, dict):
                normalized.append({
                    "outcome_type": outcome.get("outcome_type"),
                    "measure": outcome.get("measure"),
                    "title": self.normalize_string(outcome.get("title")),
                    "description": outcome.get("description"),
                    "time_frame": outcome.get("time_frame"),
                    "units": outcome.get("units")
                })

        return normalized

    def _normalize_enrollment(self, record: Dict) -> Optional[int]:
        """标准化招募人数"""
        enrollment = record.get("enrollment")

        if enrollment:
            try:
                return int(enrollment)
            except (ValueError, TypeError):
                logger.warning(f"Invalid enrollment value: {enrollment}")

        return None

    def _normalize_locations(self, locations: List) -> List[Dict]:
        """标准化研究地点"""
        normalized = []

        for location in locations:
            if isinstance(location, dict):
                normalized.append({
                    "facility": location.get("facility"),
                    "name": location.get("name"),
                    "city": location.get("city"),
                    "state": location.get("state"),
                    "country": location.get("country"),
                    "lat": location.get("lat"),
                    "lon": location.get("lon"),
                    "status": location.get("status")
                })

        return normalized

    def _normalize_sponsors(self, sponsors: Dict) -> Dict:
        """标准化赞助方信息"""
        if not isinstance(sponsors, dict):
            sponsors = {}

        return {
            "lead_sponsor": sponsors.get("lead_sponsor"),
            "collaborators": sponsors.get("collaborators", [])
        }

    def _validate_normalized(self, record: Dict) -> List[str]:
        """验证标准化记录"""
        errors = []

        if not record.get("trial_id"):
            errors.append("Missing required field: trial_id (nct_id)")

        if not record.get("title"):
            errors.append("Missing required field: title")

        # 验证 NCT ID 格式
        trial_id = record.get("trial_id")
        if trial_id and not trial_id.startswith("NCT"):
            errors.append(f"Invalid NCT ID format: {trial_id}")

        return errors


# 便捷函数
def transform_trials(
    records: List[Dict]
) -> List[TransformationResult]:
    """
    便捷函数：转换试验数据

    Args:
        records: 原始记录列表

    Returns:
        转换结果列表
    """
    transformer = ClinicalTrialTransformer()

    try:
        return transformer.transform_batch(records)
    finally:
        logger.info(f"Clinical trial transformation stats: {transformer.get_stats()}")
