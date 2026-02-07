//===========================================================
// 制药行业知识图谱 - 临床试验领域数据导入脚本
// Pharmaceutical Knowledge Graph - Clinical Domain Data Import
//===========================================================
// 版本: v1.0
// 创建日期: 2025-02-06
// 描述: 导入临床试验领域核心实体和关系到Neo4j
//===========================================================

:auto

//===========================================================
// 1. 创建唯一性约束和索引
//===========================================================

// ClinicalTrial 约束
CREATE CONSTRAINT trial_id IF NOT EXISTS FOR (t:ClinicalTrial) REQUIRE t.trial_id IS UNIQUE;
CREATE INDEX trial_phase IF NOT EXISTS FOR (t:ClinicalTrial) ON (t.trial_phase);
CREATE INDEX trial_status IF NOT EXISTS FOR (t:ClinicalTrial) ON (t.trial_status);
CREATE INDEX trial_start_date IF NOT EXISTS FOR (t:ClinicalTrial) ON (t.start_date);
CREATE INDEX trial_condition IF NOT EXISTS FOR (t:ClinicalTrial) ON (t.condition);

// Subject 约束
CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (s:Subject) REQUIRE s.subject_id IS UNIQUE;
CREATE INDEX subject_initials IF NOT EXISTS FOR (s:Subject) ON (s.initials);
CREATE INDEX subject_age IF NOT EXISTS FOR (s:Subject) ON (s.age);
CREATE INDEX subject_gender IF NOT EXISTS FOR (s:Subject) ON (s.gender);

// Intervention 约束
CREATE CONSTRAINT intervention_id IF NOT EXISTS FOR (i:Intervention) REQUIRE i.intervention_id IS UNIQUE;
CREATE INDEX intervention_type IF NOT EXISTS FOR (i:Intervention) ON (i.intervention_type);
CREATE INDEX intervention_name IF NOT EXISTS FOR (i:Intervention) ON (i.intervention_name);

// Outcome 约束
CREATE CONSTRAINT outcome_id IF NOT EXISTS FOR (o:Outcome) REQUIRE o.outcome_id IS UNIQUE;

// AdverseEvent 约束
CREATE CONSTRAINT ae_id IF NOT EXISTS FOR (ae:AdverseEvent) REQUIRE ae.ae_id IS UNIQUE;
CREATE INDEX ae_severity IF NOT EXISTS FOR (ae:AdverseEvent) ON (ae.severity);
CREATE INDEX ae_seriousness IF NOT EXISTS FOR (ae:AdverseEvent) ON (ae.seriousness);

// StudySite 约束
CREATE CONSTRAINT site_id IF NOT EXISTS FOR (site:StudySite) REQUIRE site.site_id IS UNIQUE;
CREATE INDEX site_country IF NOT EXISTS FOR (site:StudySite) ON (site.country);

// Investigator 约束
CREATE CONSTRAINT investigator_id IF NOT EXISTS FOR (inv:Investigator) REQUIRE inv.investigator_id IS UNIQUE;

// Condition/Disease 约束
CREATE CONSTRAINT condition_id IF NOT EXISTS FOR (c:Condition) REQUIRE c.condition_id IS UNIQUE;
CREATE INDEX condition_name IF NOT EXISTS FOR (c:Condition) ON (c.condition_name);

//===========================================================
// 2. 创建枚举节点
//===========================================================

// TrialPhase 枚举
MERGE (tp1:TrialPhase {id: 'phase_0', name: 'Phase 0', order: 0});
MERGE (tp2:TrialPhase {id: 'phase_1', name: 'Phase 1', order: 1});
MERGE (tp3:TrialPhase {id: 'phase_2', name: 'Phase 2', order: 2});
MERGE (tp4:TrialPhase {id: 'phase_3', name: 'Phase 3', order: 3});
MERGE (tp5:TrialPhase {id: 'phase_4', name: 'Phase 4', order: 4});
MERGE (tp6:TrialPhase {id: 'early_phase_1', name: 'Early Phase 1', order: 1});
MERGE (tp7:TrialPhase {id: 'na', name: 'N/A', order: 99});

