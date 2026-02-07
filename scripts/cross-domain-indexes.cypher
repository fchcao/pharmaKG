#===========================================================
# PharmaKG - 跨域查询索引优化脚本
# Pharmaceutical Knowledge Graph - Cross-Domain Index Optimization
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
# 描述: 为跨域查询创建专用索引，提升查询性能
#===========================================================

// 清理现有索引（可选，用于重建）
// DROP INDEX compound_id_index IF EXISTS;
// DROP INDEX target_id_index IF EXISTS;
// DROP INDEX disease_id_index IF EXISTS;
// DROP INDEX trial_id_index IF EXISTS;
// DROP INDEX manufacturer_id_index IF EXISTS;
// DROP INDEX submission_id_index IF EXISTS;

//===========================================================
// 一、R&D 领域索引
//===========================================================

// 化合物索引
CREATE INDEX compound_primary_id_index IF NOT EXISTS
FOR (c:Compound) ON (c.primary_id);

CREATE INDEX compound_name_index IF NOT EXISTS
FOR (c:Compound) ON (c.name);

CREATE INDEX compound_smiles_index IF NOT EXISTS
FOR (c:Compound) ON (c.smiles);

CREATE INDEX compound_inchikey_index IF NOT EXISTS
FOR (c:Compound) ON (c.inchikey);

CREATE FULLTEXT INDEX compound_fulltext_index IF NOT EXISTS
FOR (c:Compound) ON EACH [c.name, c.description];

// 靶点索引
CREATE INDEX target_primary_id_index IF NOT EXISTS
FOR (t:Target) ON (t.primary_id);

CREATE INDEX target_name_index IF NOT EXISTS
FOR (t:Target) ON (t.name);

CREATE INDEX target_class_index IF NOT EXISTS
FOR (t:Target) ON (t.target_class);

CREATE FULLTEXT INDEX target_fulltext_index IF NOT EXISTS
FOR (t:Target) ON EACH [t.name, t.description];

// 疾病索引
CREATE INDEX disease_primary_id_index IF NOT EXISTS
FOR (d:Disease) ON (d.primary_id);

CREATE INDEX disease_name_index IF NOT EXISTS
FOR (d:Disease) ON (d.name);

CREATE INDEX disease_class_index IF NOT EXISTS
FOR (d:Disease) ON (d.disease_class);

CREATE INDEX disease_therapeutic_area_index IF NOT EXISTS
FOR (d:Disease) ON (d.therapeutic_area);

CREATE FULLTEXT INDEX disease_fulltext_index IF NOT EXISTS
FOR (d:Disease) ON EACH [d.name, d.description];

// 通路索引
CREATE INDEX pathway_primary_id_index IF NOT EXISTS
FOR (p:Pathway) ON (p.primary_id);

CREATE INDEX pathway_name_index IF NOT EXISTS
FOR (p:Pathway) ON (p.name);

// 实验索引
CREATE INDEX assay_id_index IF NOT EXISTS
FOR (a:Assay) ON (a.assay_id);

CREATE INDEX assay_type_index IF NOT EXISTS
FOR (a:Assay) ON (a.assay_type);

//===========================================================
// 二、临床领域索引
//===========================================================

// 临床试验索引
CREATE INDEX trial_trial_id_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.trial_id);

CREATE INDEX trial_phase_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.phase);

CREATE INDEX trial_status_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.status);

CREATE INDEX trial_start_date_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.start_date);

CREATE INDEX trial_end_date_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.end_date);

CREATE FULLTEXT INDEX trial_fulltext_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON EACH [t.title, t.description];

// 受试者索引
CREATE INDEX subject_subject_id_index IF NOT EXISTS
FOR (s:Subject) ON (s.subject_id);

CREATE INDEX subject_status_index IF NOT EXISTS
FOR (s:Subject) ON (s.status);

// 干预措施索引
CREATE INDEX intervention_id_index IF NOT EXISTS
FOR (i:Intervention) ON (i.intervention_id);

CREATE INDEX intervention_type_index IF NOT EXISTS
FOR (i:Intervention) ON (i.intervention_type);

// 不良事件索引
CREATE INDEX adverse_event_id_index IF NOT EXISTS
FOR (ae:AdverseEvent) ON (ae.ae_id);

CREATE INDEX adverse_event_severity_index IF NOT EXISTS
FOR (ae:AdverseEvent) ON (ae.severity);

CREATE INDEX adverse_event_type_index IF NOT EXISTS
FOR (ae:AdverseEvent) ON (ae.adverse_event_type);

CREATE FULLTEXT INDEX adverse_event_fulltext_index IF NOT EXISTS
FOR (ae:AdverseEvent) ON EACH [ae.preferred_term, ae.description];

