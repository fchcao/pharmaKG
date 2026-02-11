#===========================================================
# 制药行业知识图谱 - FastAPI 主应用
# Pharmaceutical Knowledge Graph - FastAPI Main Application
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
# 描述: 主API应用，包含所有领域端点
#===========================================================

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from .config import settings
from .database import get_db, close_db
from .models import (
    HealthResponse, ErrorResponse, OverviewResponse,
    CountResponse, StatsResponse,
    FullTextSearchRequest, FullTextSearchResponse, SearchResultItem,
    FuzzySearchRequest, FuzzySearchResponse, FuzzySearchResultItem,
    SuggestionRequest, SuggestionResponse, SuggestionItem,
    AggregateSearchRequest, AggregateSearchResponse, AggregateSearchGroup,
    MultiEntitySearchRequest, MultiEntitySearchResponse
)

# 导入服务
from .services.research_domain import ResearchDomainService
from .services.clinical_domain import ClinicalDomainService
from .services.supply_regulatory import SupplyChainService, RegulatoryService
from .services.advanced_queries import AdvancedQueryService
from .services.aggregate_queries import AggregateQueryService
from .services.search_service import SearchService
from .cache import setup_cache_monitoring

# 导入图分析模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from graph_analytics.api import AnalyticsAPI
from graph_analytics.inference import (
    DrugDrugInteractionPredictor,
    DrugDiseasePredictor,
    TargetDiseasePredictor
)
from graph_analytics.visualization import GraphVisualizer

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 启动和关闭事件处理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # 关闭时
    await close_db()
    logger.info(f"Stopped {settings.APP_NAME}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="制药行业知识图谱REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 设置缓存监控端点
setup_cache_monitoring(app)

# 注册图分析 API 端点
try:
    db = get_db()
    analytics_api = AnalyticsAPI(db.driver)
    analytics_api.register_routers(app)
    logger.info("Registered graph analytics API routers")
except Exception as e:
    logger.warning(f"Failed to register graph analytics API: {e}")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc), "timestamp": exc.__class__.__name__}
    )


#===========================================================
# 健康检查和元数据端点
#===========================================================

@app.get("/health", response_model=HealthResponse, tags=["Meta"])
async def health_check():
    """健康检查"""
    db = get_db()
    neo4j_connected = db.verify_connection()

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        neo4j_connected=neo4j_connected
    )


@app.get("/test-data", tags=["Meta"])
async def get_test_data():
    """获取测试数据"""
    db = get_db()

    # 获取化合物数据
    compounds = []
    result = db.execute_query("""
        MATCH (c:Compound)
        RETURN c.chembl_id, c.name, c.molecule_type, c.max_phase
        LIMIT 10
    """)
    for row in result.records:
        compounds.append({
            "chembl_id": row["c.chembl_id"],
            "name": row["c.name"],
            "molecule_type": row.get("c.molecule_type"),
            "max_phase": row.get("c.max_phase")
        })

    # 获取靶点数据
    targets = []
    result = db.execute_query("""
        MATCH (t:Target)
        RETURN t.target_id, t.name, t.organism
        LIMIT 10
    """)
    for row in result.records:
        targets.append({
            "target_id": row["t.target_id"],
            "name": row["t.name"],
            "organism": row.get("t.organism")
        })

    return {
        "compounds": compounds,
        "targets": targets
    }


@app.get("/api-test", tags=["Meta"])
async def api_test():
    """简单 API 测试端点"""
    return {
        "message": "API is working!",
        "timestamp": "2024-02-10",
        "data": {"test": "success"}
    }



@app.get("/overview", response_model=OverviewResponse, tags=["Meta"])
async def get_overview():
    """获取知识图谱总览"""
    db = get_db()

    # 统计各领域实体数量
    domain_counts = {}

    try:
        # R&D领域
        rd_service = ResearchDomainService()
        domain_counts["compounds"] = rd_service.count_compounds()
        domain_counts["targets"] = rd_service.count_targets()

        # 临床领域
        clinical_service = ClinicalDomainService()
        domain_counts["trials"] = clinical_service.count_trials()
        domain_counts["subjects"] = clinical_service.count_subjects()
        domain_counts["adverse_events"] = clinical_service.count_adverse_events()

        # 供应链领域
        sc_service = SupplyChainService()
        domain_counts["manufacturers"] = sc_service.count_manufacturers()
        domain_counts["drug_shortages"] = sc_service.count_drug_shortages()

        # 监管领域
        regulatory_service = RegulatoryService()
        domain_counts["submissions"] = regulatory_service.count_submissions()
        domain_counts["approvals"] = regulatory_service.count_approvals()
        domain_counts["inspections"] = regulatory_service.count_inspections()

    except Exception as e:
        logger.error(f"Error getting overview: {str(e)}")

    # 统计总节点和关系数
    try:
        total_nodes_result = db.execute_query("MATCH (n) RETURN count(n) AS count")
        total_relationships_result = db.execute_query("MATCH ()-[r]->() RETURN count(r) AS count")

        total_nodes = total_nodes_result.records[0]["count"] if total_nodes_result.records else 0
        total_relationships = total_relationships_result.records[0]["count"] if total_relationships_result.records else 0
    except Exception as e:
        logger.error(f"Error getting total counts: {str(e)}")
        total_nodes = 0
        total_relationships = 0

    return OverviewResponse(
        total_nodes=total_nodes,
        total_relationships=total_relationships,
        domain_counts=domain_counts,
        api_version=settings.APP_VERSION
    )


#===========================================================
# R&D 领域端点
#===========================================================

@app.get("/rd/compounds/count", response_model=CountResponse, tags=["Research Domain"])
async def count_rd_compounds():
    """统计化合物数量"""
    service = ResearchDomainService()
    count = service.count_compounds()
    return CountResponse(entity_type="compounds", count=count)


