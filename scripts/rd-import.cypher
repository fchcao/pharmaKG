//===========================================================
// 制药行业知识图谱 - R&D 领域数据导入脚本
// Pharmaceutical Knowledge Graph - R&D Domain Data Import
//===========================================================
// 版本: v1.0
// 创建日期: 2025-02-06
// 描述: 导入R&D领域核心实体和关系到Neo4j
//===========================================================

// 使用 :auto 命令允许较大事务
:auto

//===========================================================
// 1. 创建唯一性约束和索引
//===========================================================

// Compound 约束
CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (c:Compound) REQUIRE c.primary_id IS UNIQUE;
CREATE INDEX compound_name IF NOT EXISTS FOR (c:Compound) ON (c.name);
CREATE INDEX compound_inchikey IF NOT EXISTS FOR (c:Compound) ON (c.inchikey);
CREATE INDEX compound_smiles IF NOT EXISTS FOR (c:Compound) ON (c.smiles);
CREATE INDEX compound_stage IF NOT EXISTS FOR (c:Compound) ON (c.development_stage);

// Target 约束
CREATE CONSTRAINT target_id IF NOT EXISTS FOR (t:Target) REQUIRE t.primary_id IS UNIQUE;
CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name);
CREATE INDEX target_uniprot IF NOT EXISTS FOR (t:Target) ON (t.uniprot_id);
CREATE INDEX target_gene_symbol IF NOT EXISTS FOR (t:Target) ON (t.gene_symbol);
CREATE INDEX target_type IF NOT EXISTS FOR (t:Target) ON (t.target_type);

// Assay 约束
CREATE CONSTRAINT assay_id IF NOT EXISTS FOR (a:Assay) REQUIRE a.assay_id IS UNIQUE;
CREATE INDEX assay_type IF NOT EXISTS FOR (a:Assay) ON (a.assay_type);
CREATE INDEX assay_format IF NOT EXISTS FOR (a:Assay) ON (a.assay_format);

// AssayResult 约束
CREATE CONSTRAINT result_id IF NOT EXISTS FOR (r:AssayResult) REQUIRE r.result_id IS UNIQUE;
CREATE INDEX result_activity IF NOT EXISTS FOR (r:AssayResult) ON (r.activity_value);

// Pathway 约束
CREATE CONSTRAINT pathway_id IF NOT EXISTS FOR (p:Pathway) REQUIRE p.primary_id IS UNIQUE;
CREATE INDEX pathway_name IF NOT EXISTS FOR (p:Pathway) ON (p.name);
CREATE INDEX pathway_kegg IF NOT EXISTS FOR (p:Pathway) ON (p.kegg_id);

// Disease 约束
CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.primary_id IS UNIQUE;
CREATE INDEX disease_name IF NOT EXISTS FOR (d:Disease) ON (d.name);
CREATE INDEX disease_mondo IF NOT EXISTS FOR (d:Disease) ON (d.mondo_id);

//===========================================================
// 2. 创建枚举节点 (结构类型、开发阶段等)
//===========================================================

// StructureType 枚举
MERGE (s1:StructureType {id: 'small_molecule', name: 'Small Molecule'})
MERGE (s2:StructureType {id: 'peptide', name: 'Peptide'})
MERGE (s3:StructureType {id: 'oligosaccharide', name: 'Oligosaccharide'})
MERGE (s4:StructureType {id: 'lipid', name: 'Lipid'})
MERGE (s5:StructureType {id: 'natural_product', name: 'Natural Product'});

