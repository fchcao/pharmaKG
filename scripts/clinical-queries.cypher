//===========================================================
// 制药行业知识图谱 - 临床试验领域示例查询
// Pharmaceutical Knowledge Graph - Clinical Domain Example Queries
//===========================================================
// 版本: v1.0
// 创建日期: 2025-02-06
// 描述: 临床试验领域常用Cypher查询示例
//===========================================================

//===========================================================
// 1. 基础查询 - 试验统计
//===========================================================

// Q1.1: 查询所有临床试验数量
MATCH (t:ClinicalTrial)
RETURN count(t) AS total_trials;

// Q1.2: 按阶段统计试验数量
MATCH (t:ClinicalTrial)-[:HAS_PHASE]->(tp:TrialPhase)
RETURN tp.name AS phase, count(t) AS trial_count
ORDER BY tp.order;

// Q1.3: 按状态统计试验数量
MATCH (t:ClinicalTrial)-[:HAS_STATUS]->(ts:TrialStatus)
RETURN ts.name AS status, count(t) AS trial_count
ORDER BY trial_count DESC;

// Q1.4: 按研究类型统计试验数量
MATCH (t:ClinicalTrial)-[:HAS_STUDY_TYPE]->(st:StudyType)
RETURN st.name AS study_type, count(t) AS trial_count
ORDER BY trial_count DESC;

//===========================================================
// 2. 试验检索查询
//===========================================================

// Q2.1: 查询指定疾病的所有试验
MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
WHERE c.condition_name = 'COVID-19'
RETURN t.trial_id, t.title, t.phase, t.status, t.enrollment
ORDER BY t.start_date DESC;

// Q2.2: 查询指定阶段的试验
MATCH (t:ClinicalTrial)-[:HAS_PHASE]->(tp:TrialPhase)
WHERE tp.id = 'phase_3'
RETURN t.trial_id, t.title, t.status, t.enrollment, t.start_date
ORDER BY t.enrollment DESC;

// Q2.3: 查询招募中的试验
MATCH (t:ClinicalTrial)-[:HAS_STATUS]->(ts:TrialStatus)
WHERE ts.id = 'recruiting'
RETURN t.trial_id, t.title, t.phase, t.enrollment, t.start_date
ORDER BY t.enrollment DESC
LIMIT 50;

// Q2.4: 查询最近开始的试验
MATCH (t:ClinicalTrial)
WHERE t.start_date >= date() - duration('P30D')
RETURN t.trial_id, t.title, t.phase, t.start_date
ORDER BY t.start_date DESC;

//===========================================================
// 3. 受试者查询
//===========================================================

// Q3.1: 查询试验的受试者列表
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})<-[:ENROLLED_IN]-(s:Subject)
RETURN s.subject_id, s.initials, s.age, s.gender, s.enrollment_date
ORDER BY s.enrollment_date;

// Q3.2: 按性别统计受试者分布
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})<-[:ENROLLED_IN]-(s:Subject)-[:HAS_GENDER]->(g:Gender)
RETURN g.name AS gender, count(s) AS subject_count;

// Q3.3: 按年龄组统计受试者分布
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})<-[:ENROLLED_IN]-(s:Subject)-[:HAS_AGE_GROUP]->(ag:AgeGroup)
RETURN ag.name AS age_group, count(s) AS subject_count;

// Q3.4: 查询受试者参与的试验历史
MATCH (s:Subject {subject_id: 'SUB001'})-[:ENROLLED_IN]->(t:ClinicalTrial)
RETURN s.subject_id, s.initials, collect({
    trial_id: t.trial_id,
    title: t.title,
    phase: t.phase,
    enrollment_date: s.enrollment_date
}) AS trials;

//===========================================================
// 4. 分组(Arm)分析
//===========================================================

// Q4.1: 查询试验的所有分组
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:HAS_ARM]->(a:Arm)
RETURN a.arm_id, a.arm_label, a.arm_type, a.description, a.target_enrollment
ORDER BY a.arm_label;

// Q4.2: 查询各组的实际入组人数
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:HAS_ARM]->(a:Arm)<-[:ASSIGNED_TO]-(s:Subject)
RETURN a.arm_label AS arm, count(s) AS actual_enrollment, a.target_enrollment
ORDER BY a.arm_label;

// Q4.3: 比较各组的基线特征
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:HAS_ARM]->(a:Arm)<-[:ASSIGNED_TO]-(s:Subject)
RETURN a.arm_label AS arm,
       avg(s.age) AS mean_age,
       min(s.age) AS min_age,
       max(s.age) AS max_age,
       count(s) AS n
ORDER BY a.arm_label;

//===========================================================
// 5. 干预措施查询
//===========================================================

