#===========================================================
# 制药行业知识图谱 - 供应链+监管领域查询服务
# Pharmaceutical Knowledge Graph - Supply Chain & Regulatory Query Service
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
#===========================================================

from typing import List, Optional, Any
import logging

from ..database import get_db

logger = logging.getLogger(__name__)


class SupplyChainService:
    """供应链查询服务"""

    def __init__(self):
        self.db = get_db()

    def count_manufacturers(self) -> int:
        """统计制造商数量"""
        query = """
        MATCH (m:Manufacturer)
        RETURN count(m) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def count_drug_shortages(self) -> int:
        """统计药品短缺数量"""
        query = """
        MATCH (ds:DrugShortage)
        RETURN count(ds) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def get_manufacturer_by_id(self, manufacturer_id: str) -> dict:
        """根据ID获取制造商"""
        query = """
        MATCH (m:Manufacturer {manufacturer_id: $manufacturer_id})
        OPTIONAL MATCH (m)-[:HAS_MANUFACTURER_TYPE]->(mt:ManufacturerType)
        OPTIONAL MATCH (m)-[:HAS_CERTIFICATION]->(cert:Certification)
        RETURN m.manufacturer_id AS manufacturer_id,
               m.name AS name,
               m.type AS manufacturer_type,
               mt.name AS manufacturer_type_name,
               m.country AS country,
               m.city AS city,
               m.state AS state,
               m.fei_code AS fei_code,
               m.website AS website
        """
        result = self.db.execute_query(query, {"manufacturer_id": manufacturer_id})
        return result.records[0] if result.records else {}

    def search_manufacturers(self, params: dict) -> List[dict]:
        """搜索制造商"""
        conditions = []
        parameters = {}

        if params.get("manufacturer_type"):
            conditions.append("m.type = $manufacturer_type")
            parameters["manufacturer_type"] = params["manufacturer_type"]

        if params.get("country"):
            conditions.append("m.country = $country")
            parameters["country"] = params["country"]

        where_clause = " AND ".join(conditions) if conditions else "true"

        query = f"""
        MATCH (m:Manufacturer)-[:HAS_MANUFACTURER_TYPE]->(mt:ManufacturerType)
        WHERE {where_clause}
        RETURN m.manufacturer_id AS manufacturer_id,
               m.name AS name,
               mt.name AS manufacturer_type,
               m.country AS country,
               m.city AS city,
               m.fei_code AS fei_code
        ORDER BY m.name
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

    def get_manufacturer_drugs(self, manufacturer_id: str) -> List[dict]:
        """获取制造商生产的药品"""
        query = """
        MATCH (m:Manufacturer {manufacturer_id: $manufacturer_id})-[:MANUFACTURES_DRUG]->(c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
        RETURN c.primary_id AS primary_id,
               c.name AS name,
               c.is_approved_drug AS is_approved,
               ds.name AS development_stage
        ORDER BY c.name
        """
        result = self.db.execute_query(query, {"manufacturer_id": manufacturer_id})
        return result.records

    def get_active_shortages(self) -> List[dict]:
        """获取活跃的药品短缺"""
        query = """
        MATCH (ds:DrugShortage)-[:HAS_SHORTAGE_STATUS]->(ss:ShortageStatus)
        WHERE ss.id = 'active'
        MATCH (ds)-[:HAS_SHORTAGE_TYPE]->(st:ShortageType)
        MATCH (ds)-[:HAS_IMPACT_LEVEL]->(il:ImpactLevel)
        MATCH (ds)-[:HAS_AFFECTED_MANUFACTURER]->(m:Manufacturer)
        RETURN ds.shortage_id AS shortage_id,
               ds.drug_name AS drug_name,
               st.name AS shortage_type,
               ds.reason AS reason,
               ds.start_date AS start_date,
               ds.affected_region AS affected_region,
               il.name AS impact_level,
               m.name AS manufacturer
        ORDER BY ds.start_date DESC
        """
        result = self.db.execute_query(query)
        return result.records

    def get_shortages_by_manufacturer(self, manufacturer_id: str) -> List[dict]:
        """获取制造商的短缺"""
        query = """
        MATCH (m:Manufacturer {manufacturer_id: $manufacturer_id})<-[:HAS_AFFECTED_MANUFACTURER]-(ds:DrugShortage)
        MATCH (ds)-[:HAS_SHORTAGE_STATUS]->(ss:ShortageStatus)
        RETURN ds.shortage_id AS shortage_id,
               ds.drug_name AS drug_name,
               ds.shortage_type AS shortage_type,
               ss.name AS status,
               ds.start_date AS start_date,
               ds.end_date AS end_date
        ORDER BY ds.start_date DESC
        """
        result = self.db.execute_query(query, {"manufacturer_id": manufacturer_id})
        return result.records

    def get_manufacturer_inspections(self, manufacturer_id: str) -> List[dict]:
        """获取制造商检查记录"""
        query = """
        MATCH (m:Manufacturer {manufacturer_id: $manufacturer_id})-[:HAS_FACILITY]->(f:Facility)<-[:INSPECTS]-(ins:Inspection)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
        OPTIONAL MATCH (ins)-[:CONDUCTED_BY]->(ra:RegulatoryAgency)
        RETURN ins.inspection_id AS inspection_id,
               f.facility_name AS facility_name,
               ins.inspection_type AS inspection_type,
               ins.inspection_date AS inspection_date,
               irt.name AS result,
               ins.inspector AS inspector,
               ra.abbreviation AS agency
        ORDER BY ins.inspection_date DESC
        """
        result = self.db.execute_query(query, {"manufacturer_id": manufacturer_id})
        return result.records

    def get_manufacturer_compliance_actions(self, manufacturer_id: str) -> List[dict]:
        """获取制造商合规行动"""
        query = """
        MATCH (m:Manufacturer {manufacturer_id: $manufacturer_id})<-[:AGAINST_MANUFACTURER]-(ca:ComplianceAction)-[:HAS_ACTION_TYPE]->(cat:ComplianceActionType)
        OPTIONAL MATCH (ca)-[:ISSUED_BY]->(ra:RegulatoryAgency)
        RETURN ca.action_id AS action_id,
               cat.name AS action_type,
               ca.action_date AS action_date,
               ca.reason AS reason,
               ca.severity AS severity,
               ca.status AS status,
               ra.abbreviation AS agency
        ORDER BY ca.action_date DESC
        """
        result = self.db.execute_query(query, {"manufacturer_id": manufacturer_id})
        return result.records


class RegulatoryService:
    """监管合规查询服务"""

    def __init__(self):
        db = get_db()
        self.db = db
        self.supply_chain = SupplyChainService()

    def count_submissions(self) -> int:
        """统计申报数量"""
        query = """
        MATCH (sub:Submission)
        RETURN count(sub) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def count_approvals(self) -> int:
        """统计批准数量"""
        query = """
        MATCH (ap:Approval)
        RETURN count(ap) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def count_inspections(self) -> int:
        """统计检查数量"""
        query = """
        MATCH (ins:Inspection)
        RETURN count(ins) AS count
        """
        result = self.db.execute_query(query)
        return result.records[0]["count"] if result.records else 0

    def get_submission_by_id(self, submission_id: str) -> dict:
        """根据ID获取申报"""
        query = """
        MATCH (sub:Submission {submission_id: $submission_id})
        OPTIONAL MATCH (sub)-[:HAS_SUBMISSION_TYPE]->(st:SubmissionType)
        OPTIONAL MATCH (sub)-[:HAS_SUBMISSION_STATUS]->(sst:SubmissionStatus)
        OPTIONAL MATCH (sub)-[:HAS_REVIEW_PRIORITY]->(rp:ReviewPriority)
        OPTIONAL MATCH (sub)-[:SUBMITTED_TO]->(ra:RegulatoryAgency)
        OPTIONAL MATCH (sub)-[:RESULTS_IN_APPROVAL]->(ap:Approval)
        OPTIONAL MATCH (sub)-[:SUBMISSION_FOR_DRUG]->(c:Compound)
        RETURN sub.submission_id AS submission_id,
               sub.submission_type AS submission_type,
               st.name AS submission_type_name,
               sub.submission_date AS submission_date,
               sub.approval_date AS approval_date,
               sub.review_days AS review_days,
               sst.name AS status,
               rp.name AS review_priority,
               ra.abbreviation AS agency,
               ap.approval_number AS approval_number,
               c.name AS drug_name
        """
        result = self.db.execute_query(query, {"submission_id": submission_id})
        return result.records[0] if result.records else {}

    def search_submissions(self, params: dict) -> List[dict]:
        """搜索申报"""
        conditions = []
        parameters = {}

        if params.get("submission_type"):
            conditions.append("sub.submission_type = $submission_type")
            parameters["submission_type"] = params["submission_type"]

        if params.get("status"):
            conditions.append("sub.status = $status")
            parameters["status"] = params["status"]

        if params.get("review_priority"):
            conditions.append("sub.review_priority = $review_priority")
            parameters["review_priority"] = params["review_priority"]

        if params.get("drug_name"):
            conditions.append("sub.drug_name CONTAINS $drug_name")
            parameters["drug_name"] = params["drug_name"]

        where_clause = " AND ".join(conditions) if conditions else "true"

        query = f"""
        MATCH (sub:Submission)-[:HAS_SUBMISSION_TYPE]->(st:SubmissionType)
        WHERE {where_clause}
        MATCH (sub)-[:HAS_SUBMISSION_STATUS]->(sst:SubmissionStatus)
        MATCH (sub)-[:HAS_REVIEW_PRIORITY]->(rp:ReviewPriority)
        MATCH (sub)-[:SUBMITTED_TO]->(ra:RegulatoryAgency)
        RETURN sub.submission_id AS submission_id,
               sub.submission_type AS submission_type,
               sub.drug_name AS drug_name,
               sub.submission_date AS submission_date,
               sub.approval_date AS approval_date,
               sub.review_days AS review_days,
               sst.name AS status,
               rp.name AS review_priority,
               ra.abbreviation AS agency
        ORDER BY sub.submission_date DESC
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

    def get_approval_by_id(self, approval_id: str) -> dict:
        """根据ID获取批准"""
        query = """
        MATCH (ap:Approval {approval_id: $approval_id})
        OPTIONAL MATCH (ap)-[:HAS_APPROVAL_TYPE]->(apt:ApprovalType)
        OPTIONAL MATCH (ap)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus)
        OPTIONAL MATCH (ap)-[:ISSUED_BY]->(ra:RegulatoryAgency)
        OPTIONAL MATCH (ap)-[:APPROVAL_FOR_DRUG]->(c:Compound)
        OPTIONAL MATCH (ap)-[:BASED_ON_SUBMISSION]->(sub:Submission)
        OPTIONAL MATCH (ap)-[:HAS_APPROVAL_HOLDER]->(mah:AuthorizationHolder)
        RETURN ap.approval_id AS approval_id,
               ap.approval_number AS approval_number,
               apt.name AS approval_type,
               ap.approval_date AS approval_date,
               ap.expiration_date AS expiration_date,
               ap.indication AS indication,
               ap.dosage_form AS dosage_form,
               ap.strength AS strength,
               ap.status AS status,
               ra.abbreviation AS agency,
               c.name AS drug_name,
               sub.submission_id AS submission_id,
               mah.name AS holder
        """
        result = self.db.execute_query(query, {"approval_id": approval_id})
        return result.records[0] if result.records else {}

    def get_approvals_by_drug(self, drug_name: str) -> List[dict]:
        """获取药品的批准"""
        query = """
        MATCH (c:Compound {name: $drug_name})<-[:APPROVAL_FOR_DRUG]-(ap:Approval)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus)
        MATCH (ap)-[:ISSUED_BY]->(ra:RegulatoryAgency)
        MATCH (ap)-[:HAS_APPROVAL_TYPE]->(apt:ApprovalType)
        WHERE ap.status = 'active'
        RETURN ap.approval_id AS approval_id,
               ap.approval_number AS approval_number,
               apt.name AS approval_type,
               ap.approval_date AS approval_date,
               ap.expiration_date AS expiration_date,
               ap.indication AS indication,
               ap.dosage_form AS dosage_form,
               ap.strength AS strength,
               ra.abbreviation AS agency
        ORDER BY ap.approval_date DESC
        """
        result = self.db.execute_query(query, {"drug_name": drug_name})
        return result.records

    def get_inspection_by_id(self, inspection_id: str) -> dict:
        """根据ID获取检查"""
        query = """
        MATCH (ins:Inspection {inspection_id: $inspection_id})
        OPTIONAL MATCH (ins)-[:HAS_INSPECTION_TYPE]->(it:InspectionType)
        OPTIONAL MATCH (ins)-[:HAS_CLASSIFICATION]->(ic:InspectionClassification)
        OPTIONAL MATCH (ins)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
        OPTIONAL MATCH (ins)-[:CONDUCTED_BY]->(ra:RegulatoryAgency)
        OPTIONAL MATCH (ins)-[:INSPECTS_FACILITY]->(f:Facility)
        OPTIONAL MATCH (f)-[:FACILITY_OF]->(m:Manufacturer)
        RETURN ins.inspection_id AS inspection_id,
               f.facility_name AS facility_name,
               it.name AS inspection_type,
               ic.name AS classification,
               irt.name AS result,
               ins.inspection_date AS inspection_date,
               ins.inspector AS inspector,
               ra.abbreviation AS agency,
               m.name AS manufacturer
        """
        result = self.db.execute_query(query, {"inspection_id": inspection_id})
        return result.records[0] if result.records else {}

    def get_inspections_by_result(self, result: str, limit: int = 50) -> List[dict]:
        """按检查结果获取检查"""
        query = """
        MATCH (ins:Inspection)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
        WHERE irt.id = $result
        MATCH (ins)-[:INSPECTS_FACILITY]->(f:Facility)
        OPTIONAL MATCH (f)-[:FACILITY_OF]->(m:Manufacturer)
        OPTIONAL MATCH (ins)-[:CONDUCTED_BY]->(ra:RegulatoryAgency)
        RETURN ins.inspection_id AS inspection_id,
               f.facility_name AS facility_name,
               ins.inspection_type AS inspection_type,
               irt.name AS result,
               ins.inspection_date AS inspection_date,
               ra.abbreviation AS agency,
               m.name AS manufacturer
        ORDER BY ins.inspection_date DESC
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"result": result, "limit": limit})
        return result.records

    def get_compliance_actions(self, active_only: bool = True) -> List[dict]:
        """获取合规行动"""
        conditions = ["1=1"]
        parameters = {}

        if active_only:
            conditions.append("ca.status = 'active'")

        where_clause = " AND ".join(conditions)

        query = f"""
        MATCH (ca:ComplianceAction)
        WHERE {where_clause}
        MATCH (ca)-[:HAS_ACTION_TYPE]->(cat:ComplianceActionType)
        MATCH (ca)-[:AGAINST_MANUFACTURER]->(m:Manufacturer)
        MATCH (ca)-[:ISSUED_BY]->(ra:RegulatoryAgency)
        RETURN ca.action_id AS action_id,
               cat.name AS action_type,
               ca.action_date AS action_date,
               ca.reason AS reason,
               ca.severity AS severity,
               ca.status AS status,
               m.name AS manufacturer,
               ra.abbreviation AS agency
        ORDER BY ca.action_date DESC
        LIMIT 100
        """
        result = self.db.execute_query(query)
        return result.records

    def get_agency_statistics(self, agency_id: str) -> dict:
        """获取监管机构统计"""
        query = """
        MATCH (ra:RegulatoryAgency {agency_id: $agency_id})
        OPTIONAL MATCH (ra)-[:REVIEWS_SUBMISSION]->(sub:Submission)
        WITH ra, count(sub) AS submissions_reviewed
        OPTIONAL MATCH (ra)-[:ISSUES_APPROVAL]->(ap:Approval)
        WITH ra, submissions_reviewed, count(ap) AS approvals_issued
        OPTIONAL MATCH (ra)-[:CONDUCTS_INSPECTION]->(ins:Inspection)
        RETURN ra.agency_id AS agency_id,
               ra.name AS name,
               ra.abbreviation AS abbreviation,
               ra.type AS agency_type,
               ra.jurisdiction AS jurisdiction,
               submissions_reviewed,
               approvals_issued,
               count(ins) AS inspections_conducted
        """
        result = self.db.execute_query(query, {"agency_id": agency_id})
        return result.records[0] if result.records else {}

    def get_post_marketing_commitments(self, status: Optional[str] = None) -> List[dict]:
        """获取上市后承诺"""
        conditions = ["1=1"]
        parameters = {}

        if status:
            conditions.append("pmc.status = $status")
            parameters["status"] = status

        where_clause = " AND ".join(conditions)

        query = f"""
        MATCH (pmc:PostMarketingCommitment)
        WHERE {where_clause}
        MATCH (pmc)-[:HAS_PMC_TYPE]->(pmt:PMCType)
        MATCH (pmc)-[:HAS_STATUS]->(pmcs:PMCStatus)
        MATCH (pmc)-[:PMC_FOR_DRUG]->(c:Compound)
        MATCH (pmc)-[:COMMITMENT_FOR]->(ap:Approval)
        RETURN pmc.pmc_id AS pmc_id,
               c.name AS drug_name,
               pmt.name AS pmc_type,
               pmc.description AS description,
               pmc.submitted_date AS submitted_date,
               pmc.due_date AS due_date,
               pmcs.name AS status,
               ap.approval_number AS approval_number
        ORDER BY pmc.due_date
        LIMIT 50
        """
        result = self.db.execute_query(query, parameters)
        return result.records

    def get_safety_signals(self, status: Optional[str] = None, limit: int = 50) -> List[dict]:
        """获取安全性信号"""
        conditions = ["1=1"]
        parameters = {}

        if status:
            conditions.append("ss.status = $status")
            parameters["status"] = status

        where_clause = " AND ".join(conditions)

        query = f"""
        MATCH (ss:SafetySignal)
        WHERE {where_clause}
        MATCH (ss)-[:HAS_SIGNAL_TYPE]->(sgt:SignalType)
        MATCH (ss)-[:HAS_SIGNAL_SEVERITY]->(sgs:SignalSeverity)
        MATCH (ss)-[:HAS_SIGNAL_STATUS]->(ssst:SignalStatus)
        MATCH (ss)-[:RELATED_TO_DRUG]->(c:Compound)
        RETURN ss.signal_id AS signal_id,
               c.name AS drug_name,
               sgt.name AS signal_type,
               sgs.name AS severity,
               ss.detection_date AS detection_date,
               ss.source AS source,
               ssst.name AS status,
               ss.description AS description
        ORDER BY ss.detection_date DESC
        LIMIT $limit
        """
        result = self.db.execute_query(query, {**parameters, "limit": limit})
        return result.records
