//===========================================================
// 制药行业知识图谱 - 供应链与监管领域示例查询
// Pharmaceutical Knowledge Graph - Supply Chain & Regulatory Example Queries
//===========================================================
// 版本: v1.0
// 创建日期: 2025-02-06
// 描述: 供应链与监管领域常用Cypher查询示例
//===========================================================

//===========================================================
// ============================================================
// 供应链领域查询 (Supply Chain Queries)
// ============================================================
//===========================================================

//===========================================================
// 1. 制造商查询
//===========================================================

// Q1.1: 查询所有制造商数量
MATCH (m:Manufacturer)
RETURN count(m) AS total_manufacturers;

// Q1.2: 按制造商类型统计
MATCH (m:Manufacturer)-[:HAS_MANUFACTURER_TYPE]->(mt:ManufacturerType)
RETURN mt.name AS manufacturer_type, count(m) AS manufacturer_count
ORDER BY manufacturer_count DESC;

// Q1.3: 按国家统计制造商分布
MATCH (m:Manufacturer)
RETURN m.country AS country, count(m) AS manufacturer_count
ORDER BY manufacturer_count DESC
LIMIT 20;

// Q1.4: 查询一体化制造商
MATCH (m:Manufacturer)-[:HAS_MANUFACTURER_TYPE]->(mt:ManufacturerType)
WHERE mt.id = 'integrated'
RETURN m.manufacturer_id, m.name, m.city, m.country, m.website
ORDER BY m.name;

// Q1.5: 查询合同生产组织(CMO)
MATCH (m:Manufacturer)-[:HAS_MANUFACTURER_TYPE]->(mt:ManufacturerType)
WHERE mt.id = 'contract'
RETURN m.manufacturer_id, m.name, m.country, m.website
ORDER BY m.name;

//===========================================================
// 2. 药品短缺分析
//===========================================================

// Q2.1: 查询所有活跃的药品短缺
MATCH (ds:DrugShortage)-[:HAS_SHORTAGE_STATUS]->(ss:ShortageStatus)
WHERE ss.id = 'active'
RETURN ds.shortage_id, ds.drug_name, ds.start_date, ds.affected_region
ORDER BY ds.start_date DESC;

// Q2.2: 按短缺原因统计
MATCH (ds:DrugShortage)-[:HAS_SHORTAGE_REASON]->(sr:ShortageReason)
RETURN sr.name AS reason, count(ds) AS shortage_count
ORDER BY shortage_count DESC;

// Q2.3: 查询严重影响的药品短缺
MATCH (ds:DrugShortage)-[:HAS_IMPACT_LEVEL]->(il:ImpactLevel)
WHERE il.id = 'critical'
RETURN ds.drug_name, ds.shortage_type, ds.affected_region, ds.start_date
ORDER BY ds.start_date DESC;

// Q2.4: 按制造商统计短缺数量
MATCH (ds:DrugShortage)-[:HAS_AFFECTED_MANUFACTURER]->(m:Manufacturer)
RETURN m.name AS manufacturer, count(ds) AS shortage_count
ORDER BY shortage_count DESC;

// Q2.5: 查询已解决的短缺及持续时间
MATCH (ds:DrugShortage)-[:HAS_SHORTAGE_STATUS]->(ss:ShortageStatus)
WHERE ss.id = 'resolved'
AND ds.end_date IS NOT NULL
RETURN ds.drug_name, ds.start_date, ds.end_date,
       duration.between(ds.start_date, ds.end_date).days AS duration_days
ORDER BY duration_days DESC;

//===========================================================
// 3. 供应商分析
//===========================================================

// Q3.1: 查询原料药供应商
MATCH (s:Supplier)-[:HAS_SUPPLIER_TYPE]->(st:SupplierType)
WHERE st.id = 'api'
RETURN s.supplier_id, s.name, s.rating
ORDER BY s.name;

// Q3.2: 查询辅料供应商
MATCH (s:Supplier)-[:HAS_SUPPLIER_TYPE]->(st:SupplierType)
WHERE st.id = 'excipient'
RETURN s.supplier_id, s.name, s.rating
ORDER BY s.name;