// Q5.1: 查询试验的干预措施
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:HAS_INTERVENTION]->(i:Intervention)
RETURN i.intervention_id, i.intervention_name, i.intervention_type,
       i.dosage, i.route, i.frequency, i.duration
ORDER BY i.arm_group_label;

// Q5.2: 查询指定类型的干预措施
MATCH (i:Intervention)-[:HAS_INTERVENTION_TYPE]->(it:InterventionType)
WHERE it.id = 'drug'
RETURN DISTINCT i.intervention_name, i.dosage, i.route
ORDER BY i.intervention_name;

// Q5.3: 查询药物的使用情况
MATCH (i:Intervention)
WHERE i.intervention_type = 'drug'
MATCH (i)-[:INTERVENTION_OF]->(t:ClinicalTrial)
RETURN i.intervention_name AS drug, count(DISTINCT t) AS trial_count,
       collect(DISTINCT t.trial_id) AS trials
ORDER BY trial_count DESC
LIMIT 20;

//===========================================================
// 6. 结局指标查询
//===========================================================

// Q6.1: 查询试验的主要终点
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:HAS_PRIMARY_OUTCOME|HAS_SECONDARY_OUTCOME]->(o:Outcome)
RETURN o.outcome_type, o.title, o.description, o.time_frame, o.unit
ORDER BY o.outcome_type;

// Q6.2: 查询指定类型的结局指标
MATCH (o:Outcome)-[:HAS_OUTCOME_TYPE]->(ot:OutcomeType)
WHERE ot.id = 'primary'
RETURN o.title, o.description, o.time_frame, o.unit
ORDER BY o.title
LIMIT 50;

// Q6.3: 查询结局指标在试验中的使用频率
MATCH (o:Outcome)-[:OUTCOME_OF]->(t:ClinicalTrial)
WITH o.title AS outcome_title, count(DISTINCT t) AS trial_count
WHERE trial_count > 1
RETURN outcome_title, trial_count
ORDER BY trial_count DESC
LIMIT 20;

//===========================================================
// 7. 不良事件分析
//===========================================================

// Q7.1: 查询试验的所有不良事件
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:REPORTS_ADVERSE_EVENT]->(ae:AdverseEvent)
RETURN ae.ae_id, ae.meddra_term, ae.severity, ae.seriousness, ae.onset_date, ae.outcome
ORDER BY ae.onset_date;

// Q7.2: 按严重程度统计不良事件
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:REPORTS_ADVERSE_EVENT]->(ae:AdverseEvent)-[:HAS_SEVERITY]->(sg:SeverityGrade)
RETURN sg.name AS severity, count(ae) AS ae_count
ORDER BY sg.order;

// Q7.3: 查询严重不良事件(SAE)
MATCH (ae:AdverseEvent)
WHERE ae.seriousness = 'serious'
MATCH (ae)<-[:REPORTS_ADVERSE_EVENT]-(t:ClinicalTrial)
RETURN t.trial_id, ae.meddra_term, ae.severity, ae.onset_date, ae.outcome
ORDER BY ae.onset_date DESC;

// Q7.4: 按MedDRA术语统计不良事件
MATCH (ae:AdverseEvent)
WITH ae.meddra_term AS term, ae.meddra_code AS code, count(ae) AS frequency
WHERE frequency > 1
RETURN term, code, frequency
ORDER BY frequency DESC
LIMIT 30;

// Q7.5: 查询受试者的不良事件
MATCH (s:Subject {subject_id: 'SUB001'})-[:EXPERIENCED_AE]->(ae:AdverseEvent)
RETURN s.subject_id, ae.meddra_term, ae.severity, ae.onset_date, ae.outcome
ORDER BY ae.onset_date;

//===========================================================
// 8. 研究中心查询
//===========================================================

// Q8.1: 查询试验的研究中心
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})<-[:SITE_OF]-(site:StudySite)
RETURN site.site_id, site.site_name, site.city, site.state, site.country,
       site.contact_name, site.contact_email
ORDER BY site.site_name;

// Q8.2: 按国家统计研究中心分布
MATCH (site:StudySite)
RETURN site.country AS country, count(DISTINCT site) AS site_count
ORDER BY site_count DESC;

// Q8.3: 查询指定国家的研究中心
MATCH (site:StudySite)
WHERE site.country = 'United States'
RETURN site.site_name, site.city, site.state, site.contact_email
ORDER BY site.city, site.site_name;

// Q8.4: 查询活跃的研究中心
MATCH (site:StudySite)-[:HAS_STATUS]->(ss:SiteStatus)
WHERE ss.id = 'active'
RETURN site.site_name, site.city, site.country
ORDER BY site.country, site.city;

