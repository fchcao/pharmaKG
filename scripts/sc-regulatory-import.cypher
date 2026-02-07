//===========================================================
// 制药行业知识图谱 - 供应链与监管领域数据导入脚本
// Pharmaceutical Knowledge Graph - Supply Chain & Regulatory Data Import
//===========================================================
// 版本: v1.0
// 创建日期: 2025-02-06
// 描述: 导入供应链与监管领域核心实体和关系到Neo4j
//===========================================================

:auto

//===========================================================
// 1. 创建唯一性约束和索引
//===========================================================

// Manufacturer 约束
CREATE CONSTRAINT manufacturer_id IF NOT EXISTS FOR (m:Manufacturer) REQUIRE m.manufacturer_id IS UNIQUE;
CREATE INDEX manufacturer_name IF NOT EXISTS FOR (m:Manufacturer) ON (m.manufacturer_name);
CREATE INDEX manufacturer_country IF NOT EXISTS FOR (m:Manufacturer) ON (m.country);
CREATE INDEX manufacturer_type IF NOT EXISTS FOR (m:Manufacturer) ON (m.manufacturer_type);

// Supplier 约束
CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.supplier_id IS UNIQUE;
CREATE INDEX supplier_name IF NOT EXISTS FOR (s:Supplier) ON (s.supplier_name);

// DrugShortage 约束
CREATE CONSTRAINT shortage_id IF NOT EXISTS FOR (ds:DrugShortage) REQUIRE ds.shortage_id IS UNIQUE;
CREATE INDEX shortage_status IF NOT EXISTS FOR (ds:DrugShortage) ON (ds.shortage_status);
CREATE INDEX shortage_start IF NOT EXISTS FOR (ds:DrugShortage) ON (ds.start_date);

// RegulatoryAgency 约束
CREATE CONSTRAINT agency_id IF NOT EXISTS FOR (ra:RegulatoryAgency) REQUIRE ra.agency_id IS UNIQUE;
CREATE INDEX agency_abbr IF NOT EXISTS FOR (ra:RegulatoryAgency) ON (ra.agency_abbreviation);

// Submission 约束
CREATE CONSTRAINT submission_id IF NOT EXISTS FOR (sub:Submission) REQUIRE sub.submission_id IS UNIQUE;
CREATE INDEX submission_status IF NOT EXISTS FOR (sub:Submission) ON (sub.submission_status);
CREATE INDEX submission_date IF NOT EXISTS FOR (sub:Submission) ON (sub.submission_date);
CREATE INDEX submission_type IF NOT EXISTS FOR (sub:Submission) ON (sub.submission_type);

// Approval 约束
CREATE CONSTRAINT approval_id IF NOT EXISTS FOR (ap:Approval) REQUIRE ap.approval_id IS UNIQUE;
CREATE INDEX approval_number IF NOT EXISTS FOR (ap:Approval) ON (ap.approval_number);
CREATE INDEX approval_date IF NOT EXISTS FOR (ap:Approval) ON (ap.approval_date);

// Inspection 约束
CREATE CONSTRAINT inspection_id IF NOT EXISTS FOR (i:Inspection) REQUIRE i.inspection_id IS UNIQUE;
CREATE INDEX inspection_result IF NOT EXISTS FOR (i:Inspection) ON (i.inspection_result);
CREATE INDEX inspection_date IF NOT EXISTS FOR (i:Inspection) ON (i.inspection_date);

//===========================================================
// 2. 创建枚举节点 - 供应链
//===========================================================

// ManufacturerType 枚举
MERGE (mt1:ManufacturerType {id: 'api', name: 'API Manufacturer'});
MERGE (mt2:ManufacturerType {id: 'formulation', name: 'Formulation Manufacturer'});
MERGE (mt3:ManufacturerType {id: 'contract', name: 'Contract Manufacturing Organization'});
MERGE (mt4:ManufacturerType {id: 'integrated', name: 'Integrated Manufacturer'});