@app.get("/rd/compounds", tags=["Research Domain"])
async def list_compounds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    name: str = Query(None),
    # 接受但不处理的其他参数
    min_molecular_weight: float = Query(None),
    max_molecular_weight: float = Query(None),
    min_logp: float = Query(None),
    max_logp: float = Query(None),
    drug_type: str = Query(None),
    is_approved: bool = Query(None),
    development_stage: str = Query(None)
):
    """获取化合物列表"""
    db = get_db()
    skip = (page - 1) * page_size

    # 构建查询条件 - 只支持 search 和 name
    conditions = []
    params = {}
    if search:
        conditions.append("c.name CONTAINS $search")
        params["search"] = search
    if name:
        conditions.append("c.name CONTAINS $name")
        params["name"] = name

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        MATCH (c:Compound)
        {where_clause}
        RETURN c.chembl_id, c.name, c.molecule_type, c.max_phase
        ORDER BY c.chembl_id
        SKIP $skip LIMIT $limit
    """

    result = db.execute_query(query, {**params, "skip": skip, "limit": page_size})

    compounds = []
    for row in result.records:
        compounds.append({
            "id": row["c.chembl_id"],
            "chemblId": row["c.chembl_id"],
            "name": row["c.name"] if row["c.name"] else "Unknown",
            "moleculeType": row.get("c.molecule_type"),
            "maxPhase": row.get("c.max_phase")
        })

    # 获取总数
    count_query = f"""
        MATCH (c:Compound)
        {where_clause}
        RETURN count(c) AS total
    """
    count_result = db.execute_query(count_query, params)
    total = count_result.records[0]["total"] if count_result.records else 0

    return {
        "items": compounds,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": (total + page_size - 1) // page_size
    }


@app.get("/rd/compounds/{compound_id}", tags=["Research Domain"])
async def get_compound(compound_id: str):
    """获取化合物详情"""
    db = get_db()

    # 使用 chembl_id 查找
    query = """
        MATCH (c:Compound {chembl_id: $compound_id})
        RETURN c.chembl_id as id,
               c.chembl_id as chemblId,
               c.name as name,
               c.molecule_type as moleculeType,
               c.max_phase as maxPhase,
               c.molregno as molregno
    """
    result = db.execute_query(query, {"compound_id": compound_id})

    if not result.records:
        raise HTTPException(status_code=404, detail=f"Compound {compound_id} not found")

    row = result.records[0]
    return {
        "id": row["id"],
        "chemblId": row["chemblId"],
        "name": row["name"] if row["name"] else "Unknown",
        "moleculeType": row.get("moleculeType", "Unknown"),
        "maxPhase": row.get("maxPhase"),
        "molregno": row.get("molregno")
    }


@app.get("/rd/compounds/{compound_id}/targets", tags=["Research Domain"])
async def get_compound_targets(compound_id: str):
    """获取化合物的靶点"""
    db = get_db()

    # 首先验证化合物存在
    check_query = """
        MATCH (c:Compound {chembl_id: $compound_id})
        RETURN c.chembl_id
    """
    check_result = db.execute_query(check_query, {"compound_id": compound_id})
    if not check_result.records:
        raise HTTPException(status_code=404, detail=f"Compound {compound_id} not found")

    # 查询化合物-靶点关系（支持 BINDS_TO 和 ACTS_ON 关系类型）
    targets_query = """
        MATCH (c:Compound {chembl_id: $compound_id})-[r:BINDS_TO|ACTS_ON]->(t:Target)
        RETURN t.target_id, t.chembl_id, t.name, t.organism, t.target_type,
               r.pchembl_value, r.standard_type
        ORDER BY r.pchembl_value DESC
        LIMIT 50
    """
    result = db.execute_query(targets_query, {"compound_id": compound_id})

    targets = []
    for row in result.records:
        targets.append({
            "targetId": row["t.target_id"],
            "chemblId": row["t.chembl_id"],
            "name": row["t.name"],
            "organism": row["t.organism"],
            "targetType": row["t.target_type"],
            "pchemblValue": row["r.pchembl_value"],
            "standardType": row["r.standard_type"]
        })

    return {"compound_id": compound_id, "targets": targets}


@app.get("/rd/targets", tags=["Research Domain"])
async def list_targets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取靶点列表"""
    db = get_db()
    skip = (page - 1) * page_size

    query = """
        MATCH (t:Target)
        RETURN t.target_id, t.chembl_id, t.name, t.organism, t.target_type
        ORDER BY t.target_id
        SKIP $skip LIMIT $limit
    """
    result = db.execute_query(query, {"skip": skip, "limit": page_size})

    targets = []
    for row in result.records:
        targets.append({
            "id": row["t.target_id"],
            "targetId": row["t.target_id"],
            "chemblId": row["t.chembl_id"],
            "uniprotId": row["t.chembl_id"],
            "name": row["t.name"],
            "organism": row.get("t.organism"),
            "proteinType": row.get("t.target_type")
        })

    # 获取总数
    count_result = db.execute_query("MATCH (t:Target) RETURN count(t) AS total")
    total = count_result.records[0]["total"] if count_result.records else 0

    return {
        "items": targets,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": (total + page_size - 1) // page_size
    }


@app.get("/rd/targets/{target_id}/compounds", tags=["Research Domain"])
async def get_target_compounds(target_id: str):
    """获取靶点的化合物"""
    service = ResearchDomainService()
    compounds = service.get_target_compounds(target_id)
    return {"target_id": target_id, "compounds": compounds}


@app.get("/rd/statistics", tags=["Research Domain"])
async def get_rd_statistics():
    """获取R&D领域统计数据"""
    db = get_db()
    service = ResearchDomainService()

    compounds_count = service.count_compounds()

    # Count approved drugs (max_phase = 4)
    approved_result = db.execute_query("""
        MATCH (c:Compound)
        WHERE c.max_phase = 4
        RETURN count(c) as approved_count
    """)
    approved_drugs = approved_result.records[0]["approved_count"] if approved_result.records else 0

    # Count clinical candidates (max_phase between 1 and 3)
    clinical_result = db.execute_query("""
        MATCH (c:Compound)
        WHERE c.max_phase >= 1 AND c.max_phase <= 3
        RETURN count(c) as clinical_count
    """)
    clinical_candidates = clinical_result.records[0]["clinical_count"] if clinical_result.records else 0

    # Calculate average molecular weight
    avg_mw_result = db.execute_query("""
        MATCH (c:Compound)
        WHERE c.molecular_weight IS NOT NULL
        RETURN avg(c.molecular_weight) as avg_mw
    """)
    avg_molecular_weight = avg_mw_result.records[0]["avg_mw"] if avg_mw_result.records and avg_mw_result.records[0]["avg_mw"] else 0

    return {
        "compounds_count": compounds_count,
        "targets_count": service.count_targets(),
        "approved_drugs": approved_drugs,
        "clinical_candidates": clinical_candidates,
        "avg_molecular_weight": round(avg_molecular_weight, 1) if avg_molecular_weight else 0,
        "assays_count": 0,  # 待实现
        "pathways_count": 0,  # 待实现
        "bioactivities_count": 0  # 待实现
    }


# Missing RD endpoints (placeholder implementations)
@app.get("/rd/assays", tags=["Research Domain"])
async def list_assays(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    assay_type: str = Query(None),
    assay_format: str = Query(None)
):
    """获取生物分析列表（暂时返回空数据）"""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": page_size,
        "totalPages": 0
    }


@app.get("/rd/assays/{assay_id}", tags=["Research Domain"])
async def get_assay(assay_id: str):
    """获取单个生物分析（暂时返回空数据）"""
    return None


@app.get("/rd/pathways", tags=["Research Domain"])
async def list_pathways(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None)
):
    """获取通路列表（暂时返回空数据）"""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": page_size,
        "totalPages": 0
    }


@app.get("/rd/pathways/{pathway_id}", tags=["Research Domain"])
async def get_pathway(pathway_id: str):
    """获取单个通路（暂时返回空数据）"""
    return None


@app.get("/rd/compounds/{compound_id}/bioactivities", tags=["Research Domain"])
async def get_compound_bioactivities(compound_id: str):
    """获取化合物生物活性数据（暂时返回空数据）"""
    return []


@app.get("/rd/targets/{target_id}/pathways", tags=["Research Domain"])
async def get_target_pathways(target_id: str):
    """获取靶点相关通路（暂时返回空数据）"""
    return []


#===========================================================
# 临床领域端点
#===========================================================

@app.get("/clinical/trials/count", response_model=CountResponse, tags=["Clinical Domain"])
async def count_clinical_trials():
    """统计临床试验数量"""
    service = ClinicalDomainService()
    count = service.count_trials()
    return CountResponse(entity_type="trials", count=count)


@app.get("/clinical/trials/{trial_id}", tags=["Clinical Domain"])
async def get_trial(trial_id: str):
    """获取试验详情"""
    service = ClinicalDomainService()
    trial = service.get_trial_by_id(trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail=f"ClinicalTrial {trial_id} not found")
    return trial


@app.get("/clinical/trials/{trial_id}/subjects", tags=["Clinical Domain"])
async def get_trial_subjects(trial_id: str):
    """获取试验受试者"""
    service = ClinicalDomainService()
    subjects = service.get_trial_subjects(trial_id)
    return {"trial_id": trial_id, "subjects": subjects}


@app.get("/clinical/trials/{trial_id}/adverse-events", tags=["Clinical Domain"])
async def get_trial_adverse_events(trial_id: str):
    """获取试验不良事件"""
    service = ClinicalDomainService()
    aes = service.get_trial_adverse_events(trial_id)
    return {"trial_id": trial_id, "adverse_events": aes}