// Q3.3: 查询供应商类型分布
MATCH (s:Supplier)-[:HAS_SUPPLIER_TYPE]->(st:SupplierType)
RETURN st.name AS supplier_type, count(s) AS supplier_count
ORDER BY supplier_count DESC;

//===========================================================
// ============================================================
// 监管合规领域查询 (Regulatory Queries)
// ============================================================
//===========================================================

//===========================================================
// 4. 申报分析
//===========================================================

// Q4.1: 查询所有申报数量
MATCH (sub:Submission)
RETURN count(sub) AS total_submissions;

// Q4.2: 按申报类型统计
MATCH (sub:Submission)-[:HAS_SUBMISSION_TYPE]->(st:SubmissionType)
RETURN st.name AS submission_type, count(sub) AS submission_count
ORDER BY submission_count DESC;

// Q4.3: 按申报状态统计
MATCH (sub:Submission)-[:HAS_SUBMISSION_STATUS]->(sst:SubmissionStatus)
RETURN sst.name AS status, count(sub) AS submission_count
ORDER BY submission_count DESC;

// Q4.4: 查询审评中的申报
MATCH (sub:Submission)-[:HAS_SUBMISSION_STATUS]->(sst:SubmissionStatus)
WHERE sst.id = 'under_review'
RETURN sub.submission_id, sub.submission_type, sub.drug_name,
       sub.submission_date, sub.review_days
ORDER BY sub.submission_date;

// Q4.5: 按审评优先级统计
MATCH (sub:Submission)-[:HAS_REVIEW_PRIORITY]->(rp:ReviewPriority)
RETURN rp.name AS priority, count(sub) AS submission_count
ORDER BY submission_count DESC;

// Q4.6: 查询优先审评的申报
MATCH (sub:Submission)-[:HAS_REVIEW_PRIORITY]->(rp:ReviewPriority)
WHERE rp.id IN ['priority', 'accelerated', 'fast_track', 'breakthrough']
RETURN sub.submission_id, sub.submission_type, sub.drug_name,
       rp.name AS priority, sub.submission_date, sub.status
ORDER BY rp.order, sub.submission_date;

//===========================================================
// 5. 批准分析
//===========================================================

// Q5.1: 查询所有批准数量
MATCH (ap:Approval)
RETURN count(ap) AS total_approvals;

// Q5.2: 按批准类型统计
MATCH (ap:Approval)-[:HAS_APPROVAL_TYPE]->(apt:ApprovalType)
RETURN apt.name AS approval_type, count(ap) AS approval_count
ORDER BY approval_count DESC;

// Q5.3: 按批准状态统计
MATCH (ap:Approval)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus)
RETURN aps.name AS status, count(ap) AS approval_count
ORDER BY approval_count DESC;

// Q5.4: 查询活跃的批准
MATCH (ap:Approval)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus)
WHERE aps.id = 'active'
RETURN ap.approval_number, ap.drug_name, ap.approval_type,
       ap.approval_date, ap.expiration_date, ap.indication
ORDER BY ap.approval_date DESC
LIMIT 50;

// Q5.5: 查询即将过期的批准
MATCH (ap:Approval)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus)
WHERE aps.id = 'active'
  AND ap.expiration_date < date() + duration('P180D')
RETURN ap.approval_number, ap.drug_name, ap.expiration_date,
       ap.holder, ap.issued_by_agency
ORDER BY ap.expiration_date;

// Q5.6: 查询加速批准
MATCH (ap:Approval)-[:HAS_APPROVAL_TYPE]->(apt:ApprovalType)
WHERE apt.id IN ['accelerated', 'tentative', 'emergency']
RETURN ap.approval_number, ap.drug_name, apt.name AS approval_type,
       ap.approval_date, ap.indication
ORDER BY ap.approval_date DESC;

//===========================================================
// 6. 审评周期分析
//===========================================================

// Q6.1: 计算平均审评周期
MATCH (sub:Submission)
WHERE sub.review_days IS NOT NULL
MATCH (sub)-[:HAS_SUBMISSION_TYPE]->(st:SubmissionType)
RETURN st.name AS submission_type,
       avg(sub.review_days) AS avg_review_days,
       min(sub.review_days) AS min_days,
       max(sub.review_days) AS max_days,
       count(sub) AS submission_count
ORDER BY avg_review_days;

