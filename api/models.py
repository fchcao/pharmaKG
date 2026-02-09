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


#===========================================================
# 搜索相关模型
#===========================================================

class SearchRequest(BaseModel):
    """搜索请求基础模型"""
    query: str = Field(..., min_length=1, description="搜索查询文本")
    limit: int = Field(20, ge=1, le=100, description="返回结果数量限制")
    skip: int = Field(0, ge=0, description="跳过结果数量")


class FullTextSearchRequest(SearchRequest):
    """全文搜索请求"""
    entity_types: Optional[List[str]] = Field(None, description="实体类型过滤列表")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    entity_type: str = Field(..., description="实体类型")
    element_id: Optional[str] = Field(None, description="元素ID")
    primary_id: Optional[str] = Field(None, description="主键ID")
    name: Optional[str] = Field(None, description="名称")
    score: float = Field(..., description="相关性得分")
    index_name: Optional[str] = Field(None, description="索引名称")


class FullTextSearchResponse(BaseModel):
    """全文搜索响应"""
    results: List[SearchResultItem] = Field(default_factory=list, description="搜索结果")
    total: int = Field(..., description="总结果数")
    returned: int = Field(..., description="返回结果数")
    query: str = Field(..., description="搜索查询")
    entity_types: Optional[List[str]] = Field(None, description="实体类型过滤")
    skip: int = Field(..., description="跳过结果数")
    limit: int = Field(..., description="结果限制")
    message: Optional[str] = Field(None, description="额外信息")


class FuzzySearchRequest(SearchRequest):
    """模糊搜索请求"""
    entity_type: str = Field(..., description="实体类型")
    search_field: str = Field("name", description="搜索字段")
    max_distance: int = Field(2, ge=0, le=4, description="最大编辑距离")


class FuzzySearchResultItem(BaseModel):
    """模糊搜索结果项"""
    entity_type: str = Field(..., description="实体类型")
    element_id: Optional[str] = Field(None, description="元素ID")
    primary_id: Optional[str] = Field(None, description="主键ID")
    name: Optional[str] = Field(None, description="名称")
    distance: Optional[int] = Field(None, description="编辑距离")
    similarity: float = Field(..., description="相似度 (0-1)")
    method: str = Field(..., description="搜索方法")


class FuzzySearchResponse(BaseModel):
    """模糊搜索响应"""
    results: List[FuzzySearchResultItem] = Field(default_factory=list, description="搜索结果")
    total: int = Field(..., description="总结果数")
    returned: int = Field(..., description="返回结果数")
    query: str = Field(..., description="搜索查询")
    entity_type: str = Field(..., description="实体类型")
    search_field: str = Field(..., description="搜索字段")
    max_distance: int = Field(..., description="最大编辑距离")
    skip: int = Field(..., description="跳过结果数")
    limit: int = Field(..., description="结果限制")
    method: str = Field(..., description="使用的搜索方法")
    message: Optional[str] = Field(None, description="额外信息")


class SuggestionRequest(BaseModel):
    """搜索建议请求"""
    prefix: str = Field(..., min_length=1, description="搜索前缀")
    entity_type: str = Field(..., description="实体类型")
    search_field: str = Field("name", description="搜索字段")
    limit: int = Field(10, ge=1, le=50, description="返回建议数量")


class SuggestionItem(BaseModel):
    """搜索建议项"""
    text: str = Field(..., description="建议文本")
    frequency: int = Field(..., description="出现频率")


class SuggestionResponse(BaseModel):
    """搜索建议响应"""
    suggestions: List[SuggestionItem] = Field(default_factory=list, description="搜索建议")
    total: int = Field(..., description="总建议数")
    prefix: str = Field(..., description="搜索前缀")
    entity_type: str = Field(..., description="实体类型")
    search_field: str = Field(..., description="搜索字段")


class AggregateSearchRequest(BaseModel):
    """聚合搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询文本")
    group_by: str = Field("entity_type", description="分组维度: entity_type 或 domain")
    limit: int = Field(100, ge=1, le=200, description="每组最大结果数")


class AggregateSearchGroup(BaseModel):
    """聚合搜索组"""
    entity_type: Optional[str] = Field(None, description="实体类型")
    domain: Optional[str] = Field(None, description="业务领域")
    count: int = Field(..., description="组内结果数")
    entity_types: Optional[List[dict]] = Field(None, description="包含的实体类型统计")
    results: List[dict] = Field(default_factory=list, description="组内搜索结果")


class AggregateSearchResponse(BaseModel):
    """聚合搜索响应"""
    groups: List[AggregateSearchGroup] = Field(default_factory=list, description="聚合分组")
    total_groups: int = Field(..., description="总分组数")
    total_results: int = Field(..., description="总结果数")
    query: str = Field(..., description="搜索查询")
    group_by: str = Field(..., description="分组维度")
    message: Optional[str] = Field(None, description="额外信息")


class MultiEntitySearchConfig(BaseModel):
    """多实体搜索配置"""
    entity_type: str = Field(..., description="实体类型")
    search_field: str = Field("name", description="搜索字段")


class MultiEntitySearchRequest(BaseModel):
    """多实体搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询文本")
    entities: List[MultiEntitySearchConfig] = Field(..., description="实体配置列表")
    limit_per_entity: int = Field(10, ge=1, le=50, description="每个实体类型的结果限制")


class MultiEntitySearchResponse(BaseModel):
    """多实体搜索响应"""
    results: dict = Field(..., description="按实体类型分组的结果")
    total_entities: int = Field(..., description="命中的实体类型数")
    total_results: int = Field(..., description="总结果数")
    query: str = Field(..., description="搜索查询")
