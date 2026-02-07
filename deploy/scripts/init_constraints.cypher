//===========================================================
// 制药行业知识图谱 - 初始化约束和索引
//===========================================================

// 创建唯一性约束
CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (c:Compound) REQUIRE c.primary_id IS UNIQUE;
CREATE CONSTRAINT target_id IF NOT EXISTS FOR (t:Target) REQUIRE t.primary_id IS UNIQUE;
CREATE CONSTRAINT trial_id IF NOT EXISTS FOR (ct:ClinicalTrial) REQUIRE ct.trial_id IS UNIQUE;
CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (s:Subject) REQUIRE s.subject_id IS UNIQUE;
CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.supplier_id IS UNIQUE;
CREATE CONSTRAINT submission_id IF NOT EXISTS FOR (rs:RegulatorySubmission) REQUIRE rs.submission_id IS UNIQUE;

// 创建节点存在性约束（用于关系）
CREATE CONSTRAINT compound_exists IF NOT EXISTS FOR () REQUIRE primary_id IS NODE KEY;

//===========================================================
// 创建索引 - R&D 领域
//===========================================================

// Compound 索引
CREATE INDEX compound_name IF NOT EXISTS FOR (c:Compound) ON (c.name);
CREATE INDEX compound_smiles IF NOT EXISTS FOR (c:Compound) ON (c.smiles);
CREATE INDEX compound_inchikey IF NOT EXISTS FOR (c:Compound) ON (c.inchikey);
CREATE INDEX compound_stage IF NOT EXISTS FOR (c:Compound) ON (c.development_stage);
CREATE INDEX compound_type IF NOT EXISTS FOR (c:Compound) ON (c.structure_type);
CREATE INDEX compound_area IF NOT EXISTS FOR (c:Compound) ON (c.therapeutic_area);

// Target 索引
CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name);
CREATE INDEX target_symbol IF NOT EXISTS FOR (t:Target) ON (t.gene_symbol);
CREATE INDEX target_function IF NOT EXISTS FOR (t:Target) ON (t.target_function);
CREATE INDEX target_druggability IF NOT EXISTS FOR (t:Target) ON (t.druggability_stage);

// Disease 索引
CREATE INDEX disease_name IF NOT EXISTS FOR (d:Disease) ON (d.name);
CREATE INDEX disease_mondo IF NOT EXISTS FOR (d:Disease) ON (d.mondo_id);

//===========================================================
// 创建索引 - 临床领域
//===========================================================

// ClinicalTrial 索引
CREATE INDEX trial_protocol IF NOT EXISTS FOR (ct:ClinicalTrial) ON (ct.protocol_id);
CREATE INDEX trial_phase IF NOT EXISTS FOR (ct:ClinicalTrial) ON (ct.trial_phase);
CREATE INDEX trial_status IF NOT EXISTS FOR (ct:ClinicalTrial) ON (ct.trial_status);
CREATE INDEX trial_start IF NOT EXISTS FOR (ct:ClinicalTrial) ON (ct.start_date);

// Subject 索引
CREATE INDEX subject_initials IF NOT EXISTS FOR (s:Subject) ON (s.initials);
CREATE INDEX subject_status IF NOT EXISTS FOR (s:Subject) ON (s.enrollment_status);
CREATE INDEX subject_arm IF NOT EXISTS FOR (s:Subject) ON (s.randomization_arm);

// InvestigationalSite 索引
CREATE INDEX site_name IF NOT EXISTS FOR (is:InvestigationalSite) ON (is.site_name);
CREATE INDEX site_tier IF NOT EXISTS FOR (is:InvestigationalSite) ON (is.site_tier);
CREATE INDEX site_country IF NOT EXISTS FOR (is:InvestigationalSite) ON (is.country);

// Endpoint 索引
CREATE INDEX endpoint_name IF NOT EXISTS FOR (e:Endpoint) ON (e.endpoint_name);
CREATE INDEX endpoint_type IF NOT EXISTS FOR (e:Endpoint) ON (e.endpoint_type);

//===========================================================
// 创建索引 - 供应链领域
//===========================================================

// Supplier 索引
CREATE INDEX supplier_name IF NOT EXISTS FOR (s:Supplier) ON (s.name);
CREATE INDEX supplier_tier IF NOT EXISTS FOR (s:Supplier) ON (s.performance_tier);
CREATE INDEX supplier_type IF NOT EXISTS FOR (s:Supplier) ON (s.supplier_type);

// Material 索引
CREATE INDEX material_name IF NOT EXISTS FOR (m:Material) ON (m.name);
CREATE INDEX material_cas IF NOT EXISTS FOR (m:Material) ON (m.cas_number);
CREATE INDEX material_type IF NOT EXISTS FOR (m:Material) ON (m.material_type);

// SupplyEvent 索引
CREATE INDEX event_date IF NOT EXISTS FOR (se:SupplyEvent) ON (se.start_date);
CREATE INDEX event_type IF NOT EXISTS FOR (se:SupplyEvent) ON (se.event_type);
CREATE INDEX event_severity IF NOT EXISTS FOR (se:SupplyEvent) ON (se.severity);

//===========================================================
// 创建索引 - 监管合规领域
//===========================================================

// RegulatorySubmission 索引
CREATE INDEX submission_number IF NOT EXISTS FOR (rs:RegulatorySubmission) ON (rs.submission_number);
CREATE INDEX submission_type IF NOT EXISTS FOR (rs:RegulatorySubmission) ON (rs.submission_type);
CREATE INDEX submission_status IF NOT EXISTS FOR (rs:RegulatorySubmission) ON (rs.submission_status);
CREATE INDEX submission_date IF NOT EXISTS FOR (rs:RegulatorySubmission) ON (rs.submission_date);

// SafetyEvent 索引
CREATE INDEX safety_date IF NOT EXISTS FOR (se:SafetyEvent) ON (se.event_date);
CREATE INDEX safety_type IF NOT EXISTS FOR (se:SafetyEvent) ON (se.event_type);
CREATE INDEX safety_seriousness IF NOT EXISTS FOR (se:SafetyEvent) ON (se.seriousness);

// RegulatoryAuthority 索引
CREATE INDEX authority_name IF NOT EXISTS FOR (ra:RegulatoryAuthority) ON (ra.name);
CREATE INDEX authority_region IF NOT EXISTS FOR (ra:RegulatoryAuthority) ON (ra.region);

//===========================================================
// 创建全文搜索索引
//===========================================================

// Compound 全文搜索
CALL db.index.fulltext.createNodeIndex(
  'compoundNames',
  ['Compound'],
  ['name', 'internal_id']
);

// Target 全文搜索
CALL db.index.fulltext.createNodeIndex(
  'targetNames',
  ['Target'],
  ['name', 'gene_symbol', 'protein_name']
);

// Disease 全文搜索
CALL db.index.fulltext.createNodeIndex(
  'diseaseNames',
  ['Disease'],
  ['name', 'synonyms']
);

// ClinicalTrial 全文搜索
CALL db.index.fulltext.createNodeIndex(
  'trialTitles',
  ['ClinicalTrial'],
  ['trial_name', 'protocol_id']
);

//===========================================================
// 显示创建的约束和索引
//===========================================================

SHOW CONSTRAINTS;
SHOW INDEXES;