//===========================================================
// 9. 研究者查询
//===========================================================

// Q9.1: 查询试验的研究者
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})<-[:SITE_OF]-(site:StudySite)<-[:ASSIGNED_TO]-(inv:Investigator)
RETURN inv.investigator_id, inv.name, inv.role, inv.degree, inv.affiliation,
       site.site_name AS site
ORDER BY inv.role, inv.name;

// Q9.2: 查询主要研究者
MATCH (inv:Investigator)-[:HAS_ROLE]->(ir:InvestigatorRole)
WHERE ir.id = 'principal_investigator'
RETURN inv.name, inv.affiliation, inv.email, count(DISTINCT inv) AS trial_count
ORDER BY trial_count DESC
LIMIT 20;

// Q9.3: 按机构统计研究者
MATCH (inv:Investigator)
RETURN inv.affiliation AS institution, count(DISTINCT inv) AS investigator_count
ORDER BY investigator_count DESC
LIMIT 20;

//===========================================================
// 10. 申办方分析
//===========================================================

// Q10.1: 查询试验的申办方
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:HAS_SPONSOR]->(org:Sponsor)
RETURN org.org_name, org.org_type;

// Q10.2: 按申办方统计试验数量
MATCH (t:ClinicalTrial)-[:HAS_SPONSOR]->(org:Sponsor)
RETURN org.org_name AS sponsor, count(t) AS trial_count
ORDER BY trial_count DESC
LIMIT 20;

// Q10.3: 按申办方类型统计
MATCH (org:Sponsor)
RETURN org.org_type AS sponsor_type, count(DISTINCT org) AS org_count;

//===========================================================
// 11. 复杂分析查询
//===========================================================

// Q11.1: 试验完成率分析
MATCH (t:ClinicalTrial)
WITH t,
     CASE WHEN t.completion_date < date() THEN 'completed'
          WHEN t.primary_completion_date < date() THEN 'primary_completed'
          WHEN t.status IN ['terminated', 'withdrawn'] THEN 'early_terminated'
          ELSE 'ongoing' END AS completion_status
RETURN completion_status, count(t) AS trial_count
ORDER BY trial_count DESC;

// Q11.2: 试验持续时间分析
MATCH (t:ClinicalTrial)
WHERE t.start_date IS NOT NULL AND t.completion_date IS NOT NULL
WITH t, duration.between(t.start_date, t.completion_date).months AS duration_months
RETURN tp.name AS phase,
       avg(duration_months) AS avg_duration,
       min(duration_months) AS min_duration,
       max(duration_months) AS max_duration,
       count(t) AS trial_count
FROM t:ClinicalTrial
LEFT JOIN t:HAS_PHASE->tp:TrialPhase
GROUP BY tp.name
ORDER BY tp.order;

// Q11.3: 入组完成率分析
MATCH (t:ClinicalTrial)
WHERE t.enrollment IS NOT NULL
MATCH (t)<-[:ENROLLED_IN]-(s:Subject)
WITH t, count(s) AS actual_enrollment
RETURN t.trial_id, t.title, t.enrollment AS target_enrollment,
       actual_enrollment,
       (actual_enrollment * 100.0 / t.enrollment) AS enrollment_rate_percent
ORDER BY enrollment_rate_percent DESC;

// Q11.4: 试验设计模式分析
MATCH (t:ClinicalTrial)
RETURN t.allocation AS allocation_type,
       t.masking AS masking_type,
       count(t) AS trial_count
ORDER BY trial_count DESC;

//===========================================================
// 12. 跨试验比较查询
//===========================================================

// Q12.1: 比较同一疾病的不同试验设计
MATCH (c:Condition)<-[:STUDIES_CONDITION]-(t:ClinicalTrial)
WHERE c.condition_name = 'Non-Small Cell Lung Cancer'
RETURN t.trial_id, t.title, t.phase, t.study_type, t.allocation, t.masking, t.enrollment
ORDER BY t.phase, t.start_date DESC;

// Q12.2: 查询相同干预措施的试验
MATCH (i:Intervention)
WHERE i.intervention_name = 'Drug X'
MATCH (i)-[:INTERVENTION_OF]->(t:ClinicalTrial)
RETURN t.trial_id, t.title, t.phase, t.status, i.dosage, i.route
ORDER BY t.phase, t.start_date;

// Q12.3: 查询相同终点的试验
MATCH (o:Outcome)
WHERE o.title CONTAINS 'Progression-Free Survival'
MATCH (o)-[:OUTCOME_OF]->(t:ClinicalTrial)
RETURN t.trial_id, t.title, o.title, o.time_frame
ORDER BY t.start_date DESC;

//===========================================================
// 13. 数据质量检查
//===========================================================