// 研究中心索引
CREATE INDEX study_site_id_index IF NOT EXISTS
FOR (ss:StudySite) ON (ss.site_id);

CREATE INDEX study_site_country_index IF NOT EXISTS
FOR (ss:StudySite) ON (ss.country);

//===========================================================
// 三、供应链领域索引
//===========================================================

// 制造商索引
CREATE INDEX manufacturer_id_index IF NOT EXISTS
FOR (m:Manufacturer) ON (m.manufacturer_id);

CREATE INDEX manufacturer_name_index IF NOT EXISTS
FOR (m:Manufacturer) ON (m.name);

CREATE INDEX manufacturer_country_index IF NOT EXISTS
FOR (m:Manufacturer) ON (m.country);

CREATE FULLTEXT INDEX manufacturer_fulltext_index IF NOT EXISTS
FOR (m:Manufacturer) ON EACH [m.name, m.location];

// 药品产品索引
CREATE INDEX drug_product_id_index IF NOT EXISTS
FOR (dp:DrugProduct) ON (dp.product_id);

CREATE INDEX drug_product_name_index IF NOT EXISTS
FOR (dp:DrugProduct) ON (dp.name);

CREATE FULLTEXT INDEX drug_product_fulltext_index IF NOT EXISTS
FOR (dp:DrugProduct) ON EACH [dp.name, dp.description];

// 药品短缺索引
CREATE INDEX drug_shortage_id_index IF NOT EXISTS
FOR (ds:DrugShortage) ON (ds.shortage_id);

CREATE INDEX shortage_status_index IF NOT EXISTS
FOR (ds:DrugShortage) ON (ds.status);

CREATE INDEX shortage_start_date_index IF NOT EXISTS
FOR (ds:DrugShortage) ON (ds.start_date);

CREATE INDEX shortage_impact_level_index IF NOT EXISTS
FOR (ds:DrugShortage) ON (ds.impact_level);

// 供应商索引
CREATE INDEX supplier_id_index IF NOT EXISTS
FOR (s:Supplier) ON (s.supplier_id);

CREATE INDEX supplier_name_index IF NOT EXISTS
FOR (s:Supplier) ON (s.name);

// 检查索引
CREATE INDEX inspection_id_index IF NOT EXISTS
FOR (i:Inspection) ON (i.inspection_id);

CREATE INDEX inspection_result_index IF NOT EXISTS
FOR (i:Inspection) ON (i.result);

CREATE INDEX inspection_date_index IF NOT EXISTS
FOR (i:Inspection) ON (i.inspection_date);

//===========================================================
// 四、监管领域索引
//===========================================================

// 申报索引
CREATE INDEX submission_id_index IF NOT EXISTS
FOR (s:Submission) ON (s.submission_id);

CREATE INDEX submission_type_index IF NOT EXISTS
FOR (s:Submission) ON (s.submission_type);

CREATE INDEX submission_date_index IF NOT EXISTS
FOR (s:Submission) ON (s.submission_date);

CREATE INDEX submission_status_index IF NOT EXISTS
FOR (s:Submission) ON (s.status);

// 批准索引
CREATE INDEX approval_id_index IF NOT EXISTS
FOR (a:Approval) ON (a.approval_id);

CREATE INDEX approval_date_index IF NOT EXISTS
FOR (a:Approval) ON (a.approval_date);

CREATE INDEX approval_status_index IF NOT EXISTS
FOR (a:Approval) ON (a.approval_status);

// 监管机构索引
CREATE INDEX agency_id_index IF NOT EXISTS
FOR (ra:RegulatoryAgency) ON (ra.agency_id);

CREATE INDEX agency_name_index IF NOT EXISTS
FOR (ra:RegulatoryAgency) ON (ra.name);

CREATE INDEX agency_type_index IF NOT EXISTS
FOR (ra:RegulatoryAgency) ON (ra.agency_type);

// 合规行动索引
CREATE INDEX compliance_action_id_index IF NOT EXISTS
FOR (ca:ComplianceAction) ON (ca.action_id);

CREATE INDEX compliance_action_type_index IF NOT EXISTS
FOR (ca:ComplianceAction) ON (ca.action_type);

CREATE INDEX compliance_action_date_index IF NOT EXISTS
FOR (ca:ComplianceAction) ON (ca.action_date);

// 安全性信号索引
CREATE INDEX safety_signal_id_index IF NOT EXISTS
FOR (ss:SafetySignal) ON (ss.signal_id);

CREATE INDEX safety_signal_status_index IF NOT EXISTS
FOR (ss:SafetySignal) ON (ss.signal_status);