// DevelopmentStage 枚举
MERGE (ds1:DevelopmentStage {id: 'hit', name: 'Hit', order: 1})
MERGE (ds2:DevelopmentStage {id: 'lead', name: 'Lead', order: 2})
MERGE (ds3:DevelopmentStage {id: 'PCC', name: 'PCC', order: 3})
MERGE (ds4:DevelopmentStage {id: 'IND', name: 'IND', order: 4})
MERGE (ds5:DevelopmentStage {id: 'phase_1', name: 'Phase 1', order: 5})
MERGE (ds6:DevelopmentStage {id: 'phase_2', name: 'Phase 2', order: 6})
MERGE (ds7:DevelopmentStage {id: 'phase_3', name: 'Phase 3', order: 7})
MERGE (ds8:DevelopmentStage {id: 'approved', name: 'Approved', order: 8})
MERGE (ds9:DevelopmentStage {id: 'withdrawn', name: 'Withdrawn', order: 9});

// TargetType 枚举
MERGE (tt1:TargetType {id: 'receptor', name: 'Receptor'})
MERGE (tt2:TargetType {id: 'enzyme', name: 'Enzyme'})
MERGE (tt3:TargetType {id: 'ion_channel', name: 'Ion Channel'})
MERGE (tt4:TargetType {id: 'transporter', name: 'Transporter'})
MERGE (tt5:TargetType {id: 'nuclear_receptor', name: 'Nuclear Receptor'})
MERGE (tt6:TargetType {id: 'gpcr', name: 'GPCR'})
MERGE (tt7:TargetType {id: 'kinase', name: 'Kinase'})
MERGE (tt8:TargetType {id: 'protease', name: 'Protease'})
MERGE (tt9:TargetType {id: 'transcription_factor', name: 'Transcription Factor'})
MERGE (tt10:TargetType {id: 'epigenetic_target', name: 'Epigenetic Target'});

// AssayType 枚举
MERGE (at1:AssayType {id: 'binding', name: 'Binding Assay'})
MERGE (at2:AssayType {id: 'functional', name: 'Functional Assay'})
MERGE (at3:AssayType {id: 'cell_based', name: 'Cell-based Assay'})
MERGE (at4:AssayType {id: 'biochemical', name: 'Biochemical Assay'})
MERGE (at5:AssayType {id: 'phenotypic', name: 'Phenotypic Assay'})
MERGE (at6:AssayType {id: 'adme', name: 'ADME Assay'});

// AssayFormat 枚举
MERGE (af1:AssayFormat {id: '96_well', name: '96-well plate'})
MERGE (af2:AssayFormat {id: '384_well', name: '384-well plate'})
MERGE (af3:AssayFormat {id: '1536_well', name: '1536-well plate'})
MERGE (af4:AssayFormat {id: 'microfluidic', name: 'Microfluidic'});

// ReadoutType 枚举
MERGE (rt1:ReadoutType {id: 'ic50', name: 'IC50', unit: 'nM'})
MERGE (rt2:ReadoutType {id: 'ec50', name: 'EC50', unit: 'nM'})
MERGE (rt3:ReadoutType {id: 'ki', name: 'Ki', unit: 'nM'})
MERGE (rt4:ReadoutType {id: 'kd', name: 'Kd', unit: 'nM'})
MERGE (rt5:ReadoutType {id: 'percent_inhibition', name: 'Percent Inhibition', unit: '%'})
MERGE (rt6:ReadoutType {id: 'percent_activation', name: 'Percent Activation', unit: '%'});

// PathwayType 枚举
MERGE (pt1:PathwayType {id: 'metabolic', name: 'Metabolic Pathway'})
MERGE (pt2:PathwayType {id: 'signaling', name: 'Signaling Pathway'})
MERGE (pt3:PathwayType {id: 'gene_regulation', name: 'Gene Regulation Pathway'})
MERGE (pt4:PathwayType {id: 'transcriptional', name: 'Transcriptional Pathway'})
MERGE (pt5:PathwayType {id: 'disease', name: 'Disease Pathway'})
MERGE (pt6:PathwayType {id: 'drug_action', name: 'Drug Action Pathway'});

//===========================================================
// 3. 示例数据导入 - Compound
//===========================================================

