#===========================================================
# PharmaKG DailyMed 处理器
# Pharmaceutical Knowledge Graph - DailyMed SPL Processor
#===========================================================
# 版本: v1.0
# 描述: 从 DailyMed SPL XML 文件提取药物标签、适应症、不良反应等数据
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
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics


logger = logging.getLogger(__name__)


class DailyMedExtractionType(str, Enum):
    """DailyMed 提取类型枚举"""
    COMPOUNDS = "compounds"
    CONDITIONS = "conditions"
    BIOMARKERS = "biomarkers"
    ADVERSE_EVENTS = "adverse_events"
    RELATIONSHIPS = "relationships"
    ALL = "all"


@dataclass
class DailyMedExtractionConfig:
    """DailyMed 提取配置"""
    batch_size: int = 100
    max_files: Optional[int] = None
    query: Optional[str] = None  # 搜索查询
    ndc: Optional[str] = None  # NDC 代码
    set_id: Optional[str] = None  # SPL ID
    include_unapproved: bool = False
    include_labeler_only: bool = False
    extract_indications: bool = True
    extract_contraindications: bool = True
    extract_warnings: bool = True
    extract_adverse_reactions: bool = True
    extract_pharmacogenomics: bool = True
    extract_boxed_warnings: bool = True
    map_to_chembl: bool = True
    map_to_drugbank: bool = True
    api_base_url: str = "https://dailymed.nlm.nih.gov/dailymed/api/v2"
    download_dir: Optional[str] = None
    use_api: bool = True  # 使用 API 还是本地文件