#===========================================================
# 供应链领域端点
#===========================================================

@app.get("/sc/manufacturers/count", response_model=CountResponse, tags=["Supply Chain"])
async def count_manufacturers():
    """统计制造商数量"""
    service = SupplyChainService()
    count = service.count_manufacturers()
    return CountResponse(entity_type="manufacturers", count=count)


@app.get("/sc/manufacturers/{manufacturer_id}", tags=["Supply Chain"])
async def get_manufacturer(manufacturer_id: str):
    """获取制造商详情"""
    service = SupplyChainService()
    manufacturer = service.get_manufacturer_by_id(manufacturer_id)
    if not manufacturer:
        raise HTTPException(status_code=404, detail=f"Manufacturer {manufacturer_id} not found")
    return manufacturer


@app.get("/sc/shortages/active", tags=["Supply Chain"])
async def get_active_shortages():
    """获取活跃的药品短缺"""
    service = SupplyChainService()
    shortages = service.get_active_shortages()
    return {"shortages": shortages}


@app.get("/sc/manufacturers/{manufacturer_id}/inspections", tags=["Supply Chain"])
async def get_manufacturer_inspections(manufacturer_id: str):
    """获取制造商检查记录"""
    service = SupplyChainService()
    inspections = service.get_manufacturer_inspections(manufacturer_id)
    return {"manufacturer_id": manufacturer_id, "inspections": inspections}


#===========================================================
# 监管领域端点
#===========================================================

@app.get("/regulatory/submissions/count", response_model=CountResponse, tags=["Regulatory"])
async def count_submissions():
    """统计申报数量"""
    service = RegulatoryService()
    count = service.count_submissions()
    return CountResponse(entity_type="submissions", count=count)