// 创建示例化合物节点
UNWIND [
    {primary_id: 'DB00312', name: 'Imatinib', smiles: 'CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC(=O)C4=CC(=C(C=C4)Cl)F', inchikey: 'CJNQAVVKURQDAF-UHFFFAOYSA-N', molecular_weight: 493.6, logp: 3.5, hbond_donors: 2, hbond_acceptors: 6, rotatable_bonds: 7, pubchem_cid: '5291', chembl_id: 'CHEMBL941', drugbank_id: 'DB00312', development_stage: 'approved'},
    {primary_id: 'DB01001', name: 'Gefitinib', smiles: 'COc1ccc2nc(Nc3ccc(F)cc3)nc(Nc3ccccc3)c2c1', inchikey: 'YCUJQIIQRUNJFU-UHFFFAOYSA-N', molecular_weight: 446.9, logp: 4.2, hbond_donors: 2, hbond_acceptors: 5, rotatable_bonds: 5, pubchem_cid: '123631', chembl_id: 'CHEMBL999', drugbank_id: 'DB01001', development_stage: 'approved'},
    {primary_id: 'CHEMBL240', name: 'Staurosporine', smiles: 'COc1ccc2nc(Nc3ccc(F)cc3)nc(Nc3ccccc3)c2c1', inchikey: 'CQXLGKRZFCNMEL-UHFFFAOYSA-N', molecular_weight: 466.5, logp: 3.8, hbond_donors: 2, hbond_acceptors: 7, rotatable_bonds: 4, pubchem_cid: '444591', chembl_id: 'CHEMBL240', development_stage: 'PCC'}
] AS row
MERGE (c:Compound {primary_id: row.primary_id})
SET c.name = row.name,
    c.smiles = row.smiles,
    c.inchikey = row.inchikey,
    c.molecular_weight = row.molecular_weight,
    c.logp = row.logp,
    c.hbond_donors = row.hbond_donors,
    c.hbond_acceptors = row.hbond_acceptors,
    c.rotatable_bonds = row.rotatable_bonds,
    c.pubchem_cid = row.pubchem_cid,
    c.chembl_id = row.chembl_id,
    c.drugbank_id = row.drugbank_id,
    c.is_approved_drug = row.development_stage = 'approved',
    c.created_at = datetime();

// 关联化合物到开发阶段
MATCH (c:Compound), (ds:DevelopmentStage)
WHERE c.development_stage = ds.id
MERGE (c)-[:HAS_DEVELOPMENT_STAGE]->(ds);

//===========================================================
// 4. 示例数据导入 - Target
//===========================================================

// 创建示例靶点节点
UNWIND [
    {primary_id: 'P00533', name: 'EGFR', gene_symbol: 'EGFR', gene_name: 'Epidermal Growth Factor Receptor', uniprot_id: 'P00533', entrez_id: '1956', ensembl_id: 'ENSG00000146648', target_type: 'receptor', organism: 'Homo sapiens'},
    {primary_id: 'P24941', name: 'c-KIT', gene_symbol: 'KIT', gene_name: 'Mast/stem cell growth factor receptor', uniprot_id: 'P24941', entrez_id: '3815', ensembl_id: 'ENSG00000157404', target_type: 'receptor', organism: 'Homo sapiens'},
    {primary_id: 'P04637', name: 'p53', gene_symbol: 'TP53', gene_name: 'Tumor protein p53', uniprot_id: 'P04637', entrez_id: '7157', ensembl_id: 'ENSG00000141510', target_type: 'transcription_factor', organism: 'Homo sapiens'},
    {primary_id: 'Q9Y6K9', name: 'ABL1', gene_symbol: 'ABL1', gene_name: 'Tyrosine-protein kinase ABL1', uniprot_id: 'P00519', entrez_id: '25', ensembl_id: 'ENSG00000095007', target_type: 'kinase', organism: 'Homo sapiens'}
] AS row
MERGE (t:Target {primary_id: row.primary_id})
SET t.name = row.name,
    t.gene_symbol = row.gene_symbol,
    t.gene_name = row.gene_name,
    t.uniprot_id = row.uniprot_id,
    t.entrez_id = row.entrez_id,
    t.ensembl_id = row.ensembl_id,
    t.target_type = row.target_type,
    t.organism = row.organism,
    t.created_at = datetime();