// TrialStatus 枚举
MERGE (ts1:TrialStatus {id: 'recruiting', name: 'Recruiting', active: true});
MERGE (ts2:TrialStatus {id: 'not_yet_recruiting', name: 'Not Yet Recruiting', active: false});
MERGE (ts3:TrialStatus {id: 'active_not_recruiting', name: 'Active, not recruiting', active: true});
MERGE (ts4:TrialStatus {id: 'completed', name: 'Completed', active: false});
MERGE (ts5:TrialStatus {id: 'suspended', name: 'Suspended', active: false});
MERGE (ts6:TrialStatus {id: 'terminated', name: 'Terminated', active: false});
MERGE (ts7:TrialStatus {id: 'withdrawn', name: 'Withdrawn', active: false});
MERGE (ts8:TrialStatus {id: 'unknown', name: 'Unknown status', active: false});
MERGE (ts9:TrialStatus {id: 'available', name: 'Available', active: true});
MERGE (ts10:TrialStatus {id: 'enrolling_by_invitation', name: 'Enrolling by invitation', active: true});

// StudyType 枚举
MERGE (st1:StudyType {id: 'interventional', name: 'Interventional'});
MERGE (st2:StudyType {id: 'observational', name: 'Observational'});
MERGE (st3:StudyType {id: 'patient_registry', name: 'Patient Registry'});
MERGE (st4:StudyType {id: 'unknown', name: 'Unknown'});

// StudyDesign 枚举
MERGE (sd1:StudyDesign {id: 'randomized', name: 'Randomized'});
MERGE (sd2:StudyDesign {id: 'non_randomized', name: 'Non-randomized'});
MERGE (sd3:StudyDesign {id: 'open_label', name: 'Open Label'});
MERGE (sd4:StudyDesign {id: 'double_blind', name: 'Double Blind'});
MERGE (sd5:StudyDesign {id: 'single_blind', name: 'Single Blind'});
MERGE (sd6:StudyDesign {id: 'placebo_controlled', name: 'Placebo Controlled'});
MERGE (sd7:StudyDesign {id: 'crossover', name: 'Crossover'});
MERGE (sd8:StudyDesign {id: 'parallel', name: 'Parallel'});
MERGE (sd9:StudyDesign {id: 'factorial', name: 'Factorial'});

// AllocationType 枚举
MERGE (at1:AllocationType {id: 'randomized', name: 'Randomized'});
MERGE (at2:AllocationType {id: 'non_randomized', name: 'Non-Randomized'});

// MaskingType 枚举
MERGE (mt1:MaskingType {id: 'none', name: 'None (Open Label)'});
MERGE (mt2:MaskingType {id: 'single', name: 'Single'});
MERGE (mt3:MaskingType {id: 'double', name: 'Double'});
MERGE (mt4:MaskingType {id: 'triple', name: 'Triple'});
MERGE (mt5:MaskingType {id: 'quadruple', name: 'Quadruple'});

// TrialPurpose 枚举
MERGE (pp1:TrialPurpose {id: 'treatment', name: 'Treatment'});
MERGE (pp2:TrialPurpose {id: 'prevention', name: 'Prevention'});
MERGE (pp3:TrialPurpose {id: 'diagnostic', name: 'Diagnostic'});
MERGE (pp4:TrialPurpose {id: 'supportive_care', name: 'Supportive Care'});
MERGE (pp5:TrialPurpose {id: 'screening', name: 'Screening'});
MERGE (pp6:TrialPurpose {id: 'health_services_research', name: 'Health Services Research'});
MERGE (pp7:TrialPurpose {id: 'basic_science', name: 'Basic Science'});
MERGE (pp8:TrialPurpose {id: 'other', name: 'Other'});

// InterventionType 枚举
MERGE (it1:InterventionType {id: 'behavioral', name: 'Behavioral'});
MERGE (it2:InterventionType {id: 'drug', name: 'Drug'});
MERGE (it3:InterventionType {id: 'device', name: 'Device'});
MERGE (it4:InterventionType {id: 'procedure', name: 'Procedure'});
MERGE (it5:InterventionType {id: 'radiation', name: 'Radiation'});
MERGE (it6:InterventionType {id: 'biological', name: 'Biological'});
MERGE (it7:InterventionType {id: 'genetic', name: 'Genetic'});
MERGE (it8:InterventionType {id: 'dietary_supplement', name: 'Dietary Supplement'});
MERGE (it9:InterventionType {id: 'combination_product', name: 'Combination Product'});
MERGE (it10:InterventionType {id: 'other', name: 'Other'});

