#===========================================================
# 制药行业知识图谱 - API 数据模型
# Pharmaceutical Knowledge Graph - API Data Models
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
#===========================================================

from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


#===========================================================
# 通用模型
#===========================================================

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    data: List[Any] = Field(default_factory=list, description="数据列表")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="状态")
    version: str = Field(..., description="API版本")
    neo4j_connected: bool = Field(..., description="Neo4j连接状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


#===========================================================
# R&D 领域模型
#===========================================================

class CompoundModel(BaseModel):
    """化合物模型"""
    primary_id: str
    name: str
    smiles: Optional[str] = None
    inchikey: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    development_stage: Optional[str] = None
    is_approved_drug: Optional[bool] = None


class TargetModel(BaseModel):
    """靶点模型"""
    primary_id: str
    name: str
    gene_symbol: Optional[str] = None
    gene_name: Optional[str] = None
    uniprot_id: Optional[str] = None
    target_type: Optional[str] = None
    organism: Optional[str] = None


class AssayModel(BaseModel):
    """实验模型"""
    assay_id: str
    name: str
    assay_type: Optional[str] = None
    assay_format: Optional[str] = None
    detection_method: Optional[str] = None
    cell_line: Optional[str] = None
    organism: Optional[str] = None


class PathwayModel(BaseModel):
    """通路模型"""
    primary_id: str
    name: str
    pathway_type: Optional[str] = None
    organism: Optional[str] = None
    kegg_id: Optional[str] = None


#===========================================================
# 临床领域模型
#===========================================================

class ClinicalTrialModel(BaseModel):
    """临床试验模型"""
    trial_id: str
    title: str
    phase: Optional[str] = None
    status: Optional[str] = None
    study_type: Optional[str] = None
    allocation: Optional[str] = None
    masking: Optional[str] = None
    purpose: Optional[str] = None
    enrollment: Optional[int] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None


class SubjectModel(BaseModel):
    """受试者模型"""
    subject_id: str
    initials: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    enrollment_date: Optional[date] = None


class InterventionModel(BaseModel):
    """干预措施模型"""
    intervention_id: str
    intervention_name: str
    intervention_type: Optional[str] = None
    dosage: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None


class AdverseEventModel(BaseModel):
    """不良事件模型"""
    ae_id: str
    meddra_term: str
    severity: Optional[str] = None
    seriousness: Optional[str] = None
    onset_date: Optional[date] = None
    outcome: Optional[str] = None


#===========================================================
# 供应链领域模型
#===========================================================

class ManufacturerModel(BaseModel):
    """制造商模型"""
    manufacturer_id: str
    name: str
    manufacturer_type: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    fei_code: Optional[str] = None
    website: Optional[str] = None


class DrugShortageModel(BaseModel):
    """药品短缺模型"""
    shortage_id: str
    drug_name: str
    shortage_type: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    affected_region: Optional[str] = None
    impact_level: Optional[str] = None


#===========================================================
# 监管领域模型
#===========================================================

class SubmissionModel(BaseModel):
    """申报模型"""
    submission_id: str
    submission_type: Optional[str] = None
    drug_name: Optional[str] = None
    submission_date: Optional[date] = None
    approval_date: Optional[date] = None
    review_days: Optional[int] = None
    review_priority: Optional[str] = None
    status: Optional[str] = None


class ApprovalModel(BaseModel):
    """批准模型"""
    approval_id: str
    approval_number: Optional[str] = None
    drug_name: Optional[str] = None
    approval_type: Optional[str] = None
    approval_date: Optional[date] = None
    expiration_date: Optional[date] = None
    indication: Optional[str] = None
    status: Optional[str] = None


class InspectionModel(BaseModel):
    """检查模型"""
    inspection_id: str
    facility_name: Optional[str] = None
    inspection_type: Optional[str] = None
    inspection_date: Optional[date] = None
    classification: Optional[str] = None
    result: Optional[str] = None


class ComplianceActionModel(BaseModel):
    """合规行动模型"""
    action_id: str
    action_type: Optional[str] = None
    action_date: Optional[date] = None
    reason: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


#===========================================================
# 查询请求模型
#===========================================================

class CompoundSearchRequest(BaseModel):
    """化合物搜索请求"""
    name: Optional[str] = None
    min_molecular_weight: Optional[float] = None
    max_molecular_weight: Optional[float] = None
    development_stage: Optional[str] = None
    is_approved: Optional[bool] = None


class TrialSearchRequest(BaseModel):
    """试验搜索请求"""
    phase: Optional[str] = None
    status: Optional[str] = None
    study_type: Optional[str] = None
    condition: Optional[str] = None
    min_enrollment: Optional[int] = None


class SubmissionSearchRequest(BaseModel):
    """申报搜索请求"""
    submission_type: Optional[str] = None
    status: Optional[str] = None
    review_priority: Optional[str] = None
    drug_name: Optional[str] = None


#===========================================================
# 统计模型
#===========================================================

class CountResponse(BaseModel):
    """计数响应"""
    entity_type: str = Field(..., description="实体类型")
    count: int = Field(..., description="数量")


class StatsResponse(BaseModel):
    """统计响应"""
    domain: str = Field(..., description="领域")
    stats: dict[str, Any] = Field(..., description="统计数据")


class OverviewResponse(BaseModel):
    """总览响应"""
    total_nodes: int = Field(..., description="总节点数")
    total_relationships: int = Field(..., description="总关系数")
    domain_counts: dict[str, int] = Field(..., description="各领域实体数")
    neo4j_version: Optional[str] = None
    api_version: str = Field(..., description="API版本")