// SupplierType 枚举
MERGE (st1:SupplierType {id: 'api', name: 'API Supplier'});
MERGE (st2:SupplierType {id: 'excipient', name: 'Excipient Supplier'});
MERGE (st3:SupplierType {id: 'packaging', name: 'Packaging Supplier'});
MERGE (st4:SupplierType {id: 'equipment', name: 'Equipment Supplier'});

// ShortageType 枚举
MERGE (sht1:ShortageType {id: 'supply', name: 'Supply Issue'});
MERGE (sht2:ShortageType {id: 'demand', name: 'Demand Increase'});
MERGE (sht3:ShortageType {id: 'quality', name: 'Quality Issue'});
MERGE (sht4:ShortageType {id: 'regulatory', name: 'Regulatory Issue'});

// ShortageReason 枚举
MERGE (shr1:ShortageReason {id: 'manufacturing', name: 'Manufacturing Problem'});
MERGE (shr2:ShortageReason {id: 'raw_material', name: 'Raw Material Shortage'});
MERGE (shr3:ShortageReason {id: 'quality', name: 'Quality Control Failure'});
MERGE (shr4:ShortageReason {id: 'regulatory', name: 'Regulatory Action'});
MERGE (shr5:ShortageReason {id: 'logistics', name: 'Logistics Issue'});
MERGE (shr6:ShortageReason {id: 'business', name: 'Business Decision'});

// ShortageStatus 枚举
MERGE (shs1:ShortageStatus {id: 'active', name: 'Active'});
MERGE (shs2:ShortageStatus {id: 'resolved', name: 'Resolved'});
MERGE (shs3:ShortageStatus {id: 'mitigated', name: 'Mitigated'});

// ImpactLevel 枚举
MERGE (il1:ImpactLevel {id: 'critical', name: 'Critical', order: 3});
MERGE (il2:ImpactLevel {id: 'moderate', name: 'Moderate', order: 2});
MERGE (il3:ImpactLevel {id: 'minor', name: 'Minor', order: 1});

//===========================================================
// 3. 创建枚举节点 - 监管
//===========================================================

// AgencyType 枚举
MERGE (at1:AgencyType {id: 'national', name: 'National Agency'});
MERGE (at2:AgencyType {id: 'regional', name: 'Regional Agency'});
MERGE (at3:AgencyType {id: 'international', name: 'International Agency'});

// SubmissionType 枚举
MERGE (sut1:SubmissionType {id: 'nda', name: 'NDA'});
MERGE (sut2:SubmissionType {id: 'anda', name: 'ANDA'});
MERGE (sut3:SubmissionType {id: 'bla', name: 'BLA'});
MERGE (sut4:SubmissionType {id: 'maa', name: 'MAA'});
MERGE (sut5:SubmissionType {id: 'snda', name: 'sNDA'});
MERGE (sut6:SubmissionType {id: 'sbla', name: 'sBLA'});

// SubmissionStatus 枚举
MERGE (sust1:SubmissionStatus {id: 'submitted', name: 'Submitted'});
MERGE (sust2:SubmissionStatus {id: 'under_review', name: 'Under Review'});
MERGE (sust3:SubmissionStatus {id: 'clock_stopped', name: 'Clock Stopped'});
MERGE (sust4:SubmissionStatus {id: 'approved', name: 'Approved'});
MERGE (sust5:SubmissionStatus {id: 'rejected', name: 'Rejected'});
MERGE (sust6:SubmissionStatus {id: 'withdrawn', name: 'Withdrawn'});

// ReviewPriority 枚举
MERGE (rp1:ReviewPriority {id: 'standard', name: 'Standard Review'});
MERGE (rp2:ReviewPriority {id: 'priority', name: 'Priority Review'});
MERGE (rp3:ReviewPriority {id: 'accelerated', name: 'Accelerated Approval'});
MERGE (rp4:ReviewPriority {id: 'fast_track', name: 'Fast Track'});
MERGE (rp5:ReviewPriority {id: 'breakthrough', name: 'Breakthrough Therapy'});
MERGE (rp6:ReviewPriority {id: 'rolling', name: 'Rolling Review'});