@dataclass
class DailyMedStats:
    """DailyMed 提取统计信息"""
    compounds_extracted: int = 0
    conditions_extracted: int = 0
    biomarkers_extracted: int = 0
    adverse_events_extracted: int = 0
    indications_extracted: int = 0
    contraindications_extracted: int = 0
    warnings_extracted: int = 0
    pharmacogenomics_extracted: int = 0
    boxed_warnings_extracted: int = 0
    relationships_created: int = 0
    files_processed: int = 0
    api_calls_made: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DailyMedProcessor(BaseProcessor):
    """
    DailyMed SPL 数据处理器

    提取内容：
    - 化合物（Compounds）- 从 medication 元素
    - 疾病/状况（Conditions）- 从 indications/contraindications
    - 生物标志物（Biomarkers）- 从 pharmacogenomic 信息
    - 不良事件（AdverseEvents）- 从 adverse reactions/warnings

    关系类型：
    - TREATS - 化合物 → 疾病（适应症）
    - CONTRAINDICATED_FOR - 化合物 → 疾病（禁忌症）
    - HAS_WARNING_FOR - 化合物 → 疾病（警告）
    - HAS_BIOMARKER - 化合物 → 生物标志物
    - CAUSES_ADVERSE_EVENT - 化合物 → 不良事件
    - HAS_BOXED_WARNING - 化合物 → 不良事件
    """

    PROCESSOR_NAME = "DailyMedProcessor"
    SUPPORTED_FORMATS = ['.xml', '.zip']
    OUTPUT_SUBDIR = "dailymed"

    # DailyMed API 端点
    API_ENDPOINTS = {
        'spls': '/spls',
        'spl': '/spls/{}',
        'search': '/spls/search'
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 DailyMed 处理器

        Args:
            config: 处理器配置字典
        """
        super().__init__(config)

        # 初始化提取配置
        extraction_config = config.get('extraction', {}) if config else {}
        self.extraction_config = DailyMedExtractionConfig(**extraction_config)

        # 统计信息
        self.stats = DailyMedStats()

        # 去重集合
        self.seen_set_ids: Set[str] = set()
        self.seen_ndcs: Set[str] = set()
        self.seen_generic_names: Set[str] = set()

        # 会话用于 API 请求
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PharmaKG-DailyMedProcessor/1.0'
        })

        # 输出文件路径
        self.output_compounds = self.entities_output_dir / "dailymed_compounds.json"
        self.output_conditions = self.entities_output_dir / "dailymed_conditions.json"
        self.output_biomarkers = self.entities_output_dir / "dailymed_biomarkers.json"
        self.output_adverse_events = self.entities_output_dir / "dailymed_adverse_events.json"
        self.output_relationships = self.relationships_output_dir / "dailymed_relationships.json"
        self.output_summary = self.documents_output_dir / "dailymed_summary.json"

        # 下载目录
        if self.extraction_config.download_dir:
            self.download_dir = Path(self.extraction_config.download_dir)
        else:
            self.download_dir = self.sources_dir / "dailymed"
        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {self.PROCESSOR_NAME} with config: {self.extraction_config}")

    def scan(self, source_path: Path) -> List[Path]:
        """
        扫描源目录，查找 DailyMed XML 文件

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
            # 查找 DailyMed XML 文件
            for ext in self.SUPPORTED_FORMATS:
                files.extend(source_path.rglob(f"*{ext}"))

            # 优先选择 SPL 文件
            spl_files = [f for f in files if 'spl' in f.name.lower() or 'label' in f.name.lower()]
            if spl_files:
                files = spl_files

        logger.info(f"Scanned {source_path}: found {len(files)} DailyMed XML files")
        return files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从 DailyMed XML 文件提取数据

        Args:
            file_path: XML 文件路径

        Returns:
            提取的原始数据
        """
        logger.info(f"Extracting data from {file_path}")

        try:
            # 解析 XML
            tree = ET.parse(str(file_path))
            root = tree.getroot()

            # 处理 SPL 命名空间
            namespaces = self._get_namespaces(root)

            raw_data = {
                'compounds': [],
                'conditions': [],
                'biomarkers': [],
                'adverse_events': [],
                'indications': [],
                'contraindications': [],
                'warnings': [],
                'pharmacogenomics': [],
                'boxed_warnings': [],
                'source_file': str(file_path),
                'extraction_timestamp': datetime.now().isoformat()
            }

            # 提取化合物信息
            compound_data = self._extract_compound_from_spl(root, namespaces)
            if compound_data:
                raw_data['compounds'].append(compound_data)

                # 提取相关数据
                if self.extraction_config.extract_indications:
                    raw_data['indications'].extend(
                        self._extract_indications(root, namespaces, compound_data)
                    )
                if self.extraction_config.extract_contraindications:
                    raw_data['contraindications'].extend(
                        self._extract_contraindications(root, namespaces, compound_data)
                    )
                if self.extraction_config.extract_warnings:
                    raw_data['warnings'].extend(
                        self._extract_warnings(root, namespaces, compound_data)
                    )
                    raw_data['boxed_warnings'].extend(
                        self._extract_boxed_warnings(root, namespaces, compound_data)
                    )
                if self.extraction_config.extract_adverse_reactions:
                    raw_data['adverse_events'].extend(
                        self._extract_adverse_reactions(root, namespaces, compound_data)
                    )
                if self.extraction_config.extract_pharmacogenomics:
                    raw_data['pharmacogenomics'].extend(
                        self._extract_pharmacogenomics(root, namespaces, compound_data)
                    )

            logger.info(f"Extracted {len(raw_data['compounds'])} compounds, "
                       f"{len(raw_data['indications'])} indications, "
                       f"{len(raw_data['adverse_events'])} adverse events")

            return raw_data

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            self.stats.errors.append(f"Extraction error: {str(e)}")
            return {'error': str(e)}

    def _get_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """获取 XML 命名空间"""
        namespaces = {}
        for key, value in root.attrib.items():
            if key.startswith('xmlns:'):
                prefix = key.split(':')[1]
                namespaces[prefix] = value
            elif key == 'xmlns':
                namespaces['default'] = value

        # 添加常见的 SPL 命名空间
        if 'default' not in namespaces:
            namespaces['default'] = 'urn:hl7-org:v3'

        return namespaces

    def _extract_compound_from_spl(self, root: ET.Element, namespaces: Dict) -> Optional[Dict]:
        """从 SPL 提取化合物信息"""
        try:
            compound_data = {}

            # 基本信息
            compound_data['set_id'] = self._find_text(root, './/id[@root="2.16.840.1.113883.4.9"]', namespaces)
            compound_data['generic_name'] = self._find_text(root, './/substanceAgentSubstance/code/@displayName', namespaces)
            compound_data['brand_names'] = self._find_all_texts(root, './/manufacturerOfMedicalProduct/name', namespaces)

            # NDC 代码
            compound_data['ndc'] = self._find_text(root, './/code[@codeSystem="2.16.840.1.113883.6.69"]/@code', namespaces)

            # 剂型和给药途径
            compound_data['dosage_form'] = self._find_text(root, './/administrableDrugFormCode/@displayName', namespaces)
            compound_data['route'] = self._find_text(root, './/routeOfAdministrationCode/@displayName', namespaces)
            compound_data['strength'] = self._find_text(root, './/activeIngredient/activeIngredientStrength/substanceAmountQuantity/@value', namespaces)

            # 状态
            compound_data['marketing_status'] = self._find_text(root, './/marketingStatus/code/@displayName', namespaces)
            compound_data['approval_date'] = self._find_text(root, './/approvalDate/@value', namespaces)

            # 制造商
            compound_data['manufacturer'] = self._find_text(root, './/manufacturerOfMedicalProduct/name', namespaces)

            # 描述
            compound_data['description'] = self._find_text(root, './/text//paragraph', namespaces)

            # 成分
            compound_data['active_ingredients'] = self._extract_active_ingredients(root, namespaces)
            compound_data['inactive_ingredients'] = self._extract_inactive_ingredients(root, namespaces)

            return compound_data if compound_data.get('generic_name') else None

        except Exception as e:
            logger.warning(f"提取化合物信息失败: {e}")
            return None

    def _extract_active_ingredients(self, root: ET.Element, namespaces: Dict) -> List[Dict]:
        """提取活性成分"""
        ingredients = []
        ingredient_elems = root.findall('.//activeIngredient', namespaces)

        for elem in ingredient_elems:
            ingredient_data = {
                'name': self._find_text(elem, './/substanceAgentSubstance/code/@displayName', namespaces),
                'strength': self._find_text(elem, './/substanceAmountQuantity/@value', namespaces),
                'unit': self._find_text(elem, './/substanceAmountQuantity/@unit', namespaces)
            }
            if ingredient_data['name']:
                ingredients.append(ingredient_data)

        return ingredients

    def _extract_inactive_ingredients(self, root: ET.Element, namespaces: Dict) -> List[str]:
        """提取非活性成分"""
        ingredients = []
        ingredient_elems = root.findall('.//inactiveIngredient', namespaces)

        for elem in ingredient_elems:
            name = self._find_text(elem, './/code/@displayName', namespaces)
            if name:
                ingredients.append(name)

        return ingredients

    def _extract_indications(self, root: ET.Element, namespaces: Dict, compound_data: Dict) -> List[Dict]:
        """提取适应症"""
        indications = []

        # 查找适应症章节
        sections = root.findall('.//section', namespaces)
        for section in sections:
            title = self._find_text(section, './/title', namespaces)
            if title and 'indications' in title.lower():
                text = self._find_text(section, './/text', namespaces)

                # 解析疾病名称
                diseases = self._parse_diseases_from_text(text)

                for disease in diseases:
                    indications.append({
                        'drug_id': compound_data.get('set_id'),
                        'drug_name': compound_data.get('generic_name'),
                        'disease_name': disease,
                        'indication_type': 'primary',
                        'description': text[:500] if text else ''
                    })
                    self.stats.indications_extracted += 1

        return indications

    def _extract_contraindications(self, root: ET.Element, namespaces: Dict, compound_data: Dict) -> List[Dict]:
        """提取禁忌症"""
        contraindications = []

        # 查找禁忌症章节
        sections = root.findall('.//section', namespaces)
        for section in sections:
            title = self._find_text(section, './/title', namespaces)
            if title and 'contraindications' in title.lower():
                text = self._find_text(section, './/text', namespaces)

                # 解析疾病名称
                diseases = self._parse_diseases_from_text(text)

                for disease in diseases:
                    contraindications.append({
                        'drug_id': compound_data.get('set_id'),
                        'drug_name': compound_data.get('generic_name'),
                        'disease_name': disease,
                        'severity': 'severe',
                        'description': text[:500] if text else ''
                    })
                    self.stats.contraindications_extracted += 1

        return contraindications

    def _extract_warnings(self, root: ET.Element, namespaces: Dict, compound_data: Dict) -> List[Dict]:
        """提取警告和注意事项"""
        warnings = []

        # 查找警告章节
        sections = root.findall('.//section', namespaces)
        for section in sections:
            title = self._find_text(section, './/title', namespaces)
            if title and any(term in title.lower() for term in ['warnings', 'precautions', 'adverse reactions']):
                text = self._find_text(section, './/text', namespaces)

                # 解析疾病/状况名称
                conditions = self._parse_diseases_from_text(text)

                for condition in conditions:
                    warnings.append({
                        'drug_id': compound_data.get('set_id'),
                        'drug_name': compound_data.get('generic_name'),
                        'condition_name': condition,
                        'warning_type': 'precaution',
                        'description': text[:500] if text else ''
                    })
                    self.stats.warnings_extracted += 1

        return warnings

    def _extract_boxed_warnings(self, root: ET.Element, namespaces: Dict, compound_data: Dict) -> List[Dict]:
        """提取黑框警告"""
        boxed_warnings = []

        # 查找黑框警告章节
        sections = root.findall('.//section', namespaces)
        for section in sections:
            title = self._find_text(section, './/title', namespaces)
            if title and 'boxed warning' in title.lower():
                text = self._find_text(section, './/text', namespaces)

                # 解析不良事件
                adverse_events = self._parse_adverse_events_from_text(text)

                for event in adverse_events:
                    boxed_warnings.append({
                        'drug_id': compound_data.get('set_id'),
                        'drug_name': compound_data.get('generic_name'),
                        'event_name': event,
                        'severity': 'severe',
                        'description': text[:500] if text else '',
                        'is_boxed_warning': True
                    })
                    self.stats.boxed_warnings_extracted += 1

        return boxed_warnings

    def _extract_adverse_reactions(self, root: ET.Element, namespaces: Dict, compound_data: Dict) -> List[Dict]:
        """提取不良反应"""
        adverse_events = []

        # 查找不良反应章节
        sections = root.findall('.//section', namespaces)
        for section in sections:
            title = self._find_text(section, './/title', namespaces)
            if title and 'adverse reaction' in title.lower():
                text = self._find_text(section, './/text', namespaces)

                # 解析不良事件
                events = self._parse_adverse_events_from_text(text)

                for event in events:
                    adverse_events.append({
                        'drug_id': compound_data.get('set_id'),
                        'drug_name': compound_data.get('generic_name'),
                        'event_name': event,
                        'severity': self._determine_severity(event, text),
                        'description': text[:500] if text else ''
                    })
                    self.stats.adverse_events_extracted += 1

        return adverse_events

    def _extract_pharmacogenomics(self, root: ET.Element, namespaces: Dict, compound_data: Dict) -> List[Dict]:
        """提取药物基因组学信息"""
        pharmacogenomics = []

        # 查找药物基因组学章节
        sections = root.findall('.//section', namespaces)
        for section in sections:
            title = self._find_text(section, './/title', namespaces)
            if title and any(term in title.lower() for term in ['pharmacogenomics', 'genetic', 'biomarker']):
                text = self._find_text(section, './/text', namespaces)

                # 解析生物标志物
                biomarkers = self._parse_biomarkers_from_text(text)

                for biomarker in biomarkers:
                    pharmacogenomics.append({
                        'drug_id': compound_data.get('set_id'),
                        'drug_name': compound_data.get('generic_name'),
                        'biomarker_name': biomarker['name'],
                        'biomarker_type': biomarker.get('type', 'pharmacogenomic'),
                        'clinical_significance': biomarker.get('significance', 'unknown'),
                        'affected_population': biomarker.get('population', 'general'),
                        'description': text[:500] if text else ''
                    })
                    self.stats.pharmacogenomics_extracted += 1

        return pharmacogenomics

    def _parse_diseases_from_text(self, text: str) -> List[str]:
        """从文本中解析疾病名称"""
        if not text:
            return []

        diseases = []

        # 简单的疾病名称模式匹配
        # 匹配大写开头的词组
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:disease|disorder|syndrome|condition)\b',
            r'\b(?:treatment|indicated|used)\s+for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'\b(?:patients?\s+with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                disease = match.group(1) if match.lastindex else match.group(0)
                disease = disease.strip()
                if len(disease) > 2 and disease not in diseases:
                    diseases.append(disease)

        return diseases

    def _parse_adverse_events_from_text(self, text: str) -> List[str]:
        """从文本中解析不良事件"""
        if not text:
            return []

        events = []

        # 常见不良事件关键词
        adverse_keywords = [
            'nausea', 'vomiting', 'diarrhea', 'headache', 'dizziness',
            'rash', 'fever', 'fatigue', 'pain', 'infection',
            'hypersensitivity', 'anaphylaxis', 'hepatotoxicity',
            'cardiotoxicity', 'nephrotoxicity', 'myelosuppression'
        ]

        for keyword in adverse_keywords:
            if keyword.lower() in text.lower():
                events.append(keyword.title())

        # 提取以句号分隔的不良事件列表
        sentences = text.split('.')
        for sentence in sentences[:20]:  # 限制处理数量
            sentence = sentence.strip()
            if len(sentence) > 3 and len(sentence) < 100:
                if any(adverse in sentence.lower() for adverse in ['may cause', 'can cause', 'associated with']):
                    events.append(sentence[:50])

        return list(set(events))

    def _parse_biomarkers_from_text(self, text: str) -> List[Dict]:
        """从文本中解析生物标志物"""
        if not text:
            return []

        biomarkers = []

        # 基因/蛋白质名称模式
        gene_patterns = [
            r'\b[A-Z]{2,}\d*\b',  # CYP2D6, HLA-B*57:01
            r'\b[Cc]YP\d+[A-Z]?\b',  # CYP2C19, CYP3A4
            r'\bHLA-[A-Z]\*?\d*:?[\dA-Z]+\b',  # HLA-B*57:01
        ]

        for pattern in gene_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                biomarker_name = match.group(0)
                if biomarker_name not in [b['name'] for b in biomarkers]:
                    biomarkers.append({
                        'name': biomarker_name,
                        'type': 'pharmacogenomic',
                        'significance': self._determine_significance(text, biomarker_name),
                        'population': 'general'
                    })

        return biomarkers

    def _determine_severity(self, event: str, text: str) -> str:
        """确定不良事件严重程度"""
        text_lower = text.lower()

        if any(term in text_lower for term in ['fatal', 'life-threatening', 'severe', 'serious']):
            return 'severe'
        elif any(term in text_lower for term in ['moderate', 'significant']):
            return 'moderate'
        else:
            return 'mild'

    def _determine_significance(self, text: str, biomarker: str) -> str:
        """确定生物标志物临床意义"""
        text_lower = text.lower()

        if any(term in text_lower for term in ['contraindicated', 'should not be used', 'avoid']):
            return 'contraindication'
        elif any(term in text_lower for term in ['reduced efficacy', 'decreased response']):
            return 'reduced_efficacy'
        elif any(term in text_lower for term in ['increased risk', 'higher risk']):
            return 'increased_risk'
        elif any(term in text_lower for term in ['may require', 'dose adjustment']):
            return 'dose_adjustment'
        else:
            return 'informational'

    def _find_text(self, elem: ET.Element, path: str, namespaces: Dict) -> str:
        """安全查找元素文本"""
        try:
            # 处理带命名空间的路径
            if namespaces:
                # 替换默认命名空间
                if 'default' in namespaces:
                    path = path.replace('//', '//default:')

                found = elem.find(path, namespaces)
                if found is not None:
                    if found.text:
                        return found.text.strip()
                    # 检查属性
                    for attr, value in found.attrib.items():
                        return value.strip()
        except Exception:
            pass
        return ''

    def _find_all_texts(self, elem: ET.Element, path: str, namespaces: Dict) -> List[str]:
        """查找所有匹配的文本"""
        texts = []
        try:
            found = elem.findall(path, namespaces)
            texts = [f.text.strip() for f in found if f and f.text]
        except Exception:
            pass
        return texts

    def fetch_from_api(self) -> List[Path]:
        """从 DailyMed API 获取数据"""
        logger.info("Fetching data from DailyMed API")

        downloaded_files = []
        api_base = self.extraction_config.api_base_url

        try:
            # 构建搜索参数
            params = {}
            if self.extraction_config.query:
                params['query'] = self.extraction_config.query
            if self.extraction_config.ndc:
                params['ndc'] = self.extraction_config.ndc
            if self.extraction_config.set_id:
                params['set_id'] = self.extraction_config.set_id

            # 获取 SPL 列表
            endpoint = f"{api_base}{self.API_ENDPOINTS['search']}"
            response = self.session.get(endpoint, params=params, timeout=30)
            self.stats.api_calls_made += 1

            if response.status_code == 200:
                data = response.json()

                # 获取 SPL 列表
                spls = data.get('data', [])
                if self.extraction_config.max_files:
                    spls = spls[:self.extraction_config.max_files]

                logger.info(f"Found {len(spls)} SPLs to download")

                # 下载 SPL 文件
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(self._download_spl, spl): spl
                        for spl in spls
                    }

                    for future in as_completed(futures):
                        spl = futures[future]
                        try:
                            file_path = future.result()
                            if file_path:
                                downloaded_files.append(file_path)
                                logger.debug(f"Downloaded: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to download SPL {spl.get('setid')}: {e}")

            else:
                logger.error(f"API request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to fetch from API: {e}", exc_info=True)
            self.stats.errors.append(f"API fetch error: {str(e)}")

        return downloaded_files

    def _download_spl(self, spl: Dict) -> Optional[Path]:
        """下载单个 SPL 文件"""
        try:
            set_id = spl.get('setid')
            if not set_id:
                return None

            # 构建下载 URL
            url = f"{self.extraction_config.api_base_url}{self.API_ENDPOINTS['spl'].format(set_id)}/download"

            response = self.session.get(url, timeout=30)
            self.stats.api_calls_made += 1

            if response.status_code == 200:
                # 保存文件
                file_path = self.download_dir / f"{set_id}.xml"
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                return file_path

        except Exception as e:
            logger.warning(f"Failed to download SPL: {e}")

        return None

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
                'clinical:Condition': [],
                'clinical:Biomarker': [],
                'clinical:AdverseEvent': []
            },
            'relationships': []
        }

        # 转换化合物
        for compound_data in raw_data.get('compounds', []):
            entity = self._transform_compound(compound_data)
            if entity:
                transformed['entities']['rd:Compound'].append(entity)

        # 转换疾病/状况（从 indications, contraindications, warnings）
        conditions_map = {}
        for indication in raw_data.get('indications', []):
            condition_name = indication.get('disease_name')
            if condition_name and condition_name not in conditions_map:
                conditions_map[condition_name] = self._transform_condition(indication, 'indication')

        for contraindication in raw_data.get('contraindications', []):
            condition_name = contraindication.get('disease_name')
            if condition_name and condition_name not in conditions_map:
                conditions_map[condition_name] = self._transform_condition(contraindication, 'contraindication')

        for warning in raw_data.get('warnings', []):
            condition_name = warning.get('condition_name')
            if condition_name and condition_name not in conditions_map:
                conditions_map[condition_name] = self._transform_condition(warning, 'warning')

        transformed['entities']['clinical:Condition'].extend(conditions_map.values())

        # 转换生物标志物
        biomarkers_map = {}
        for pgx in raw_data.get('pharmacogenomics', []):
            biomarker_name = pgx.get('biomarker_name')
            if biomarker_name and biomarker_name not in biomarkers_map:
                biomarkers_map[biomarker_name] = self._transform_biomarker(pgx)

        transformed['entities']['clinical:Biomarker'].extend(biomarkers_map.values())

        # 转换不良事件
        adverse_events_map = {}
        for ae in raw_data.get('adverse_events', []):
            event_name = ae.get('event_name')
            if event_name and event_name not in adverse_events_map:
                adverse_events_map[event_name] = self._transform_adverse_event(ae)

        for bw in raw_data.get('boxed_warnings', []):
            event_name = bw.get('event_name')
            if event_name and event_name not in adverse_events_map:
                adverse_events_map[event_name] = self._transform_adverse_event(bw)

        transformed['entities']['clinical:AdverseEvent'].extend(adverse_events_map.values())

        # 创建关系
        transformed['relationships'] = self._create_relationships(raw_data)

        logger.info(f"Transformed {sum(len(v) for v in transformed['entities'].values())} entities "
                   f"and {len(transformed['relationships'])} relationships")

        return transformed

    def _transform_compound(self, compound_data: Dict) -> Optional[Dict]:
        """转换化合物数据"""
        try:
            # 生成主标识符
            set_id = compound_data.get('set_id')
            generic_name = compound_data.get('generic_name')

            if not set_id:
                return None

            primary_id = f"DAILYMED-{set_id}"

            # 去重
            if set_id in self.seen_set_ids:
                return None
            self.seen_set_ids.add(set_id)

            # 构建标识符字典
            identifiers = {
                'DailyMed': set_id,
                'NDC': compound_data.get('ndc'),
                'GenericName': generic_name
            }

            # 构建属性字典
            properties = {
                'name': generic_name,
                'generic_name': generic_name,
                'brand_names': compound_data.get('brand_names', []),
                'dosage_form': compound_data.get('dosage_form'),
                'route': compound_data.get('route'),
                'strength': compound_data.get('strength'),
                'marketing_status': compound_data.get('marketing_status'),
                'approval_date': compound_data.get('approval_date'),
                'manufacturer': compound_data.get('manufacturer'),
                'active_ingredients': compound_data.get('active_ingredients', []),
                'inactive_ingredients': compound_data.get('inactive_ingredients', []),
                'description': compound_data.get('description'),
                'source': 'DailyMed',
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

    def _transform_condition(self, condition_data: Dict, condition_type: str) -> Optional[Dict]:
        """转换疾病/状况数据"""
        try:
            condition_name = condition_data.get('disease_name') or condition_data.get('condition_name')

            if not condition_name:
                return None

            # 生成主标识符
            primary_id = f"CONDITION-{condition_name.replace(' ', '-').upper()}"

            # 构建属性字典
            properties = {
                'name': condition_name,
                'condition_type': condition_type,
                'description': condition_data.get('description', ''),
                'source': 'DailyMed',
                'version': 'latest'
            }

            return {
                'primary_id': primary_id,
                'identifiers': {'name': condition_name},
                'properties': properties,
                'entity_type': 'clinical:Condition'
            }

        except Exception as e:
            logger.warning(f"转换疾病失败: {e}")
            return None

    def _transform_biomarker(self, biomarker_data: Dict) -> Optional[Dict]:
        """转换生物标志物数据"""
        try:
            biomarker_name = biomarker_data.get('biomarker_name')

            if not biomarker_name:
                return None

            # 生成主标识符
            primary_id = f"BIOMARKER-{biomarker_name.replace(' ', '-').upper()}"

            # 构建属性字典
            properties = {
                'name': biomarker_name,
                'biomarker_type': biomarker_data.get('biomarker_type', 'pharmacogenomic'),
                'clinical_significance': biomarker_data.get('clinical_significance', 'unknown'),
                'affected_population': biomarker_data.get('affected_population', 'general'),
                'description': biomarker_data.get('description', ''),
                'source': 'DailyMed',
                'version': 'latest'
            }

            return {
                'primary_id': primary_id,
                'identifiers': {'name': biomarker_name},
                'properties': properties,
                'entity_type': 'clinical:Biomarker'
            }

        except Exception as e:
            logger.warning(f"转换生物标志物失败: {e}")
            return None

    def _transform_adverse_event(self, ae_data: Dict) -> Optional[Dict]:
        """转换不良事件数据"""
        try:
            event_name = ae_data.get('event_name')

            if not event_name:
                return None

            # 生成主标识符
            primary_id = f"ADVERSE-EVENT-{event_name.replace(' ', '-').upper()}"

            # 构建属性字典
            properties = {
                'name': event_name,
                'severity': ae_data.get('severity', 'unknown'),
                'is_boxed_warning': ae_data.get('is_boxed_warning', False),
                'description': ae_data.get('description', ''),
                'source': 'DailyMed',
                'version': 'latest'
            }

            return {
                'primary_id': primary_id,
                'identifiers': {'name': event_name},
                'properties': properties,
                'entity_type': 'clinical:AdverseEvent'
            }

        except Exception as e:
            logger.warning(f"转换不良事件失败: {e}")
            return None

    def _create_relationships(self, raw_data: Dict) -> List[Dict]:
        """创建关系"""
        relationships = []

        # 适应症关系
        for indication in raw_data.get('indications', []):
            rel = self._create_treats_relationship(indication)
            if rel:
                relationships.append(rel)

        # 禁忌症关系
        for contraindication in raw_data.get('contraindications', []):
            rel = self._create_contraindicated_relationship(contraindication)
            if rel:
                relationships.append(rel)

        # 警告关系
        for warning in raw_data.get('warnings', []):
            rel = self._create_warning_relationship(warning)
            if rel:
                relationships.append(rel)

        # 生物标志物关系
        for pgx in raw_data.get('pharmacogenomics', []):
            rel = self._create_biomarker_relationship(pgx)
            if rel:
                relationships.append(rel)

        # 不良事件关系
        for ae in raw_data.get('adverse_events', []):
            rel = self._create_adverse_event_relationship(ae)
            if rel:
                relationships.append(rel)

        # 黑框警告关系
        for bw in raw_data.get('boxed_warnings', []):
            rel = self._create_boxed_warning_relationship(bw)
            if rel:
                relationships.append(rel)

        self.stats.relationships_created = len(relationships)
        return relationships

    def _create_treats_relationship(self, indication: Dict) -> Optional[Dict]:
        """创建治疗关系"""
        try:
            drug_id = indication.get('drug_id')
            disease_name = indication.get('disease_name')

            if not drug_id or not disease_name:
                return None

            return {
                'relationship_type': 'TREATS',
                'source_entity_id': f"Compound-DAILYMED-{drug_id}",
                'target_entity_id': f"CONDITION-{disease_name.replace(' ', '-').upper()}",
                'properties': {
                    'indication_type': indication.get('indication_type', 'primary'),
                    'description': indication.get('description', '')
                },
                'source': 'DailyMed-indications'
            }

        except Exception as e:
            logger.warning(f"创建治疗关系失败: {e}")
            return None

    def _create_contraindicated_relationship(self, contraindication: Dict) -> Optional[Dict]:
        """创建禁忌关系"""
        try:
            drug_id = contraindication.get('drug_id')
            disease_name = contraindication.get('disease_name')

            if not drug_id or not disease_name:
                return None

            return {
                'relationship_type': 'CONTRAINDICATED_FOR',
                'source_entity_id': f"Compound-DAILYMED-{drug_id}",
                'target_entity_id': f"CONDITION-{disease_name.replace(' ', '-').upper()}",
                'properties': {
                    'severity': contraindication.get('severity', 'severe'),
                    'description': contraindication.get('description', '')
                },
                'source': 'DailyMed-contraindications'
            }

        except Exception as e:
            logger.warning(f"创建禁忌关系失败: {e}")
            return None

    def _create_warning_relationship(self, warning: Dict) -> Optional[Dict]:
        """创建警告关系"""
        try:
            drug_id = warning.get('drug_id')
            condition_name = warning.get('condition_name')

            if not drug_id or not condition_name:
                return None

            return {
                'relationship_type': 'HAS_WARNING_FOR',
                'source_entity_id': f"Compound-DAILYMED-{drug_id}",
                'target_entity_id': f"CONDITION-{condition_name.replace(' ', '-').upper()}",
                'properties': {
                    'warning_type': warning.get('warning_type', 'precaution'),
                    'description': warning.get('description', '')
                },
                'source': 'DailyMed-warnings'
            }

        except Exception as e:
            logger.warning(f"创建警告关系失败: {e}")
            return None

    def _create_biomarker_relationship(self, pgx: Dict) -> Optional[Dict]:
        """创建生物标志物关系"""
        try:
            drug_id = pgx.get('drug_id')
            biomarker_name = pgx.get('biomarker_name')

            if not drug_id or not biomarker_name:
                return None

            return {
                'relationship_type': 'HAS_BIOMARKER',
                'source_entity_id': f"Compound-DAILYMED-{drug_id}",
                'target_entity_id': f"BIOMARKER-{biomarker_name.replace(' ', '-').upper()}",
                'properties': {
                    'clinical_significance': pgx.get('clinical_significance', 'unknown'),
                    'affected_population': pgx.get('affected_population', 'general'),
                    'description': pgx.get('description', '')
                },
                'source': 'DailyMed-pharmacogenomics'
            }

        except Exception as e:
            logger.warning(f"创建生物标志物关系失败: {e}")
            return None

    def _create_adverse_event_relationship(self, ae: Dict) -> Optional[Dict]:
        """创建不良事件关系"""
        try:
            drug_id = ae.get('drug_id')
            event_name = ae.get('event_name')

            if not drug_id or not event_name:
                return None

            return {
                'relationship_type': 'CAUSES_ADVERSE_EVENT',
                'source_entity_id': f"Compound-DAILYMED-{drug_id}",
                'target_entity_id': f"ADVERSE-EVENT-{event_name.replace(' ', '-').upper()}",
                'properties': {
                    'severity': ae.get('severity', 'unknown'),
                    'description': ae.get('description', '')
                },
                'source': 'DailyMed-adverse_reactions'
            }

        except Exception as e:
            logger.warning(f"创建不良事件关系失败: {e}")
            return None

    def _create_boxed_warning_relationship(self, bw: Dict) -> Optional[Dict]:
        """创建黑框警告关系"""
        try:
            drug_id = bw.get('drug_id')
            event_name = bw.get('event_name')

            if not drug_id or not event_name:
                return None

            return {
                'relationship_type': 'HAS_BOXED_WARNING',
                'source_entity_id': f"Compound-DAILYMED-{drug_id}",
                'target_entity_id': f"ADVERSE-EVENT-{event_name.replace(' ', '-').upper()}",
                'properties': {
                    'severity': 'severe',
                    'is_boxed_warning': True,
                    'description': bw.get('description', '')
                },
                'source': 'DailyMed-boxed_warnings'
            }

        except Exception as e:
            logger.warning(f"创建黑框警告关系失败: {e}")
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

        logger.info(f"Validation passed: {total_entities} entities, {len(relationships)} relationships")
        return True

    def process(
        self,
        source_path,
        output_to: Optional[str] = None,
        save_intermediate: bool = True
    ) -> ProcessingResult:
        """处理 DailyMed 数据的主流程"""
        start_time = datetime.now()
        source_path = Path(source_path)

        logger.info(f"[{self.PROCESSOR_NAME}] 开始处理: {source_path}")

        # 重置状态
        self._metrics = ProcessingMetrics()
        self.stats = DailyMedStats()
        self.seen_set_ids.clear()
        self.seen_ndcs.clear()
        self.seen_generic_names.clear()

        try:
            # 1. 获取文件列表
            files = []

            if self.extraction_config.use_api:
                # 从 API 获取数据
                logger.info("Using DailyMed API to fetch data")
                files = self.fetch_from_api()
            else:
                # 扫描本地文件
                files = self.scan(source_path)

            self._metrics.files_scanned = len(files)

            if not files:
                self._warnings.append(f"未找到 DailyMed 文件: {source_path}")
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

            for file_path in files[:self.extraction_config.max_files] if self.extraction_config.max_files else files:
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
                output_path = self._save_dailymed_results(
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
                'source': 'DailyMed SPL Database',
                'extraction_config': {
                    'max_files': self.extraction_config.max_files,
                    'query': self.extraction_config.query,
                    'use_api': self.extraction_config.use_api,
                    'api_calls_made': self.stats.api_calls_made
                },
                'stats': {
                    'compounds': len([e for e in all_entities if e.get('entity_type') == 'rd:Compound']),
                    'conditions': len([e for e in all_entities if e.get('entity_type') == 'clinical:Condition']),
                    'biomarkers': len([e for e in all_entities if e.get('entity_type') == 'clinical:Biomarker']),
                    'adverse_events': len([e for e in all_entities if e.get('entity_type') == 'clinical:AdverseEvent']),
                    'indications': self.stats.indications_extracted,
                    'contraindications': self.stats.contraindications_extracted,
                    'boxed_warnings': self.stats.boxed_warnings_extracted
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

    def _save_dailymed_results(
        self,
        all_entities: List[Dict],
        all_relationships: List[Dict],
        entities_by_type: Dict[str, List[Dict]],
        output_to: Optional[str] = None
    ) -> Path:
        """保存 DailyMed 处理结果"""
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

            type_name = entity_type.replace(':', '_').lower()
            entities_file = output_dir / f"dailymed_{type_name}s_{timestamp}.json"

            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 {len(entities)} 个 {entity_type} 到: {entities_file}")

        # 保存关系
        if all_relationships:
            relationships_file = output_dir / f"dailymed_relationships_{timestamp}.json"

            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(all_relationships, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 {len(all_relationships)} 个关系到: {relationships_file}")

        # 保存处理摘要
        summary = {
            "processor": self.PROCESSOR_NAME,
            "source": "DailyMed SPL Database",
            "timestamp": timestamp,
            "extraction_config": {
                'max_files': self.extraction_config.max_files,
                'query': self.extraction_config.query,
                'use_api': self.extraction_config.use_api
            },
            "statistics": {
                "compounds_extracted": self.stats.compounds_extracted,
                "conditions_extracted": self.stats.conditions_extracted,
                "biomarkers_extracted": self.stats.biomarkers_extracted,
                "adverse_events_extracted": self.stats.adverse_events_extracted,
                "indications_extracted": self.stats.indications_extracted,
                "contraindications_extracted": self.stats.contraindications_extracted,
                "warnings_extracted": self.stats.warnings_extracted,
                "pharmacogenomics_extracted": self.stats.pharmacogenomics_extracted,
                "boxed_warnings_extracted": self.stats.boxed_warnings_extracted,
                "relationships_created": self.stats.relationships_created,
                "processing_time_seconds": self.stats.processing_time_seconds,
                "api_calls_made": self.stats.api_calls_made
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

        summary_file = output_dir / f"dailymed_summary_{timestamp}.json"
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
        description='DailyMed SPL 数据处理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 处理本地 DailyMed XML 文件
  python -m processors.dailymed_processor /path/to/dailymed/files --use-api false

  # 从 API 获取数据
  python -m processors.dailymed_processor --query "cancer" --max-files 100

  # 按 NDC 搜索
  python -m processors.dailymed_processor --ndc "1234-5678"

  # 自定义输出目录
  python -m processors.dailymed_processor --output /custom/output/path
        """
    )

    parser.add_argument(
        'source_path',
        nargs='?',
        default='.',
        help='DailyMed XML 文件目录（默认使用 API）'
    )

    parser.add_argument(
        '--output',
        help='输出目录（默认为 data/processed/documents/dailymed/）'
    )

    parser.add_argument(
        '--query',
        help='搜索查询（使用 API）'
    )

    parser.add_argument(
        '--ndc',
        help='NDC 代码（使用 API）'
    )

    parser.add_argument(
        '--set-id',
        help='SPL ID（使用 API）'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        default=100,
        help='最大处理文件数（默认: 100）'
    )

    parser.add_argument(
        '--use-api',
        type=lambda x: x.lower() == 'true',
        default=True,
        help='使用 DailyMed API（默认: true）'
    )

    parser.add_argument(
        '--api-url',
        default='https://dailymed.nlm.nih.gov/dailymed/api/v2',
        help='DailyMed API 基础 URL'
    )

    parser.add_argument(
        '--download-dir',
        help='下载文件保存目录'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='批处理大小（默认: 100）'
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
            'max_files': args.max_files,
            'query': args.query,
            'ndc': args.ndc,
            'set_id': args.set_id,
            'api_base_url': args.api_url,
            'use_api': args.use_api,
            'download_dir': args.download_dir
        }
    }

    # 创建处理器
    processor = DailyMedProcessor(config)

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
        print(f"  疾病/状况: {stats.get('conditions', 0)}")
        print(f"  生物标志物: {stats.get('biomarkers', 0)}")
        print(f"  不良事件: {stats.get('adverse_events', 0)}")
        print(f"  适应症: {stats.get('indications', 0)}")
        print(f"  禁忌症: {stats.get('contraindications', 0)}")
        print(f"  黑框警告: {stats.get('boxed_warnings', 0)}")

        if stats.get('api_calls_made', 0) > 0:
            print(f"  API 调用: {stats.get('api_calls_made', 0)}")

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