// Q6.2: 按年份统计批准数量
MATCH (ap:Approval)
WHERE ap.approval_date IS NOT NULL
WITH ap.approval_date.year AS year, count(ap) AS approval_count
RETURN year, approval_count
ORDER BY year DESC
LIMIT 10;

// Q6.3: 申报审评周期分布
MATCH (sub:Submission)
WHERE sub.review_days IS NOT NULL
RETURN sub.submission_type,
       CASE
         WHEN sub.review_days <= 180 THEN '≤6 months'
         WHEN sub.review_days <= 365 THEN '6-12 months'
         WHEN sub.review_days <= 540 THEN '12-18 months'
         ELSE '>18 months'
       END AS review_period,
       count(sub) AS submission_count
ORDER BY sub.submission_type, review_period;

//===========================================================
// 7. 检查分析
//===========================================================

// Q7.1: 查询所有检查数量
MATCH (ins:Inspection)
RETURN count(ins) AS total_inspections;

// Q7.2: 按检查类型统计
MATCH (ins:Inspection)-[:HAS_INSPECTION_TYPE]->(it:InspectionType)
RETURN it.name AS inspection_type, count(ins) AS inspection_count
ORDER BY inspection_count DESC;

// Q7.3: 按检查结果统计
MATCH (ins:Inspection)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
RETURN irt.name AS result, count(ins) AS inspection_count
ORDER BY irt.order;

// Q7.4: 查询需要官方行动的检查
MATCH (ins:Inspection)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
WHERE irt.id = 'oai'
RETURN ins.inspection_id, ins.facility_name, ins.inspection_type,
       ins.classification, ins.inspection_date, ins.inspector
ORDER BY ins.inspection_date DESC;

// Q7.5: 查询最近的有因检查
MATCH (ins:Inspection)-[:HAS_CLASSIFICATION]->(ic:InspectionClassification)
WHERE ic.id = 'fc'
RETURN ins.inspection_id, ins.facility_name, ins.inspection_date,
       ins.result, ins.inspector
ORDER BY ins.inspection_date DESC;

//===========================================================
// 8. 合规行动分析
//===========================================================

// Q8.1: 查询所有合规行动数量
MATCH (ca:ComplianceAction)
RETURN count(ca) AS total_actions;

// Q8.2: 按行动类型统计
MATCH (ca:ComplianceAction)-[:HAS_ACTION_TYPE]->(cat:ComplianceActionType)
RETURN cat.name AS action_type, count(ca) AS action_count
ORDER BY action_count DESC;

// Q8.3: 查询活跃的合规行动
MATCH (ca:ComplianceAction)
WHERE ca.status = 'active'
RETURN ca.action_id, cat.name AS action_type, ca.action_date,
       ca.reason, ca.severity
ORDER BY ca.action_date DESC;

// Q8.4: 按制造商统计合规行动
MATCH (ca:ComplianceAction)-[:AGAINST_MANUFACTURER]->(m:Manufacturer)
RETURN m.name AS manufacturer, count(ca) AS action_count
ORDER BY action_count DESC
LIMIT 20;

// Q8.5: 查询严重合规行动
MATCH (ca:ComplianceAction)
WHERE ca.severity IN ('serious', 'severe')
RETURN ca.action_id, ca.action_type, ca.action_date,
       ca.reason, m.name AS manufacturer
FROM ca
LEFT JOIN ca-AGAINST_MANUFACTURER->m:Manufacturer
ORDER BY ca.action_date DESC;

//===========================================================
// 9. 上市后承诺分析
//===========================================================

// Q9.1: 查询所有PMC数量
MATCH (pmc:PostMarketingCommitment)
RETURN count(pmc) AS total_pmcs;

// Q9.2: 按PMC类型统计
MATCH (pmc:PostMarketingCommitment)-[:HAS_PMC_TYPE]->(pmt:PMCType)
RETURN pmt.name AS pmc_type, count(pmc) AS pmc_count
ORDER BY pmc_count DESC;

// Q9.3: 按PMC状态统计
MATCH (pmc:PostMarketingCommitment)-[:HAS_STATUS]->(pmcs:PMCStatus)
RETURN pmcs.name AS status, count(pmc) AS pmc_count
ORDER BY pmc_count DESC;