// ApprovalType 枚举
MERGE (apt1:ApprovalType {id: 'full', name: 'Full Approval'});
MERGE (apt2:ApprovalType {id: 'accelerated', name: 'Accelerated Approval'});
MERGE (apt3:ApprovalType {id: 'tentative', name: 'Tentative Approval'});
MERGE (apt4:ApprovalType {id: 'emergency', name: 'Emergency Use Authorization'});

// ApprovalStatus 枚举
MERGE (aps1:ApprovalStatus {id: 'active', name: 'Active'});
MERGE (aps2:ApprovalStatus {id: 'suspended', name: 'Suspended'});
MERGE (aps3:ApprovalStatus {id: 'withdrawn', name: 'Withdrawn'});
MERGE (aps4:ApprovalStatus {id: 'expired', name: 'Expired'});

// InspectionType 枚举
MERGE (it1:InspectionType {id: 'pre_approval', name: 'Pre-approval Inspection'});
MERGE (it2:InspectionType {id: 'routine', name: 'Routine Inspection'});
MERGE (it3:InspectionType {id: 'for_cause', name: 'For-cause Inspection'});
MERGE (it4:InspectionType {id: 'followup', name: 'Follow-up Inspection'});

// InspectionResult 枚举
MERGE (irt1:InspectionResult {id: 'nai', name: 'No Action Indicated', order: 1});
MERGE (irt2:InspectionResult {id: 'vai', name: 'Voluntary Action Indicated', order: 2});
MERGE (irt3:InspectionResult {id: 'oai', name: 'Official Action Indicated', order: 3});

// ComplianceActionType 枚举
MERGE (cat1:ComplianceActionType {id: 'warning_letter', name: 'Warning Letter'});
MERGE (cat2:ComplianceActionType {id: 'import_alert', name: 'Import Alert'});
MERGE (cat3:ComplianceActionType {id: 'injunction', name: 'Injunction'});
MERGE (cat4:ComplianceActionType {id: 'seizure', name: 'Seizure'});
MERGE (cat5:ComplianceActionType {id: 'criminal', name: 'Criminal Prosecution'});

// PMCStatus 枚举
MERGE (pmcs1:PMCStatus {id: 'pending', name: 'Pending'});
MERGE (pmcs2:PMCStatus {id: 'submitted', name: 'Submitted'});
MERGE (pmcs3:PMCStatus {id: 'in_progress', name: 'In Progress'});
MERGE (pmcs4:PMCStatus {id: 'completed', name: 'Completed'});
MERGE (pmcs5:PMCStatus {id: 'delayed', name: 'Delayed'});
MERGE (pmcs6:PMCStatus {id: 'released', name: 'Released'});

//===========================================================
// 4. 示例数据导入 - Manufacturer
//===========================================================

UNWIND [
    {manufacturer_id: 'MFR001', name: 'Pfizer Inc.', type: 'integrated', country: 'United States', state: 'NY', city: 'New York', fei_code: '100000123456', website: 'https://www.pfizer.com'},
    {manufacturer_id: 'MFR002', name: 'Novartis Pharma AG', type: 'integrated', country: 'Switzerland', city: 'Basel', fei_code: '100000234567', website: 'https://www.novartis.com'},
    {manufacturer_id: 'MFR003', name: 'Lonza Group', type: 'contract', country: 'Switzerland', city: 'Basel', fei_code: '100000345678', website: 'https://www.lonza.com'},
    {manufacturer_id: 'MFR004', name: 'Teva Pharmaceutical Industries', type: 'formulation', country: 'Israel', city: 'Petah Tikva', fei_code: '100000456789', website: 'https://www.tevapharm.com'},
    {manufacturer_id: 'MFR005', name: 'API Manufacturing Co.', type: 'api', country: 'India', city: 'Hyderabad', fei_code: '100000567890', website: 'https://www.apimfg.com'}
] AS row
MERGE (m:Manufacturer {manufacturer_id: row.manufacturer_id})
SET m.name = row.name,
    m.type = row.type,
    m.country = row.country,
    m.state = row.state,
    m.city = row.city,
    m.fei_code = row.fei_code,
    m.website = row.website,
    m.created_at = datetime()