// 关联靶点到类型
MATCH (t:Target), (tt:TargetType)
WHERE t.target_type = tt.id
MERGE (t)-[:HAS_TARGET_TYPE]->(tt);

//===========================================================
// 5. 示例数据导入 - Pathway
//===========================================================

// 创建示例通路节点
UNWIND [
    {primary_id: 'hsa04012', name: 'ErbB signaling pathway', kegg_id: 'hsa04012', pathway_type: 'signaling', organism: 'Homo sapiens'},
    {primary_id: 'hsa04010', name: 'MAPK signaling pathway', kegg_id: 'hsa04010', pathway_type: 'signaling', organism: 'Homo sapiens'},
    {primary_id: 'hsa05200', name: 'Pathways in cancer', kegg_id: 'hsa05200', pathway_type: 'disease', organism: 'Homo sapiens'},
    {primary_id: 'R-HSA-177929', name: 'Signaling by EGFR', reactome_id: 'R-HSA-177929', pathway_type: 'signaling', organism: 'Homo sapiens'}
] AS row
MERGE (p:Pathway {primary_id: row.primary_id})
SET p.name = row.name,
    p.kegg_id = row.kegg_id,
    p.reactome_id = row.reactome_id,
    p.organism = row.organism,
    p.created_at = datetime();

// 关联通路到类型
MATCH (p:Pathway), (pt:PathwayType)
WHERE p.pathway_type = pt.id
MERGE (p)-[:HAS_PATHWAY_TYPE]->(pt);

// 通路-靶点关联
MATCH (p:Pathway {primary_id: 'hsa04012'}), (t:Target {uniprot_id: 'P00533'})
MERGE (p)-[:INCLUDES_TARGET]->(t);

MATCH (p:Pathway {primary_id: 'R-HSA-177929'}), (t:Target {uniprot_id: 'P00533'})
MERGE (p)-[:INCLUDES_TARGET]->(t);

//===========================================================
// 6. 示例数据导入 - Disease
//===========================================================

// 创建示例疾病节点
UNWIND [
    {primary_id: 'MONDO:0001913', name: 'Lung cancer', mondo_id: 'MONDO:0001913', doid: 'DOID:1324', icd10_code: 'C78'},
    {primary_id: 'MONDO:0007254', name: 'Chronic myeloid leukemia', mondo_id: 'MONDO:0007254', doid: 'DOID:8876', icd10_code: 'C92'},
    {primary_id: 'MONDO:0002025', name: 'Glioma', mondo_id: 'MONDO:0002025', doid: 'DOID:2065', icd10_code: 'C71'}
] AS row
MERGE (d:Disease {primary_id: row.primary_id})
SET d.name = row.name,
    d.mondo_id = row.mondo_id,
    d.doid = row.doid,
    d.icd10_code = row.icd10_code,
    d.created_at = datetime();

//===========================================================
// 7. 化合物-靶点关系 (INHIBITS)
//===========================================================

UNWIND [
    {compound: 'DB00312', target: 'Q9Y6K9', activity_type: 'INHIBITS', ic50: 0.2, ic50_unit: 'nM'},
    {compound: 'DB01001', target: 'P00533', activity_type: 'INHIBITS', ic50: 33, ic50_unit: 'nM'}
] AS row
MATCH (c:Compound {primary_id: row.compound})
MATCH (t:Target {primary_id: row.target})
MERGE (c)-[r:INHIBITS]->(t)
SET r.ic50 = row.ic50,
    r.ic50_unit = row.ic50_unit,
    r.activity_type = row.activity_type,
    r.created_at = datetime();

//===========================================================
// 8. 示例数据导入 - Assay
//===========================================================