// Q13.1: 查找缺失入组人数的试验
MATCH (t:ClinicalTrial)
WHERE t.enrollment IS NULL
RETURN t.trial_id, t.title, t.phase, t.status
LIMIT 50;

// Q13.2: 查找缺失日期信息的试验
MATCH (t:ClinicalTrial)
WHERE t.start_date IS NULL OR t.completion_date IS NULL
RETURN t.trial_id, t.title, t.start_date, t.completion_date
LIMIT 50;

// Q13.3: 查找无干预措施的试验
MATCH (t:ClinicalTrial)
WHERE NOT (t)-[:HAS_INTERVENTION]->(:Intervention)
RETURN t.trial_id, t.title, t.study_type
LIMIT 50;

// Q13.4: 查找无结局指标的试验
MATCH (t:ClinicalTrial)
WHERE NOT (t)-[:HAS_PRIMARY_OUTCOME|HAS_SECONDARY_OUTCOME]->(:Outcome)
RETURN t.trial_id, t.title, t.phase
LIMIT 50;

//===========================================================
// 14. 受试者安全性分析
//===========================================================

// Q14.1: 试验不良事件发生率
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})
OPTIONAL MATCH (t)-[:REPORTS_ADVERSE_EVENT]->(ae:AdverseEvent)
OPTIONAL MATCH (t)<-[:ENROLLED_IN]-(s:Subject)
WITH t, count(DISTINCT ae) AS total_ae, count(DISTINCT s) AS total_subjects
RETURN total_ae, total_subjects,
       (total_ae * 1.0 / total_subjects) AS ae_per_subject;

// Q14.2: 严重不良事件率
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})-[:REPORTS_ADVERSE_EVENT]->(ae:AdverseEvent)
WHERE ae.seriousness = 'serious'
MATCH (t)<-[:ENROLLED_IN]-(s:Subject)
WITH count(DISTINCT ae) AS sae_count, count(DISTINCT s) AS total_subjects
RETURN sae_count, total_subjects,
       (sae_count * 100.0 / total_subjects) AS sae_rate_percent;

// Q14.3: 不良事件导致退出的分析
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})<-[:ENROLLED_IN]-(s:Subject)
WHERE s.withdrawal_reason IS NOT NULL
MATCH (s)-[:EXPERIENCED_AE]->(ae:AdverseEvent)
RETURN s.subject_id, s.withdrawal_date, ae.meddra_term, ae.severity
ORDER BY s.withdrawal_date;

//===========================================================
// 15. 时间线分析
//===========================================================

// Q15.1: 试验启动时间趋势（按月）
MATCH (t:ClinicalTrial)
WHERE t.start_date IS NOT NULL
WITH t.start_date.year AS year, t.start_date.month AS month, count(t) AS new_trials
RETURN year, month, new_trials
ORDER BY year DESC, month DESC
LIMIT 24;

// Q15.2: 试验完成时间趋势
MATCH (t:ClinicalTrial)
WHERE t.completion_date IS NOT NULL
WITH t.completion_date.year AS year, count(t) AS completed_trials
RETURN year, completed_trials
ORDER BY year DESC
LIMIT 10;

// Q15.3: 试验状态变化追踪
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'})
RETURN t.trial_id,
       t.start_date AS started,
       t.primary_completion_date AS primary_completed,
       t.completion_date AS completed,
       t.status AS current_status;

//===========================================================
// 16. 综合分析查询
//===========================================================

// Q16.1: 疾病-试验-干预措施全景图
MATCH (c:Condition)<-[:STUDIES_CONDITION]-(t:ClinicalTrial)-[:HAS_INTERVENTION]->(i:Intervention)
WHERE c.condition_name = 'COVID-19'
RETURN c.condition_name AS disease,
       collect(DISTINCT {
           trial_id: t.trial_id,
           title: t.title,
           phase: t.phase,
           status: t.status,
           intervention: i.intervention_name,
           type: i.intervention_type
       }) AS trials
LIMIT 1;

// Q16.2: 药物-疾病-试验关联网络
MATCH (i:Intervention)-[:INTERVENTION_OF]->(t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
WHERE i.intervention_type = 'drug'
WITH i.intervention_name AS drug, c.condition_name AS disease, count(DISTINCT t) AS trial_count
WHERE trial_count > 0
RETURN drug, disease, trial_count
ORDER BY trial_count DESC
LIMIT 50;

// Q16.3: 试验设计特征汇总
MATCH (t:ClinicalTrial)
RETURN t.phase,
       t.study_type,
       t.allocation,
       t.masking,
       t.purpose,
       count(t) AS trial_count
ORDER BY t.phase, count(t) DESC;

//===========================================================
// 查询示例结束
//===========================================================
