#===========================================================
# PharmaKG API - 聚合统计查询服务
# Pharmaceutical Knowledge Graph - Aggregate Query Service
#===========================================================
# 版本: v1.0
# 描述: 实现聚合统计查询，包括领域统计概览、时序分析、
#       地理分布分析、成功率分析等
#===========================================================

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..database import Neo4jConnection


class AggregateQueryService:
    """聚合统计查询服务"""

    def __init__(self):
        """初始化数据库连接"""
        self.db = Neo4jConnection()

    #===========================================================
    # 一、领域统计概览 (Domain Statistics Overview)
    #===========================================================

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱综合统计概览

        Returns:
            综合统计信息
        """
        query = """
        MATCH (n)
        WITH labels(n)[0] AS entity_type, count(n) AS count
        RETURN {
            entity_types: collect({
                type: entity_type,
                count: count
            }),
            total_entities: sum(count)
        } AS entity_stats
        """

        result = self.db.execute_query(query)
        entity_stats = result.records[0] if result.records else {}

        # 关系统计
        rel_query = """
        MATCH ()-[r]->()
        WITH type(r) AS rel_type, count(r) AS count
        RETURN {
            relationship_types: collect({
                type: rel_type,
                count: count
            }),
            total_relationships: sum(count)
        } AS rel_stats
        """

        rel_result = self.db.execute_query(rel_query)
        rel_stats = rel_result.records[0] if rel_result.records else {}

        return {
            "entities": entity_stats.get("entity_stats", {}),
            "relationships": rel_stats.get("rel_stats", {}),
            "last_updated": datetime.now().isoformat()
        }

    def get_domain_breakdown(self) -> Dict[str, Any]:
        """
        获取各领域详细统计

        Returns:
            各领域统计详情
        """
        query = """
        // R&D 领域
        MATCH (c:Compound)
        WITH count(c) AS compound_count
        MATCH (t:Target)
        WITH compound_count, count(t) AS target_count
        MATCH (a:Assay)
        WITH compound_count, target_count, count(a) AS assay_count
        MATCH (p:Pathway)
        WITH compound_count, target_count, assay_count, count(p) AS pathway_count

        // 临床领域
        MATCH (trial:ClinicalTrial)
        WITH compound_count, target_count, assay_count, pathway_count, count(trial) AS trial_count
        MATCH (s:Subject)
        WITH compound_count, target_count, assay_count, pathway_count, trial_count, count(s) AS subject_count
        MATCH (ae:AdverseEvent)
        WITH compound_count, target_count, assay_count, pathway_count, trial_count, subject_count, count(ae) AS ae_count

        // 供应链领域
        MATCH (m:Manufacturer)
        WITH compound_count, target_count, assay_count, pathway_count, trial_count, subject_count, ae_count, count(m) AS mfg_count
        MATCH (ds:DrugShortage)
        WITH compound_count, target_count, assay_count, pathway_count, trial_count, subject_count, ae_count, mfg_count, count(ds) AS shortage_count

        // 监管领域
        MATCH (sub:Submission)
        WITH compound_count, target_count, assay_count, pathway_count, trial_count, subject_count, ae_count, mfg_count, shortage_count, count(sub) AS sub_count
        MATCH (app:Approval)
        WITH compound_count, target_count, assay_count, pathway_count, trial_count, subject_count, ae_count, mfg_count, shortage_count, sub_count, count(app) AS approval_count

        RETURN {
            rd_domain: {
                name: "Research & Development",
                entities: {
                    compounds: compound_count,
                    targets: target_count,
                    assays: assay_count,
                    pathways: pathway_count
                },
                total: compound_count + target_count + assay_count + pathway_count
            },
            clinical_domain: {
                name: "Clinical",
                entities: {
                    trials: trial_count,
                    subjects: subject_count,
                    adverse_events: ae_count
                },
                total: trial_count + subject_count + ae_count
            },
            supply_chain_domain: {
                name: "Supply Chain",
                entities: {
                    manufacturers: mfg_count,
                    drug_shortages: shortage_count
                },
                total: mfg_count + shortage_count
            },
            regulatory_domain: {
                name: "Regulatory",
                entities: {
                    submissions: sub_count,
                    approvals: approval_count
                },
                total: sub_count + approval_count
            }
        } AS domain_breakdown
        """

        result = self.db.execute_query(query)
        if result.records:
            return result.records[0]
        return {}

    #===========================================================
    # 二、时序分析查询 (Temporal Analysis Queries)
    #===========================================================

    def get_submission_timeline(
        self,
        years: int = 10,
        submission_type: Optional[str] = None
    ) -> List[dict]:
        """
        获取申报数量随时间变化

        Args:
            years: 统计年数
            submission_type: 申报类型筛选 (NDA, ANDA, BLA)

        Returns:
            时序统计数据
        """
        type_filter = ""
        params = {"years": years}

        if submission_type:
            type_filter = "AND s.submission_type = $submission_type"
            params["submission_type"] = submission_type

        query = f"""
        MATCH (s:Submission)
        WHERE s.submission_date >= date() - duration('P{years}Y')
        {type_filter}
        WITH s.submission_date.year AS year,
             count(s) AS submission_count,
             s.submission_type AS sub_type
        RETURN year, sub_type, submission_count
        ORDER BY year DESC, sub_type
        """

        result = self.db.execute_query(query, params)
        return result.records if True else []

    def get_approval_rate_timeline(
        self,
        years: int = 10
    ) -> List[dict]:
        """
        获取批准率随时间变化

        Args:
            years: 统计年数

        Returns:
            批准率时序数据
        """
        query = """
        MATCH (sub:Submission)
        WHERE sub.submission_date >= date() - duration($years)
        OPTIONAL MATCH (sub)-[:SUBMITTED_FOR_APPROVAL]->(app:Approval)
        WITH sub.submission_date.year AS year,
             count(DISTINCT sub) AS total_submissions,
             count(DISTINCT app) AS total_approvals
        RETURN year,
               total_submissions,
               total_approvals,
               CASE
                   WHEN total_submissions > 0
                   THEN (total_approvals * 100.0 / total_submissions)
                   ELSE 0
               END AS approval_rate
        ORDER BY year DESC
        """

        result = self.db.execute_query(query, {"years": f"P{years}Y"})
        return result.records if True else []

    def get_clinical_trial_timeline(
        self,
        years: int = 10,
        phase: Optional[str] = None
    ) -> List[dict]:
        """
        获取临床试验时序统计

        Args:
            years: 统计年数
            phase: 试验阶段筛选

        Returns:
            试验时序数据
        """
        phase_filter = ""
        params = {"years": f"P{years}Y"}

        if phase:
            phase_filter = "AND t.phase = $phase"
            params["phase"] = phase

        query = f"""
        MATCH (t:ClinicalTrial)
        WHERE t.start_date >= date() - duration($years)
        {phase_filter}
        WITH t.start_date.year AS year,
             t.phase AS trial_phase,
             count(t) AS trial_count
        RETURN year, trial_phase, trial_count
        ORDER BY year DESC, trial_phase
        """

        result = self.db.execute_query(query, params)
        return result.records if True else []

    def get_shortage_timeline(
        self,
        years: int = 5,
        impact_level: Optional[str] = None
    ) -> List[dict]:
        """
        获取药品短缺时序统计

        Args:
            years: 统计年数
            impact_level: 影响级别筛选

        Returns:
            短缺时序数据
        """
        impact_filter = ""
        params = {"years": f"P{years}Y"}

        if impact_level:
            impact_filter = "AND s.impact_level = $impact_level"
            params["impact_level"] = impact_level

        query = f"""
        MATCH (s:DrugShortage)
        WHERE s.start_date >= date() - duration($years)
        {impact_filter}
        WITH s.start_date.year AS year,
             s.impact_level AS impact,
             count(s) AS shortage_count
        RETURN year, impact, shortage_count
        ORDER BY year DESC, impact
        """

        result = self.db.execute_query(query, params)
        return result.records if True else []

    #===========================================================
    # 三、地理分布分析 (Geographic Distribution Analysis)
    #===========================================================

    def get_trial_geographic_distribution(
        self,
        top_n: int = 20
    ) -> List[dict]:
        """
        获取试验地理分布统计

        Args:
            top_n: 返回前N个国家/地区

        Returns:
            地理分布统计
        """
        query = """
        MATCH (t:ClinicalTrial)-[:CONDUCTED_AT_SITE]->(site:StudySite)
        WITH site.country AS country, count(DISTINCT t) AS trial_count
        WHERE country IS NOT NULL
        RETURN country, trial_count
        ORDER BY trial_count DESC
        LIMIT $top_n
        """

        result = self.db.execute_query(query, {"top_n": top_n})
        return result.records if True else []

    def get_manufacturer_geographic_distribution(
        self,
        top_n: int = 20
    ) -> List[dict]:
        """
        获取制造商地理分布统计

        Args:
            top_n: 返回前N个国家/地区

        Returns:
            制造商地理分布
        """
        query = """
        MATCH (m:Manufacturer)
        WITH m.country AS country, count(m) AS manufacturer_count
        WHERE country IS NOT NULL
        RETURN country, manufacturer_count
        ORDER BY manufacturer_count DESC
        LIMIT $top_n
        """

        result = self.db.execute_query(query, {"top_n": top_n})
        return result.records if True else []

    def get_regional_trial_statistics(
        self,
        region: str = None
    ) -> List[dict]:
        """
        获取区域试验统计

        Args:
            region: 区域筛选

        Returns:
            区域试验统计
        """
        region_filter = ""
        params = {}

        if region:
            region_filter = "WHERE site.country = $region"
            params["region"] = region

        query = f"""
        MATCH (t:ClinicalTrial)-[:CONDUCTED_AT_SITE]->(site:StudySite)
        {region_filter}
        WITH site.country AS country, t.phase AS phase, count(DISTINCT t) AS trial_count
        RETURN country, phase, trial_count
        ORDER BY country, phase
        """

        result = self.db.execute_query(query, params)
        return result.records if True else []

    #===========================================================
    # 四、成功率分析 (Success Rate Analysis)
    #===========================================================

    def get_trial_success_rate_by_phase(
        self,
        min_trial_count: int = 10
    ) -> List[dict]:
        """
        获取各阶段试验成功率

        Args:
            min_trial_count: 最小试验数量阈值

        Returns:
            各阶段成功率
        """
        query = """
        MATCH (t:ClinicalTrial)
        WITH t.phase AS phase,
             count(t) AS total_trials,
             count(DISTINCT CASE WHEN t.status = 'completed' THEN t END) AS completed_trials,
             count(DISTINCT CASE WHEN t.status = 'terminated' THEN t END) AS terminated_trials,
             count(DISTINCT CASE WHEN t.primary_endpoint_met = true THEN t END) AS successful_trials
        WHERE total_trials >= $min_count
        RETURN phase,
               total_trials,
               completed_trials,
               terminated_trials,
               successful_trials,
               CASE
                   WHEN total_trials > 0
                   THEN (completed_trials * 100.0 / total_trials)
                   ELSE 0
               END AS completion_rate,
               CASE
                   WHEN completed_trials > 0
                   THEN (successful_trials * 100.0 / completed_trials)
                   ELSE 0
               END AS success_rate
        ORDER BY phase
        """

        result = self.db.execute_query(query, {"min_count": min_trial_count})
        return result.records if True else []

    def get_approval_rate_by_therapeutic_area(
        self,
        min_submissions: int = 5
    ) -> List[dict]:
        """
        获取各治疗领域批准率

        Args:
            min_submissions: 最小申报数量阈值

        Returns:
            各治疗领域批准率
        """
        query = """
        MATCH (sub:Submission)-[:SUBMISSION_FOR_PRODUCT]->(drug:DrugProduct)
        MATCH (drug)-[:TREATS]->(disease:Disease)
        WITH disease.therapeutic_area AS therapeutic_area,
             count(DISTINCT sub) AS total_submissions,
             count(DISTINCT CASE WHEN sub.outcome = 'approved' THEN sub END) AS approved_submissions
        WHERE total_submissions >= $min_count
        RETURN therapeutic_area,
               total_submissions,
               approved_submissions,
               CASE
                   WHEN total_submissions > 0
                   THEN (approved_submissions * 100.0 / total_submissions)
                   ELSE 0
               END AS approval_rate
        ORDER BY approval_rate DESC
        """

        result = self.db.execute_query(query, {"min_count": min_submissions})
        return result.records if True else []

    def get_target_based_success_rate(
        self,
        min_compounds: int = 5
    ) -> List[dict]:
        """
        获取基于靶点的化合物成功率

        Args:
            min_compounds: 最小化合物数量阈值

        Returns:
            靶点成功率分析
        """
        query = """
        MATCH (t:Target)<-[:INHIBITS|ACTIVATES]-(c:Compound)
        OPTIONAL MATCH (c)-[:APPROVED_AS_DRUG]->(app:Approval)
        WITH t.primary_id AS target_id,
             t.name AS target_name,
             t.target_class AS target_class,
             count(DISTINCT c) AS total_compounds,
             count(DISTINCT app) AS approved_compounds
        WHERE total_compounds >= $min_count
        RETURN target_id,
               target_name,
               target_class,
               total_compounds,
               approved_compounds,
               CASE
                   WHEN total_compounds > 0
                   THEN (approved_compounds * 100.0 / total_compounds)
                   ELSE 0
               END AS approval_rate
        ORDER BY approval_rate DESC, total_compounds DESC
        """

        result = self.db.execute_query(query, {"min_count": min_compounds})
        return result.records if True else []

    #===========================================================
    # 五、热点分析 (Hotspot Analysis)
    #===========================================================

    def get_research_hotspots(self, top_n: int = 20) -> List[dict]:
        """
        获取研究热点（活跃靶点和疾病）

        Args:
            top_n: 返回前N个热点

        Returns:
            研究热点列表
        """
        query = """
        // 热门靶点
        MATCH (c:Compound)-[r:INHIBITS|ACTIVATES]->(t:Target)
        WITH t.primary_id AS target_id, t.name AS target_name, count(DISTINCT c) AS compound_count
        ORDER BY compound_count DESC
        LIMIT $top_n
        WITH collect({target_id: target_id, target_name: target_name, compound_count: compound_count}) AS hot_targets

        // 热门疾病
        MATCH (c:Compound)-[:TREATS|PREVENTS]->(d:Disease)
        WITH hot_targets,
             d.primary_id AS disease_id,
             d.name AS disease_name,
             d.therapeutic_area AS area,
             count(DISTINCT c) AS compound_count
        ORDER BY compound_count DESC
        LIMIT $top_n
        RETURN {
            hot_targets: hot_targets,
            hot_diseases: collect({
                disease_id: disease_id,
                disease_name: disease_name,
                therapeutic_area: area,
                compound_count: compound_count
            })
        } AS hotspots
        """

        result = self.db.execute_query(query, {"top_n": top_n})
        if result.records:
            return result.records[0]
        return {}

    def get_emerging_targets(self, years: int = 3, min_growth: float = 1.5) -> List[dict]:
        """
        获取新兴靶点（增长最快的靶点）

        Args:
            years: 对比年数
            min_growth: 最小增长率

        Returns:
            新兴靶点列表
        """
        query = """
        // 早期化合物数量
        MATCH (c:Compound)-[r:INHIBITS|ACTIVATES]->(t:Target)
        WHERE c.created_at <= date() - duration($years)
        WITH t, count(DISTINCT c) AS early_count

        // 近期化合物数量
        MATCH (c:Compound)-[r:INHIBITS|ACTIVATES]->(t)
        WHERE c.created_at > date() - duration($years)
        WITH t, early_count, count(DISTINCT c) AS recent_count

        // 计算增长率
        WITH t.primary_id AS target_id,
             t.name AS target_name,
             early_count,
             recent_count,
             CASE
                 WHEN early_count > 0
                 THEN (recent_count * 1.0 / early_count)
                 ELSE 0
             END AS growth_rate
        WHERE growth_rate >= $min_growth
        RETURN target_id, target_name, early_count, recent_count, growth_rate
        ORDER BY growth_rate DESC
        LIMIT 20
        """

        result = self.db.execute_query(query, {
            "years": f"P{years}Y",
            "min_growth": min_growth
        })
        return result.records if True else []

    #===========================================================
    # 六、质量评估分析 (Quality Assessment Analysis)
    #===========================================================

    def get_manufacturer_quality_statistics(self) -> List[dict]:
        """
        获取制造商质量统计

        Returns:
            制造商质量评分
        """
        query = """
        MATCH (m:Manufacturer)
        OPTIONAL MATCH (m)-[r:SUBJECT_TO_INSPECTION]->(i:Inspection)
        WITH m,
             count(DISTINCT i) AS total_inspections,
             count(DISTINCT CASE WHEN i.result = 'passed' THEN i END) AS passed_inspections,
             count(DISTINCT CASE WHEN i.result = 'failed' THEN i END) AS failed_inspections
        WHERE total_inspections > 0
        RETURN m.manufacturer_id AS manufacturer_id,
               m.name AS manufacturer_name,
               m.location AS location,
               total_inspections,
               passed_inspections,
               failed_inspections,
               CASE
                   WHEN total_inspections > 0
                   THEN (passed_inspections * 100.0 / total_inspections)
                   ELSE 0
               END AS pass_rate,
               CASE
                   WHEN failed_inspections >= 3 THEN 'HIGH_RISK'
                   WHEN failed_inspections >= 1 THEN 'MEDIUM_RISK'
                   ELSE 'LOW_RISK'
               END AS risk_level
        ORDER BY pass_rate ASC, failed_inspections DESC
        """

        result = self.db.execute_query(query)
        return result.records if True else []

    def get_drug_shortage_analysis(self) -> Dict[str, Any]:
        """
        获取药品短缺分析

        Returns:
            短缺统计和分析
        """
        query = """
        MATCH (ds:DrugShortage)
        WITH ds.status AS status,
             ds.impact_level AS impact,
             count(ds) AS shortage_count
        RETURN {
            status_distribution: collect({
                status: status,
                count: shortage_count
            }),
            impact_distribution: collect(DISTINCT {
                impact_level: impact,
                count: shortage_count
            }),
            total_shortages: sum(shortage_count),
            active_shortages: sum(CASE WHEN status = 'active' THEN shortage_count ELSE 0 END)
        } AS shortage_analysis
        """

        result = self.db.execute_query(query)
        if result.records:
            return result.records[0]
        return {}

    #===========================================================
    # 七、网络分析 (Network Analysis)
    #===========================================================

    def get_highly_connected_entities(
        self,
        entity_type: str = None,
        min_degree: int = 10,
        limit: int = 50
    ) -> List[dict]:
        """
        获取高度连接的实体（枢纽节点）

        Args:
            entity_type: 实体类型筛选
            min_degree: 最小度数
            limit: 返回数量限制

        Returns:
            高连接实体列表
        """
        type_filter = ""
        params = {"min_degree": min_degree, "limit": limit}

        if entity_type:
            type_filter = "WHERE n:" + entity_type
            # 注意：实际实现中需要更安全的参数化方式

        query = f"""
        MATCH (n)
        {type_filter}
        WHERE size((n)-[]-()) >= $min_degree
        RETURN n.primary_id AS entity_id,
               n.name AS name,
               labels(n)[0] AS entity_type,
               size((n)-[]-()) AS degree
        ORDER BY degree DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, params)
        return result.records if True else []

    def get_pathway_coverage_analysis(self) -> List[dict]:
        """
        获取通路覆盖分析

        Returns:
            通路覆盖统计
        """
        query = """
        MATCH (p:Pathway)<-[r:PARTICIPATES_IN|REGULATES_PATHWAY]-(t:Target)
        WITH p.primary_id AS pathway_id,
             p.name AS pathway_name,
             count(DISTINCT t) AS target_count
        RETURN pathway_id, pathway_name, target_count
        ORDER BY target_count DESC
        LIMIT 30
        """

        result = self.db.execute_query(query)
        return result.records if True else []

    #===========================================================
    # 八、辅助方法
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
