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
import logging

from .config import settings
from .database import get_db, close_db
from .models import (
    HealthResponse, ErrorResponse, OverviewResponse,
    CountResponse, StatsResponse
)

# 导入服务
from .services.research_domain import ResearchDomainService
from .services.clinical_domain import ClinicalDomainService
from .services.supply_regulatory import SupplyChainService, RegulatoryService

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="制药行业知识图谱REST API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 启动和关闭事件处理
@asynccontextmanager
async def lifespan():
    """应用生命周期管理"""
    # 启动时
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # 关闭时
    await close_db()
    logger.info(f"Stopped {settings.APP_NAME}")

app.router.lifespan_context = lifespan


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


@app.get("/rd/compounds/{compound_id}", tags=["Research Domain"])
async def get_compound(compound_id: str):
    """获取化合物详情"""
    service = ResearchDomainService()
    compound = service.get_compound_by_id(compound_id)
    if not compound:
        raise HTTPException(status_code=404, detail=f"Compound {compound_id} not found")
    return compound


@app.get("/rd/compounds/{compound_id}/targets", tags=["Research Domain"])
async def get_compound_targets(compound_id: str):
    """获取化合物的靶点"""
    service = ResearchDomainService()
    targets = service.get_compound_targets(compound_id)
    return {"compound_id": compound_id, "targets": targets}


@app.get("/rd/targets/{target_id}/compounds", tags=["Research Domain"])
async def get_target_compounds(target_id: str):
    """获取靶点的化合物"""
    service = ResearchDomainService()
    compounds = service.get_target_compounds(target_id)
    return {"target_id": target_id, "compounds": compounds}


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