// OutcomeType 枚举
MERGE (ot1:OutcomeType {id: 'primary', name: 'Primary', order: 1});
MERGE (ot2:OutcomeType {id: 'secondary', name: 'Secondary', order: 2});
MERGE (ot3:OutcomeType {id: 'other_pre_specified', name: 'Other Pre-specified', order: 3});
MERGE (ot4:OutcomeType {id: 'post_hoc', name: 'Post-hoc', order: 4});

// SeverityGrade 枚举
MERGE (sg1:SeverityGrade {id: 'grade_1', name: 'Grade 1 - Mild', order: 1});
MERGE (sg2:SeverityGrade {id: 'grade_2', name: 'Grade 2 - Moderate', order: 2});
MERGE (sg3:SeverityGrade {id: 'grade_3', name: 'Grade 3 - Severe', order: 3});
MERGE (sg4:SeverityGrade {id: 'grade_4', name: 'Grade 4 - Life-threatening', order: 4});
MERGE (sg5:SeverityGrade {id: 'grade_5', name: 'Grade 5 - Death', order: 5});

// Gender 枚举
MERGE (g1:Gender {id: 'all', name: 'All'});
MERGE (g2:Gender {id: 'male', name: 'Male'});
MERGE (g3:Gender {id: 'female', name: 'Female'});

// AgeGroup 枚举
MERGE (ag1:AgeGroup {id: 'child', name: 'Child (birth-17)'});
MERGE (ag2:AgeGroup {id: 'adult', name: 'Adult (18-64)'});
MERGE (ag3:AgeGroup {id: 'older_adult', name: 'Older Adult (65+)'});

// InvestigatorRole 枚举
MERGE (ir1:InvestigatorRole {id: 'principal_investigator', name: 'Principal Investigator'});
MERGE (ir2:InvestigatorRole {id: 'sub_investigator', name: 'Sub-Investigator'});
MERGE (ir3:InvestigatorRole {id: 'study_coordinator', name: 'Study Coordinator'});

// SiteStatus 枚举
MERGE (ss1:SiteStatus {id: 'active', name: 'Active'});
MERGE (ss2:SiteStatus {id: 'closed_to_accrual', name: 'Closed to accrual'});
MERGE (ss3:SiteStatus {id: 'in_setup', name: 'In setup'});
MERGE (ss4:SiteStatus {id: 'suspended', name: 'Suspended'});

//===========================================================
// 3. 示例数据导入 - ClinicalTrial
//===========================================================

UNWIND [
    {trial_id: 'NCT04368728', title: 'A Study of Drug X in COVID-19', phase: 'phase_3', status: 'recruiting', study_type: 'interventional', allocation: 'randomized', masking: 'double', purpose: 'treatment', enrollment: 300, start_date: '2020-04-01', primary_completion: '2020-12-31', completion: '2021-03-31'},
    {trial_id: 'NCT04042149', title: 'Efficacy and Safety of Drug Y in Advanced NSCLC', phase: 'phase_2', status: 'active_not_recruiting', study_type: 'interventional', allocation: 'randomized', masking: 'double', purpose: 'treatment', enrollment: 150, start_date: '2019-08-01', primary_completion: '2021-08-01', completion: '2022-02-01'},
    {trial_id: 'NCT03827074', title: 'Drug Z vs Placebo in Rheumatoid Arthritis', phase: 'phase_2', status: 'completed', study_type: 'interventional', allocation: 'randomized', masking: 'double', purpose: 'treatment', enrollment: 200, start_date: '2019-01-15', primary_completion: '2020-06-30', completion: '2020-12-31'},
    {trial_id: 'NCT04567890', title: 'Observational Study of Biomarkers in Cancer', phase: 'na', status: 'recruiting', study_type: 'observational', allocation: 'non_randomized', masking: 'none', purpose: 'basic_science', enrollment: 500, start_date: '2021-01-01', primary_completion: '2023-12-31', completion: '2024-12-31'}
] AS row
MERGE (t:ClinicalTrial {trial_id: row.trial_id})
SET t.title = row.title,
    t.phase = row.phase,
    t.status = row.status,
    t.study_type = row.study_type,
    t.allocation = row.allocation,
    t.masking = row.masking,
    t.purpose = row.purpose,
    t.enrollment = row.enrollment,
    t.start_date = date(row.start_date),
    t.primary_completion_date = date(row.primary_completion),
    t.completion_date = date(row.completion),
    t.created_at = datetime();

