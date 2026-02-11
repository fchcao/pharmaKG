#===========================================================
# 制药行业知识图谱 - 临床领域查询服务
# Pharmaceutical Knowledge Graph - Clinical Domain Query Service
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
#===========================================================

from typing import List, Optional, Any
import logging

from ..database import get_db

logger = logging.getLogger(__name__)


class ClinicalDomainService:
    """临床领域查询服务"""

    def __init__(self):
        self.db = get_db()

    def count_trials(self) -> int:
        """统计临床试验数量"""
        query = """
        MATCH (t:ClinicalTrial)
        RETURN count(t) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def count_subjects(self) -> int:
        """统计受试者数量"""
        query = """
        MATCH (s:Subject)
        RETURN count(s) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def count_adverse_events(self) -> int:
        """统计不良事件数量"""
        query = """
        MATCH (ae:AdverseEvent)
        RETURN count(ae) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def get_trial_by_id(self, trial_id: str) -> dict:
        """根据ID获取试验"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})
        OPTIONAL MATCH (t)-[:HAS_PHASE]->(tp:TrialPhase)
        OPTIONAL MATCH (t)-[:HAS_STATUS]->(ts:TrialStatus)
        OPTIONAL MATCH (t)-[:HAS_STUDY_TYPE]->(st:StudyType)
        OPTIONAL MATCH (t)-[:STUDIES_CONDITION]->(c:Condition)
        RETURN t.trial_id AS trial_id,
               t.title AS title,
               tp.name AS phase,
               ts.name AS status,
               st.name AS study_type,
               t.allocation AS allocation,
               t.masking AS masking,
               t.purpose AS purpose,
               t.enrollment AS enrollment,
               t.start_date AS start_date,
               t.completion_date AS completion_date,
               collect(DISTINCT c.condition_name) AS conditions
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.records[0] if result.records else {}

    def search_trials(self, params: dict) -> List[dict]:
        """搜索试验"""
        conditions = []
        parameters = {}

        if params.get("phase"):
            conditions.append("t.phase = $phase")
            parameters["phase"] = params["phase"]

        if params.get("status"):
            conditions.append("t.status = $status")
            parameters["status"] = params["status"]

        if params.get("study_type"):
            conditions.append("t.study_type = $study_type")
            parameters["study_type"] = params["study_type"]

        if params.get("condition"):
            conditions.append("EXISTS((t)-[:STUDIES_CONDITION]->(:Condition {condition_name: $condition}))")
            parameters["condition"] = params["condition"]

        if params.get("min_enrollment"):
            conditions.append("t.enrollment >= $min_enrollment")
            parameters["min_enrollment"] = params["min_enrollment"]

        where_clause = " AND ".join(conditions) if conditions else "true"

        query = f"""
        MATCH (t:ClinicalTrial)-[:HAS_PHASE]->(tp:TrialPhase)
        WHERE {where_clause}
        RETURN t.trial_id AS trial_id,
               t.title AS title,
               tp.name AS phase,
               t.status AS status,
               t.study_type AS study_type,
               t.enrollment AS enrollment,
               t.start_date AS start_date,
               t.completion_date AS completion_date
        ORDER BY t.start_date DESC
        LIMIT $limit
        SKIP $offset
        """

        page = params.get("page", 1)
        page_size = params.get("page_size", 20)

        result = self.db.execute_query(query, {
            **parameters,
            "limit": page_size,
            "offset": (page - 1) * page_size
        })

        return result.records

    def get_trial_subjects(self, trial_id: str) -> List[dict]:
        """获取试验的受试者"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})<-[:ENROLLED_IN]-(s:Subject)-[:HAS_GENDER]->(g:Gender)
        OPTIONAL MATCH (s)-[:HAS_AGE_GROUP]->(ag:AgeGroup)
        OPTIONAL MATCH (s)-[:ASSIGNED_TO]->(a:Arm)
        RETURN s.subject_id AS subject_id,
               s.initials AS initials,
               s.age AS age,
               g.name AS gender,
               ag.name AS age_group,
               s.enrollment_date AS enrollment_date,
               a.arm_label AS arm
        ORDER BY s.enrollment_date
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.records

    def get_trial_arms(self, trial_id: str) -> List[dict]:
        """获取试验分组"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})-[:HAS_ARM]->(a:Arm)
        OPTIONAL MATCH (a)<-[:ASSIGNED_TO]-(s:Subject)
        RETURN a.arm_id AS arm_id,
               a.arm_label AS arm_label,
               a.arm_type AS arm_type,
               a.description AS description,
               a.target_enrollment AS target_enrollment,
               count(s) AS actual_enrollment
        ORDER BY a.arm_label
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.records

    def get_trial_interventions(self, trial_id: str) -> List[dict]:
        """获取试验干预措施"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})-[:HAS_INTERVENTION]->(i:Intervention)-[:HAS_INTERVENTION_TYPE]->(it:InterventionType)
        RETURN i.intervention_id AS intervention_id,
               i.intervention_name AS intervention_name,
               it.name AS intervention_type,
               i.dosage AS dosage,
               i.route AS route,
               i.frequency AS frequency,
               i.duration AS duration
        ORDER BY i.arm_group_label
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.records

    def get_trial_outcomes(self, trial_id: str) -> List[dict]:
        """获取试验终点"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})-[:HAS_PRIMARY_OUTCOME|HAS_SECONDARY_OUTCOME]->(o:Outcome)-[:HAS_OUTCOME_TYPE]->(ot:OutcomeType)
        RETURN o.outcome_id AS outcome_id,
               o.title AS title,
               ot.name AS outcome_type,
               o.description AS description,
               o.time_frame AS time_frame,
               o.unit AS unit
        ORDER BY ot.order, o.title
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.records

    def get_trial_adverse_events(self, trial_id: str) -> List[dict]:
        """获取试验不良事件"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})-[:REPORTS_ADVERSE_EVENT]->(ae:AdverseEvent)-[:HAS_SEVERITY]->(sg:SeverityGrade)
        RETURN ae.ae_id AS ae_id,
               ae.meddra_term AS meddra_term,
               sg.name AS severity,
               ae.seriousness AS seriousness,
               ae.onset_date AS onset_date,
               ae.outcome AS outcome,
               ae.action_taken AS action_taken
        ORDER BY ae.onset_date
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.results if hasattr(result, 'results') else result.records

    def get_adverse_events_by_severity(self, severity: str, limit: int = 50) -> List[dict]:
        """按严重程度获取不良事件"""
        query = """
        MATCH (ae:AdverseEvent)-[:HAS_SEVERITY]->(sg:SeverityGrade)
        WHERE sg.id = $severity
        MATCH (ae)<-[:REPORTS_ADVERSE_EVENT]-(t:ClinicalTrial)
        MATCH (ae)<-[:EXPERIENCED_AE]-(s:Subject)
        RETURN ae.ae_id AS ae_id,
               ae.meddra_term AS meddra_term,
               sg.name AS severity,
               t.trial_id AS trial_id,
               t.title AS trial_title,
               s.subject_id AS subject_id,
               ae.onset_date AS onset_date,
               ae.outcome AS outcome
        ORDER BY ae.onset_date DESC
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"severity": severity, "limit": limit})
        return result.records

    def get_trial_sites(self, trial_id: str) -> List[dict]:
        """获取试验中心"""
        query = """
        MATCH (t:ClinicalTrial {trial_id: $trial_id})<-[:SITE_OF]-(site:StudySite)-[:HAS_STATUS]->(ss:SiteStatus)
        OPTIONAL MATCH (site)<-[:ASSIGNED_TO]-(inv:Investigator)-[:HAS_ROLE]->(ir:InvestigatorRole)
        WHERE ir.id = 'principal_investigator'
        RETURN site.site_id AS site_id,
               site.site_name AS site_name,
               site.city AS city,
               site.country AS country,
               ss.name AS status,
               collect(DISTINCT inv.name) AS investigators
        ORDER BY site.site_name
        """
        result = self.db.execute_query(query, {"trial_id": trial_id})
        return result.records

    def get_trials_by_condition(self, condition_name: str) -> List[dict]:
        """获取疾病相关的试验"""
        query = """
        MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(:Condition {condition_name: $condition_name})
        MATCH (t)-[:HAS_PHASE]->(tp:TrialPhase)
        MATCH (t)-[:HAS_STATUS]->(ts:TrialStatus)
        RETURN t.trial_id AS trial_id,
               t.title AS title,
               tp.name AS phase,
               ts.name AS status,
               t.enrollment AS enrollment,
               t.start_date AS start_date
        ORDER BY t.start_date DESC
        LIMIT 50
        """
        result = self.db.execute_query(query, {"condition_name": condition_name})
        return result.records

    def get_subject_adverse_events(self, subject_id: str) -> List[dict]:
        """获取受试者的不良事件"""
        query = """
        MATCH (s:Subject {subject_id: $subject_id})-[:EXPERIENCED_AE]->(ae:AdverseEvent)-[:HAS_SEVERITY]->(sg:SeverityGrade)
        MATCH (ae)<-[:REPORTS_ADVERSE_EVENT]-(t:ClinicalTrial)
        RETURN s.subject_id AS subject_id,
               ae.meddra_term AS meddra_term,
               sg.name AS severity,
               t.trial_id AS trial_id,
               t.title AS trial_title,
               ae.onset_date AS onset_date,
               ae.outcome AS outcome
        ORDER BY ae.onset_date
        """
        result = self.db.execute_query(query, {"subject_id": subject_id})
        return result.records