MERGE (m)-[:HAS_MANUFACTURER_TYPE]->(mt:ManufacturerType {id: row.type});

//===========================================================
// 5. 示例数据导入 - RegulatoryAgency
//===========================================================

UNWIND [
    {agency_id: 'FDA', name: 'Food and Drug Administration', abbreviation: 'FDA', type: 'national', jurisdiction: 'United States', website: 'https://www.fda.gov'},
    {agency_id: 'EMA', name: 'European Medicines Agency', abbreviation: 'EMA', type: 'regional', jurisdiction: 'European Union', website: 'https://www.ema.europa.eu'},
    {agency_id: 'PMDA', name: 'Pharmaceuticals and Medical Devices Agency', abbreviation: 'PMDA', type: 'national', jurisdiction: 'Japan', website: 'https://www.pmda.go.jp'},
    {agency_id: 'NMPA', name: 'National Medical Products Administration', abbreviation: 'NMPA', type: 'national', jurisdiction: 'China', website: 'https://www.nmpa.gov.cn'},
    {agency_id: 'WHO', name: 'World Health Organization', abbreviation: 'WHO', type: 'international', jurisdiction: 'Global', website: 'https://www.who.int'}
] AS row
MERGE (ra:RegulatoryAgency {agency_id: row.agency_id})
SET ra.name = row.name,
    ra.abbreviation = row.abbreviation,
    ra.type = row.type,
    ra.jurisdiction = row.jurisdiction,
    ra.website = row.website,
    ra.created_at = datetime()
MERGE (ra)-[:HAS_AGENCY_TYPE]->(at:AgencyType {id: row.type});

//===========================================================
// 6. 示例数据导入 - DrugShortage
//===========================================================

UNWIND [
    {shortage_id: 'DS001', drug_name: 'EpiPen', shortage_type: 'supply', reason: 'manufacturing', status: 'resolved', start_date: '2018-05-01', end_date: '2019-02-15', affected_region: 'Nationwide', impact_level: 'critical', manufacturer_id: 'MFR001'},
    {shortage_id: 'DS002', drug_name: 'Doxycycline Hyclate', shortage_type: 'demand', reason: 'raw_material', status: 'active', start_date: '2023-01-15', affected_region: 'Nationwide', impact_level: 'moderate', manufacturer_id: 'MFR004'},
    {shortage_id: 'DS003', drug_name: 'Albuterol Sulfate', shortage_type: 'quality', reason: 'quality', status: 'resolved', start_date: '2022-08-01', end_date: '2022-12-01', affected_region: 'Midwest', impact_level: 'minor', manufacturer_id: 'MFR001'}
] AS row
MERGE (ds:DrugShortage {shortage_id: row.shortage_id})
SET ds.drug_name = row.drug_name,
    ds.shortage_type = row.shortage_type,
    ds.reason = row.reason,
    ds.status = row.status,
    ds.start_date = date(row.start_date),
    ds.end_date = CASE row.end_date WHEN null THEN null ELSE date(row.end_date) END,
    ds.affected_region = row.affected_region,
    ds.created_at = datetime()