// Q9.4: 查询延期未完成的PMC
MATCH (pmc:PostMarketingCommitment)-[:HAS_STATUS]->(pmcs:PMCStatus)
WHERE pmcs.id IN ['pending', 'in_progress', 'delayed']
  AND pmc.due_date < date()
RETURN pmc.pmc_id, pmc.description, pmc.due_date,
       duration.between(date(), pmc.due_date).days AS overdue_days,
       pmcs.name AS status
ORDER BY overdue_days DESC;

// Q9.5: 查询与指定药品相关的PMC
MATCH (pmc:PostMarketingCommitment)-[:PMC_FOR_DRUG]->(c:Compound {name: 'Drug X'})
RETURN pmc.pmc_id, pmc.pmc_type, pmc.description,
       pmc.submitted_date, pmc.due_date, pmc.status
ORDER BY pmc.due_date;

//===========================================================
// 10. 安全性信号分析
//===========================================================

// Q10.1: 查询所有安全性信号数量
MATCH (ss:SafetySignal)
RETURN count(ss) AS total_signals;

// Q10.2: 按信号类型统计
MATCH (ss:SafetySignal)-[:HAS_SIGNAL_TYPE]->(sgt:SignalType)
RETURN sgt.name AS signal_type, count(ss) AS signal_count
ORDER BY signal_count DESC;

// Q10.3: 按信号状态统计
MATCH (ss:SafetySignal)-[:HAS_SIGNAL_STATUS]->(sgst:SignalStatus)
RETURN sgst.name AS status, count(ss) AS signal_count
ORDER BY signal_count DESC;

// Q10.4: 查询调查中的严重信号
MATCH (ss:SafetySignal)-[:HAS_SIGNAL_STATUS]->(sgst:SignalStatus)
WHERE sgst.id = 'under_investigation'
MATCH (ss)-[:HAS_SIGNAL_SEVERITY]->(sgs:SignalSeverity)
WHERE sgs.id = 'serious'
RETURN ss.signal_id, ss.signal_type, ss.detection_date,
       ss.description, c.name AS drug
FROM ss
LEFT JOIN ss-RELATED_TO_DRUG->c:Compound
ORDER BY ss.detection_date DESC;

// Q10.5: 按药品统计安全性信号
MATCH (ss:SafetySignal)-[:RELATED_TO_DRUG]->(c:Compound)
WITH c.name AS drug, count(ss) AS signal_count
WHERE signal_count > 0
RETURN drug, signal_count
ORDER BY signal_count DESC
LIMIT 20;

//===========================================================
// 11. 跨域综合查询
//===========================================================

// Q11.1: 查询制造商的监管检查记录
MATCH (m:Manufacturer)<-[:INSPECTS_FACILITY]-(f:Facility)<-[:INSPECTS]-(ins:Inspection)
RETURN m.name AS manufacturer,
       collect({
         inspection_id: ins.inspection_id,
         inspection_type: ins.inspection_type,
         inspection_date: ins.inspection_date,
         result: ins.result
       }) AS inspections
ORDER BY m.name;

// Q11.2: 查询制造商的合规行动历史
MATCH (m:Manufacturer)<-[:AGAINST_MANUFACTURER]-(ca:ComplianceAction)
RETURN m.name AS manufacturer,
       collect({
         action_id: ca.action_id,
         action_type: ca.action_type,
         action_date: ca.action_date,
         reason: ca.reason,
         status: ca.status
       }) AS compliance_actions
ORDER BY m.name;

// Q11.3: 药品短缺与监管行动关联分析
MATCH (ds:DrugShortage)-[:HAS_SHORTAGE_REASON]->(sr:ShortageReason)
WHERE sr.id = 'regulatory'
MATCH (ca:ComplianceAction)
WHERE ca.action_date >= ds.start_date
  AND (ca.action_date <= ds.end_date OR ds.end_date IS NULL)
RETURN ds.drug_name AS drug,
       ds.shortage_type,
       sr.name AS shortage_reason,
       collect(DISTINCT ca.action_type) AS related_actions;