// 关联试验到阶段、状态等
MATCH (t:ClinicalTrial), (tp:TrialPhase)
WHERE t.phase = tp.id
MERGE (t)-[:HAS_PHASE]->(tp);

MATCH (t:ClinicalTrial), (ts:TrialStatus)
WHERE t.status = ts.id
MERGE (t)-[:HAS_STATUS]->(ts);

MATCH (t:ClinicalTrial), (st:StudyType)
WHERE t.study_type = st.id
MERGE (t)-[:HAS_STUDY_TYPE]->(st);

MATCH (t:ClinicalTrial), (at:AllocationType)
WHERE t.allocation = at.id
MERGE (t)-[:HAS_ALLOCATION]->(at);

MATCH (t:ClinicalTrial), (mt:MaskingType)
WHERE t.masking = mt.id
MERGE (t)-[:HAS_MASKING]->(mt);

MATCH (t:ClinicalTrial), (pp:TrialPurpose)
WHERE t.purpose = pp.id
MERGE (t)-[:HAS_PURPOSE]->(pp);

//===========================================================
// 4. 示例数据导入 - Condition/Disease
//===========================================================

UNWIND [
    {condition_id: 'COND001', condition_name: 'COVID-19', meddra_code: '10001215', icd_code: 'U07.1'},
    {condition_id: 'COND002', condition_name: 'Non-Small Cell Lung Cancer', meddra_code: '10028641', icd_code: 'C34.9'},
    {condition_id: 'COND003', condition_name: 'Rheumatoid Arthritis', meddra_code: '10006918', icd_code: 'M05.9'},
    {condition_id: 'COND004', condition_name: 'Type 2 Diabetes Mellitus', meddra_code: '10006944', icd_code: 'E11.9'},
    {condition_id: 'COND005', condition_name: 'Alzheimer Disease', meddra_code: '10007795', icd_code: 'G30.9'}
] AS row
MERGE (c:Condition {condition_id: row.condition_id})
SET c.condition_name = row.condition_name,
    c.meddra_code = row.meddra_code,
    c.icd_code = row.icd_code,
    c.created_at = datetime();

// 试验-疾病关联
MATCH (t:ClinicalTrial {trial_id: 'NCT04368728'}), (c:Condition {condition_name: 'COVID-19'})
MERGE (t)-[:STUDIES_CONDITION]->(c);

MATCH (t:ClinicalTrial {trial_id: 'NCT04042149'}), (c:Condition {condition_name: 'Non-Small Cell Lung Cancer'})
MERGE (t)-[:STUDIES_CONDITION]->(c);

MATCH (t:ClinicalTrial {trial_id: 'NCT03827074'}), (c:Condition {condition_name: 'Rheumatoid Arthritis'})
MERGE (t)-[:STUDIES_CONDITION]->(c);

//===========================================================
// 5. 示例数据导入 - Arm
//===========================================================

UNWIND [
    {arm_id: 'ARM001', trial_id: 'NCT04368728', arm_label: 'Experimental Drug X', arm_type: 'experimental', description: 'Drug X 10mg orally once daily', target_enrollment: 150},
    {arm_id: 'ARM002', trial_id: 'NCT04368728', arm_label: 'Placebo', arm_type: 'placebo', description: 'Matching placebo orally once daily', target_enrollment: 150},
    {arm_id: 'ARM003', trial_id: 'NCT04042149', arm_label: 'Drug Y High Dose', arm_type: 'experimental', description: 'Drug Y 200mg IV every 3 weeks', target_enrollment: 75},
    {arm_id: 'ARM004', trial_id: 'NCT04042149', arm_label: 'Drug Y Low Dose', arm_type: 'experimental', description: 'Drug Y 100mg IV every 3 weeks', target_enrollment: 75}
] AS row
MERGE (a:Arm {arm_id: row.arm_id})
SET a.arm_label = row.arm_label,
    a.arm_type = row.arm_type,
    a.description = row.description,
    a.target_enrollment = row.target_enrollment
MERGE (a)-[:ARM_OF]->(t:ClinicalTrial {trial_id: row.trial_id});

//===========================================================
// 6. 示例数据导入 - Intervention
//===========================================================