MERGE (ds)-[:HAS_SHORTAGE_TYPE]->(sht:ShortageType {id: row.shortage_type})
MERGE (ds)-[:HAS_SHORTAGE_REASON]->(shr:ShortageReason {id: row.reason})
MERGE (ds)-[:HAS_SHORTAGE_STATUS]->(shs:ShortageStatus {id: row.status})
MERGE (ds)-[:HAS_IMPACT_LEVEL]->(il:ImpactLevel {id: row.impact_level})
MERGE (ds)-[:HAS_AFFECTED_MANUFACTURER]->(m:Manufacturer {manufacturer_id: row.manufacturer_id});

//===========================================================
// 7. 示例数据导入 - Submission
//===========================================================

UNWIND [
    {submission_id: 'NDA123456', submission_type: 'nda', submission_date: '2022-03-15', approval_date: '2023-01-20', review_days: 310, review_priority: 'priority', review_standard: 'full', status: 'approved', drug_name: 'Drug X', submitter: 'Pfizer Inc.', agency: 'FDA'},
    {submission_id: 'ANDA654321', submission_type: 'anda', submission_date: '2022-06-01', approval_date: '2023-02-15', review_days: 260, review_priority: 'standard', review_standard: 'full', status: 'approved', drug_name: 'Generic Y', submitter: 'Teva', agency: 'FDA'},
    {submission_id: 'BLA789012', submission_type: 'bla', submission_date: '2022-01-10', approval_date: '2022-12-01', review_days: 326, review_priority: 'accelerated', review_standard: 'accelerated', status: 'approved', drug_name: 'BioTherapy Z', submitter: 'Novartis', agency: 'FDA'}
] AS row
MERGE (sub:Submission {submission_id: row.submission_id})
SET sub.submission_type = row.submission_type,
    sub.submission_date = date(row.submission_date),
    sub.approval_date = date(row.approval_date),
    sub.review_days = row.review_days,
    sub.review_priority = row.review_priority,
    sub.review_standard = row.review_standard,
    sub.status = row.status,
    sub.drug_name = row.drug_name,
    sub.created_at = datetime()
MERGE (sub)-[:HAS_SUBMISSION_TYPE]->(sut:SubmissionType {id: row.submission_type})
MERGE (sub)-[:HAS_SUBMISSION_STATUS]->(sust:SubmissionStatus {id: row.status})
MERGE (sub)-[:HAS_REVIEW_PRIORITY]->(rp:ReviewPriority {id: row.review_priority})
MERGE (sub)-[:HAS_REVIEW_STANDARD]->(rs:ReviewStandard {id: row.review_standard})
MERGE (sub)-[:SUBMITTED_TO]->(ra:RegulatoryAgency {abbreviation: row.agency});

//===========================================================
// 8. 示例数据导入 - Approval
//===========================================================

UNWIND [
    {approval_id: 'AP001', approval_number: 'NDA012345', approval_type: 'full', approval_date: '2023-01-20', expiration_date: '2028-01-20', status: 'active', indication: 'Treatment of Type 2 Diabetes', dosage_form: 'Tablet', strength: '100mg', drug_name: 'Drug X', holder: 'Pfizer Inc.', agency: 'FDA'},
    {approval_id: 'AP002', approval_number: 'ANDA054321', approval_type: 'full', approval_date: '2023-02-15', expiration_date: '2028-02-15', status: 'active', indication: 'Hypertension', dosage_form: 'Capsule', strength: '50mg', drug_name: 'Generic Y', holder: 'Teva', agency: 'FDA'},
    {approval_id: 'AP003', approval_number: 'BLA078901', approval_type: 'accelerated', approval_date: '2022-12-01', expiration_date: '2027-12-01', status: 'active', indication: 'Oncology', dosage_form: 'Injection', strength: '100mg/mL', drug_name: 'BioTherapy Z', holder: 'Novartis', agency: 'FDA'}
] AS row
MERGE (ap:Approval {approval_id: row.approval_id})
SET ap.approval_number = row.approval_number,
    ap.approval_type = row.approval_type,
    ap.approval_date = date(row.approval_date),
    ap.expiration_date = date(row.expiration_date),
    ap.status = row.status,
    ap.indication = row.indication,
    ap.dosage_form = row.dosage_form,
    ap.strength = row.strength,
    ap.drug_name = row.drug_name,
    ap.created_at = datetime()