// Q11.4: 查询制造商的批准药品
MATCH (m:Manufacturer)
OPTIONAL MATCH (m)-[:MANUFACTURES_DRUG]->(c:Compound)<-[:APPROVAL_FOR_DRUG]-(ap:Approval)-[:ISSUED_BY]->(ra:RegulatoryAgency)
RETURN m.name AS manufacturer,
       collect(DISTINCT {
         drug: c.name,
         approval_number: ap.approval_number,
         approval_date: ap.approval_date,
         agency: ra.abbreviation
       }) AS approvals
ORDER BY m.name;

// Q11.5: 监管机构统计
MATCH (ra:RegulatoryAgency)
RETURN ra.abbreviation AS agency,
       ra.name AS full_name,
       ra.type AS agency_type,
       ra.jurisdiction,
       size((ra)-[:REVIEWS_SUBMISSION]->()) AS submissions_reviewed,
       size((ra)-[:ISSUES_APPROVAL]->()) AS approvals_issued,
       size((ra)-[:CONDUCTS_INSPECTION]->()) AS inspections_conducted
ORDER BY agency;

//===========================================================
// 12. 复杂分析查询
//===========================================================

// Q12.1: 审评效率分析（按申报类型和优先级）
MATCH (sub:Submission)-[:HAS_SUBMISSION_TYPE]->(st:SubmissionType)
MATCH (sub)-[:HAS_REVIEW_PRIORITY]->(rp:ReviewPriority)
WHERE sub.approval_date IS NOT NULL
WITH st.name AS submission_type, rp.name AS priority,
     avg(sub.review_days) AS avg_days,
     count(sub) AS submission_count
RETURN submission_type, priority, avg_days, submission_count
ORDER BY submission_type, rp.order;

// Q12.2: 制造商合规评分
MATCH (m:Manufacturer)
OPTIONAL MATCH (m)<-[:INSPECTS_FACILITY]-(f:Facility)<-[:INSPECTS]-(ins:Inspection)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
WITH m.name AS manufacturer,
     count(CASE WHEN irt.id = 'nai' THEN 1 END) AS nai_count,
     count(CASE WHEN irt.id = 'vai' THEN 1 END) AS vai_count,
     count(CASE WHEN irt.id = 'oai' THEN 1 END) AS oai_count,
     count(ins) AS total_inspections
RETURN manufacturer, total_inspections, nai_count, vai_count, oai_count,
       CASE
         WHEN oai_count > 0 THEN 'High Risk'
         WHEN vai_count > 0 THEN 'Medium Risk'
         ELSE 'Low Risk'
       END AS risk_level
ORDER BY risk_level, oai_count DESC;

// Q12.3: 药品供应链风险评估
MATCH (ds:DrugShortage)-[:HAS_AFFECTED_MANUFACTURER]->(m:Manufacturer)
OPTIONAL MATCH (m)<-[:INSPECTS_FACILITY]-(f:Facility)<-[:INSPECTS]-(ins:Inspection)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult)
OPTIONAL MATCH (m)<-[:AGAINST_MANUFACTURER]-(ca:ComplianceAction)
WITH ds.drug_name AS drug,
       ds.shortage_type,
       m.name AS manufacturer,
       collect(DISTINCT irt.name) AS inspection_results,
       size((ca)-[:AGAINST_MANUFACTURER]->(m)) AS compliance_actions
RETURN drug, shortage_type, manufacturer,
       inspection_results,
       compliance_actions,
       CASE
         WHEN 'Official Action Indicated' IN inspection_results OR compliance_actions > 0 THEN 'High Risk'
         WHEN 'Voluntary Action Indicated' IN inspection_results THEN 'Medium Risk'
         ELSE 'Low Risk'
       END AS supply_chain_risk
ORDER BY supply_chain_risk, drug;

// Q12.4: 监管时间线分析
MATCH (sub:Submission)
WHERE sub.submission_date IS NOT NULL AND sub.approval_date IS NOT NULL
MATCH (sub)-[:RESULTS_IN_APPROVAL]->(ap:Approval)
MATCH (sub)-[:SUBMITTED_TO]->(ra:RegulatoryAgency)
WITH sub.submission_id AS submission_id,
       sub.drug_name AS drug,
       ra.abbreviation AS agency,
       sub.submission_date AS submitted,
       sub.approval_date AS approved,
       ap.approval_type AS approval_type,
       duration.between(sub.submission_date, sub.approval_date).days AS review_days