CREATE INDEX safety_signal_date_index IF NOT EXISTS
FOR (ss:SafetySignal) ON (ss.signal_date);

//===========================================================
// 五、跨域关系索引
//===========================================================

// 化合物-试验跨域索引
CREATE INDEX compound_trial_index IF NOT EXISTS
FOR ()-[r:TESTED_IN_CLINICAL_TRIAL]->() ON (r.created_at);

// 化合物-批准跨域索引
CREATE INDEX compound_approval_index IF NOT EXISTS
FOR ()-[r:APPROVED_AS_DRUG]->() ON (r.approval_date);

// 靶点-疾病跨域索引
CREATE INDEX target_disease_index IF NOT EXISTS
FOR ()-[r:ASSOCIATED_WITH_DISEASE|CAUSES_DISEASE|BIOMARKER_FOR]->() ON (r.evidence_level);

// 试验-疾病跨域索引
CREATE INDEX trial_disease_index IF NOT EXISTS
FOR ()-[r:TRIAL_FOR_DISEASE]->() ON (r.indication);

// 制造商-监管跨域索引
CREATE INDEX manufacturer_agency_index IF NOT EXISTS
FOR ()-[r:HOLDS_LICENSE_FROM]->() ON (r.license_type);

//===========================================================
// 六、复合索引（用于常见查询模式）
//===========================================================

// 试验阶段+状态复合索引
CREATE INDEX trial_phase_status_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.phase, t.status);

// 试验日期范围复合索引
CREATE INDEX trial_date_range_index IF NOT EXISTS
FOR (t:ClinicalTrial) ON (t.start_date, t.end_date);

// 申报类型+状态复合索引
CREATE INDEX submission_type_status_index IF NOT EXISTS
FOR (s:Submission) ON (s.submission_type, s.status);

// 申报日期范围复合索引
CREATE INDEX submission_date_range_index IF NOT EXISTS
FOR (s:Submission) ON (s.submission_date, s.review_date);

// 短缺状态+开始日期复合索引
CREATE INDEX shortage_status_date_index IF NOT EXISTS
FOR (ds:DrugShortage) ON (ds.status, ds.start_date);

// 检查结果+日期复合索引
CREATE INDEX inspection_result_date_index IF NOT EXISTS
FOR (i:Inspection) ON (i.result, i.inspection_date);

// 不良事件严重程度+类型复合索引
CREATE INDEX ae_severity_type_index IF NOT EXISTS
FOR (ae:AdverseEvent) ON (ae.severity, ae.adverse_event_type);

//===========================================================
// 七、关系属性索引
//===========================================================

// IC50值索引（用于化合物-靶点关系）
CREATE INDEX relationship_ic50_index IF NOT EXISTS
FOR ()-[r:INHIBITS|ACTIVATES]->() ON (r.ic50);

// 关系强度索引
CREATE INDEX relationship_strength_index IF NOT EXISTS
FOR ()-[r]->() ON (r.strength);

// 关系证据级别索引
CREATE INDEX relationship_evidence_index IF NOT EXISTS
FOR ()-[r]->() ON (r.evidence_level);

// 关系时间戳索引
CREATE INDEX relationship_timestamp_index IF NOT EXISTS
FOR ()-[r]->() ON (r.created_at);

//===========================================================
// 八、全文搜索索引
//===========================================================

// 通用实体全文索引
CREATE FULLTEXT INDEX entity_general_fulltext IF NOT EXISTS
FOR (n:Compound) ON EACH [n.name, n.description]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: "standard"
  }
};

CREATE FULLTEXT INDEX entity_general_fulltext_2 IF NOT EXISTS
FOR (n:Target) ON EACH [n.name, n.description]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: "standard"
  }
};

CREATE FULLTEXT INDEX entity_general_fulltext_3 IF NOT EXISTS
FOR (n:Disease) ON EACH [n.name, n.description]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: "standard"
  }
};

//===========================================================
// 索引验证查询
//===========================================================

// 显示所有索引
SHOW INDEXES;

// 统计各类型索引数量
CALL db.indexes() YIELD name, labelsOrTypes, properties, state
RETURN
    labelsOrTypes AS entity_type,
    properties AS indexed_properties,
    state AS index_state,
    count(*) AS index_count
GROUP BY entity_type, indexed_properties, index_state
ORDER BY entity_type, index_count DESC;

// 检查索引使用情况
CALL db.indexes() YIELD name, labelsOrTypes, properties, state, populationPercent, uniqueness
WHERE state = 'ONLINE'
RETURN
    name AS index_name,
    labelsOrTypes AS entity_type,
    properties AS indexed_property,
    populationPercent AS population_percentage,
    uniqueness
ORDER BY populationPercentage DESC;