UNWIND [
    {intervention_id: 'INT001', trial_id: 'NCT04368728', intervention_type: 'drug', intervention_name: 'Drug X', arm_group_label: 'Experimental Drug X', dosage: '10 mg', dosage_form: 'Tablet', route: 'Oral', frequency: 'Once daily', duration: '14 days'},
    {intervention_id: 'INT002', trial_id: 'NCT04368728', intervention_type: 'drug', intervention_name: 'Placebo', arm_group_label: 'Placebo', dosage: '10 mg', dosage_form: 'Tablet', route: 'Oral', frequency: 'Once daily', duration: '14 days'},
    {intervention_id: 'INT003', trial_id: 'NCT04042149', intervention_type: 'drug', intervention_name: 'Drug Y', arm_group_label: 'Drug Y High Dose', dosage: '200 mg', dosage_form: 'Injection', route: 'Intravenous', frequency: 'Every 3 weeks', duration: 'Until progression'}
] AS row
MERGE (i:Intervention {intervention_id: row.intervention_id})
SET i.intervention_type = row.intervention_type,
    i.intervention_name = row.intervention_name,
    i.arm_group_label = row.arm_group_label,
    i.dosage = row.dosage,
    i.dosage_form = row.dosage_form,
    i.route = row.route,
    i.frequency = row.frequency,
    i.duration = row.duration,
    i.created_at = datetime()
MERGE (i)-[:INTERVENTION_OF]->(t:ClinicalTrial {trial_id: row.trial_id});

// 关联干预类型
MATCH (i:Intervention), (it:InterventionType)
WHERE i.intervention_type = it.id
MERGE (i)-[:HAS_INTERVENTION_TYPE]->(it);

//===========================================================
// 7. 示例数据导入 - Outcome
//===========================================================

UNWIND [
    {outcome_id: 'OUT001', trial_id: 'NCT04368728', outcome_type: 'primary', title: 'Time to Clinical Recovery', description: 'Time to recovery defined as fever resolution and respiratory improvement', time_frame: 'Up to 28 days', unit: 'Days'},
    {outcome_id: 'OUT002', trial_id: 'NCT04368728', outcome_type: 'secondary', title: 'Mortality Rate', description: 'All-cause mortality at day 28', time_frame: '28 days', unit: 'Percentage'},
    {outcome_id: 'OUT003', trial_id: 'NCT04042149', outcome_type: 'primary', title: 'Progression-Free Survival', description: 'Time from randomization to disease progression or death', time_frame: 'Up to 24 months', unit: 'Months'},
    {outcome_id: 'OUT004', trial_id: 'NCT04042149', outcome_type: 'secondary', title: 'Overall Response Rate', description: 'Proportion of patients with complete or partial response', time_frame: 'Up to 24 months', unit: 'Percentage'}
] AS row
MERGE (o:Outcome {outcome_id: row.outcome_id})
SET o.outcome_type = row.outcome_type,
    o.title = row.title,
    o.description = row.description,
    o.time_frame = row.time_frame,
    o.unit = row.unit,
    o.created_at = datetime()
MERGE (o)-[:OUTCOME_OF]->(t:ClinicalTrial {trial_id: row.trial_id});

// 关联结局类型
MATCH (o:Outcome), (ot:OutcomeType)
WHERE o.outcome_type = ot.id
MERGE (o)-[:HAS_OUTCOME_TYPE]->(ot);

//===========================================================
// 8. 示例数据导入 - Subject
//===========================================================

UNWIND [
    {subject_id: 'SUB001', trial_id: 'NCT04368728', initials: 'AB', age: 45, gender: 'male', age_group: 'adult', weight: 75.5, height: 178.0, bmi: 23.8, enrollment_date: '2020-04-15', arm_id: 'ARM001'},
    {subject_id: 'SUB002', trial_id: 'NCT04368728', initials: 'CD', age: 52, gender: 'female', age_group: 'adult', weight: 62.0, height: 165.0, bmi: 22.8, enrollment_date: '2020-04-18', arm_id: 'ARM002'},
    {subject_id: 'SUB003', trial_id: 'NCT04042149', initials: 'EF', age: 68, gender: 'male', age_group: 'older_adult', weight: 70.0, height: 172.0, bmi: 23.7, enrollment_date: '2019-08-10', arm_id: 'ARM003'},
    {subject_id: 'SUB004', trial_id: 'NCT04042149', initials: 'GH', age: 61, gender: 'female', age_group: 'older_adult', weight: 58.0, height: 160.0, bmi: 22.7, enrollment_date: '2019-08-15', arm_id: 'ARM004'}
] AS row
MERGE (s:Subject {subject_id: row.subject_id})
SET s.initials = row.initials,
    s.age = row.age,
    s.gender = row.gender,
    s.weight = row.weight,
    s.height = row.height,
    s.bmi = row.bmi,
    s.enrollment_date = date(row.enrollment_date),
    s.created_at = datetime()