RETURN submission_id, drug, agency, submitted, approved,
       approval_type, review_days
ORDER BY approved DESC
LIMIT 50;

//===========================================================
// 13. 数据质量检查
//===========================================================

// Q13.1: 查找无FEI代码的制造商
MATCH (m:Manufacturer)
WHERE m.fei_code IS NULL
RETURN m.manufacturer_id, m.name, m.country
LIMIT 50;

// Q13.2: 查找无检查结果的检查记录
MATCH (ins:Inspection)
WHERE ins.result IS NULL
RETURN ins.inspection_id, ins.facility_name, ins.inspection_date
LIMIT 50;

// Q13.3: 查找无批准日期的批准
MATCH (ap:Approval)
WHERE ap.approval_date IS NULL
RETURN ap.approval_id, ap.approval_number, ap.drug_name
LIMIT 50;

// Q13.4: 查找无过期日期的活跃批准
MATCH (ap:Approval)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus)
WHERE aps.id = 'active' AND ap.expiration_date IS NULL
RETURN ap.approval_id, ap.approval_number, ap.drug_name
LIMIT 50;

// Q13.5: 查找无描述的PMC
MATCH (pmc:PostMarketingCommitment)
WHERE pmc.description IS NULL OR pmc.description = ''
RETURN pmc.pmc_id, pmc.status, pmc.due_date
LIMIT 50;

//===========================================================
// 14. 统计报表
//===========================================================

// Q14.1: 供应链统计报表
MATCH (m:Manufacturer)
WITH count(m) AS total_mfr,
     count(DISTINCT m.country) AS countries
RETURN 'Manufacturers' AS metric, total_mfr AS count, countries AS unique_countries
UNION ALL
MATCH (ds:DrugShortage)
WITH count(ds) AS total_shortages,
     count(CASE WHEN ds.end_date IS NULL THEN 1 END) AS active_shortages
RETURN 'Drug Shortages' AS metric, total_shortages AS count, active_shortages AS active
UNION ALL
MATCH (s:Supplier)
RETURN 'Suppliers' AS metric, count(s) AS count, null AS unique_countries
ORDER BY metric;

// Q14.2: 监管统计报表
MATCH (sub:Submission)
WITH count(sub) AS total_submissions,
     count(CASE WHEN sub.status = 'approved' THEN 1 END) AS approved
RETURN 'Submissions' AS metric, total_submissions AS total, approved AS approved_count
UNION ALL
MATCH (ap:Approval)
WITH count(ap) AS total_approvals,
     count(CASE WHEN ap.status = 'active' THEN 1 END) AS active
RETURN 'Approvals' AS metric, total_approvals AS total, active AS active_count
UNION ALL
MATCH (ins:Inspection)
WITH count(ins) AS total_inspections,
     count(CASE WHEN ins.result = 'nai' THEN 1 END) AS nai_count
RETURN 'Inspections' AS metric, total_inspections AS total, nai_count AS compliant_count
UNION ALL
MATCH (ca:ComplianceAction)
WITH count(ca) AS total_actions,
     count(CASE WHEN ca.status = 'active' THEN 1 END) AS active
RETURN 'Compliance Actions' AS metric, total_actions AS total, active AS active_count
ORDER BY metric;

//===========================================================
// 15. 时间趋势分析
//===========================================================

// Q15.1: 申报提交趋势（按月）
MATCH (sub:Submission)
WHERE sub.submission_date IS NOT NULL
WITH sub.submission_date.year AS year, sub.submission_date.month AS month,
     count(sub) AS submissions
RETURN year, month, submissions
ORDER BY year DESC, month DESC
LIMIT 24;

// Q15.2: 药品短缺趋势
MATCH (ds:DrugShortage)
WHERE ds.start_date IS NOT NULL
WITH ds.start_date.year AS year, count(ds) AS shortages
RETURN year, shortages
ORDER BY year DESC
LIMIT 10;

// Q15.3: 合规行动趋势
MATCH (ca:ComplianceAction)
WHERE ca.action_date IS NOT NULL
WITH ca.action_date.year AS year, count(ca) AS actions
RETURN year, actions
ORDER BY year DESC
LIMIT 10;

//===========================================================
// 查询示例结束
//===========================================================