MERGE (ap)-[:HAS_APPROVAL_TYPE]->(apt:ApprovalType {id: row.approval_type})
MERGE (ap)-[:HAS_APPROVAL_STATUS]->(aps:ApprovalStatus {id: row.status})
MERGE (ap)-[:ISSUED_BY]->(ra:RegulatoryAgency {abbreviation: row.agency});

// 关联批准到申报
MATCH (ap:Approval {approval_id: 'AP001'}), (sub:Submission {submission_id: 'NDA123456'})
MERGE (sub)-[:RESULTS_IN_APPROVAL]->(ap);

//===========================================================
// 9. 示例数据导入 - Inspection
//===========================================================

UNWIND [
    {inspection_id: 'INS001', facility_name: 'Pfizer NY Facility', inspection_type: 'routine', inspection_date: '2022-09-15', classification: 'ra', result: 'nai', inspector: 'J. Smith', agency: 'FDA'},
    {inspection_id: 'INS002', facility_name: 'Novartis Basel Site', inspection_type: 'pre_approval', inspection_date: '2022-11-01', classification: 'pa', result: 'vai', inspector: 'M. Mueller', agency: 'FDA'},
    {inspection_id: 'INS003', facility_name: 'Teva Plant A', inspection_type: 'for_cause', inspection_date: '2023-01-20', classification: 'fc', result: 'oai', inspector: 'R. Johnson', agency: 'FDA'}
] AS row
MERGE (ins:Inspection {inspection_id: row.inspection_id})
SET ins.facility_name = row.facility_name,
    ins.inspection_type = row.inspection_type,
    ins.inspection_date = date(row.inspection_date),
    ins.classification = row.classification,
    ins.result = row.result,
    ins.inspector = row.inspector,
    ins.created_at = datetime()
MERGE (ins)-[:HAS_INSPECTION_TYPE]->(it:InspectionType {id: row.inspection_type})
MERGE (ins)-[:HAS_CLASSIFICATION]->(ic:InspectionClassification {id: row.classification})
MERGE (ins)-[:HAS_INSPECTION_RESULT]->(irt:InspectionResult {id: row.result})
MERGE (ins)-[:CONDUCTED_BY]->(ra:RegulatoryAgency {abbreviation: row.agency});

//===========================================================
// 10. 示例数据导入 - ComplianceAction
//===========================================================

UNWIND [
    {action_id: 'CA001', action_type: 'warning_letter', action_date: '2023-02-01', reason: 'cGMP violations', severity: 'moderate', status: 'active', manufacturer_id: 'MFR004', agency: 'FDA'},
    {action_id: 'CA002', action_type: 'import_alert', action_date: '2023-03-15', reason: ' adulteration', severity: 'serious', status: 'active', manufacturer_id: 'MFR005', agency: 'FDA'}
] AS row
MERGE (ca:ComplianceAction {action_id: row.action_id})
SET ca.action_type = row.action_type,
    ca.action_date = date(row.action_date),
    ca.reason = row.reason,
    ca.severity = row.severity,
    ca.status = row.status,
    ca.created_at = datetime()
MERGE (ca)-[:HAS_ACTION_TYPE]->(cat:ComplianceActionType {id: row.action_type})
MERGE (ca)-[:AGAINST_MANUFACTURER]->(m:Manufacturer {manufacturer_id: row.manufacturer_id})
MERGE (ca)-[:ISSUED_BY]->(ra:RegulatoryAgency {abbreviation: row.agency});

//===========================================================
// 11. 示例数据导入 - PostMarketingCommitment
//===========================================================