// 创建示例实验节点
UNWIND [
    {assay_id: 'ASSAY001', name: 'EGFR Kinase Inhibition Assay', assay_type: 'biochemical', assay_format: '384_well', detection_method: 'fluorescence', cell_line: null, organism: 'Homo sapiens'},
    {assay_id: 'ASSAY002', name: 'Cell Proliferation Assay', assay_type: 'cell_based', assay_format: '96_well', detection_method: 'luminescence', cell_line: 'A549', organism: 'Homo sapiens'}
] AS row
MERGE (a:Assay {assay_id: row.assay_id})
SET a.name = row.name,
    a.assay_type = row.assay_type,
    a.assay_format = row.assay_format,
    a.detection_method = row.detection_method,
    a.cell_line = row.cell_line,
    a.organism = row.organism,
    a.created_at = datetime();

// 关联实验到类型和形式
MATCH (a:Assay), (at:AssayType)
WHERE a.assay_type = at.id
MERGE (a)-[:HAS_ASSAY_TYPE]->(at);

MATCH (a:Assay), (af:AssayFormat)
WHERE a.assay_format = af.id
MERGE (a)-[:HAS_ASSAY_FORMAT]->(af);

// 实验-靶点关联
MATCH (a:Assay {assay_id: 'ASSAY001'}), (t:Target {uniprot_id: 'P00533'})
MERGE (a)-[:MEASURES]->(t);

//===========================================================
// 9. 示例数据导入 - AssayResult
//===========================================================

// 创建示例实验结果节点
UNWIND [
    {result_id: 'RESULT001', assay: 'ASSAY001', compound: 'DB01001', activity_value: 33, activity_unit: 'nM', measurement_type: 'ic50', confidence_interval: '28-38', standard_deviation: 5.2, replicate_count: 3},
    {result_id: 'RESULT002', assay: 'ASSAY002', compound: 'DB00312', activity_value: 15, activity_unit: '%', measurement_type: 'percent_inhibition', confidence_interval: '12-18', standard_deviation: 2.1, replicate_count: 3}
] AS row
MATCH (a:Assay {assay_id: row.assay})
MATCH (c:Compound {primary_id: row.compound})
MERGE (r:AssayResult {result_id: row.result_id})
SET r.activity_value = row.activity_value,
    r.activity_unit = row.activity_unit,
    r.measurement_type = row.measurement_type,
    r.confidence_interval = row.confidence_interval,
    r.standard_deviation = row.standard_deviation,
    r.replicate_count = row.replicate_count,
    r.created_at = datetime()
MERGE (a)-[:PRODUCES_RESULT]->(r)
MERGE (r)-[:MEASURED_FOR_COMPOUND]->(c);

//===========================================================
// 10. 创建虚拟关系
//===========================================================

// 靶点-通路关系 (participates_in)
MATCH (t:Target {uniprot_id: 'P00533'})
MATCH (p:Pathway {primary_id: 'hsa04012'})
MERGE (t)-[:PARTICIPATES_IN]->(p);

// 疾病-靶点关联
MATCH (d:Disease {primary_id: 'MONDO:0001913'})
MATCH (t:Target {uniprot_id: 'P00533'})
MERGE (d)-[:HAS_TARGET_ASSOCIATION]->(t);

//===========================================================
// 11. 验证导入
//===========================================================

// 统计各类节点数量
MATCH (c:Compound) RETURN 'Compound' as type, count(c) as count
UNION ALL
MATCH (t:Target) RETURN 'Target' as type, count(t) as count
UNION ALL
MATCH (a:Assay) RETURN 'Assay' as type, count(a) as count
UNION ALL
MATCH (p:Pathway) RETURN 'Pathway' as type, count(p) as count
UNION ALL
MATCH (d:Disease) RETURN 'Disease' as type, count(d) as count;

// 显示关系统计
MATCH ()-[r]->() RETURN type(r) as relationship_type, count(r) as count ORDER BY count DESC;

//===========================================================
// 脚本结束
//===========================================================
