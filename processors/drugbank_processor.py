#===========================================================
# PharmaKG DrugBank 处理器
# Pharmaceutical Knowledge Graph - DrugBank Processor
#===========================================================
# 版本: v1.0
# 描述: 从 DrugBank XML 文件提取化合物、靶点、药物相互作用等数据
#===========================================================

import logging
import xml.etree.ElementTree as ET
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Generator
from enum import Enum
import hashlib
import re

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


class DrugBankExtractionType(str, Enum):
    """DrugBank 提取类型枚举"""
    COMPOUNDS = "compounds"
    TARGETS = "targets"
    INTERACTIONS = "interactions"
    PHARMACOKINETICS = "pharmacokinetics"
    ALL = "all"


@dataclass
class DrugBankExtractionConfig:
    """DrugBank 提取配置"""
    batch_size: int = 1000
    limit_compounds: Optional[int] = None
    include_withdrawn: bool = False
    include_experimental: bool = True
    include_illicit: bool = False
    min_approval_level: str = "all"  # all, approved, investigational, experimental
    extract_interactions: bool = True
    extract_pharmacokinetics: bool = True
    extract_enzymes: bool = True
    extract_transporters: bool = True
    extract_targets: bool = True
    map_to_chembl: bool = True


@dataclass
class DrugBankStats:
    """DrugBank 提取统计信息"""
    compounds_extracted: int = 0
    targets_extracted: int = 0
    interactions_extracted: int = 0
    pharmacokinetics_extracted: int = 0
    enzymes_extracted: int = 0
    transporters_extracted: int = 0
    pathways_extracted: int = 0
    relationships_created: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DrugBankProcessor(BaseProcessor):
    """
    DrugBank XML 数据处理器

    提取内容：
    - 化合物（Compounds）- 从 drug 元素
    - 靶点（Targets）- 从 targets 元素
    - 酶（Enzymes）- 从 enzymes 元素
    - 转运体（Transporters）- 从 transporters 元素
    - 药物相互作用（Drug-Drug Interactions）- 从 drug-interactions 元素
    - 药代动力学（Pharmacokinetics）- 从 pharmacokinetics 元素

    关系类型：
    - INTERACTS_WITH - 化合物 → 化合物（药物相互作用）
    - METABOLIZED_BY - 化合物 → 靶点（酶）
    - TRANSPORTED_BY - 化合物 → 靶点（转运体）
    - TARGETS - 化合物 → 靶点（作用机制）
    - IS_PRODRUG_OF - 化合物 → 化合物
    - HAS_SALT - 化合物 → 化合物
    - HAS_BRAND - 化合物 → 化合物（品牌-通用关系）
    """

    PROCESSOR_NAME = "DrugBankProcessor"
    SUPPORTED_FORMATS = ['.xml']
    OUTPUT_SUBDIR = "drugbank"

    # DrugBank XML 命名空间
    DRUGBANK_NS = {'db': 'http://drugbank.ca'}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 DrugBank 处理器

        Args:
            config: 处理器配置字典
        """
        super().__init__(config)

        # 初始化提取配置
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = DrugBankExtractionConfig(**extraction_config)

        # 统计信息
        self.stats = DrugBankStats()

        # 去重集合
        self.seen_drugbank_ids: Set[str] = set()
        self.seen_inchikeys: Set[str] = set()
        self.seen_unii: Set[str] = set()

        # 输出文件路径
        self.output_compounds = self.entities_output_dir / "drugbank_compounds.json"
        self.output_targets = self.entities_output_dir / "drugbank_targets.json"
        self.output_interactions = self.relationships_output_dir / "drugbank_interactions.json"
        self.output_pharmacokinetics = self.entities_output_dir / "drugbank_pharmacokinetics.json"
        self.output_summary = self.documents_output_dir / "drugbank_summary.json"

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录，查找 DrugBank XML 文件

        Args:
            source_path: 源目录路径

        Returns:
            找到的 XML 文件列表
        """
        source_path = Path(source_path)
        files = []

        if source_path.is_file():
            if source_path.suffix in self.SUPPORTED_FORMATS:
                files.append(source_path)
        else:
            # 查找 DrugBank XML 文件
            for ext in self.SUPPORTED_FORMATS:
                files.extend(source_path.rglob(f"*{ext}"))

            # 优先选择 drugbank.xml
            drugbank_files = [f for f in files if 'drugbank' in f.name.lower()]
            if drugbank_files:
                files = drugbank_files

        logger.info(f"Scanned {source_path}: found {len(files)} DrugBank XML files")
        return files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从 DrugBank XML 文件提取数据

        Args:
            file_path: XML 文件路径

        Returns:
            提取的原始数据
        """
        logger.info(f"Extracting data from {file_path}")

        try:
            # 使用 iterparse 处理大文件
            raw_data = {
                'compounds': [],
                'targets': [],
                'interactions': [],
                'pharmacokinetics': [],
                'enzymes': [],
                'transporters': [],
                'pathways': [],
                'source_file': str(file_path),
                'extraction_timestamp': datetime.now().isoformat()
            }

            # 获取文件大小用于进度跟踪
            file_size = file_path.stat().st_size
            processed_bytes = 0

            # 使用 iterparse 逐步处理
            context = ET.iterparse(str(file_path), events=('start', 'end'))
            context = iter(context)

            # 跳过开始事件
            event, root = next(context)

            drug_count = 0
            for event, elem in context:
                if event == 'end':
                    # 检查是否为 drug 元素
                    if elem.tag.endswith('drug'):
                        try:
                            drug_data = self._extract_drug_element(elem)

                            if self._should_include_drug(drug_data):
                                raw_data['compounds'].append(drug_data)
                                drug_count += 1

                                # 提取相关数据
                                if self.extraction_config.extract_targets:
                                    raw_data['targets'].extend(
                                        self._extract_targets_from_drug(elem, drug_data)
                                    )
                                if self.extraction_config.extract_enzymes:
                                    raw_data['enzymes'].extend(
                                        self._extract_enzymes_from_drug(elem, drug_data)
                                    )
                                if self.extraction_config.extract_transporters:
                                    raw_data['transporters'].extend(
                                        self._extract_transporters_from_drug(elem, drug_data)
                                    )
                                if self.extraction_config.extract_interactions:
                                    raw_data['interactions'].extend(
                                        self._extract_interactions_from_drug(elem, drug_data)
                                    )

                                # 清理元素以节省内存
                                elem.clear()

                            # 检查限制
                            if self.extraction_config.limit_compounds:
                                if drug_count >= self.extraction_config.limit_compounds:
                                    break

                        except Exception as e:
                            logger.warning(f"Error processing drug element: {e}")
                            self.stats.warnings.append(f"Drug element error: {str(e)}")

                    # 移除已处理的元素
                    if elem.tag.endswith('drug'):
                        root.remove(elem)

            logger.info(f"Extracted {len(raw_data['compounds'])} compounds, "
                       f"{len(raw_data['targets'])} targets, "
                       f"{len(raw_data['interactions'])} interactions")

            return raw_data

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            self.stats.errors.append(f"Extraction error: {str(e)}")
            return {'error': str(e)}

    def _should_include_drug(self, drug_data: Dict) -> bool:
        """
        判断是否应该包含该药物

        Args:
            drug_data: 药物数据

        Returns:
            是否包含
        """
        # 检查批准状态
        approval_status = drug_data.get('approval_status', '').lower()
        groups = drug_data.get('groups', [])

        # 过滤撤回药物
        if not self.extraction_config.include_withdrawn:
            if 'withdrawn' in approval_status or 'Withdrawn' in groups:
                return False

        # 过滤非法药物
        if not self.extraction_config.include_illicit:
            if 'illicit' in groups:
                return False

        # 过滤实验性药物
        if not self.extraction_config.include_experimental:
            if 'experimental' in groups:
                return False

        # 检查最低批准级别
        if self.extraction_config.min_approval_level != "all":
            if self.extraction_config.min_approval_level == "approved":
                if approval_status != 'approved':
                    return False

        return True

    def _extract_drug_element(self, elem: ET.Element) -> Dict:
        """
        从 drug 元素提取药物数据

        Args:
            elem: drug XML 元素

        Returns:
            药物数据字典
        """
        drug_data = {}

        # 基本信息
        drug_data['drugbank_id'] = self._get_text(elem, './/{http://drugbank.ca}drugbank-id[@primary="true"]')
        drug_data['name'] = self._get_text(elem, './/{http://drugbank.ca}name')
        drug_data['description'] = self._get_text(elem, './/{http://drugbank.ca}description')
        drug_data['cas_number'] = self._get_text(elem, './/{http://drugbank.ca}cas-number')
        drug_data['unii'] = self._get_text(elem, './/{http://drugbank.ca}unii')
        drug_data['state'] = self._get_text(elem, './/{http://drugbank.ca}state')

        # 类型
        drug_data['type'] = self._get_text(elem, './/{http://drugbank.ca}type')
        drug_data['groups'] = self._get_list(elem, './/{http://drugbank.ca}groups/{http://drugbank.ca}group')

        # 状态
        drug_data['approval_status'] = self._get_text(elem, './/{http://drugbank.ca}approval-status')
        drug_data['approved'] = self._get_bool(elem, './/{http://drugbank.ca}approved')
        drug_data['withdrawn'] = self._get_bool(elem, './/{http://drugbank.ca}withdrawn')

        # 化学结构
        drug_data['inchi'] = self._get_text(elem, './/{http://drugbank.ca}inchi')
        drug_data['inchikey'] = self._get_text(elem, './/{http://drugbank.ca}inchikey')
        drug_data['smiles'] = self._get_text(elem, './/{http://drugbank.ca}smiles')

        # 外部标识符
        drug_data['chembl_id'] = self._get_text(elem, './/{http://drugbank.ca}external-identifiers/'
                                                     '{http://drugbank.ca}external-identifier['
                                                     '{http://drugbank.ca}resource="ChEMBL"]/'
                                                     '{http://drugbank.ca}identifier')
        drug_data['pubchem_cid'] = self._get_text(elem, './/{http://drugbank.ca}external-identifiers/'
                                                        '{http://drugbank.ca}external-identifier['
                                                        '{http://drugbank.ca}resource="PubChem Compound"]/'
                                                        '{http://drugbank.ca}identifier')

        # 品牌名称
        drug_data['brand_names'] = self._get_list(elem, './/{http://drugbank.ca}international-brands/'
                                                       '{http://drugbank.ca}international-brand/'
                                                       '{http://drugbank.ca}name')

        # 剂型和给药途径
        drug_data['dosage_forms'] = self._get_list(elem, './/{http://drugbank.ca}dosage/'
                                                        '{http://drugbank.ca}dosage/{http://drugbank.ca}form')
        drug_data['routes_of_administration'] = self._get_list(
            elem, './/{http://drugbank.ca}dosage/{http://drugbank.ca}dosage/{http://drugbank.ca}route')

        # ATC 代码
        drug_data['atc_codes'] = self._extract_atc_codes(elem)

        # 药代动力学
        drug_data['pharmacokinetics'] = self._extract_pharmacokinetics(elem)

        # 毒性
        drug_data['toxicity'] = self._extract_toxicity(elem)

        # 作用机制
        drug_data['mechanism_of_action'] = self._extract_mechanism_of_action(elem)

        # 前药信息
        drug_data['is_prodrug'] = self._get_bool(elem, './/{http://drugbank.ca}prodrug')
        drug_data['parent_drug'] = self._get_text(elem, './/{http://drugbank.ca}parent-drug/'
                                                       '{http://drugbank.ca}drugbank-id')

        # 盐类信息
        drug_data['salts'] = self._get_list(elem, './/{http://drugbank.ca}salts/{http://drugbank.ca}salt/'
                                                   '{http://drugbank.ca}drugbank-id')

        # 合成参考
        drug_data['synthesis_reference'] = self._get_text(elem, './/{http://drugbank.ca}synthesis-reference')

        return drug_data

    def _extract_targets_from_drug(self, elem: ET.Element, drug_data: Dict) -> List[Dict]:
        """从药物元素提取靶点"""
        targets = []
        target_elems = elem.findall('.//{http://drugbank.ca}targets/{http://drugbank.ca}target')

        for target_elem in target_elems:
            target_data = {
                'id': self._get_text(target_elem, './/{http://drugbank.ca}id'),
                'name': self._get_text(target_elem, './/{http://drugbank.ca}name'),
                'organism': self._get_text(target_elem, './/{http://drugbank.ca}organism'),
                'action': self._get_text(target_elem, './/{http://drugbank.ca}action'),
                'drugbank_id': drug_data.get('drugbank_id'),
                'known_action': self._get_bool(target_elem, './/{http://drugbank.ca}known-action'),
                'polypeptide_id': self._get_text(target_elem, './/{http://drugbank.ca}polypeptide/@id')
            }

            # 外部标识符
            target_data['uniprot_id'] = self._get_text(
                target_elem, './/{http://drugbank.ca}polypeptide/{http://drugbank.ca}external-identifiers/'
                            '{http://drugbank.ca}external-identifier[{http://drugbank.ca}resource="UniProtKB"]/'
                            '{http://drugbank.ca}identifier')

            # 基因名称
            target_data['gene_names'] = self._get_list(
                target_elem, './/{http://drugbank.ca}polypeptide/{http://drugbank.ca}genes/'
                            '{http://drugbank.ca}gene/{http://drugbank.ca}name')

            if target_data['id']:
                targets.append(target_data)
                self.stats.targets_extracted += 1

        return targets

    def _extract_enzymes_from_drug(self, elem: ET.Element, drug_data: Dict) -> List[Dict]:
        """从药物元素提取酶"""
        enzymes = []
        enzyme_elems = elem.findall('.//{http://drugbank.ca}enzymes/{http://drugbank.ca}enzyme')

        for enzyme_elem in enzyme_elems:
            enzyme_data = {
                'id': self._get_text(enzyme_elem, './/{http://drugbank.ca}id'),
                'name': self._get_text(enzyme_elem, './/{http://drugbank.ca}name'),
                'organism': self._get_text(enzyme_elem, './/{http://drugbank.ca}organism'),
                'drugbank_id': drug_data.get('drugbank_id'),
                'uniprot_id': self._get_text(
                    enzyme_elem, './/{http://drugbank.ca}polypeptide/{http://drugbank.ca}external-identifiers/'
                                '{http://drugbank.ca}external-identifier[{http://drugbank.ca}resource="UniProtKB"]/'
                                '{http://drugbank.ca}identifier')
            }

            if enzyme_data['id']:
                enzymes.append(enzyme_data)
                self.stats.enzymes_extracted += 1

        return enzymes

    def _extract_transporters_from_drug(self, elem: ET.Element, drug_data: Dict) -> List[Dict]:
        """从药物元素提取转运体"""
        transporters = []
        transporter_elems = elem.findall('.//{http://drugbank.ca}transporters/{http://drugbank.ca}transporter')

        for transporter_elem in transporter_elems:
            transporter_data = {
                'id': self._get_text(transporter_elem, './/{http://drugbank.ca}id'),
                'name': self._get_text(transporter_elem, './/{http://drugbank.ca}name'),
                'organism': self._get_text(transporter_elem, './/{http://drugbank.ca}organism'),
                'drugbank_id': drug_data.get('drugbank_id'),
                'uniprot_id': self._get_text(
                    transporter_elem, './/{http://drugbank.ca}polypeptide/{http://drugbank.ca}external-identifiers/'
                                    '{http://drugbank.ca}external-identifier[{http://drugbank.ca}resource="UniProtKB"]/'
                                    '{http://drugbank.ca}identifier')
            }

            if transporter_data['id']:
                transporters.append(transporter_data)
                self.stats.transporters_extracted += 1

        return transporters

    def _extract_interactions_from_drug(self, elem: ET.Element, drug_data: Dict) -> List[Dict]:
        """从药物元素提取药物相互作用"""
        interactions = []
        interaction_elems = elem.findall('.//{http://drugbank.ca}drug-interactions/'
                                         '{http://drugbank.ca}drug-interaction')

        for interaction_elem in interaction_elems:
            interaction_data = {
                'drugbank_id': drug_data.get('drugbank_id'),
                'drug_name': drug_data.get('name'),
                'interacting_drug_id': self._get_text(interaction_elem, './/{http://drugbank.ca}drugbank-id'),
                'interacting_drug_name': self._get_text(interaction_elem, './/{http://drugbank.ca}name'),
                'description': self._get_text(interaction_elem, './/{http://drugbank.ca}description'),
                'severity': self._extract_severity(interaction_elem),
                'interaction_type': self._extract_interaction_type(interaction_elem)
            }

            if interaction_data['interacting_drug_id']:
                interactions.append(interaction_data)
                self.stats.interactions_extracted += 1

        return interactions

    def _extract_atc_codes(self, elem: ET.Element) -> List[Dict]:
        """提取 ATC 代码"""
        atc_codes = []
        atc_elems = elem.findall('.//{http://drugbank.ca}atc-codes/{http://drugbank.ca}atc-code')

        for atc_elem in atc_elems:
            atc_data = {
                'code': atc_elem.get('code'),
                'level': atc_elem.get('level'),
                'name': self._get_text(atc_elem, './/{http://drugbank.ca}code')
            }
            if atc_data['code']:
                atc_codes.append(atc_data)

        return atc_codes

    def _extract_pharmacokinetics(self, elem: ET.Element) -> Dict:
        """提取药代动力学数据"""
        pk_data = {
            'absorption': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                              '{http://drugbank.ca}absorption'),
            'distribution': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                                 '{http://drugbank.ca}distribution'),
            'metabolism': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                               '{http://drugbank.ca}metabolism'),
            'excretion': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                              '{http://drugbank.ca}excretion'),
            'half_life': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                              '{http://drugbank.ca}half-life'),
            'clearance': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                              '{http://drugbank.ca}clearance'),
            'route_of_elimination': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                                        '{http://drugbank.ca}route-of-elimination'),
            'volume_of_distribution': self._get_text(elem, './/{http://drugbank.ca}pharmacokinetics/'
                                                            '{http://drugbank.ca}volume-of-distribution')
        }

        # 检查是否有任何数据
        if any(pk_data.values()):
            self.stats.pharmacokinetics_extracted += 1
            return pk_data

        return {}

    def _extract_toxicity(self, elem: ET.Element) -> Dict:
        """提取毒性数据"""
        toxicity_data = {
            'toxicity_summary': self._get_text(elem, './/{http://drugbank.ca}toxicity'),
            'carcinogenicity': self._get_text(elem, './/{http://drugbank.ca}carcinogenicity'),
            'mutagenicity': self._get_text(elem, './/{http://drugbank.ca}mutagenicity'),
            'ld50': self._get_text(elem, './/{http://drugbank.ca}ld50'),
            'toxicity_category': self._get_text(elem, './/{http://drugbank.ca}toxicity-category')
        }

        # 检查是否有任何数据
        if any(toxicity_data.values()):
            return toxicity_data

        return {}

    def _extract_mechanism_of_action(self, elem: ET.Element) -> Dict:
        """提取作用机制"""
        moa_data = {
            'action': self._get_text(elem, './/{http://drugbank.ca}mechanism-of-action/'
                                            '{http://drugbank.ca}action'),
            'description': self._get_text(elem, './/{http://drugbank.ca}mechanism-of-action/'
                                                 '{http://drugbank.ca}description-of-action'),
            'targets': self._get_list(elem, './/{http://drugbank.ca}mechanism-of-action/'
                                            '{http://drugbank.ca}mechanism-of-action/'
                                            '{http://drugbank.ca}targets/{http://drugbank.ca}target/'
                                            '{http://drugbank.ca}name')
        }

        # 检查是否有任何数据
        if any(moa_data.values()):
            return moa_data

        return {}

    def _extract_severity(self, elem: ET.Element) -> str:
        """从描述中提取严重程度"""
        description = self._get_text(elem, './/{http://drugbank.ca}description')

        if not description:
            return 'unknown'

        description_lower = description.lower()

        if any(term in description_lower for term in ['contraindicated', 'serious', 'severe']):
            return 'severe'
        elif any(term in description_lower for term in ['moderate', 'caution', 'monitor']):
            return 'moderate'
        elif any(term in description_lower for term in ['minor', 'mild']):
            return 'mild'
        else:
            return 'unknown'

    def _extract_interaction_type(self, elem: ET.Element) -> str:
        """从描述中提取相互作用类型"""
        description = self._get_text(elem, './/{http://drugbank.ca}description')

        if not description:
            return 'unknown'

        description_lower = description.lower()

        if any(term in description_lower for term in ['increase', 'enhance', 'potentiate']):
            return 'increases_effect'
        elif any(term in description_lower for term in ['decrease', 'reduce', 'diminish']):
            return 'decreases_effect'
        elif 'metabolized' in description_lower:
            return 'metabolism'
        elif 'absorption' in description_lower:
            return 'absorption'
        else:
            return 'other'

    def _get_text(self, elem: ET.Element, path: str) -> str:
        """安全获取元素文本"""
        try:
            found = elem.find(path)
            if found is not None and found.text:
                return found.text.strip()
        except Exception:
            pass
        return ''

    def _get_bool(self, elem: ET.Element, path: str) -> bool:
        """安全获取布尔值"""
        text = self._get_text(elem, path)
        return text.lower() in ['true', 'yes', '1']

    def _get_list(self, elem: ET.Element, path: str) -> List[str]:
        """获取文本列表"""
        items = []
        try:
            found = elem.findall(path)
            items = [f.text.strip() for f in found if f.text]
        except Exception:
            pass
        return items

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据为知识图谱格式

        Args:
            raw_data: 原始提取数据

        Returns:
            转换后的实体和关系数据
        """
        if 'error' in raw_data:
            return raw_data

        logger.info("Transforming extracted data")

        transformed = {
            'entities': {
                'rd:Compound': [],
                'rd:Target': []
            },
            'relationships': []
        }

        # 转换化合物
        for compound_data in raw_data.get('compounds', []):
            entity = self._transform_compound(compound_data)
            if entity:
                transformed['entities']['rd:Compound'].append(entity)

        # 转换靶点（合并 targets、enzymes、transporters）
        all_targets = []
        all_targets.extend(raw_data.get('targets', []))
        all_targets.extend(raw_data.get('enzymes', []))
        all_targets.extend(raw_data.get('transporters', []))

        for target_data in all_targets:
            entity = self._transform_target(target_data)
            if entity:
                transformed['entities']['rd:Target'].append(entity)

        # 创建关系
        transformed['relationships'] = self._create_relationships(raw_data)

        logger.info(f"Transformed {sum(len(v) for v in transformed['entities'].values())} entities "
                   f"and {len(transformed['relationships'])} relationships")

        return transformed

    def _transform_compound(self, compound_data: Dict) -> Optional[Dict]:
        """转换化合物数据为知识图谱实体格式"""
        try:
            # 生成主标识符
            primary_id = compound_data.get('drugbank_id') or f"DRUGBANK-{compound_data.get('name')}"

            # 去重
            if primary_id in self.seen_drugbank_ids:
                return None
            self.seen_drugbank_ids.add(primary_id)

            inchikey = compound_data.get('inchikey')
            if inchikey and inchikey in self.seen_inchikeys:
                return None
            if inchikey:
                self.seen_inchikeys.add(inchikey)

            # 构建标识符字典
            identifiers = {
                'DrugBank': compound_data.get('drugbank_id'),
                'ChEMBL': compound_data.get('chembl_id'),
                'PubChem': compound_data.get('pubchem_cid'),
                'UNII': compound_data.get('unii'),
                'CAS': compound_data.get('cas_number'),
                'InChIKey': inchikey
            }

            # 确定药物类型
            drug_type = compound_data.get('type', 'SmallMolecule')
            groups = compound_data.get('groups', [])

            if 'Biotech' in groups:
                drug_type = 'Biotech'
            elif 'Cell' in groups:
                drug_type = 'CellTherapy'
            elif 'Vaccine' in groups:
                drug_type = 'Vaccine'

            # 构建属性字典
            properties = {
                'name': compound_data.get('name'),
                'generic_name': compound_data.get('name'),
                'brand_names': compound_data.get('brand_names', []),
                'drug_type': drug_type,
                'approval_status': compound_data.get('approval_status'),
                'groups': groups,
                'state': compound_data.get('state'),
                'mechanism_of_action': compound_data.get('mechanism_of_action', {}),
                'pharmacokinetics': compound_data.get('pharmacokinetics', {}),
                'toxicity': compound_data.get('toxicity', {}),
                'dosage_forms': compound_data.get('dosage_forms', []),
                'routes_of_administration': compound_data.get('routes_of_administration', []),
                'atc_codes': compound_data.get('atc_codes', []),
                'chemical_structure': {
                    'smiles': compound_data.get('smiles'),
                    'inchi': compound_data.get('inchi'),
                    'inchikey': inchikey
                },
                'is_prodrug': compound_data.get('is_prodrug', False),
                'synthesis_reference': compound_data.get('synthesis_reference'),
                'description': compound_data.get('description'),
                'source': 'DrugBank',
                'version': 'latest'
            }

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Compound'
            }

        except Exception as e:
            logger.warning(f"转换化合物失败: {e}")
            return None

    def _transform_target(self, target_data: Dict) -> Optional[Dict]:
        """转换靶点数据为知识图谱实体格式"""
        try:
            # 生成主标识符
            target_id = target_data.get('id')
            uniprot_id = target_data.get('uniprot_id')
            primary_id = uniprot_id or f"DRUGBANK-TARGET-{target_id}"

            if not target_id:
                return None

            # 构建标识符字典
            identifiers = {
                'DrugBank': target_id,
                'UniProt': uniprot_id
            }

            # 确定靶点类型
            target_type = 'Target'
            if 'enzyme' in str(target_data).lower():
                target_type = 'Enzyme'
            elif 'transporter' in str(target_data).lower():
                target_type = 'Transporter'

            # 构建属性字典
            properties = {
                'name': target_data.get('name'),
                'target_type': target_type,
                'organism': target_data.get('organism'),
                'gene_names': target_data.get('gene_names', []),
                'action': target_data.get('action'),
                'known_action': target_data.get('known_action', True),
                'source': 'DrugBank',
                'version': 'latest'
            }

            return {
                'primary_id': primary_id,
                'identifiers': identifiers,
                'properties': properties,
                'entity_type': 'rd:Target'
            }

        except Exception as e:
            logger.warning(f"转换靶点失败: {e}")
            return None

    def _create_relationships(self, raw_data: Dict) -> List[Dict]:
        """从原始数据创建关系"""
        relationships = []

        # 药物相互作用
        for interaction in raw_data.get('interactions', []):
            rel = self._create_interaction_relationship(interaction)
            if rel:
                relationships.append(rel)

        # 酶关系
        for enzyme in raw_data.get('enzymes', []):
            rel = self._create_enzyme_relationship(enzyme)
            if rel:
                relationships.append(rel)

        # 转运体关系
        for transporter in raw_data.get('transporters', []):
            rel = self._create_transporter_relationship(transporter)
            if rel:
                relationships.append(rel)

        # 靶点关系
        for target in raw_data.get('targets', []):
            rel = self._create_target_relationship(target)
            if rel:
                relationships.append(rel)

        self.stats.relationships_created = len(relationships)
        return relationships

    def _create_interaction_relationship(self, interaction: Dict) -> Optional[Dict]:
        """创建药物相互作用关系"""
        try:
            source_id = interaction.get('drugbank_id')
            target_id = interaction.get('interacting_drug_id')

            if not source_id or not target_id:
                return None

            return {
                'relationship_type': 'INTERACTS_WITH',
                'source_entity_id': f"Compound-{source_id}",
                'target_entity_id': f"Compound-{target_id}",
                'properties': {
                    'description': interaction.get('description'),
                    'severity': interaction.get('severity'),
                    'interaction_type': interaction.get('interaction_type'),
                    'source_drug_name': interaction.get('drug_name'),
                    'target_drug_name': interaction.get('interacting_drug_name')
                },
                'source': 'DrugBank-interactions'
            }

        except Exception as e:
            logger.warning(f"创建相互作用关系失败: {e}")
            return None

    def _create_enzyme_relationship(self, enzyme: Dict) -> Optional[Dict]:
        """创建酶关系"""
        try:
            source_id = enzyme.get('drugbank_id')
            target_id = enzyme.get('uniprot_id') or enzyme.get('id')

            if not source_id or not target_id:
                return None

            return {
                'relationship_type': 'METABOLIZED_BY',
                'source_entity_id': f"Compound-{source_id}",
                'target_entity_id': f"Target-{target_id}",
                'properties': {
                    'enzyme_name': enzyme.get('name'),
                    'organism': enzyme.get('organism')
                },
                'source': 'DrugBank-enzymes'
            }

        except Exception as e:
            logger.warning(f"创建酶关系失败: {e}")
            return None

    def _create_transporter_relationship(self, transporter: Dict) -> Optional[Dict]:
        """创建转运体关系"""
        try:
            source_id = transporter.get('drugbank_id')
            target_id = transporter.get('uniprot_id') or transporter.get('id')

            if not source_id or not target_id:
                return None

            return {
                'relationship_type': 'TRANSPORTED_BY',
                'source_entity_id': f"Compound-{source_id}",
                'target_entity_id': f"Target-{target_id}",
                'properties': {
                    'transporter_name': transporter.get('name'),
                    'organism': transporter.get('organism')
                },
                'source': 'DrugBank-transporters'
            }

        except Exception as e:
            logger.warning(f"创建转运体关系失败: {e}")
            return None

    def _create_target_relationship(self, target: Dict) -> Optional[Dict]:
        """创建靶点关系"""
        try:
            source_id = target.get('drugbank_id')
            target_id = target.get('uniprot_id') or target.get('id')

            if not source_id or not target_id:
                return None

            return {
                'relationship_type': 'TARGETS',
                'source_entity_id': f"Compound-{source_id}",
                'target_entity_id': f"Target-{target_id}",
                'properties': {
                    'action': target.get('action'),
                    'known_action': target.get('known_action'),
                    'target_name': target.get('name')
                },
                'source': 'DrugBank-targets'
            }

        except Exception as e:
            logger.warning(f"创建靶点关系失败: {e}")
            return None

    def validate(self, data: Dict[str, Any]) -> bool:
        """验证转换后的数据"""
        if 'error' in data:
            return False

        entities = data.get('entities', {})
        relationships = data.get('relationships', [])

        # 检查实体
        total_entities = sum(len(v) for v in entities.values())
        if total_entities == 0:
            self.stats.warnings.append("No entities extracted")
            return False

        # 验证必需字段
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if not self._validate_entity(entity):
                    self.stats.warnings.append(f"Invalid entity in {entity_type}")
                    return False

        logger.info(f"Validation passed: {total_entities} entities, {len(relationships)} relationships")
        return True

    def _validate_entity(self, entity: Dict) -> bool:
        """验证实体数据"""
        if 'primary_id' not in entity:
            return False

        if 'properties' not in entity:
            return False

        return True

    def process(
        self,
        source_path,
        output_to: Optional[str] = None,
        save_intermediate: bool = True
    ) -> ProcessingResult:
        """处理 DrugBank 数据的主流程"""
        start_time = datetime.now()
        source_path = Path(source_path)

        logger.info(f"[{self.PROCESSOR_NAME}] 开始处理: {source_path}")

        # 重置状态
        self._metrics = ProcessingMetrics()
        self.stats = DrugBankStats()
        self.seen_drugbank_ids.clear()
        self.seen_inchikeys.clear()
        self.seen_unii.clear()

        try:
            # 1. 扫描文件
            files = self.scan(source_path)
            self._metrics.files_scanned = len(files)

            if not files:
                self._warnings.append(f"未找到 DrugBank XML 文件: {source_path}")
                return ProcessingResult(
                    status=ProcessingStatus.SKIPPED,
                    processor_name=self.PROCESSOR_NAME,
                    source_path=str(source_path),
                    metrics=self._metrics,
                    warnings=self._warnings
                )

            # 2. 处理每个文件
            all_entities = []
            all_relationships = []

            for file_path in files:
                try:
                    logger.info(f"Processing {file_path}")

                    # 提取
                    raw_data = self.extract(file_path)
                    if 'error' in raw_data:
                        self._warnings.append(f"提取失败: {file_path.name} - {raw_data['error']}")
                        self._metrics.files_failed += 1
                        continue

                    # 转换
                    transformed_data = self.transform(raw_data)
                    if not transformed_data:
                        self._metrics.files_skipped += 1
                        continue

                    # 验证
                    if not self.validate(transformed_data):
                        self._warnings.append(f"数据验证失败: {file_path.name}")
                        self._metrics.files_skipped += 1
                        continue

                    # 收集实体和关系
                    entities_dict = transformed_data.get('entities', {})
                    relationships = transformed_data.get('relationships', [])

                    # 展平实体字典
                    for entity_type, entity_list in entities_dict.items():
                        for entity in entity_list:
                            all_entities.append({
                                **entity,
                                'entity_type': entity_type
                            })

                    all_relationships.extend(relationships)

                    self._metrics.files_processed += 1
                    self._metrics.entities_extracted += len(all_entities)
                    self._metrics.relationships_extracted += len(all_relationships)

                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}", exc_info=True)
                    self._errors.append(f"{file_path.name}: {str(e)}")
                    self._metrics.files_failed += 1

            # 3. 保存结果
            output_path = None
            if save_intermediate and (all_entities or all_relationships):
                output_path = self._save_drugbank_results(
                    all_entities,
                    all_relationships,
                    transformed_data.get('entities', {}),
                    output_to
                )

            # 4. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            self._metrics.processing_time_seconds = processing_time
            self.stats.processing_time_seconds = processing_time

            # 5. 确定最终状态
            if self._metrics.files_failed > 0:
                status = ProcessingStatus.PARTIAL
            elif self._metrics.files_processed == 0:
                status = ProcessingStatus.SKIPPED
            else:
                status = ProcessingStatus.COMPLETED

            # 添加元数据
            metadata = {
                'processor': self.PROCESSOR_NAME,
                'source': 'DrugBank XML Database',
                'extraction_config': {
                    'limit_compounds': self.extraction_config.limit_compounds,
                    'include_withdrawn': self.extraction_config.include_withdrawn,
                    'include_experimental': self.extraction_config.include_experimental
                },
                'stats': {
                    'compounds': len([e for e in all_entities if e.get('entity_type') == 'rd:Compound']),
                    'targets': len([e for e in all_entities if e.get('entity_type') == 'rd:Target']),
                    'interactions': len([r for r in all_relationships if r.get('relationship_type') == 'INTERACTS_WITH']),
                    'enzymes': self.stats.enzymes_extracted,
                    'transporters': self.stats.transporters_extracted
                }
            }

            logger.info(f"[{self.PROCESSOR_NAME}] 处理完成: "
                       f"处理={self._metrics.files_processed}, "
                       f"失败={self._metrics.files_failed}, "
                       f"实体={len(all_entities)}, "
                       f"关系={len(all_relationships)}, "
                       f"耗时={processing_time:.2f}秒")

            return ProcessingResult(
                status=status,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_path),
                metrics=self._metrics,
                entities=all_entities,
                relationships=all_relationships,
                errors=self._errors,
                warnings=self._warnings,
                metadata=metadata,
                output_path=str(output_path) if output_path else None
            )

        except Exception as e:
            logger.error(f"[{self.PROCESSOR_NAME}] 处理失败: {e}", exc_info=True)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.PROCESSOR_NAME,
                source_path=str(source_path),
                metrics=self._metrics,
                errors=[str(e)]
            )

    def _save_drugbank_results(
        self,
        all_entities: List[Dict],
        all_relationships: List[Dict],
        entities_by_type: Dict[str, List[Dict]],
        output_to: Optional[str] = None
    ) -> Path:
        """保存 DrugBank 处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定输出目录
        if output_to:
            output_dir = Path(output_to)
        else:
            output_dir = self.documents_output_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # 按类型保存实体
        for entity_type, entities in entities_by_type.items():
            if not entities:
                continue

            type_name = entity_type.replace('rd:', '').lower()
            entities_file = output_dir / f"drugbank_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 {len(entities)} 个 {entity_type} 到: {entities_file}")

        # 保存关系
        if all_relationships:
            relationships_file = output_dir / f"drugbank_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(all_relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 {len(all_relationships)} 个关系到: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "DrugBank XML Database",
            "timestamp": timestamp,
            "extraction_config": {
                'limit_compounds': self.extraction_config.limit_compounds,
                'include_withdrawn': self.extraction_config.include_withdrawn,
                'include_experimental': self.extraction_config.include_experimental
            },
            "statistics": {
                "compounds_extracted": self.stats.compounds_extracted,
                "targets_extracted": self.stats.targets_extracted,
                "interactions_extracted": self.stats.interactions_extracted,
                "pharmacokinetics_extracted": self.stats.pharmacokinetics_extracted,
                "enzymes_extracted": self.stats.enzymes_extracted,
                "transporters_extracted": self.stats.transporters_extracted,
                "relationships_created": self.stats.relationships_created,
                "processing_time_seconds": self.stats.processing_time_seconds
            },
            "entities_by_type": {
                entity_type: len(entities)
                for entity_type, entities in entities_by_type.items()
            },
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "errors": self.stats.errors,
            "warnings": self.stats.warnings
        }

        summary_file = output_dir / f"drugbank_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"保存处理摘要到: {summary_file}")

        return summary_file


#===========================================================
# 命令行接口
#===========================================================

def main():
    """命令行主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='DrugBank XML 数据库处理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 处理 DrugBank XML 文件
  python -m processors.drugbank_processor /path/to/drugbank.xml

  # 限制提取数量
  python -m processors.drugbank_processor /path/to/drugbank.xml --limit-compounds 1000

  # 自定义输出目录
  python -m processors.drugbank_processor /path/to/drugbank.xml --output /custom/output/path

  # 包含撤回药物
  python -m processors.drugbank_processor /path/to/drugbank.xml --include-withdrawn

  # 只提取已批准药物
  python -m processors.drugbank_processor /path/to/drugbank.xml --min-approval-level approved
        """
    )

    parser.add_argument(
        'source_path',
        help='DrugBank XML 文件路径或目录'
    )

    parser.add_argument(
        '--output',
        help='输出目录（默认为 data/processed/documents/drugbank/）'
    )

    parser.add_argument(
        '--limit-compounds',
        type=int,
        help='化合物数量限制'
    )

    parser.add_argument(
        '--include-withdrawn',
        action='store_true',
        help='包含撤回药物'
    )

    parser.add_argument(
        '--no-experimental',
        action='store_true',
        help='不包含实验性药物'
    )

    parser.add_argument(
        '--min-approval-level',
        choices=['all', 'approved', 'investigational'],
        default='all',
        help='最低批准级别（默认: all）'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='批处理大小（默认: 1000）'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 构建配置
    config = {
        'extraction': {
            'batch_size': args.batch_size,
            'limit_compounds': args.limit_compounds,
            'include_withdrawn': args.include_withdrawn,
            'include_experimental': not args.no_experimental,
            'min_approval_level': args.min_approval_level
        }
    }

    # 创建处理器
    processor = DrugBankProcessor(config)

    # 处理数据
    result = processor.process(
        source_path=args.source_path,
        output_to=args.output,
        save_intermediate=True
    )

    # 输出结果
    print(f"\n{'='*60}")
    print(f"处理状态: {result.status.value}")
    print(f"{'='*60}")
    print(f"处理的文件: {result.metrics.files_processed}")
    print(f"失败的文件: {result.metrics.files_failed}")
    print(f"跳过的文件: {result.metrics.files_skipped}")
    print(f"提取的实体: {result.metrics.entities_extracted}")
    print(f"提取的关系: {result.metrics.relationships_extracted}")
    print(f"处理时间: {result.metrics.processing_time_seconds:.2f} 秒")

    if result.metadata:
        stats = result.metadata.get('stats', {})
        print(f"\n详细统计:")
        print(f"  化合物: {stats.get('compounds', 0)}")
        print(f"  靶点: {stats.get('targets', 0)}")
        print(f"  相互作用: {stats.get('interactions', 0)}")
        print(f"  酶: {stats.get('enzymes', 0)}")
        print(f"  转运体: {stats.get('transporters', 0)}")

    if result.errors:
        print(f"\n错误 ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"  - {error}")
        if len(result.errors) > 5:
            print(f"  ... 还有 {len(result.errors) - 5} 个错误")

    if result.warnings:
        print(f"\n警告 ({len(result.warnings)}):")
        for warning in result.warnings[:5]:
            print(f"  - {warning}")
        if len(result.warnings) > 5:
            print(f"  ... 还有 {len(result.warnings) - 5} 个警告")

    if result.output_path:
        print(f"\n输出文件: {result.output_path}")

    # 返回状态码
    return 0 if result.status == ProcessingStatus.COMPLETED else 1


if __name__ == '__main__':
    exit(main())