UNWIND [
    {pmc_id: 'PMC001', pmc_type: 'study', description: 'Phase 4 safety study', submitted_date: '2023-02-01', due_date: '2025-02-01', status: 'in_progress', drug_name: 'Drug X', approval_id: 'AP001'},
    {pmc_id: 'PMC002', pmc_type: 'trial', description: 'Randomized controlled trial', submitted_date: '2023-03-15', due_date: '2026-03-15', status: 'pending', drug_name: 'BioTherapy Z', approval_id: 'AP003'}
] AS row
MERGE (pmc:PostMarketingCommitment {pmc_id: row.pmc_id})
SET pmc.pmc_type = row.pmc_type,
    pmc.description = row.description,
    pmc.submitted_date = date(row.submitted_date),
    pmc.due_date = date(row.due_date),
    pmc.status = row.status,
    pmc.created_at = datetime()
MERGE (pmc)-[:HAS_PMC_TYPE]->(pmt:PMCType {id: row.pmc_type})
MERGE (pmc)-[:HAS_STATUS]->(pmcs:PMCStatus {id: row.status})
MERGE (pmc)-[:PMC_FOR_DRUG]->(c:Compound {name: row.drug_name})
MERGE (pmc)-[:COMMITMENT_FOR]->(ap:Approval {approval_id: row.approval_id});

//===========================================================
// 12. 示例数据导入 - SafetySignal
//===========================================================

UNWIND [
    {signal_id: 'SS001', signal_type: 'adr', detection_date: '2023-04-01', source: 'FAERS', severity: 'serious', status: 'under_investigation', drug_name: 'Drug X', description: 'Cardiovascular events'},
    {signal_id: 'SS002', signal_type: 'quality', detection_date: '2023-05-15', source: 'FDA MedWatch', severity: 'moderate', status: 'confirmed', drug_name: 'Generic Y', description: 'Particulate matter'}
] AS row
MERGE (ss:SafetySignal {signal_id: row.signal_id})
SET ss.signal_type = row.signal_type,
    ss.detection_date = date(row.detection_date),
    ss.source = row.source,
    ss.severity = row.severity,
    ss.status = row.status,
    ss.description = row.description,
    ss.created_at = datetime()
MERGE (ss)-[:HAS_SIGNAL_TYPE]->(sgt:SignalType {id: row.signal_type})
MERGE (ss)-[:HAS_SIGNAL_SEVERITY]->(sgs:SignalSeverity {id: row.severity})
MERGE (ss)-[:HAS_SIGNAL_STATUS]->(sgst:SignalStatus {id: row.status})
MERGE (ss)-[:RELATED_TO_DRUG]->(c:Compound {name: row.drug_name});

//===========================================================
// 13. 验证导入
//===========================================================

// 统计各类节点数量
MATCH (m:Manufacturer) RETURN 'Manufacturer' as type, count(m) as count
UNION ALL
MATCH (s:Supplier) RETURN 'Supplier' as type, count(s) as count
UNION ALL
MATCH (ds:DrugShortage) RETURN 'DrugShortage' as type, count(ds) as count
UNION ALL
MATCH (ra:RegulatoryAgency) RETURN 'RegulatoryAgency' as type, count(ra) as count
UNION ALL
MATCH (sub:Submission) RETURN 'Submission' as type, count(sub) as count
UNION ALL
MATCH (ap:Approval) RETURN 'Approval' as type, count(ap) as count
UNION ALL
MATCH (ins:Inspection) RETURN 'Inspection' as type, count(ins) as count
UNION ALL
MATCH (ca:ComplianceAction) RETURN 'ComplianceAction' as type, count(ca) as count
UNION ALL
MATCH (pmc:PostMarketingCommitment) RETURN 'PostMarketingCommitment' as type, count(pmc) as count
UNION ALL
MATCH (ss:SafetySignal) RETURN 'SafetySignal' as type, count(ss) as count;

// 显示关系统计
MATCH ()-[r]->() RETURN type(r) as relationship_type, count(r) as count ORDER BY count DESC;

//===========================================================
// 脚本结束
//===========================================================
