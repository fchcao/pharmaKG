//===========================================================
// 制药行业知识图谱 - R&D 领域示例查询
// Pharmaceutical Knowledge Graph - R&D Domain Example Queries
//===========================================================
// 版本: v1.0
// 创建日期: 2025-02-06
// 描述: R&D领域常用Cypher查询示例
//===========================================================

//===========================================================
// 1. 基础查询
//===========================================================

// Q1.1: 查询所有化合物数量
MATCH (c:Compound)
RETURN count(c) AS total_compounds;

// Q1.2: 查询所有靶点数量
MATCH (t:Target)
RETURN count(t) AS total_targets;

// Q1.3: 查询指定开发阶段的化合物
MATCH (c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
WHERE ds.id = 'PCC'
RETURN c.primary_id, c.name, c.smiles, c.inchikey
ORDER BY c.name;

// Q1.4: 查询指定类型的靶点
MATCH (t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
WHERE tt.id = 'kinase'
RETURN t.primary_id, t.name, t.gene_symbol, t.uniprot_id
ORDER BY t.name;

//===========================================================
// 2. 化合物-靶点关系查询
//===========================================================

// Q2.1: 查询化合物的所有靶点
MATCH (c:Compound {primary_id: 'DB00312'})-[r:INHIBITS|ACTIVATES|BINDS_TO]->(t:Target)
RETURN c.name AS compound, type(r) AS relationship, t.name AS target, t.gene_symbol, r.ic50, r.ic50_unit
ORDER BY t.name;

// Q2.2: 查询靶点的所有调节化合物
MATCH (t:Target {primary_id: 'P00533'})<[r:INHIBITS|ACTIVATES|BINDS_TO]-(c:Compound)
RETURN t.name AS target, type(r) AS relationship, c.name AS compound, r.ic50, r.ic50_unit
ORDER BY r.ic50;

// Q2.3: 查询多靶点化合物（选择性较低）
MATCH (c:Compound)-[r:INHIBITS|ACTIVATES]->(t:Target)
WITH c, count(DISTINCT t) AS target_count
WHERE target_count > 1
MATCH (c)-[r:INHIBITS|ACTIVATES]->(t:Target)
RETURN c.name AS compound, target_count, collect(DISTINCT t.name) AS targets
ORDER BY target_count DESC;

// Q2.4: 查询高选择性化合物（单一靶点）
MATCH (c:Compound)-[r:INHIBITS|ACTIVATES]->(t:Target)
WITH c, count(DISTINCT t) AS target_count
WHERE target_count = 1
MATCH (c)-[r:INHIBITS]->(t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
RETURN c.name AS compound, t.name AS target, tt.name AS target_type, r.ic50, r.ic50_unit
ORDER BY r.ic50
LIMIT 50;

//===========================================================
// 3. 活性数据查询
//===========================================================

// Q3.1: 查询指定活性范围的化合物-靶点对
MATCH (c:Compound)-[r:INHIBITS]->(t:Target)
WHERE r.ic50 IS NOT NULL AND r.ic50 > 0 AND r.ic50 < 100
RETURN c.name AS compound, t.name AS target, t.gene_symbol, r.ic50, r.ic50_unit
ORDER BY r.ic50
LIMIT 100;

// Q3.2: 查询高活性化合物（IC50 < 10 nM）
MATCH (c:Compound)-[r:INHIBITS]->(t:Target)
WHERE r.ic50 < 10
RETURN c.name AS compound, c.smiles, t.name AS target, t.gene_symbol, r.ic50
ORDER BY r.ic50;

// Q3.3: 查询实验结果详情
MATCH (ar:AssayResult)-[:MEASURED_FOR_COMPOUND]->(c:Compound)
MATCH (ar)-[:DERIVED_FROM_ASSAY]->(a:Assay)
WHERE c.primary_id = 'DB01001'
RETURN c.name AS compound, a.name AS assay, ar.activity_value, ar.activity_unit,
       ar.measurement_type, ar.standard_deviation, ar.replicate_count
ORDER BY ar.activity_value;

// Q3.4: 查询高质量实验（Z-factor > 0.5）
MATCH (a:Assay)
WHERE a.z_factor > 0.5
RETURN a.assay_id, a.name, a.assay_type, a.z_factor
ORDER BY a.z_factor DESC;

//===========================================================
// 4. 通路分析查询
//===========================================================

// Q4.1: 查询指定通路的所有靶点
MATCH (p:Pathway {primary_id: 'hsa04012'})-[:INCLUDES_TARGET]->(t:Target)
RETURN p.name AS pathway, t.name AS target, t.gene_symbol, t.uniprot_id
ORDER BY t.name;

// Q4.2: 查询靶点参与的所有通路
MATCH (t:Target {primary_id: 'P00533'})-[:PARTICIPATES_IN]->(p:Pathway)
RETURN t.name AS target, collect(DISTINCT p.name) AS pathways, count(p) AS pathway_count
ORDER BY pathway_count DESC;

// Q4.3: 查询通路-疾病关联
MATCH (p:Pathway)-[:RELATED_TO_DISEASE]->(d:Disease)
RETURN p.name AS pathway, d.name AS disease, d.mondo_id
ORDER BY p.name, d.name;

// Q4.4: 查询两个通路的共同靶点（crosstalk分析）
MATCH (p1:Pathway {primary_id: 'hsa04012'})-[:INCLUDES_TARGET]->(t:Target)<-[:INCLUDES_TARGET]-(p2:Pathway {primary_id: 'hsa04010'})
RETURN p1.name AS pathway1, p2.name AS pathway2, collect(t.name) AS common_targets, count(t) AS target_count;

//===========================================================
// 5. 疾病关联查询
//===========================================================

// Q5.1: 查询疾病相关的所有靶点
MATCH (d:Disease {primary_id: 'MONDO:0001913'})-[:HAS_TARGET_ASSOCIATION]->(t:Target)
RETURN d.name AS disease, t.name AS target, t.gene_symbol, t.target_type
ORDER BY t.target_type, t.name;

// Q5.2: 查询靶点相关的所有疾病
MATCH (t:Target {primary_id: 'P00533'})<-[:HAS_TARGET_ASSOCIATION]-(d:Disease)
RETURN t.name AS target, collect(DISTINCT d.name) AS diseases, count(d) AS disease_count
ORDER BY disease_count DESC;

// Q5.3: 查询疾病相关的药物（已批准）
MATCH (d:Disease {primary_id: 'MONDO:0001913'})-[:HAS_TARGET_ASSOCIATION]->(t:Target)<-[r:INHIBITS]-(c:Compound)
WHERE c.is_approved_drug = true
RETURN d.name AS disease, c.name AS approved_drug, t.name AS target, r.ic50
ORDER BY c.name;

//===========================================================
// 6. SAR分析查询
//===========================================================

// Q6.1: 查询同一SAR系列的化合物
MATCH (c1:Compound)-[:HAS_SAR_DATA]->(sar:SARData)-[:HAS_SAR_SERIES]->(series:SARSeries)
MATCH (series)-[:HAS_SAR_SERIES]->(c2:Compound)
WHERE c1.primary_id = 'DB00312' AND c1.primary_id <> c2.primary_id
RETURN c1.name AS reference_compound, collect(DISTINCT c2.name) AS series_compounds;

// Q6.2: 查询具有相同母核结构的化合物
MATCH (c1:Compound)-[:HAS_SAR_DATA]->(sar:SARData)-[:HAS_SAR_SERIES]->(series:SARSeries)-[:HAS_SCAFFOLD]->(s:Scaffold)
MATCH (series)-[:HAS_SAR_SERIES]->(c2:Compound)
WHERE c1.primary_id = 'DB00312' AND c1.primary_id <> c2.primary_id
RETURN c1.name AS reference, s.name AS scaffold, collect(DISTINCT c2.name) AS same_scaffold_compounds;

// Q6.3: 比较类似化合物的活性
MATCH (c1:Compound)-[:IS_SIMILAR_TO]->(c2:Compound)
MATCH (c1)-[r1:INHIBITS]->(t:Target)<-[r2:INHIBITS]-(c2)
WHERE c1.primary_id = 'DB00312'
RETURN c1.name AS compound1, c2.name AS compound2, t.name AS target,
       r1.ic50 AS ic50_1, r2.ic50 AS ic50_2,
       (r2.ic50 / r1.ic50) AS activity_ratio
ORDER BY activity_ratio;

//===========================================================
// 7. 蛋白质相互作用查询
//===========================================================

// Q7.1: 查询蛋白质相互作用网络
MATCH (t1:Target)-[r:INTERACTS_WITH]->(t2:Target)
WHERE t1.primary_id = 'P00533'
RETURN t1.name AS protein1, t2.name AS protein2, t2.gene_symbol
ORDER BY t2.name;

// Q7.2: 查询蛋白复合物（相互作用的蛋白质群）
MATCH (t:Target)-[:INTERACTS_WITH]->(partner:Target)
WITH t, collect(partner.name) AS interaction_partners
WHERE size(interaction_partners) > 2
RETURN t.name AS hub_protein, interaction_partners, size(interaction_partners) AS interaction_count
ORDER BY interaction_count DESC
LIMIT 20;

//===========================================================
// 8. 开发阶段追踪
//===========================================================

// Q8.1: 查询开发进展最快的靶点（多个化合物在高级阶段）
MATCH (t:Target)<-[r:INHIBITS]-(c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
WHERE ds.order >= 5  // Phase 1或更高级别
WITH t, ds, count(DISTINCT c) AS compound_count
WHERE compound_count > 0
RETURN t.name AS target, t.target_type, ds.name AS highest_stage, compound_count
ORDER BY ds.order DESC, compound_count DESC;

// Q8.2: 查询从Hit到Lead的化合物演化路径
MATCH path = (c1:Compound)-[:HAS_DERIVATIVE*]->(c2:Compound)
WHERE c1.development_stage = 'hit' AND c2.development_stage = 'lead'
RETURN c1.name AS hit_compound, c2.name AS lead_compound, length(path) AS optimization_steps
ORDER BY length(path);

//===========================================================
// 9. 数据质量检查
//===========================================================

// Q9.1: 查找缺失SMILES的化合物
MATCH (c:Compound)
WHERE c.smiles IS NULL
RETURN c.primary_id, c.name, c.chembl_id, c.drugbank_id
LIMIT 100;

// Q9.2: 查找缺失InChIKey的化合物
MATCH (c:Compound)
WHERE c.inchikey IS NULL
RETURN count(c) AS compounds_without_inchikey;

// Q9.3: 查找缺失Uniprot ID的靶点
MATCH (t:Target)
WHERE t.uniprot_id IS NULL
RETURN t.primary_id, t.name, t.gene_symbol
LIMIT 100;

// Q9.4: 查找没有活性数据的化合物-靶点关系
MATCH (c:Compound)-[r:INHIBITS|ACTIVATES]->(t:Target)
WHERE r.ic50 IS NULL
RETURN c.name AS compound, t.name AS target, type(r) AS relationship_type
LIMIT 100;

//===========================================================
// 10. 统计分析
//===========================================================

// Q10.1: 靶点类型分布
MATCH (t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
RETURN tt.name AS target_type, count(DISTINCT t) AS target_count
ORDER BY target_count DESC;

// Q10.2: 开发阶段分布
MATCH (c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
RETURN ds.name AS stage, count(DISTINCT c) AS compound_count
ORDER BY ds.order;

// Q10.3: 实验类型分布
MATCH (a:Assay)-[:HAS_ASSAY_TYPE]->(at:AssayType)
RETURN at.name AS assay_type, count(DISTINCT a) AS assay_count
ORDER BY assay_count DESC;

// Q10.4: 通路类型分布
MATCH (p:Pathway)-[:HAS_PATHWAY_TYPE]->(pt:PathwayType)
RETURN pt.name AS pathway_type, count(DISTINCT p) AS pathway_count
ORDER BY pathway_count DESC;

//===========================================================
// 11. 高级分析查询
//===========================================================

// Q11.1: 多步路径查询 - 化合物->靶点->通路->疾病
MATCH path = (c:Compound)-[:INHIBITS]->(t:Target)-[:PARTICIPATES_IN]->(p:Pathway)-[:RELATED_TO_DISEASE]->(d:Disease)
WHERE c.primary_id = 'DB00312'
RETURN c.name AS compound, t.name AS target, p.name AS pathway, d.name AS disease;

// Q11.2: 查询"可成药"基因组的覆盖情况
MATCH (t:Target)-[:HAS_TARGET_TYPE]->(tt:TargetType)
WHERE tt.id IN ['kinase', 'gpcr', 'ion_channel', 'protease', 'nuclear_receptor']
MATCH (t)<-[r:INHIBITS|ACTIVATES]-(c:Compound)
WITH tt, count(DISTINCT t) AS total_targets, count(DISTINCT c) AS covered_compounds
RETURN tt.name AS target_class, total_targets, covered_compounds,
       (covered_compounds * 1.0 / total_targets) AS coverage_ratio
ORDER BY coverage_ratio DESC;

// Q11.3: 药物重定位机会 - 已批准药物在其他疾病中的作用
MATCH (c:Compound)-[:HAS_DEVELOPMENT_STAGE]->(ds:DevelopmentStage)
WHERE ds.id = 'approved'
MATCH (c)-[r:INHIBITS|ACTIVATES]->(t:Target)-[:PARTICIPATES_IN]->(p:Pathway)-[:RELATED_TO_DISEASE]->(d:Disease)
WHERE NOT (c)-[:TREATS]->(d)  // 假设有TREATS关系
RETURN c.name AS approved_drug, t.name AS target, p.name AS pathway,
       collect(DISTINCT d.name) AS potential_indications;

// Q11.4: Lipinski规则违例检查
MATCH (c:Compound)
WITH c,
     CASE WHEN c.molecular_weight > 500 THEN 1 ELSE 0 END AS mw_violation,
     CASE WHEN c.logp > 5 THEN 1 ELSE 0 END AS logp_violation,
     CASE WHEN c.hbond_donors > 5 THEN 1 ELSE 0 END AS hbd_violation,
     CASE WHEN c.hbond_acceptors > 10 THEN 1 ELSE 0 END AS hba_violation
WITH c, mw_violation + logp_violation + hbd_violation + hba_violation AS total_violations
RETURN c.name AS compound, c.molecular_weight, c.logp, c.hbond_donors, c.hbond_acceptors, total_violations
ORDER BY total_violations DESC, c.name
LIMIT 50;

//===========================================================
// 12. 数据导入辅助查询
//===========================================================

// Q12.1: 批量创建化合物的开发阶段关系
MATCH (c:Compound)
WHERE c.development_stage IS NOT NULL
MATCH (ds:DevelopmentStage {id: c.development_stage})
MERGE (c)-[:HAS_DEVELOPMENT_STAGE]->(ds);

// Q12.2: 批量创建靶点类型关系
MATCH (t:Target)
WHERE t.target_type IS NOT NULL
MATCH (tt:TargetType {id: t.target_type})
MERGE (t)-[:HAS_TARGET_TYPE]->(tt);

// Q12.3: 批量创建通路类型关系
MATCH (p:Pathway)
WHERE p.pathway_type IS NOT NULL
MATCH (pt:PathwayType {id: p.pathway_type})
MERGE (p)-[:HAS_PATHWAY_TYPE]->(pt);

//===========================================================
// 13. 性能优化查询
//===========================================================

// Q13.1: 使用索引提示的查询
MATCH (c:Compound)
USING INDEX c:Compound(primary_id)
WHERE c.primary_id = 'DB00312'
MATCH (c)-[r:INHIBITS]->(t:Target)
RETURN c.name, t.name, r.ic50;

// Q13.2: 批量查询优化 - 使用IN操作符
MATCH (c:Compound)
USING INDEX c:Compound(primary_id)
WHERE c.primary_id IN ['DB00312', 'DB01001', 'CHEMBL240']
MATCH (c)-[r:INHIBITS]->(t:Target)
RETURN c.primary_id, c.name, collect({target: t.name, ic50: r.ic50}) AS targets;

//===========================================================
// 查询示例结束
//===========================================================
