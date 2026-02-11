#===========================================================
# PharmaKG API - 高级多跳关联查询服务
# Pharmaceutical Knowledge Graph - Advanced Multi-hop Query Service
#===========================================================
# 版本: v1.0
# 描述: 实现多跳关联查询，包括药物重定位、竞争分析、
#       安全性传播、供应链影响等复杂查询
#===========================================================

from typing import List, Dict, Optional, Any
from datetime import datetime
from ..database import Neo4jConnection


class AdvancedQueryService:
    """高级多跳关联查询服务"""

    def __init__(self):
        """初始化数据库连接"""
        self.db = Neo4jConnection()

    #===========================================================
    # 一、药物重定位查询 (Drug Repurposing Queries)
    #===========================================================

    def get_compound_repurposing_opportunities(
        self,
        compound_id: str,
        min_evidence_level: str = "C",
        limit: int = 50
    ) -> List[dict]:
        """
        获取化合物的药物重定位机会

        查询路径: Compound → INHIBITS → Target → ASSOCIATED_WITH_DISEASE → Disease
        逻辑: 找出化合物抑制的靶点相关的疾病，但化合物尚未明确治疗这些疾病

        Args:
            compound_id: 化合物ID
            min_evidence_level: 最低证据级别 (A, B, C, D)
            limit: 返回结果数量限制

        Returns:
            潜在可治疗疾病列表
        """
        query = """
        MATCH (c:Compound {primary_id: $compound_id})-[r1:INHIBITS|ACTIVATES|MODULATES]->(t:Target)
        MATCH (t)-[r2:ASSOCIATED_WITH_DISEASE|CAUSES_DISEASE|BIOMARKER_FOR]->(d:Disease)
        WHERE NOT EXISTS {
            MATCH (c)-[:TREATS|PREVENTS]->(d)
        }
        WITH c, t, d, r1, r2,
             CASE r2.evidence_level
                 WHEN 'A' THEN 4
                 WHEN 'B' THEN 3
                 WHEN 'C' THEN 2
                 WHEN 'D' THEN 1
                 ELSE 0
             END AS evidence_score
        WHERE evidence_score >= $min_score
        RETURN DISTINCT
            d.primary_id AS disease_id,
            d.name AS disease_name,
            d.disease_class AS disease_class,
            t.primary_id AS target_id,
            t.name AS target_name,
            r1.strength AS interaction_strength,
            type(r1) AS mechanism_of_action,
            r2.evidence_level AS target_disease_evidence,
            evidence_score,
            CASE
                WHEN r2.evidence_level = 'A' THEN 'strong'
                WHEN r2.evidence_level = 'B' THEN 'moderate'
                WHEN r2.evidence_level = 'C' THEN 'weak'
                ELSE 'theoretical'
            END AS confidence_level
        ORDER BY evidence_score DESC, interaction_strength DESC
        LIMIT $limit
        """

        evidence_scores = {"A": 4, "B": 3, "C": 2, "D": 1}

        result = self.db.execute_query(
            query,
            {
                "compound_id": compound_id,
                "min_score": evidence_scores.get(min_evidence_level, 1),
                "limit": limit
            }
        )

        return result.records if result.success else []

    def get_disease_potential_compounds(
        self,
        disease_id: str,
        mechanism: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        获取疾病潜在的治疗化合物（药物重定位反向查询）

        查询路径: Disease ← ASSOCIATED_WITH_DISEASE ← Target ← INHIBITS ← Compound
        逻辑: 找出与疾病相关靶点作用的化合物

        Args:
            disease_id: 疾病ID
            mechanism: 作用机制筛选 (INHIBITS, ACTIVATES, MODULATES)
            limit: 返回结果数量限制

        Returns:
            潜在治疗化合物列表
        """
        mechanism_filter = ""
        params = {"disease_id": disease_id, "limit": limit}

        if mechanism:
            mechanism_filter = "AND type(r1) = $mechanism"
            params["mechanism"] = mechanism

        query = f"""
        MATCH (d:Disease {{primary_id: $disease_id}})<-[r2:ASSOCIATED_WITH_DISEASE|CAUSES_DISEASE|BIOMARKER_FOR]-(t:Target)
        MATCH (t)<-[r1:INHIBITS|ACTIVATES|MODULATES]-(c:Compound)
        WHERE NOT EXISTS {{
            MATCH (c)-[:TREATS|PREVENTS]->(d)
        }}
        {mechanism_filter}
        RETURN DISTINCT
            c.primary_id AS compound_id,
            c.name AS compound_name,
            c.smiles AS smiles,
            t.primary_id AS target_id,
            t.name AS target_name,
            type(r1) AS mechanism_of_action,
            r1.ic50 AS ic50_nm,
            r1.ki AS ki_nm,
            r2.evidence_level AS target_disease_evidence,
            CASE
                WHEN r1.ic50 IS NOT NULL AND r1.ic50 < 100 THEN 'potent'
                WHEN r1.ic50 IS NOT NULL AND r1.ic50 < 1000 THEN 'moderate'
                WHEN r1.ic50 IS NOT NULL THEN 'weak'
                ELSE 'unknown'
            END AS potency_category
        ORDER BY target_disease_evidence, potency_category
        LIMIT $limit
        """

        result = self.db.execute_query(query, params)
        return result.records if result.success else []

    def get_compound_combination_therapy_opportunities(
        self,
        compound_id: str,
        limit: int = 30
    ) -> List[dict]:
        """
        获取化合物的联合治疗机会

        查询逻辑: 找出作用于同一通路的其他化合物，可能具有协同作用

        Args:
            compound_id: 化合物ID
            limit: 返回结果数量限制

        Returns:
            潜在联合治疗化合物列表
        """
        query = """
        MATCH (c1:Compound {primary_id: $compound_id})-[r1:INHIBITS|ACTIVATES]->(t:Target)
        MATCH (t)<-[r2:INHIBITS|ACTIVATES]-(c2:Compound)
        WHERE c1 <> c2
        WITH c1, c2, t, r1, r2
        MATCH (t)-[r3:PARTICIPATES_IN|REGULATES_PATHWAY]->(p:Pathway)
        RETURN DISTINCT
            c2.primary_id AS combination_compound_id,
            c2.name AS combination_compound_name,
            collect(DISTINCT {
                target_id: t.primary_id,
                target_name: t.name,
                compound1_mechanism: type(r1),
                compound2_mechanism: type(r2),
                pathway: p.name
            }) AS shared_targets,
            count(DISTINCT t) AS shared_target_count,
            CASE
                WHEN count(DISTINCT t) >= 3 THEN 'high_synergy_potential'
                WHEN count(DISTINCT t) >= 2 THEN 'moderate_synergy_potential'
                ELSE 'low_synergy_potential'
            END AS synergy_potential
        ORDER BY shared_target_count DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, {"compound_id": compound_id, "limit": limit})
        return result.records if result.success else []

    #===========================================================
    # 二、竞争分析查询 (Competitive Landscape Queries)
    #===========================================================

    def get_target_competitive_landscape(
        self,
        target_id: str,
        include_pipeline_status: bool = True,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取靶点的竞争格局分析

        查询路径: Target ← compounds → Company → Pipeline_Status
        逻辑: 分析所有作用于该靶点的化合物及其研发状态

        Args:
            target_id: 靶点ID
            include_pipeline_status: 是否包含研发管线状态
            limit: 返回结果数量限制

        Returns:
            竞争格局分析结果
        """
        query = """
        MATCH (t:Target {primary_id: $target_id})
        OPTIONAL MATCH (t)<-[r:INHIBITS|ACTIVATES|MODULATES|BINDS_TO]-(c:Compound)
        OPTIONAL MATCH (c)-[:DEVELOPED_BY]->(company:Company)
        OPTIONAL MATCH (c)-[:HAS_PIPELINE_STATUS]->(status:PipelineStatus)
        RETURN {
            target_id: t.primary_id,
            target_name: t.name,
            target_class: t.target_class,
            total_compounds: count(DISTINCT c),
            mechanism_distribution: {
                inhibitors: count(DISTINCT CASE WHEN type(r) = 'INHIBITS' THEN c END),
                activators: count(DISTINCT CASE WHEN type(r) = 'ACTIVATES' THEN c END),
                modulators: count(DISTINCT CASE WHEN type(r) = 'MODULATES' THEN c END),
                binders: count(DISTINCT CASE WHEN type(r) = 'BINDS_TO' THEN c END)
            },
            pipeline_status: CASE $include_status
                WHEN true THEN
                    collect(DISTINCT {
                        compound_id: c.primary_id,
                        compound_name: c.name,
                        mechanism: type(r),
                        ic50: r.ic50,
                        company: company.name,
                        pipeline_stage: status.stage,
                        phase: status.phase,
                        status_date: status.status_date
                    })
                ELSE []
            END
        } AS landscape
        """

        result = self.db.execute_query(
            query,
            {
                "target_id": target_id,
                "include_status": include_pipeline_status
            }
        )

        if result.success and result.records:
            return result.records[0]
        return {}

    def get_disease_competitive_landscape(
        self,
        disease_id: str,
        limit: int = 100
    ) -> List[dict]:
        """
        获取疾病的竞争格局分析

        查询逻辑: 分析治疗该疾病的所有化合物及所在公司

        Args:
            disease_id: 疾病ID
            limit: 返回结果数量限制

        Returns:
            疾病治疗竞争格局
        """
        query = """
        MATCH (d:Disease {primary_id: $disease_id})
        MATCH (d)<-[r1:TREATS|PREVENTS]-(c:Compound)
        OPTIONAL MATCH (c)-[:DEVELOPED_BY]->(company:Company)
        OPTIONAL MATCH (c)-[r2:INHIBITS|ACTIVATES]->(t:Target)
        RETURN DISTINCT
            c.primary_id AS compound_id,
            c.name AS compound_name,
            company.name AS developer,
            r1.approval_status AS approval_status,
            r1.indication AS indication,
            collect(DISTINCT {
                target_id: t.primary_id,
                target_name: t.name,
                mechanism: type(r2)
            }) AS targets,
            count(DISTINCT t) AS target_count
        ORDER BY
            CASE r1.approval_status
                WHEN 'approved' THEN 1
                WHEN 'in_review' THEN 2
                WHEN 'clinical_trial' THEN 3
                ELSE 4
            END,
            target_count DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, {"disease_id": disease_id, "limit": limit})
        return result.records if result.success else []

    def get_company_pipeline_analysis(
        self,
        company_name: Optional[str] = None,
        therapeutic_area: Optional[str] = None
    ) -> List[dict]:
        """
        获取公司研发管线分析

        Args:
            company_name: 公司名称筛选
            therapeutic_area: 治疗领域筛选

        Returns:
            公司研发管线分析
        """
        company_filter = ""
        params = {}

        if company_name:
            company_filter = "WHERE company.name = $company_name"
            params["company_name"] = company_name

        if therapeutic_area:
            if company_filter:
                company_filter += " AND d.therapeutic_area = $therapeutic_area"
            else:
                company_filter = "WHERE d.therapeutic_area = $therapeutic_area"
            params["therapeutic_area"] = therapeutic_area

        query = f"""
        MATCH (company:Company)<-[:DEVELOPED_BY]-(c:Compound)
        OPTIONAL MATCH (c)-[:TREATS|PREVENTS]->(d:Disease)
        OPTIONAL MATCH (c)-[:HAS_PIPELINE_STATUS]->(status:PipelineStatus)
        {company_filter}
        RETURN
            company.name AS company_name,
            count(DISTINCT c) AS total_compounds,
            count(DISTINCT CASE WHEN status.stage = 'approved' THEN c END) AS approved_count,
            count(DISTINCT CASE WHEN status.stage = 'phase_3' THEN c END) AS phase_3_count,
            count(DISTINCT CASE WHEN status.stage = 'phase_2' THEN c END) AS phase_2_count,
            count(DISTINCT CASE WHEN status.stage = 'phase_1' THEN c END) AS phase_1_count,
            count(DISTINCT CASE WHEN status.stage = 'preclinical' THEN c END) AS preclinical_count,
            collect(DISTINCT d.therapeutic_area) AS therapeutic_areas
        ORDER BY total_compounds DESC
        """

        result = self.db.execute_query(query, params)
        return result.records if result.success else []

    #===========================================================
    # 三、安全性信号传播查询 (Safety Signal Propagation)
    #===========================================================

    def get_compound_safety_profile(
        self,
        compound_id: str,
        include_preclinical: bool = True
    ) -> Dict[str, Any]:
        """
        获取化合物的安全性全景视图

        查询路径: Compound → clinical_trials → adverse_events
                 → regulatory:SafetySignal → ComplianceAction

        Args:
            compound_id: 化合物ID
            include_preclinical: 是否包含毒理学数据

        Returns:
            安全性全景视图
        """
        query = """
        MATCH (c:Compound {primary_id: $compound_id})
        OPTIONAL MATCH (c)-[:TESTED_IN_CLINICAL_TRIAL]->(t:ClinicalTrial)
        OPTIONAL MATCH (t)-[:REPORTED_ADVERSE_EVENT]->(ae:AdverseEvent)
        OPTIONAL MATCH (c)-[:HAS_SAFETY_SIGNAL]->(ss:SafetySignal)
        OPTIONAL MATCH (c)-[:SUBJECT_TO_RECALL|WARNED_ABOUT]->(ca:ComplianceAction)
        OPTIONAL MATCH (c)-[:HAS_TOXICITY_DATA]->(tox:ToxicityData)
        RETURN {
            compound_id: c.primary_id,
            compound_name: c.name,
            clinical_safety: {
                total_trials: count(DISTINCT t),
                trials_with_ae: count(DISTINCT CASE WHEN ae IS NOT NULL THEN t END),
                total_adverse_events: count(DISTINCT ae),
                serious_adverse_events: count(DISTINCT CASE WHEN ae.severity = 'serious' THEN ae END),
                common_adverse_events: [
                    {
                        event_name: ae.preferred_term,
                        frequency: count(DISTINCT ae)
                    }
                    | ae WHERE ae IS NOT NULL
                    | ORDER BY count(DISTINCT ae) DESC
                    | LIMIT 10
                ]
            },
            regulatory_safety: {
                active_safety_signals: count(DISTINCT CASE WHEN ss.status = 'active' THEN ss END),
                confirmed_risks: count(DISTINCT CASE WHEN ss.status = 'confirmed' THEN ss END),
                compliance_actions: count(DISTINCT ca),
                action_types: collect(DISTINCT ca.action_type)
            },
            preclinical_toxicity: CASE $include_preclinical
                WHEN true THEN {
                    has_toxicity_data: count(DISTINCT tox) > 0,
                    toxicity_findings: collect(DISTINCT {
                        species: tox.species,
                        toxicity_type: tox.toxicity_type,
                        severity: tox.severity
                    })
                }
                ELSE null
            END
        } AS safety_profile
        """

        result = self.db.execute_query(
            query,
            {"compound_id": compound_id, "include_preclinical": include_preclinical}
        )

        if result.success and result.records:
            return result.records[0]
        return {}

    def get_safety_signal_propagation(
        self,
        compound_id: str,
        max_hops: int = 3
    ) -> List[dict]:
        """
        获取安全性信号传播路径

        查询逻辑: 找出化合物相关的所有安全性问题及其关联

        Args:
            compound_id: 化合物ID
            max_hops: 最大跳数

        Returns:
            安全性信号传播路径
        """
        query = """
        MATCH path = (c:Compound {primary_id: $compound_id})-[:TESTED_IN_CLINICAL_TRIAL|HAS_SAFETY_SIGNAL|CAUSES_ADVERSE_EVENT*1..3]-(related)
        WHERE related:AdverseEvent OR related:SafetySignal OR related:ComplianceAction
        WITH path,
             [node IN nodes(path) |
              CASE node
                WHEN node:ClinicalTrial THEN {type: 'trial', id: node.trial_id, name: node.title}
                WHEN node:AdverseEvent THEN {type: 'adverse_event', id: node.ae_id, name: node.preferred_term, severity: node.severity}
                WHEN node:SafetySignal THEN {type: 'safety_signal', id: node.signal_id, status: node.status}
                WHEN node:ComplianceAction THEN {type: 'compliance_action', id: node.action_id, action_type: node.action_type}
                WHEN node:Compound THEN {type: 'compound', id: node.primary_id, name: node.name}
              END
             ] AS path_nodes
        RETURN
            path_nodes,
            [rel IN relationships(path) | type(rel)] AS relationship_types,
            length(path) AS path_length
        ORDER BY path_length
        """

        result = self.db.execute_query(query, {"compound_id": compound_id})
        return result.records if result.success else []

    def get_target_safety_association(
        self,
        target_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        获取靶点相关的安全性问题

        查询逻辑: 找出作用于该靶点的化合物及其安全性问题

        Args:
            target_id: 靶点ID
            limit: 返回结果数量限制

        Returns:
            靶点安全性关联
        """
        query = """
        MATCH (t:Target {primary_id: $target_id})<-[r:INHIBITS|ACTIVATES]-(c:Compound)
        OPTIONAL MATCH (c)-[:TESTED_IN_CLINICAL_TRIAL]->(trial:ClinicalTrial)
        OPTIONAL MATCH (trial)-[:REPORTED_ADVERSE_EVENT]->(ae:AdverseEvent)
        OPTIONAL MATCH (c)-[:HAS_SAFETY_SIGNAL]->(ss:SafetySignal)
        RETURN DISTINCT
            c.primary_id AS compound_id,
            c.name AS compound_name,
            type(r) AS mechanism,
            count(DISTINCT trial) AS trial_count,
            count(DISTINCT ae) AS adverse_event_count,
            count(DISTINCT CASE WHEN ae.severity = 'serious' THEN ae END) AS serious_ae_count,
            count(DISTINCT ss) AS safety_signal_count,
            collect(DISTINCT {
                signal_id: ss.signal_id,
                status: ss.status,
                description: ss.description
            }) AS safety_signals
        ORDER BY adverse_event_count DESC, safety_signal_count DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, {"target_id": target_id, "limit": limit})
        return result.records if result.success else []

    #===========================================================
    # 四、供应链影响分析查询 (Supply Chain Impact Analysis)
    #===========================================================

    def get_manufacturer_supply_chain_impact(
        self,
        manufacturer_id: str,
        include_downstream: bool = True
    ) -> Dict[str, Any]:
        """
        获取制造商的供应链影响分析

        查询路径: Manufacturer → manufactures → Drug → experiences_shortage
                                       → supplied_to → other_manufacturers

        Args:
            manufacturer_id: 制造商ID
            include_downstream: 是否包含下游影响分析

        Returns:
            供应链影响分析
        """
        query = """
        MATCH (m:Manufacturer {manufacturer_id: $manufacturer_id})
        OPTIONAL MATCH (m)-[:MANUFACTURES|PRODUCES_ACTIVE_INGREDIENT]->(product:DrugProduct)
        OPTIONAL MATCH (product)-[:EXPERIENCES_SHORTAGE]->(shortage:DrugShortage)
        OPTIONAL MATCH (m)-[:SUPPLIES_TO]->(downstream:Manufacturer)
        RETURN {
            manufacturer_id: m.manufacturer_id,
            manufacturer_name: m.name,
            location: m.location,
            products: {
                total_products: count(DISTINCT product),
                products_with_active_shortage: count(DISTINCT CASE
                    WHEN shortage.status = 'active' THEN product
                END),
                product_details: collect(DISTINCT {
                    product_id: product.product_id,
                    product_name: product.name,
                    is_shortage: shortage IS NOT NULL,
                    shortage_status: shortage.status,
                    shortage_impact: shortage.impact_level
                })
            },
            supply_role: {
                is_api_supplier: EXISTS((m)-[:PRODUCES_ACTIVE_INGREDIENT]->()),
                supplies_to_count: count(DISTINCT downstream),
                downstream_manufacturers: collect(DISTINCT {
                    manufacturer_id: downstream.manufacturer_id,
                    manufacturer_name: downstream.name
                })
            },
            risk_assessment: {
                active_shortages: count(DISTINCT CASE
                    WHEN shortage.status = 'active' THEN shortage
                END),
                quality_issues: EXISTS((m)-[:FAILED_INSPECTION]->()),
                last_inspection_score: m.last_inspection_score
            }
        } AS impact_analysis
        """

        result = self.db.execute_query(query, {"manufacturer_id": manufacturer_id})

        if result.success and result.records:
            return result.records[0]
        return {}

    def get_drug_shortage_cascading_impact(
        self,
        drug_product_id: str,
        max_depth: int = 3
    ) -> List[dict]:
        """
        获取药品短缺的级联影响分析

        查询逻辑: 分析药品短缺对下游产品、患者、治疗的连锁影响

        Args:
            drug_product_id: 药品产品ID
            max_depth: 最大分析深度

        Returns:
            级联影响路径
        """
        query = f"""
        MATCH (drug:DrugProduct {{product_id: $drug_product_id}})-[:EXPERIENCES_SHORTAGE]->(shortage:DrugShortage)
        OPTIONAL MATCH (drug)-[:USED_IN]->(formulation:DrugFormulation)
        OPTIONAL MATCH (formulation)-[:PRESCRIBED_FOR]->(disease:Disease)
        OPTIONAL MATCH (drug)-[:COMPETES_WITH]->(competitor:DrugProduct)
        WITH drug, shortage, formulation, disease, competitor
        RETURN {{
            drug_product: {{
                id: drug.product_id,
                name: drug.name
            }},
            shortage: {{
                shortage_id: shortage.shortage_id,
                status: shortage.status,
                start_date: shortage.start_date,
                impact_level: shortage.impact_level,
                estimated_resolution: shortage.estimated_end_date
            }},
            downstream_impact: {{
                affected_formulations: count(DISTINCT formulation),
                affected_diseases: collect(DISTINCT {{
                    disease_id: disease.disease_id,
                    disease_name: disease.name,
                    patient_impact: disease.prevalence * shortage.impact_level
                }}),
                alternatives_available: count(DISTINCT competitor)
            }}
        }} AS cascade_analysis
        LIMIT 1
        """

        result = self.db.execute_query(query, {"drug_product_id": drug_product_id})
        return result.records if result.success else []

    def get_api_supply_vulnerability(
        self,
        api_name: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        获取API(原料药)供应脆弱性分析

        查询逻辑: 分析单一供应商的API，识别供应风险

        Args:
            api_name: API名称筛选
            limit: 返回结果数量限制

        Returns:
            API供应脆弱性分析
        """
        api_filter = ""
        params = {"limit": limit}

        if api_name:
            api_filter = "WHERE api.name = $api_name"
            params["api_name"] = api_name

        query = f"""
        MATCH (api:ActivePharmaceuticalIngredient)
        OPTIONAL MATCH (supplier:Manufacturer)-[:PRODUCES_ACTIVE_INGREDIENT]->(api)
        OPTIONAL MATCH (manufacturer:Manufacturer)-[:USES_API]->(api)
        OPTIONAL MATCH (drug:DrugProduct)-[:CONTAINS_API]->(api)
        {api_filter}
        RETURN DISTINCT
            api.primary_id AS api_id,
            api.name AS api_name,
            count(DISTINCT supplier) AS supplier_count,
            count(DISTINCT manufacturer) AS dependent_manufacturer_count,
            count(DISTINCT drug) AS affected_product_count,
            CASE
                WHEN count(DISTINCT supplier) = 1 THEN 'critical'
                WHEN count(DISTINCT supplier) = 2 THEN 'high'
                WHEN count(DISTINCT supplier) <= 3 THEN 'moderate'
                ELSE 'low'
            END AS supply_risk_level,
            collect(DISTINCT {{
                supplier_id: supplier.manufacturer_id,
                supplier_name: supplier.name,
                location: supplier.location
            }}) AS suppliers
        ORDER BY supply_risk_level, affected_product_count DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, params)
        return result.records if result.success else []

    #===========================================================
    # 五、知识图谱路径查询 (Knowledge Graph Path Queries)
    #===========================================================

    def find_shortest_path(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_path_length: int = 5,
        relationship_types: Optional[List[str]] = None
    ) -> List[dict]:
        """
        查找两个实体之间的最短路径

        Args:
            start_entity_id: 起始实体ID
            end_entity_id: 结束实体ID
            max_path_length: 最大路径长度
            relationship_types: 关系类型筛选

        Returns:
            路径列表
        """
        rel_filter = ""
        params = {
            "start_id": start_entity_id,
            "end_id": end_entity_id,
            "max_length": max_path_length
        }

        if relationship_types:
            rel_filter = "WHERE type(r) IN $rel_types"
            params["rel_types"] = relationship_types

        query = f"""
        MATCH path = (start)-[:RELATED_TO*1..$max_length]]->(end)
        WHERE start.primary_id = $start_id
          AND end.primary_id = $end_id
        {rel_filter}
        RETURN
            [node IN nodes(path) | {{
                id: node.primary_id,
                name: node.name,
                type: labels(node)[0]
            }}] AS path_nodes,
            [rel IN relationships(path) | type(rel)] AS relationship_types,
            length(path) AS path_length
        ORDER BY path_length
        LIMIT 10
        """

        result = self.db.execute_query(query, params)
        return result.records if result.success else []

    def get_entity_neighborhood(
        self,
        entity_id: str,
        depth: int = 2,
        min_degree: int = 1
    ) -> Dict[str, Any]:
        """
        获取实体的邻域分析

        Args:
            entity_id: 实体ID
            depth: 邻域深度
            min_degree: 最小度数

        Returns:
            实体邻域分析
        """
        query = """
        MATCH (center {primary_id: $entity_id})
        OPTIONAL MATCH path = (center)-[r*1..depth]-(neighbor)
        WHERE degree(neighbor) >= $min_degree
        WITH center, neighbor, r
        RETURN {
            center_entity: {
                id: center.primary_id,
                name: center.name,
                type: labels(center)[0]
            },
            neighborhood: {
                total_neighbors: count(DISTINCT neighbor),
                neighbor_types: collect(DISTINCT {
                    type: labels(neighbor)[0],
                    count: count(DISTINCT neighbor)
                }),
                highly_connected_neighbors: [
                    {
                        id: neighbor.primary_id,
                        name: neighbor.name,
                        type: labels(neighbor)[0],
                        degree: degree(neighbor)
                    }
                    | neighbor
                    | WHERE degree(neighbor) > 10
                    | ORDER BY degree(neighbor) DESC
                    | LIMIT 20
                ]
            }
        } AS neighborhood_analysis
        """

        result = self.db.execute_query(
            query,
            {"entity_id": entity_id, "depth": depth, "min_degree": min_degree}
        )

        if result.success and result.records:
            return result.records[0]
        return {}

    #===========================================================
    # 六、辅助方法
    #===========================================================

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
