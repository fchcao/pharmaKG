#===========================================================
# PharmaKG ETL - 数据质量测试
# Pharmaceutical Knowledge Graph - Data Quality Tests
#===========================================================
# 版本: v1.0
# 描述: ETL 管道的测试套件
#===========================================================

import logging
import pytest
from typing import Dict, List, Any
from datetime import datetime

from ..transformers.compound import CompoundTransformer
from ..transformers.target_disease import TargetTransformer, DiseaseTransformer
from ..transformers.trial import ClinicalTrialTransformer
from ..quality.validators import (
    CompoundValidator,
    TargetValidator,
    DiseaseValidator,
    ClinicalTrialValidator,
    ValidationResult
)
from ..quality.checker import (
    DataQualityChecker,
    check_date_consistency,
    check_phase_consistency,
    check_molecular_weight_consistency
)


logger = logging.getLogger(__name__)


class TestCompoundData:
    """化合物数据测试"""

    @pytest.fixture
    def valid_compound(self) -> Dict:
        return {
            "chembl_id": "CHEMBL25",
            "pref_name": "Aspirin",
            "molecule_structures": {
                "standard_inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
                "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "standard_inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
            },
            "molecule_properties": {
                "full_mwt": 180.16
            },
            "max_phase": 4,
            "therapeutic_flag": True
        }

    @pytest.fixture
    def invalid_compound(self) -> Dict:
        return {
            "chembl_id": "CHEMBL25",
            # Missing pref_name
            "molecule_structures": {
                "standard_inchi": "Invalid InChI"
            }
        }

    def test_transform_valid_compound(self, valid_compound):
        """测试转换有效化合物"""
        transformer = CompoundTransformer()
        result = transformer.transform(valid_compound)

        assert result.is_valid
        assert result.output_record is not None
        assert result.output_record["name"] == "Aspirin"
        assert result.output_record["inchikey"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"

    def test_transform_invalid_compound(self, invalid_compound):
        """测试转换无效化合物"""
        transformer = CompoundTransformer()
        result = transformer.transform(invalid_compound)

        assert not result.is_valid
        assert result.errors

    def test_validate_compound(self, valid_compound):
        """测试化合物验证"""
        validator = CompoundValidator()
        result = validator.validate(valid_compound)

        # Note: valid_compound needs transformation first
        transformer = CompoundTransformer()
        transformed = transformer.transform(valid_compound)
        result = validator.validate(transformed.output_record)

        assert result.is_valid or result.warnings


class TargetData:
    """靶点数据测试"""

    @pytest.fixture
    def valid_target(self) -> Dict:
        return {
            "target_chembl_id": "CHEMBL240",
            "target_pref_name": "Cyclooxygenase-1",
            "target_type": "receptor",
            "organism": "Homo sapiens",
            "accession": "P23219"
        }

    @pytest.fixture
    def invalid_target(self) -> Dict:
        return {
            "target_chembl_id": "CHEMBL240",
            # Missing target_pref_name
            "accession": "INVALID123"  # Invalid UniProt ID format
        }

    def test_transform_valid_target(self, valid_target):
        """测试转换有效靶点"""
        transformer = TargetTransformer()
        result = transformer.transform(valid_target)

        assert result.is_valid
        assert result.output_record is not None
        assert result.output_record["name"] == "Cyclooxygenase-1"
        assert result.output_record["uniprot_id"] == "P23219"

    def test_validate_uniprot_id(self):
        """测试 UniProt ID 验证"""
        validator = TargetValidator()

        valid_record = {
            "primary_id": "uniprot:P23219",
            "name": "Cyclooxygenase-1",
            "uniprot_id": "P23219"
        }
        result = validator.validate(valid_record)
        assert result.is_valid

        invalid_record = {
            "primary_id": "uniprot:INVALID",
            "name": "Test",
            "uniprot_id": "INVALID"
        }
        result = validator.validate(invalid_record)
        assert not result.is_valid


class TestDiseaseData:
    """疾病数据测试"""

    @pytest.fixture
    def valid_disease(self) -> Dict:
        return {
            "mondo_id": "MONDO:0002020",
            "name": "Lung Cancer",
            "disease_class": "cancer",
            "therapeutic_area": "oncology"
        }

    def test_transform_valid_disease(self, valid_disease):
        """测试转换有效疾病"""
        transformer = DiseaseTransformer()
        result = transformer.transform(valid_disease)

        assert result.is_valid
        assert result.output_record["primary_id"] == "mondo:0002020"
        assert result.output_record["therapeutic_area"] == "Oncology"


class TestClinicalTrialData:
    """临床试验数据测试"""

    @pytest.fixture
    def valid_trial(self) -> Dict:
        return {
            "nct_id": "NCT00001234",
            "brief_title": "A Study of Drug X",
            "phase": "Phase 2",
            "status": "Recruiting",
            "start_date": "2020-01-01",
            "completion_date": "2022-12-31",
            "conditions": ["Lung Cancer"],
            "interventions": [
                {
                    "intervention_type": "Drug",
                    "intervention_name": "Drug X"
                }
            ]
        }

    @pytest.fixture
    def invalid_trial_dates(self) -> Dict:
        return {
            "nct_id": "NCT00001235",
            "brief_title": "Invalid Date Trial",
            "phase": "Phase 2",
            "start_date": "2022-01-01",
            "completion_date": "2020-12-31"  # Before start date
        }

    def test_transform_valid_trial(self, valid_trial):
        """测试转换有效试验"""
        transformer = ClinicalTrialTransformer()
        result = transformer.transform(valid_trial)

        assert result.is_valid
        assert result.output_record["primary_id"] == "nct:NCT00001234"
        assert result.output_record["phase"] == "Phase 2"
        assert result.output_record["status"] == "RECRUITING"

    def test_validate_trial_dates(self, invalid_trial_dates):
        """测试试验日期验证"""
        validator = ClinicalTrialValidator()

        # First transform
        transformer = ClinicalTrialTransformer()
        transformed = transformer.transform(invalid_trial_dates)

        # Then validate
        result = validator.validate(transformed.output_record)

        # Should have error about date range
        assert not result.is_valid
        assert any("completion_date" in issue.field.lower() for issue in result.issues)


class TestDataQualityChecker:
    """数据质量检查器测试"""

    @pytest.fixture
    def compound_records(self) -> List[Dict]:
        return [
            {
                "primary_id": "inchikey:BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "molecular_weight": 180.16
            },
            {
                "primary_id": "inchikey:XXXXXXXXXXXXXX",
                "name": "Paracetamol",
                "smiles": "CC(=O)NC1=CC=C(C=C1)O",
                "inchikey": "XXXXXXXXXXXXXX",
                "molecular_weight": 151.16
            },
            {
                "primary_id": "inchikey:YYYYYYYYYYYYYY",
                "name": "Ibuprofen",
                "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
                "inchikey": "YYYYYYYYYYYYYY",
                "molecular_weight": 206.28
            }
        ]

    def test_completeness_check(self, compound_records):
        """测试完整性检查"""
        checker = DataQualityChecker(threshold=0.8)

        metric = checker.check_completeness(
            compound_records,
            required_fields=["primary_id", "name", "smiles"]
        )

        assert metric.passed
        assert metric.value == 1.0

    def test_uniqueness_check(self, compound_records):
        """测试唯一性检查"""
        checker = DataQualityChecker()

        metric = checker.check_uniqueness(compound_records, "primary_id")

        assert metric.passed
        assert metric.value == 1.0

    def test_duplicate_detection(self):
        """测试重复检测"""
        checker = DataQualityChecker()

        records_with_duplicates = [
            {"primary_id": "ID001", "name": "Drug A"},
            {"primary_id": "ID001", "name": "Drug A"},  # Duplicate
            {"primary_id": "ID002", "name": "Drug B"}
        ]

        metric = checker.check_uniqueness(records_with_duplicates, "primary_id")

        assert not metric.passed
        assert metric.details["duplicate_keys"] == 1

    def test_quality_report_generation(self, compound_records):
        """测试质量报告生成"""
        checker = DataQualityChecker()

        report = checker.generate_report(
            records=compound_records,
            record_type="compound",
            required_fields=["primary_id", "name", "smiles"]
        )

        assert report.record_type == "compound"
        assert report.total_records == 3
        assert report.valid_records > 0
        assert len(report.metrics) > 0
        assert 0 <= report.overall_quality_score <= 1


class TestConsistencyRules:
    """一致性规则测试"""

    def test_date_consistency(self):
        """测试日期一致性规则"""
        valid_record = {
            "start_date": "2020-01-01",
            "end_date": "2022-12-31"
        }
        result = check_date_consistency(valid_record)
        assert result["valid"]

        invalid_record = {
            "start_date": "2022-01-01",
            "end_date": "2020-12-31"
        }
        result = check_date_consistency(invalid_record)
        assert not result["valid"]

    def test_phase_consistency(self):
        """测试阶段一致性规则"""
        valid_record = {
            "phase": "Phase 2",
            "status": "Completed"
        }
        result = check_phase_consistency(valid_record)
        assert result["valid"]

        invalid_record = {
            "phase": None,
            "status": "Completed"
        }
        result = check_phase_consistency(invalid_record)
        assert not result["valid"]

    def test_molecular_weight_consistency(self):
        """测试分子量一致性规则"""
        valid_record = {
            "molecular_weight": 180.16,
            "molecular_formula": "C9H8O4"
        }
        result = check_molecular_weight_consistency(valid_record)
        assert result["valid"]

        invalid_record = {
            "molecular_weight": -50,
            "molecular_formula": "C9H8O4"
        }
        result = check_molecular_weight_consistency(invalid_record)
        assert not result["valid"]


# 运行测试的便捷函数
def run_etl_tests(verbose: bool = True) -> bool:
    """
    运行 ETL 测试套件

    Args:
        verbose: 详细输出

    Returns:
        所有测试是否通过
    """
    import sys

    args = [
        __file__,
        "-v" if verbose else "",
        "--tb=short"
    ]

    return pytest.main(args) == 0


# 快速验证函数
def quick_validate(
    records: List[Dict],
    record_type: str
) -> Dict[str, Any]:
    """
    快速验证数据

    Args:
        records: 记录列表
        record_type: 记录类型

    Returns:
        验证结果摘要
    """
    from ..quality.validators import validate_batch

    results = validate_batch(records, record_type)

    valid_count = sum(1 for r in results if r.is_valid)
    error_count = sum(1 for r in results if not r.is_valid)

    # 统计错误类型
    error_types = {}
    for result in results:
        for issue in result.issues:
            error_types[issue.code] = error_types.get(issue.code, 0) + 1

    return {
        "total": len(results),
        "valid": valid_count,
        "invalid": error_count,
        "validity_rate": valid_count / len(results) if results else 0,
        "error_types": error_types
    }