MERGE (s)-[:ENROLLED_IN]->(t:ClinicalTrial {trial_id: row.trial_id});

// 关联受试者性别和年龄组
MATCH (s:Subject), (g:Gender)
WHERE s.gender = g.id
MERGE (s)-[:HAS_GENDER]->(g);

MATCH (s:Subject), (ag:AgeGroup)
WHERE s.age_group = ag.id
MERGE (s)-[:HAS_AGE_GROUP]->(ag);

// 关联受试者到组别
MATCH (s:Subject), (a:Arm)
WHERE s.subject_id = 'SUB001' AND a.arm_id = 'ARM001'
MERGE (s)-[:ASSIGNED_TO]->(a);

MATCH (s:Subject), (a:Arm)
WHERE s.subject_id = 'SUB002' AND a.arm_id = 'ARM002'
MERGE (s)-[:ASSIGNED_TO]->(a);

MATCH (s:Subject), (a:Arm)
WHERE s.subject_id = 'SUB003' AND a.arm_id = 'ARM003'
MERGE (s)-[:ASSIGNED_TO]->(a);

MATCH (s:Subject), (a:Arm)
WHERE s.subject_id = 'SUB004' AND a.arm_id = 'ARM004'
MERGE (s)-[:ASSIGNED_TO]->(a);

//===========================================================
// 9. 示例数据导入 - AdverseEvent
//===========================================================

UNWIND [
    {ae_id: 'AE001', trial_id: 'NCT04368728', subject_id: 'SUB001', meddra_code: '10015911', meddra_term: 'Nausea', severity: 'grade_1', seriousness: 'non_serious', onset_date: '2020-04-20', outcome: 'Recovered', action_taken: 'No action taken'},
    {ae_id: 'AE002', trial_id: 'NCT04368728', subject_id: 'SUB001', meddra_code: '10013491', meddra_term: 'Headache', severity: 'grade_2', seriousness: 'non_serious', onset_date: '2020-04-22', outcome: 'Recovered', action_taken: 'Dose reduced'},
    {ae_id: 'AE003', trial_id: 'NCT04042149', subject_id: 'SUB003', meddra_code: '10027217', meddra_term: 'Neutropenia', severity: 'grade_3', seriousness: 'serious', onset_date: '2019-09-01', outcome: 'Not recovered', action_taken: 'Dose interrupted'},
    {ae_id: 'AE004', trial_id: 'NCT04042149', subject_id: 'SUB004', meddra_code: '10017999', meddra_term: 'Fatigue', severity: 'grade_1', seriousness: 'non_serious', onset_date: '2019-08-25', outcome: 'Recovered', action_taken: 'No action taken'}
] AS row
MERGE (ae:AdverseEvent {ae_id: row.ae_id})
SET ae.meddra_code = row.meddra_code,
    ae.meddra_term = row.meddra_term,
    ae.severity = row.severity,
    ae.seriousness = row.seriousness,
    ae.onset_date = date(row.onset_date),
    ae.outcome = row.outcome,
    ae.action_taken = row.action_taken,
    ae.created_at = datetime()
MERGE (t:ClinicalTrial {trial_id: row.trial_id})-[:REPORTS_ADVERSE_EVENT]->(ae)
MERGE (s:Subject {subject_id: row.subject_id})-[:EXPERIENCED_AE]->(ae);

// 关联严重程度
MATCH (ae:AdverseEvent), (sg:SeverityGrade)
WHERE ae.severity = sg.id
MERGE (ae)-[:HAS_SEVERITY]->(sg);

//===========================================================
// 10. 示例数据导入 - StudySite
//===========================================================