@app.get("/regulatory/submissions/{submission_id}", tags=["Regulatory"])
async def get_submission(submission_id: str):
    """获取申报详情"""
    service = RegulatoryService()
    submission = service.get_submission_by_id(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
    return submission


@app.get("/regulatory/approvals/{approval_id}", tags=["Regulatory"])
async def get_approval(approval_id: str):
    """获取批准详情"""
    service = RegulatoryService()
    approval = service.get_approval_by_id(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    return approval


@app.get("/regulatory/inspections/{inspection_id}", tags=["Regulatory"])
async def get_inspection(inspection_id: str):
    """获取检查详情"""
    service = RegulatoryService()
    inspection = service.get_inspection_by_id(inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection {inspection_id} not found")
    return inspection


@app.get("/regulatory/compliance-actions", tags=["Regulatory"])
async def get_compliance_actions(active_only: bool = True):
    """获取合规行动"""
    service = RegulatoryService()
    actions = service.get_compliance_actions(active_only=active_only)
    return {"compliance_actions": actions}


@app.get("/regulatory/safety-signals", tags=["Regulatory"])
async def get_safety_signals(
    status: str = Query(None, description="Filter by signal status"),
    limit: int = Query(50, description="Maximum number of signals to return", ge=1, le=100)
):
    """获取安全性信号"""
    service = RegulatoryService()
    signals = service.get_safety_signals(status=status, limit=limit)
    return {"safety_signals": signals}


@app.get("/regulatory/agencies/{agency_id}/statistics", tags=["Regulatory"])
async def get_agency_statistics(agency_id: str):
    """获取监管机构统计"""
    service = RegulatoryService()
    stats = service.get_agency_statistics(agency_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Agency {agency_id} not found")
    return stats


#===========================================================
# 跨域查询端点
#===========================================================

@app.get("/cross/drug/{drug_name}/trials", tags=["Cross-Domain"])
async def get_drug_trials(drug_name: str):
    """获取药品相关试验"""
    service = ClinicalDomainService()
    trials = service.get_trials_by_condition(drug_name)
    return {"drug_name": drug_name, "trials": trials}


@app.get("/cross/drug/{drug_name}/approvals", tags=["Cross-Domain"])
async def get_drug_approvals(drug_name: str):
    """获取药品相关批准"""
    service = RegulatoryService()
    approvals = service.get_approvals_by_drug(drug_name)
    return {"drug_name": drug_name, "approvals": approvals}


@app.get("/cross/drug/{drug_name}/overview", tags=["Cross-Domain"])
async def get_drug_overview(drug_name: str):
    """获取药品全景视图"""
    # 获取基本信息
    rd_service = ResearchDomainService()
    clinical_service = ClinicalDomainService()
    regulatory_service = RegulatoryService()

    # 这里可以组合多个查询
    overview = {
        "drug_name": drug_name,
        "clinical_trials": [],
        "regulatory_approvals": [],
        "related_entities": {}
    }

    # 获取试验
    try:
        trials = clinical_service.get_trials_by_condition(drug_name)
        overview["clinical_trials"] = trials[:5]  # 限制返回数量
    except Exception as e:
        logger.error(f"Error getting trials: {str(e)}")

    # 获取批准
    try:
        approvals = regulatory_service.get_approvals_by_drug(drug_name)
        overview["regulatory_approvals"] = approvals[:5]
    except Exception as e:
        logger.error(f"Error getting approvals: {str(e)}")

    return overview


#===========================================================
# 高级多跳查询端点 (Advanced Multi-hop Queries)
#===========================================================

@app.get("/advanced/compounds/{compound_id}/repurposing-opportunities", tags=["Advanced Queries"])
async def get_compound_repurposing(
    compound_id: str,
    min_evidence_level: str = Query("C", description="Minimum evidence level (A, B, C, D)"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100)
):
    """获取化合物的药物重定位机会"""
    service = AdvancedQueryService()
    opportunities = service.get_compound_repurposing_opportunities(
        compound_id,
        min_evidence_level=min_evidence_level,
        limit=limit
    )
    return {
        "compound_id": compound_id,
        "repurposing_opportunities": opportunities,
        "count": len(opportunities)
    }


@app.get("/advanced/diseases/{disease_id}/potential-compounds", tags=["Advanced Queries"])
async def get_disease_potential_compounds(
    disease_id: str,
    mechanism: str = Query(None, description="Filter by mechanism (INHIBITS, ACTIVATES, MODULATES)"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100)
):
    """获取疾病潜在的治疗化合物"""
    service = AdvancedQueryService()
    compounds = service.get_disease_potential_compounds(
        disease_id,
        mechanism=mechanism,
        limit=limit
    )
    return {
        "disease_id": disease_id,
        "potential_compounds": compounds,
        "count": len(compounds)
    }


@app.get("/advanced/compounds/{compound_id}/combination-therapy", tags=["Advanced Queries"])
async def get_combination_therapy_opportunities(
    compound_id: str,
    limit: int = Query(30, description="Maximum results", ge=1, le=100)
):
    """获取化合物的联合治疗机会"""
    service = AdvancedQueryService()
    combinations = service.get_compound_combination_therapy_opportunities(
        compound_id,
        limit=limit
    )
    return {
        "compound_id": compound_id,
        "combination_opportunities": combinations,
        "count": len(combinations)
    }


@app.get("/advanced/targets/{target_id}/competitive-landscape", tags=["Advanced Queries"])
async def get_target_competitive_landscape(
    target_id: str,
    include_pipeline_status: bool = Query(True, description="Include pipeline status")
):
    """获取靶点竞争格局分析"""
    service = AdvancedQueryService()
    landscape = service.get_target_competitive_landscape(
        target_id,
        include_pipeline_status=include_pipeline_status
    )
    if not landscape:
        raise HTTPException(status_code=404, detail=f"Target {target_id} not found")
    return landscape


@app.get("/advanced/diseases/{disease_id}/competitive-landscape", tags=["Advanced Queries"])
async def get_disease_competitive_landscape(
    disease_id: str,
    limit: int = Query(100, description="Maximum results", ge=1, le=200)
):
    """获取疾病竞争格局分析"""
    service = AdvancedQueryService()
    landscape = service.get_disease_competitive_landscape(disease_id, limit=limit)
    return {
        "disease_id": disease_id,
        "competitive_landscape": landscape,
        "count": len(landscape)
    }


@app.get("/advanced/company-pipeline", tags=["Advanced Queries"])
async def get_company_pipeline_analysis(
    company_name: str = Query(None, description="Filter by company name"),
    therapeutic_area: str = Query(None, description="Filter by therapeutic area")
):
    """获取公司研发管线分析"""
    service = AdvancedQueryService()
    pipeline = service.get_company_pipeline_analysis(
        company_name=company_name,
        therapeutic_area=therapeutic_area
    )
    return {
        "company_pipeline_analysis": pipeline,
        "count": len(pipeline)
    }


@app.get("/advanced/compounds/{compound_id}/safety-profile", tags=["Advanced Queries"])
async def get_compound_safety_profile(
    compound_id: str,
    include_preclinical: bool = Query(True, description="Include preclinical toxicity data")
):
    """获取化合物安全性全景视图"""
    service = AdvancedQueryService()
    profile = service.get_compound_safety_profile(
        compound_id,
        include_preclinical=include_preclinical
    )
    if not profile:
        raise HTTPException(status_code=404, detail=f"Compound {compound_id} not found")
    return profile


@app.get("/advanced/compounds/{compound_id}/safety-propagation", tags=["Advanced Queries"])
async def get_safety_signal_propagation(
    compound_id: str,
    max_hops: int = Query(3, description="Maximum path length", ge=1, le=5)
):
    """获取安全性信号传播路径"""
    service = AdvancedQueryService()
    paths = service.get_safety_signal_propagation(compound_id, max_hops=max_hops)
    return {
        "compound_id": compound_id,
        "propagation_paths": paths,
        "count": len(paths)
    }


@app.get("/advanced/targets/{target_id}/safety-association", tags=["Advanced Queries"])
async def get_target_safety_association(
    target_id: str,
    limit: int = Query(50, description="Maximum results", ge=1, le=100)
):
    """获取靶点相关的安全性问题"""
    service = AdvancedQueryService()
    associations = service.get_target_safety_association(target_id, limit=limit)
    return {
        "target_id": target_id,
        "safety_associations": associations,
        "count": len(associations)
    }


@app.get("/advanced/manufacturers/{manufacturer_id}/supply-chain-impact", tags=["Advanced Queries"])
async def get_manufacturer_supply_impact(
    manufacturer_id: str,
    include_downstream: bool = Query(True, description="Include downstream impact analysis")
):
    """获取制造商供应链影响分析"""
    service = AdvancedQueryService()
    impact = service.get_manufacturer_supply_chain_impact(
        manufacturer_id,
        include_downstream=include_downstream
    )
    if not impact:
        raise HTTPException(status_code=404, detail=f"Manufacturer {manufacturer_id} not found")
    return impact


@app.get("/advanced/drugs/{drug_product_id}/shortage-cascading-impact", tags=["Advanced Queries"])
async def get_drug_shortage_impact(
    drug_product_id: str,
    max_depth: int = Query(3, description="Maximum analysis depth", ge=1, le=5)
):
    """获取药品短缺的级联影响"""
    service = AdvancedQueryService()
    impact = service.get_drug_shortage_cascading_impact(drug_product_id, max_depth=max_depth)
    return {
        "drug_product_id": drug_product_id,
        "cascading_impact": impact
    }


@app.get("/advanced/api-supply-vulnerability", tags=["Advanced Queries"])
async def get_api_supply_vulnerability(
    api_name: str = Query(None, description="Filter by API name"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100)
):
    """获取API(原料药)供应脆弱性分析"""
    service = AdvancedQueryService()
    vulnerabilities = service.get_api_supply_vulnerability(api_name=api_name, limit=limit)
    return {
        "api_supply_vulnerabilities": vulnerabilities,
        "count": len(vulnerabilities)
    }


@app.get("/advanced/path/shortest", tags=["Advanced Queries"])
async def find_shortest_path(
    start_entity_id: str = Query(..., description="Start entity ID"),
    end_entity_id: str = Query(..., description="End entity ID"),
    max_path_length: int = Query(5, description="Maximum path length", ge=1, le=10),
    relationship_types: str = Query(None, description="Comma-separated relationship types")
):
    """查找两个实体之间的最短路径"""
    rel_types = relationship_types.split(',') if relationship_types else None
    service = AdvancedQueryService()
    paths = service.find_shortest_path(
        start_entity_id,
        end_entity_id,
        max_path_length=max_path_length,
        relationship_types=rel_types
    )
    return {
        "start_entity": start_entity_id,
        "end_entity": end_entity_id,
        "paths": paths,
        "count": len(paths)
    }


@app.get("/advanced/entities/{entity_id}/neighborhood", tags=["Advanced Queries"])
async def get_entity_neighborhood(
    entity_id: str,
    depth: int = Query(2, description="Neighborhood depth", ge=1, le=3),
    min_degree: int = Query(1, description="Minimum degree", ge=0, le=10)
):
    """获取实体的邻域分析"""
    service = AdvancedQueryService()
    neighborhood = service.get_entity_neighborhood(
        entity_id,
        depth=depth,
        min_degree=min_degree
    )
    if not neighborhood:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    return neighborhood


#===========================================================
# 聚合统计查询端点 (Aggregate Statistics Queries)
#===========================================================

@app.get("/statistics/overview", tags=["Statistics"])
async def get_statistics_overview():
    """获取知识图谱综合统计概览"""
    service = AggregateQueryService()
    stats = service.get_comprehensive_statistics()
    return stats


@app.get("/statistics/domain-breakdown", tags=["Statistics"])
async def get_domain_breakdown():
    """获取各领域详细统计"""
    try:
        db = get_db()

        # 获取R&D领域统计
        compound_result = db.execute_query("MATCH (c:Compound) RETURN count(c) as count")
        compound_count = compound_result.records[0]["count"] if compound_result.records else 0

        target_result = db.execute_query("MATCH (t:Target) RETURN count(t) as count")
        target_count = target_result.records[0]["count"] if target_result.records else 0

        assay_result = db.execute_query("MATCH (a:Assay) RETURN count(a) as count")
        assay_count = assay_result.records[0]["count"] if assay_result.records else 0

        pathway_result = db.execute_query("MATCH (p:Pathway) RETURN count(p) as count")
        pathway_count = pathway_result.records[0]["count"] if pathway_result.records else 0

        # 获取临床领域统计
        trial_result = db.execute_query("MATCH (t:ClinicalTrial) RETURN count(t) as count")
        trial_count = trial_result.records[0]["count"] if trial_result.records else 0

        subject_result = db.execute_query("MATCH (s:Subject) RETURN count(s) as count")
        subject_count = subject_result.records[0]["count"] if subject_result.records else 0

        ae_result = db.execute_query("MATCH (ae:AdverseEvent) RETURN count(ae) as count")
        ae_count = ae_result.records[0]["count"] if ae_result.records else 0

        # 获取供应链领域统计
        mfg_result = db.execute_query("MATCH (m:Manufacturer) RETURN count(m) as count")
        mfg_count = mfg_result.records[0]["count"] if mfg_result.records else 0

        shortage_result = db.execute_query("MATCH (ds:DrugShortage) RETURN count(ds) as count")
        shortage_count = shortage_result.records[0]["count"] if shortage_result.records else 0

        # 获取监管领域统计
        sub_result = db.execute_query("MATCH (s:Submission) RETURN count(s) as count")
        sub_count = sub_result.records[0]["count"] if sub_result.records else 0

        approval_result = db.execute_query("MATCH (a:Approval) RETURN count(a) as count")
        approval_count = approval_result.records[0]["count"] if approval_result.records else 0

        return {
            "rd_domain": {
                "name": "Research & Development",
                "entities": {
                    "compounds": compound_count,
                    "targets": target_count,
                    "assays": assay_count,
                    "pathways": pathway_count
                },
                "total": compound_count + target_count + assay_count + pathway_count
            },
            "clinical_domain": {
                "name": "Clinical Trials",
                "entities": {
                    "trials": trial_count,
                    "subjects": subject_count,
                    "adverse_events": ae_count
                },
                "total": trial_count + subject_count + ae_count
            },
            "supply_chain_domain": {
                "name": "Supply Chain",
                "entities": {
                    "manufacturers": mfg_count,
                    "shortages": shortage_count
                },
                "total": mfg_count + shortage_count
            },
            "regulatory_domain": {
                "name": "Regulatory",
                "entities": {
                    "submissions": sub_count,
                    "approvals": approval_count
                },
                "total": sub_count + approval_count
            }
        }
    except Exception as e:
        logger.error(f"Error getting domain breakdown: {e}")
        return {
            "rd_domain": {"name": "Research & Development", "entities": {"compounds": 0, "targets": 0, "assays": 0, "pathways": 0}, "total": 0},
            "clinical_domain": {"name": "Clinical Trials", "entities": {"trials": 0, "subjects": 0, "adverse_events": 0}, "total": 0},
            "supply_chain_domain": {"name": "Supply Chain", "entities": {"manufacturers": 0, "shortages": 0}, "total": 0},
            "regulatory_domain": {"name": "Regulatory", "entities": {"submissions": 0, "approvals": 0}, "total": 0}
        }


@app.get("/statistics/submissions/timeline", tags=["Statistics"])
async def get_submission_timeline(
    years: int = Query(10, description="Number of years to analyze", ge=1, le=50),
    submission_type: str = Query(None, description="Filter by submission type (NDA, ANDA, BLA)")
):
    """获取申报数量时序统计"""
    service = AggregateQueryService()
    timeline = service.get_submission_timeline(years=years, submission_type=submission_type)
    return {
        "years_analyzed": years,
        "submission_type_filter": submission_type,
        "timeline": timeline
    }


@app.get("/statistics/approvals/rate-timeline", tags=["Statistics"])
async def get_approval_rate_timeline(
    years: int = Query(10, description="Number of years to analyze", ge=1, le=50)
):
    """获取批准率时序统计"""
    service = AggregateQueryService()
    timeline = service.get_approval_rate_timeline(years=years)
    return {
        "years_analyzed": years,
        "approval_rate_timeline": timeline
    }


@app.get("/statistics/trials/timeline", tags=["Statistics"])
async def get_trial_timeline(
    years: int = Query(10, description="Number of years to analyze", ge=1, le=50),
    phase: str = Query(None, description="Filter by trial phase")
):
    """获取试验时序统计"""
    service = AggregateQueryService()
    timeline = service.get_clinical_trial_timeline(years=years, phase=phase)
    return {
        "years_analyzed": years,
        "phase_filter": phase,
        "trial_timeline": timeline
    }


@app.get("/statistics/shortages/timeline", tags=["Statistics"])
async def get_shortage_timeline(
    years: int = Query(5, description="Number of years to analyze", ge=1, le=20),
    impact_level: str = Query(None, description="Filter by impact level")
):
    """获取短缺时序统计"""
    service = AggregateQueryService()
    timeline = service.get_shortage_timeline(years=years, impact_level=impact_level)
    return {
        "years_analyzed": years,
        "impact_filter": impact_level,
        "shortage_timeline": timeline
    }


@app.get("/statistics/trials/geographic-distribution", tags=["Statistics"])
async def get_trial_geographic_distribution(
    top_n: int = Query(20, description="Top N countries to return", ge=5, le=100)
):
    """获取试验地理分布统计"""
    service = AggregateQueryService()
    distribution = service.get_trial_geographic_distribution(top_n=top_n)
    return {
        "geographic_distribution": distribution,
        "count": len(distribution)
    }


@app.get("/statistics/manufacturers/geographic-distribution", tags=["Statistics"])
async def get_manufacturer_geographic_distribution(
    top_n: int = Query(20, description="Top N countries to return", ge=5, le=100)
):
    """获取制造商地理分布统计"""
    service = AggregateQueryService()
    distribution = service.get_manufacturer_geographic_distribution(top_n=top_n)
    return {
        "geographic_distribution": distribution,
        "count": len(distribution)
    }


@app.get("/statistics/trials/success-rate-by-phase", tags=["Statistics"])
async def get_trial_success_rate_by_phase(
    min_trial_count: int = Query(10, description="Minimum trial count threshold", ge=1, le=100)
):
    """获取各阶段试验成功率"""
    service = AggregateQueryService()
    rates = service.get_trial_success_rate_by_phase(min_trial_count=min_trial_count)
    return {
        "min_trial_threshold": min_trial_count,
        "success_rates": rates
    }


@app.get("/statistics/approvals/rate-by-therapeutic-area", tags=["Statistics"])
async def get_approval_rate_by_therapeutic_area(
    min_submissions: int = Query(5, description="Minimum submission threshold", ge=1, le=50)
):
    """获取各治疗领域批准率"""
    service = AggregateQueryService()
    rates = service.get_approval_rate_by_therapeutic_area(min_submissions=min_submissions)
    return {
        "min_submission_threshold": min_submissions,
        "approval_rates_by_area": rates
    }


@app.get("/statistics/targets/success-rate", tags=["Statistics"])
async def get_target_based_success_rate(
    min_compounds: int = Query(5, description="Minimum compound threshold", ge=1, le=50)
):
    """获取基于靶点的化合物成功率"""
    service = AggregateQueryService()
    rates = service.get_target_based_success_rate(min_compounds=min_compounds)
    return {
        "min_compound_threshold": min_compounds,
        "target_success_rates": rates
    }


@app.get("/statistics/research-hotspots", tags=["Statistics"])
async def get_research_hotspots(
    top_n: int = Query(20, description="Top N hotspots to return", ge=5, le=100)
):
    """获取研究热点（活跃靶点和疾病）"""
    service = AggregateQueryService()
    hotspots = service.get_research_hotspots(top_n=top_n)
    return hotspots


@app.get("/statistics/targets/emerging", tags=["Statistics"])
async def get_emerging_targets(
    years: int = Query(3, description="Years to compare", ge=1, le=10),
    min_growth: float = Query(1.5, description="Minimum growth rate", ge=1.0, le=10.0)
):
    """获取新兴靶点（增长最快的靶点）"""
    service = AggregateQueryService()
    targets = service.get_emerging_targets(years=years, min_growth=min_growth)
    return {
        "years_compared": years,
        "min_growth_rate": min_growth,
        "emerging_targets": targets
    }


@app.get("/statistics/manufacturers/quality", tags=["Statistics"])
async def get_manufacturer_quality_statistics():
    """获取制造商质量统计"""
    service = AggregateQueryService()
    quality = service.get_manufacturer_quality_statistics()
    return {
        "manufacturer_quality_statistics": quality,
        "count": len(quality)
    }


@app.get("/statistics/shortages/analysis", tags=["Statistics"])
async def get_drug_shortage_analysis():
    """获取药品短缺分析"""
    service = AggregateQueryService()
    analysis = service.get_drug_shortage_analysis()
    return analysis


@app.get("/statistics/network/hub-entities", tags=["Statistics"])
async def get_highly_connected_entities(
    entity_type: str = Query(None, description="Filter by entity type"),
    min_degree: int = Query(10, description="Minimum degree threshold", ge=1, le=100),
    limit: int = Query(50, description="Maximum results", ge=1, le=200)
):
    """获取高度连接的实体（枢纽节点）"""
    service = AggregateQueryService()
    entities = service.get_highly_connected_entities(
        entity_type=entity_type,
        min_degree=min_degree,
        limit=limit
    )
    return {
        "entity_type_filter": entity_type,
        "min_degree": min_degree,
        "hub_entities": entities,
        "count": len(entities)
    }


@app.get("/statistics/pathways/coverage", tags=["Statistics"])
async def get_pathway_coverage_analysis():
    """获取通路覆盖分析"""
    service = AggregateQueryService()
    coverage = service.get_pathway_coverage_analysis()
    return {
        "pathway_coverage": coverage,
        "count": len(coverage)
    }


#===========================================================
# 搜索端点 (Search Endpoints)
#===========================================================

@app.post("/api/v1/search/fulltext", response_model=FullTextSearchResponse, tags=["Search"])
async def fulltext_search(request: FullTextSearchRequest):
    """全文搜索 - 在知识图谱中搜索实体"""
    try:
        service = SearchService()
        result = service.fulltext_search(
            query_text=request.query,
            entity_types=request.entity_types,
            limit=request.limit,
            skip=request.skip
        )

        # 转换结果为响应模型
        search_results = []
        for item in result.get("results", []):
            search_results.append(SearchResultItem(
                entity_type=item.get("entity_type", "Unknown"),
                element_id=item.get("element_id"),
                primary_id=item.get("primary_id"),
                name=item.get("name"),
                score=item.get("score", 0.0),
                index_name=item.get("index_name")
            ))

        return FullTextSearchResponse(
            results=search_results,
            total=result.get("total", 0),
            returned=len(search_results),
            query=request.query,
            entity_types=request.entity_types,
            skip=request.skip,
            limit=request.limit,
            message=result.get("message")
        )
    except Exception as e:
        logger.error(f"Fulltext search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/v1/search/fuzzy", response_model=FuzzySearchResponse, tags=["Search"])
async def fuzzy_search(request: FuzzySearchRequest):
    """模糊搜索 - 使用编辑距离进行模糊匹配"""
    try:
        service = SearchService()
        result = service.fuzzy_search(
            query_text=request.query,
            entity_type=request.entity_type,
            search_field=request.search_field,
            max_distance=request.max_distance,
            limit=request.limit,
            skip=request.skip
        )

        # 转换结果为响应模型
        search_results = []
        for item in result.get("results", []):
            search_results.append(FuzzySearchResultItem(
                entity_type=item.get("entity_type", request.entity_type),
                element_id=item.get("element_id"),
                primary_id=item.get("primary_id"),
                name=item.get("name"),
                distance=item.get("distance"),
                similarity=item.get("similarity", 0.0),
                method=item.get("method", "UNKNOWN")
            ))

        return FuzzySearchResponse(
            results=search_results,
            total=result.get("total", 0),
            returned=len(search_results),
            query=request.query,
            entity_type=request.entity_type,
            search_field=request.search_field,
            max_distance=request.max_distance,
            skip=request.skip,
            limit=request.limit,
            method=result.get("method", "UNKNOWN"),
            message=result.get("message")
        )
    except Exception as e:
        logger.error(f"Fuzzy search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fuzzy search failed: {str(e)}")


@app.get("/api/v1/search/suggestions", response_model=SuggestionResponse, tags=["Search"])
async def get_search_suggestions(
    prefix: str = Query(..., min_length=1, description="搜索前缀"),
    entity_type: str = Query(..., description="实体类型"),
    search_field: str = Query("name", description="搜索字段"),
    limit: int = Query(10, ge=1, le=50, description="返回建议数量")
):
    """获取搜索建议 - 自动完成功能"""
    try:
        service = SearchService()
        result = service.get_suggestions(
            prefix=prefix,
            entity_type=entity_type,
            search_field=search_field,
            limit=limit
        )

        # 转换结果为响应模型
        suggestions = []
        for item in result.get("suggestions", []):
            suggestions.append(SuggestionItem(
                text=item.get("text"),
                frequency=item.get("frequency", 0)
            ))

        return SuggestionResponse(
            suggestions=suggestions,
            total=len(suggestions),
            prefix=prefix,
            entity_type=entity_type,
            search_field=search_field
        )
    except Exception as e:
        logger.error(f"Suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@app.post("/api/v1/search/aggregate", response_model=AggregateSearchResponse, tags=["Search"])
async def aggregate_search(request: AggregateSearchRequest):
    """聚合搜索 - 按维度分组统计搜索结果"""
    try:
        service = SearchService()
        result = service.aggregate_search(
            query_text=request.query,
            group_by=request.group_by,
            limit=request.limit
        )

        # 转换结果为响应模型
        groups = []
        for item in result.get("groups", []):
            groups.append(AggregateSearchGroup(
                entity_type=item.get("entity_type"),
                domain=item.get("domain"),
                count=item.get("count", 0),
                entity_types=item.get("entity_types"),
                results=item.get("results", [])
            ))

        return AggregateSearchResponse(
            groups=groups,
            total_groups=result.get("total_groups", 0),
            total_results=result.get("total_results", 0),
            query=request.query,
            group_by=request.group_by,
            message=result.get("message")
        )
    except Exception as e:
        logger.error(f"Aggregate search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Aggregate search failed: {str(e)}")


@app.post("/api/v1/search/multi-entity", response_model=MultiEntitySearchResponse, tags=["Search"])
async def multi_entity_search(request: MultiEntitySearchRequest):
    """多实体搜索 - 在多个实体类型中同时搜索"""
    try:
        service = SearchService()

        # 转换请求配置为服务层格式
        entity_config = [
            {"entity_type": e.entity_type, "search_field": e.search_field}
            for e in request.entities
        ]

        result = service.multi_entity_search(
            query_text=request.query,
            entity_config=entity_config,
            limit_per_entity=request.limit_per_entity
        )

        return MultiEntitySearchResponse(
            results=result.get("results", {}),
            total_entities=result.get("total_entities", 0),
            total_results=result.get("total_results", 0),
            query=request.query
        )
    except Exception as e:
        logger.error(f"Multi-entity search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Multi-entity search failed: {str(e)}")


@app.post("/api/v1/search/indexes/create", tags=["Search Admin"])
async def create_search_indexes():
    """创建全文搜索索引 - 管理员端点"""
    try:
        db = get_db()
        result = db.create_fulltext_indexes()
        return result
    except Exception as e:
        logger.error(f"Failed to create search indexes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create indexes: {str(e)}")


@app.get("/api/v1/search/indexes", tags=["Search Admin"])
async def list_search_indexes():
    """列出所有全文搜索索引"""
    try:
        service = SearchService()
        indexes = service.list_fulltext_indexes()
        return {
            "indexes": indexes,
            "total": len(indexes)
        }
    except Exception as e:
        logger.error(f"Failed to list indexes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list indexes: {str(e)}")


#===========================================================
# 额外统计端点 (Additional Statistics Endpoints)
#===========================================================

@app.get("/statistics/timeline", tags=["Statistics"])
async def get_general_timeline(
    years: int = Query(10, description="Number of years to analyze", ge=1, le=50)
):
    """获取通用时序统计（返回submissions timeline）"""
    try:
        service = AggregateQueryService()
        timeline = service.get_submission_timeline(years=years, submission_type=None)
        # timeline 可能是空列表或包含数据
        return {
            "years_analyzed": years,
            "timeline": timeline if isinstance(timeline, list) else []
        }
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        return {
            "years_analyzed": years,
            "timeline": []
        }


#===========================================================
# Clinical Domain 额外端点
#===========================================================

@app.get("/clinical/statistics", tags=["Clinical Domain"])
async def get_clinical_statistics():
    """获取临床领域统计"""
    try:
        service = ClinicalDomainService()
        db = get_db()
        # 获取试验数量
        trial_count_result = db.execute_query(
            "MATCH (t:ClinicalTrial) RETURN count(t) as count"
        )
        trial_count = trial_count_result.records[0]["count"] if trial_count_result else 0

        # 获取受试者数量
        subject_count_result = db.execute_query(
            "MATCH (s:Subject) RETURN count(s) as count"
        )
        subject_count = subject_count_result.records[0]["count"] if subject_count_result else 0

        # 获取不良事件数量
        ae_count_result = db.execute_query(
            "MATCH (ae:AdverseEvent) RETURN count(ae) as count"
        )
        ae_count = ae_count_result.records[0]["count"] if ae_count_result else 0

        return {
            "total_trials": trial_count,
            "total_subjects": subject_count,
            "total_adverse_events": ae_count,
            "phases": {
                "phase_1": 0,
                "phase_2": 0,
                "phase_3": 0,
                "phase_4": 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting clinical statistics: {e}")
        return {
            "total_trials": 0,
            "total_subjects": 0,
            "total_adverse_events": 0,
            "phases": {}
        }


@app.get("/clinical/trials", tags=["Clinical Domain"])
async def list_clinical_trials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    phase: str = Query(None, description="Filter by trial phase"),
    status: str = Query(None, description="Filter by trial status")
):
    """获取临床试验列表"""
    try:
        db = get_db()
        skip = (page - 1) * page_size

        # 构建查询条件
        where_clauses = []
        if phase:
            where_clauses.append(f"t.phase = '{phase}'")
        if status:
            where_clauses.append(f"t.status = '{status}'")

        where_clause = " AND " .join(where_clauses) if where_clauses else ""

        # 获取总数
        count_query = f"MATCH (t:ClinicalTrial) WHERE {where_clause} RETURN count(t) as count" if where_clause else "MATCH (t:ClinicalTrial) RETURN count(t) as count"
        count_result = db.execute_query(count_query)
        total = count_result.records[0]["count"] if count_result else 0

        # 获取列表
        list_query = f"""
            MATCH (t:ClinicalTrial)
            WHERE {where_clause}
            RETURN t.nct_id as nct_id, t.brief_title as title, t.phase as phase, t.status as status
            SKIP {skip}
            LIMIT {page_size}
        """ if where_clause else f"""
            MATCH (t:ClinicalTrial)
            RETURN t.nct_id as nct_id, t.brief_title as title, t.phase as phase, t.status as status
            SKIP {skip}
            LIMIT {page_size}
        """

        result = db.execute_query(list_query)

        items = []
        for record in result.records:
            items.append({
                "nct_id": record.get("nct_id"),
                "title": record.get("title"),
                "phase": record.get("phase"),
                "status": record.get("status")
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error listing clinical trials: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }


#===========================================================
# Supply Chain 额外端点（使用 /supply 路径）
#===========================================================

@app.get("/supply/manufacturers", tags=["Supply Chain"])
async def list_supply_manufacturers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str = Query(None, description="Filter by country")
):
    """获取制造商/公司列表（使用 /supply 路径）"""
    try:
        db = get_db()
        skip = (page - 1) * page_size

        # 先查询 Manufacturer 节点，如果没有则查询 Company 节点
        count_query = "MATCH (m:Manufacturer) RETURN count(m) as count"
        count_result = db.execute_query(count_query)
        mfg_count = count_result.records[0]["count"] if count_result and count_result.records else 0

        if mfg_count > 0:
            # 有 Manufacturer 节点
            list_query = f"""
                MATCH (m:Manufacturer)
                RETURN m.manufacturer_id as id, m.name as name, m.country as location, m.type as type, m.status as status
                ORDER BY m.name
                SKIP {skip}
                LIMIT {page_size}
            """
            total = mfg_count
        else:
            # 使用 Company 节点作为制造商
            list_query = f"""
                MATCH (c:Company)
                RETURN c.name as id, c.name as name, c.address as location, 'Pharmaceutical' as type, 'active' as status
                ORDER BY c.name
                SKIP {skip}
                LIMIT {page_size}
            """
            count_query = "MATCH (c:Company) RETURN count(c) as count"
            count_result = db.execute_query(count_query)
            total = count_result.records[0]["count"] if count_result and count_result.records else 0

        result = db.execute_query(list_query)

        data = []
        for record in result.records:
            data.append({
                "id": record.get("id"),
                "name": record.get("name"),
                "location": record.get("location"),
                "type": record.get("type"),
                "status": record.get("status")
            })

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error listing manufacturers: {e}")
        return {
            "data": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }


@app.get("/supply/facilities", tags=["Supply Chain"])
async def list_supply_facilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str = Query(None, description="Filter by country"),
    facility_type: str = Query(None, description="Filter by facility type")
):
    """获取生产设施列表（暂时返回空数据）"""
    # TODO: 实现完整的生产设施数据查询
    return {
        "data": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "total_pages": 0
    }


@app.get("/supply/statistics", tags=["Supply Chain"])
async def get_supply_statistics():
    """获取供应链统计"""
    try:
        db = get_db()

        # 获取制造商数量 (优先 Manufacturer，fallback 到 Company)
        mfg_count_result = db.execute_query(
            "MATCH (m:Manufacturer) RETURN count(m) as count"
        )
        mfg_count = mfg_count_result.records[0]["count"] if mfg_count_result and mfg_count_result.records else 0

        if mfg_count == 0:
            # Fallback to Company nodes
            company_count_result = db.execute_query(
                "MATCH (c:Company) RETURN count(c) as count"
            )
            mfg_count = company_count_result.records[0]["count"] if company_count_result and company_count_result.records else 0

        # 获取短缺数量
        shortage_count_result = db.execute_query(
            "MATCH (s:DrugShortage) RETURN count(s) as count"
        )
        shortage_count = shortage_count_result.records[0]["count"] if shortage_count_result and shortage_count_result.records else 0

        return {
            "total_manufacturers": mfg_count,
            "active_shortages": shortage_count
        }
    except Exception as e:
        logger.error(f"Error getting supply statistics: {e}")
        return {
            "total_manufacturers": 0,
            "active_shortages": 0
        }


#===========================================================
# Regulatory 额外端点
#===========================================================

@app.get("/regulatory/statistics", tags=["Regulatory"])
async def get_regulatory_statistics():
    """获取监管领域统计"""
    try:
        db = get_db()

        # 获取申报数量
        submission_count_result = db.execute_query(
            "MATCH (s:RegulatorySubmission) RETURN count(s) as count"
        )
        submission_count = submission_count_result.records[0]["count"] if submission_count_result else 0

        # 获取批准数量
        approval_count_result = db.execute_query(
            "MATCH (a:RegulatoryApproval) RETURN count(a) as count"
        )
        approval_count = approval_count_result.records[0]["count"] if approval_count_result else 0

        return {
            "total_submissions": submission_count,
            "total_approvals": approval_count,
            "pending_reviews": 0,
            "approved_this_year": 0
        }
    except Exception as e:
        logger.error(f"Error getting regulatory statistics: {e}")
        return {
            "total_submissions": 0,
            "total_approvals": 0,
            "pending_reviews": 0,
            "approved_this_year": 0
        }


@app.get("/regulatory/submissions", tags=["Regulatory"])
async def list_regulatory_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    submission_type: str = Query(None, description="Filter by submission type (NDA, ANDA, BLA)")
):
    """获取监管申报列表"""
    try:
        db = get_db()
        skip = (page - 1) * page_size

        # 构建查询条件
        where_clause = f"s.submission_type = '{submission_type}'" if submission_type else ""

        # 获取总数
        count_query = f"MATCH (s:RegulatorySubmission) WHERE {where_clause} RETURN count(s) as count" if where_clause else "MATCH (s:RegulatorySubmission) RETURN count(s) as count"
        count_result = db.execute_query(count_query)
        total = count_result.records[0]["count"] if count_result else 0

        # 获取列表
        list_query = f"""
            MATCH (s:RegulatorySubmission)
            WHERE {where_clause}
            RETURN s.submission_id as submission_id, s.submission_type as submission_type, s.submit_date as submit_date, s.status as status
            SKIP {skip}
            LIMIT {page_size}
        """ if where_clause else f"""
            MATCH (s:RegulatorySubmission)
            RETURN s.submission_id as submission_id, s.submission_type as submission_type, s.submit_date as submit_date, s.status as status
            SKIP {skip}
            LIMIT {page_size}
        """

        result = db.execute_query(list_query)

        items = []
        for record in result.records:
            items.append({
                "submission_id": record.get("submission_id"),
                "submission_type": record.get("submission_type"),
                "submit_date": record.get("submit_date"),
                "status": record.get("status")
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error listing regulatory submissions: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }


@app.get("/regulatory/approvals", tags=["Regulatory"])
async def list_regulatory_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    therapeutic_area: str = Query(None, description="Filter by therapeutic area")
):
    """获取监管批准列表"""
    try:
        db = get_db()
        skip = (page - 1) * page_size

        # 构建查询条件
        where_clause = f"a.therapeutic_area = '{therapeutic_area}'" if therapeutic_area else ""

        # 获取总数
        count_query = f"MATCH (a:RegulatoryApproval) WHERE {where_clause} RETURN count(a) as count" if where_clause else "MATCH (a:RegulatoryApproval) RETURN count(a) as count"
        count_result = db.execute_query(count_query)
        total = count_result.records[0]["count"] if count_result else 0

        # 获取列表
        list_query = f"""
            MATCH (a:RegulatoryApproval)
            WHERE {where_clause}
            RETURN a.approval_id as approval_id, a.drug_name as drug_name, a.therapeutic_area as therapeutic_area, a.approval_date as approval_date
            SKIP {skip}
            LIMIT {page_size}
        """ if where_clause else f"""
            MATCH (a:RegulatoryApproval)
            RETURN a.approval_id as approval_id, a.drug_name as drug_name, a.therapeutic_area as therapeutic_area, a.approval_date as approval_date
            SKIP {skip}
            LIMIT {page_size}
        """

        result = db.execute_query(list_query)

        items = []
        for record in result.records:
            items.append({
                "approval_id": record.get("approval_id"),
                "drug_name": record.get("drug_name"),
                "therapeutic_area": record.get("therapeutic_area"),
                "approval_date": record.get("approval_date")
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error listing regulatory approvals: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }


# Missing regulatory endpoints (placeholder implementations)
@app.get("/regulatory/agencies", tags=["Regulatory"])
async def list_agencies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: str = Query(None)
):
    """获取监管机构列表（暂时返回空数据）"""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": page_size,
        "totalPages": 0
    }


@app.get("/regulatory/agencies/{agency_id}", tags=["Regulatory"])
async def get_agency(agency_id: str):
    """获取单个监管机构（暂时返回空数据）"""
    return None


@app.get("/regulatory/agencies/{agency_id}/statistics", tags=["Regulatory"])
async def get_agency_statistics(agency_id: str):
    """获取监管机构统计数据（暂时返回空数据）"""
    return {}


@app.get("/regulatory/documents", tags=["Regulatory"])
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_type: str = Query(None)
):
    """获取监管文档列表（暂时返回空数据）"""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": page_size,
        "totalPages": 0
    }


@app.get("/regulatory/documents/{document_id}", tags=["Regulatory"])
async def get_document(document_id: str):
    """获取单个监管文档（暂时返回空数据）"""
    return None


@app.get("/regulatory/submissions/{submission_id}/timeline", tags=["Regulatory"])
async def get_submission_timeline(submission_id: str):
    """获取申报时间线（暂时返回空数据）"""
    return []


@app.get("/regulatory/submissions/{submission_id}/approvals", tags=["Regulatory"])
async def get_submission_approvals(submission_id: str):
    """获取申报相关的批准（暂时返回空数据）"""
    return []


@app.get("/regulatory/submissions/{submission_id}/documents", tags=["Regulatory"])
async def get_submission_documents(submission_id: str):
    """获取申报相关文档（暂时返回空数据）"""
    return []


@app.get("/regulatory/approvals/{approval_id}/submission", tags=["Regulatory"])
async def get_approval_submission(approval_id: str):
    """获取批准相关的申报（暂时返回空数据）"""
    return None


@app.get("/regulatory/compliance/{entity_id}", tags=["Regulatory"])
async def get_compliance(entity_id: str):
    """获取合规记录（暂时返回空数据）"""
    return []


@app.get("/regulatory/crls", tags=["Regulatory"])
async def list_crls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_name: str = Query(None),
    approval_status: str = Query(None),
    letter_type: str = Query(None)
):
    """获取 FDA Complete Response Letters 列表"""
    db = get_db()

    conditions = ["1=1"]
    parameters = {}

    if company_name:
        conditions.append("c.company_name CONTAINS $company_name")
        parameters["company_name"] = company_name

    if approval_status:
        conditions.append("c.approval_status = $approval_status")
        parameters["approval_status"] = approval_status

    if letter_type:
        conditions.append("c.letter_type = $letter_type")
        parameters["letter_type"] = letter_type

    where_clause = " AND ".join(conditions)

    # Count query
    count_query = f"""
        MATCH (c:CompleteResponseLetter)
        WHERE {where_clause}
        RETURN count(c) as total
    """
    count_result = db.execute_query(count_query, parameters)
    total = count_result.records[0]["total"] if count_result.records else 0

    # Data query
    data_query = f"""
        MATCH (c:CompleteResponseLetter)
        WHERE {where_clause}
        RETURN c.file_name as id,
               c.letter_type as letter_type,
               c.company_name as company_name,
               c.approval_status as approval_status,
               c.letter_date as letter_date,
               c.approver_center as approver_center,
               c.application_number as application_number,
               c.text_preview as text_preview
        ORDER BY c.letter_date DESC
        SKIP $skip
        LIMIT $limit
    """
    parameters["skip"] = (page - 1) * page_size
    parameters["limit"] = page_size

    result = db.execute_query(data_query, parameters)
    data = [dict(record) for record in result.records]

    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
    }


@app.get("/regulatory/crls/{file_name}", tags=["Regulatory"])
async def get_crl(file_name: str):
    """获取单个 FDA Complete Response Letter 详情"""
    db = get_db()

    query = """
        MATCH (c:CompleteResponseLetter {file_name: $file_name})
        RETURN c.file_name as id,
               c.letter_type as letter_type,
               c.company_name as company_name,
               c.company_address as company_address,
               c.company_rep as company_rep,
               c.approval_status as approval_status,
               c.letter_date as letter_date,
               c.letter_year as letter_year,
               c.approver_name as approver_name,
               c.approver_title as approver_title,
               c.approver_center as approver_center,
               c.application_number as application_number,
               c.text_preview as text_preview,
               c.source as source
    """
    result = db.execute_query(query, {"file_name": file_name})

    if not result.records:
        raise HTTPException(status_code=404, detail="CRL not found")

    return dict(result.records[0])


#===========================================================
# 主应用入口（如果直接运行）
#===========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