UNWIND [
    {site_id: 'SITE001', trial_id: 'NCT04368728', site_name: 'University Hospital A', status: 'active', contact_name: 'Dr. John Smith', contact_email: 'john.smith@univa.edu', city: 'Boston', state: 'MA', country: 'United States', postal_code: '02115'},
    {site_id: 'SITE002', trial_id: 'NCT04368728', site_name: 'City Medical Center', status: 'active', contact_name: 'Dr. Jane Doe', contact_email: 'jane.doe@citymed.com', city: 'New York', state: 'NY', country: 'United States', postal_code: '10001'},
    {site_id: 'SITE003', trial_id: 'NCT04042149', site_name: 'Cancer Research Institute', status: 'active', contact_name: 'Dr. Robert Lee', contact_email: 'rlee@cancerinst.edu', city: 'Los Angeles', state: 'CA', country: 'United States', postal_code: '90095'}
] AS row
MERGE (site:StudySite {site_id: row.site_id})
SET site.site_name = row.site_name,
    site.status = row.status,
    site.contact_name = row.contact_name,
    site.contact_email = row.contact_email,
    site.city = row.city,
    site.state = row.state,
    site.country = row.country,
    site.postal_code = row.postal_code,
    site.created_at = datetime()
MERGE (site)-[:SITE_OF]->(t:ClinicalTrial {trial_id: row.trial_id});

//===========================================================
// 11. 示例数据导入 - Investigator
//===========================================================

UNWIND [
    {investigator_id: 'INV001', site_id: 'SITE001', name: 'John Smith', role: 'principal_investigator', degree: 'MD', affiliation: 'University Hospital A', email: 'john.smith@univa.edu'},
    {investigator_id: 'INV002', site_id: 'SITE002', name: 'Jane Doe', role: 'principal_investigator', degree: 'MD', affiliation: 'City Medical Center', email: 'jane.doe@citymed.com'},
    {investigator_id: 'INV003', site_id: 'SITE003', name: 'Robert Lee', role: 'principal_investigator', degree: 'MD PhD', affiliation: 'Cancer Research Institute', email: 'rlee@cancerinst.edu'}
] AS row
MERGE (inv:Investigator {investigator_id: row.investigator_id})
SET inv.name = row.name,
    inv.role = row.role,
    inv.degree = row.degree,
    inv.affiliation = row.affiliation,
    inv.email = row.email,
    inv.created_at = datetime()
MERGE (inv)-[:ASSIGNED_TO]->(site:StudySite {site_id: row.site_id});

// 关联研究者角色
MATCH (inv:Investigator), (ir:InvestigatorRole)
WHERE inv.role = ir.id
MERGE (inv)-[:HAS_ROLE]->(ir);

//===========================================================
// 12. 示例数据导入 - Sponsor
//===========================================================

UNWIND [
    {org_id: 'ORG001', trial_id: 'NCT04368728', org_name: 'PharmaCorp Inc.', org_type: 'industry'},
    {org_id: 'ORG002', trial_id: 'NCT04042149', org_name: 'BioTech LLC', org_type: 'industry'},
    {org_id: 'ORG003', trial_id: 'NCT03827074', org_name: 'National Institutes of Health', org_type: 'nih'}
] AS row
MERGE (org:Sponsor {org_id: row.org_id})
SET org.org_name = row.org_name,
    org.org_type = row.org_type,
    org.created_at = datetime()
MERGE (t:ClinicalTrial {trial_id: row.trial_id})-[:HAS_SPONSOR]->(org);

//===========================================================
// 13. 验证导入
//===========================================================

// 统计各类节点数量
MATCH (t:ClinicalTrial) RETURN 'ClinicalTrial' as type, count(t) as count
UNION ALL
MATCH (s:Subject) RETURN 'Subject' as type, count(s) as count
UNION ALL
MATCH (i:Intervention) RETURN 'Intervention' as type, count(i) as count
UNION ALL
MATCH (o:Outcome) RETURN 'Outcome' as type, count(o) as count
UNION ALL
MATCH (ae:AdverseEvent) RETURN 'AdverseEvent' as type, count(ae) as count
UNION ALL
MATCH (site:StudySite) RETURN 'StudySite' as type, count(site) as count
UNION ALL
MATCH (inv:Investigator) RETURN 'Investigator' as type, count(inv) as count
UNION ALL
MATCH (c:Condition) RETURN 'Condition' as type, count(c) as count;

// 显示关系统计
MATCH ()-[r]->() RETURN type(r) as relationship_type, count(r) as count ORDER BY count DESC;

//===========================================================
// 脚本结束
//===========================================================
