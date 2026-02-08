#===========================================================
# PharmaKG PDA Technical Reports PDF数据处理器
# Pharmaceutical Knowledge Graph - PDA TR PDF Processor
#===========================================================
# 版本: v1.0
# 描述: 处理PDA (Parenteral Drug Association) 技术报告PDF文档，
#       提取制药设施、设备制造商、质量标准、检测方法等实体和关系
#===========================================================

import json
import logging
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import threading

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from processors.base import (
    BaseProcessor, ProcessingResult, ProcessingStatus,
    ProcessingMetrics
)

logger = logging.getLogger(__name__)


#===========================================================
# 数据模型
#===========================================================

@dataclass
class PDAReportMetadata:
    """PDA技术报告元数据"""
    report_number: str = ""
    title: str = ""
    year: int = 0
    revision: str = ""
    category: str = ""
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_number': self.report_number,
            'title': self.title,
            'year': self.year,
            'revision': self.revision,
            'category': self.category,
            'language': self.language
        }


@dataclass
class FacilityEntity:
    """设施实体"""
    name: str
    facility_type: str
    classification: str = ""
    environmental_requirements: Dict[str, Any] = field(default_factory=dict)
    design_criteria: Dict[str, Any] = field(default_factory=dict)
    intended_use: str = ""
    confidence: float = 0.8


@dataclass
class EquipmentManufacturerEntity:
    """设备制造商实体"""
    manufacturer_name: str
    equipment_name: str = ""
    equipment_type: str = ""
    specifications: Dict[str, Any] = field(default_factory=dict)
    validation_requirements: List[str] = field(default_factory=list)
    confidence: float = 0.8


@dataclass
class QualityStandardEntity:
    """质量标准实体"""
    standard_name: str
    standard_type: str
    requirements: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    monitoring_parameters: List[str] = field(default_factory=list)
    confidence: float = 0.9


@dataclass
class AssayEntity:
    """检测方法实体"""
    assay_name: str
    assay_type: str
    test_method: str = ""
    sampling_plan: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    limits: Dict[str, str] = field(default_factory=dict)
    frequency: str = ""
    confidence: float = 0.8


@dataclass
class ProcessEntity:
    """工艺实体"""
    process_name: str
    process_type: str
    critical_parameters: List[str] = field(default_factory=list)
    validation_approach: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    confidence: float = 0.8


#===========================================================
# 主处理器类
#===========================================================

class PDAPDFProcessor(BaseProcessor):
    """
    PDA技术报告PDF处理器

    处理PDA (Parenteral Drug Association) 发布的技术报告PDF文档，
    从中提取制药生产相关的实体和关系：
    - 设施 (sc:Facility): 洁净室、生产区、包装区等
    - 制造商 (sc:Manufacturer): 设备制造商及其产品
    - 质量标准 (sc:QualityStandard): ISO、EU GMP等标准
    - 检测方法 (rd:Assay): 质量控制检测方法
    - 工艺 (sc:Process): 灭菌、过滤、灌装等工艺
    """

    PROCESSOR_NAME = "PDAPDFProcessor"
    SUPPORTED_FORMATS = ['.pdf']
    OUTPUT_SUBDIR = "pda_technical_reports"

    # PDA技术报告分类映射
    PDA_CATEGORIES = {
        'TR1': 'sterilization',
        'TR11': 'sterilization',
        'TR12': 'components',
        'TR13': 'environmental_monitoring',
        'TR14': 'purification',
        'TR15': 'filtration',
        'TR16': 'sterilization',
        'TR21': 'sterilization',
        'TR22': 'process_simulation',
        'TR26': 'sterilization',
        'TR29': 'inspection',
        'TR30': 'sterilization',
        'TR34': 'aseptic_processing',
        'TR41': 'risk_assessment',
        'TR43': 'bioburden',
        'TR44': 'filtration',
        'TR49': 'biotechnology',
        'TR51': 'sterilization',
        'TR54': 'cleaning',
        'TR60': 'packaging',
        'TR69': 'sterilization',
        'TR70': 'cleaning',
        'TR78': 'sterilization',
        'TR83': 'containers',
        'TR87': 'sterilization',
        'TR88': 'containers',
        'TR98': 'visual_inspection',
        'TR99': 'filtration',
        'TR100': 'air_systems',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        super().__init__(config)

        # 检查依赖
        if not PDFPLUMBER_AVAILABLE and not PYPDF2_AVAILABLE:
            raise ImportError(
                "PDF processing library required. "
                "Install with: pip install pdfplumber PyPDF2"
            )

        # 配置参数
        self.use_ocr = config.get('use_ocr', False)
        self.ocr_language = config.get('ocr_language', 'eng')
        self.batch_size = config.get('batch_size', 10)
        self.min_confidence = config.get('min_confidence', 0.6)
        self.cache_enabled = config.get('cache_enabled', True)
        self.parallel_workers = config.get('parallel_workers', 1)

        # 初始化模式
        self._init_patterns()

        # 缓存
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()

        # 统计信息
        self.extraction_stats = defaultdict(int)

    def _init_patterns(self):
        """初始化正则表达式模式"""

        # PDA报告编号模式: TR1, TR13, TR34等
        self.pda_number_pattern = re.compile(
            r'\bPDA\s*TR(\d+)\b',
            re.IGNORECASE
        )

        # 质量标准模式
        self.standard_patterns = {
            'iso': re.compile(
                r'\bISO\s*(\d+(?:-\d+)?)\b',
                re.IGNORECASE
            ),
            'eu_gmp': re.compile(
                r'\bEU\s*GMP\s*(?:Annex\s+(\d+|[A-Z]))?\b',
                re.IGNORECASE
            ),
            'fda': re.compile(
                r'\bFDA\s*(?:Guidance|Guide|Regulation)?\s*(?:\d+(?:\.\d+)?)?\b',
                re.IGNORECASE
            ),
            'usp': re.compile(
                r'\b(?:USP|<(\d+(?:-\d+)?)>)\b',
                re.IGNORECASE
            ),
            'ep': re.compile(
                r'\b(?:European\s*Pharmacopoeia|EP)\s*(\d+(?:\.\d+)?)?\b',
                re.IGNORECASE
            ),
            'astm': re.compile(
                r'\bASTM\s*(?:E|F)?(\d+(?:-\d+)?)?\b',
                re.IGNORECASE
            ),
        }

        # 洁净室分级模式
        self.cleanroom_class_patterns = [
            re.compile(r'\bISO\s*Class\s*(\d+)\b', re.IGNORECASE),
            re.compile(r'\bISO\s*(\d+)\b', re.IGNORECASE),
            re.compile(r'\bEU\s*GMP\s*(Grade\s*([A-D]))\b', re.IGNORECASE),
            re.compile(r'\bGrade\s*([A-D])\b', re.IGNORECASE),
            re.compile(r'\bClass\s*(\d{3,6})\b', re.IGNORECASE),
        ]

        # 设施类型模式
        self.facility_type_patterns = [
            re.compile(r'\b(clean\s*room|cleanroom)\b', re.IGNORECASE),
            re.compile(r'\b(manufactur(?:ing|e)\s*area|production\s*area)\b', re.IGNORECASE),
            re.compile(r'\b(packag(?:ing|e)\s*area|packing\s*area)\b', re.IGNORECASE),
            re.compile(r'\b(aseptic\s*(?:area|room|suite))\b', re.IGNORECASE),
            re.compile(r'\b(stor(?:age|e)\s*area|warehouse)\b', re.IGNORECASE),
            re.compile(r'\b(corridor|passage|hall)\b', re.IGNORECASE),
            re.compile(r'\b(chang(?:ing|e)\s*room|gown\s*room)\b', re.IGNORECASE),
        ]

        # 工艺类型模式
        self.process_type_patterns = [
            re.compile(r'\b(moist\s*heat\s*sterilization|steam\s*sterilization)\b', re.IGNORECASE),
            re.compile(r'\b(dry\s*heat\s*sterilization)\b', re.IGNORECASE),
            re.compile(r'\b(gamma\s*irradiation|gamma\s*sterilization)\b', re.IGNORECASE),
            re.compile(r'\b(ethylene\s*oxide|ETO|EtO)\s*sterilization\b', re.IGNORECASE),
            re.compile(r'\b(filtration|steriliz(?:ing|e)\s*filtration)\b', re.IGNORECASE),
            re.compile(r'\b(fill(?:ing|e)|aseptic\s*fill)\b', re.IGNORECASE),
            re.compile(r'\b(lyophilization|freeze\s*drying)\b', re.IGNORECASE),
            re.compile(r'\b(inspect(?:ion|e)|visual\s*inspect(?:ion|e))\b', re.IGNORECASE),
            re.compile(r'\b(media\s*fill|process\s*simulation)\b', re.IGNORECASE),
            re.compile(r'\b(clean(?:ing|e)|sanitiz(?:ation|e))\b', re.IGNORECASE),
        ]

        # 检测方法模式
        self.assay_type_patterns = [
            re.compile(r'\b(microbio(?:logical|logic)\s*(?:test|examination|analysis))\b', re.IGNORECASE),
            re.compile(r'\b(endotoxin|LAL)\s*test\b', re.IGNORECASE),
            re.compile(r'\b(sterylity|sterile)\s*test\b', re.IGNORECASE),
            re.compile(r'\b(particle\s*(?:count|test)|particulate)\b', re.IGNORECASE),
            re.compile(r'\b(bioburden)\b', re.IGNORECASE),
            re.compile(r'\b(HPLC|UPLC|LC)\b', re.IGNORECASE),
            re.compile(r'\b(GC|gas\s*chromatography)\b', re.IGNORECASE),
            re.compile(r'\b(FTIR|IR)\s*(?:spectroscopy)?\b', re.IGNORECASE),
            re.compile(r'\b(visibility|clarity)\s*test\b', re.IGNORECASE),
            re.compile(r'\b(pH)\s*(?:determination|measurement)?\b', re.IGNORECASE),
            re.compile(r'\b(osmolality|osmolarity)\b', re.IGNORECASE),
        ]

        # 环境参数模式 (温度、湿度、压差等)
        self.environmental_param_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*[°-]?\s*C\b'),  # 温度
            re.compile(r'(\d+(?:\.\d+)?)\s*%?\s*RH?\b'),  # 湿度
            re.compile(r'(?:≥|>=|more than|greater than)\s*(\d+)\s*(?:CFU|m³)\b', re.IGNORECASE),  # 微生物限度
            re.compile(r'(\d+)\s*CFU/(m³|ft³|plate)\b', re.IGNORECASE),  # 菌落
            re.compile(r'(\d+(?:\.\d+)?)\s*Pa(?:scal)?\b'),  # 压力
            re.compile(r'(\d+)\s*(?:air changes|ACH)\b', re.IGNORECASE),  # 换气次数
            re.compile(r'(?:≥|>=|<=|≤)\s*(\d+(?:\.\d+)?)\s*(?:µm|micron)\b'),  # 粒径
            re.compile(r'(\d+(?:,\d+)*)\s*particles/(m³|ft³)\b', re.IGNORECASE),  # 粒子数
        ]

        # 频率模式
        self.frequency_patterns = [
            re.compile(r'\b(once|per batch|batch-wise)\b', re.IGNORECASE),
            re.compile(r'\b(daily|every day)\b', re.IGNORECASE),
            re.compile(r'\b(weekly|every week)\b', re.IGNORECASE),
            re.compile(r'\b(monthly|every month)\b', re.IGNORECASE),
            re.compile(r'\b(quarterly|every quarter|every 3 months)\b', re.IGNORECASE),
            re.compile(r'\b(annually|yearly|every year)\b', re.IGNORECASE),
            re.compile(r'\b(per shift|each shift)\b', re.IGNORECASE),
            re.compile(r'\b(continuous|continuously|on-line)\b', re.IGNORECASE),
        ]

        # 设备制造商模式
        self.manufacturer_patterns = [
            re.compile(r'\b([A-Z][a-zA-Z0-9\s&\-]+(?:Corporation|Corp|Inc|LLC|Ltd|GmbH|AG|SA|S\.p\.A))\b'),
            re.compile(r'\b([A-Z][a-zA-Z0-9\s&\-]+(?:Technologies|Systems|Equipment|Machinery|Engineering))\b'),
        ]

        # 数值范围模式
        self.range_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*[~-]\s*(\d+(?:\.\d+)?)\s*([°C%F]+)?',
            re.IGNORECASE
        )

        # 单位模式
        self.unit_patterns = [
            re.compile(r'\b(°C|C|F|K)\b'),  # 温度
            re.compile(r'\b(%RH?|relative humidity)\b', re.IGNORECASE),  # 湿度
            re.compile(r'\b(Pa|bar|psi|mbar)\b', re.IGNORECASE),  # 压力
            re.compile(r'\b(CFU|m³|ft³|L|ml|g|kg)\b', re.IGNORECASE),  # 其他
        ]

    #===========================================================
    # BaseProcessor 抽象方法实现
    #===========================================================

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """
        扫描源目录，查找PDA TR PDF文件

        Args:
            source_path: 源目录或单个PDF文件路径

        Returns:
            待处理的PDF文件列表
        """
        source_path = Path(source_path)

        if source_path.is_file():
            if source_path.suffix in self.SUPPORTED_FORMATS:
                return [source_path]
            return []

        # 扫描目录
        pdf_files = []
        for ext in self.SUPPORTED_FORMATS:
            pdf_files.extend(source_path.glob(f"*{ext}"))
            pdf_files.extend(source_path.rglob(f"PDA*{ext}"))

        # 过滤已处理的文件
        unprocessed = [f for f in pdf_files if not self.is_processed(f)]

        self.logger.info(f"扫描完成: {len(unprocessed)}/{len(pdf_files)} 文件待处理")
        return unprocessed

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        从PDA TR PDF文件中提取数据

        Args:
            file_path: PDF文件路径

        Returns:
            提取的数据字典
        """
        self.logger.debug(f"提取文件: {file_path.name}")

        try:
            # 检查缓存
            if self.cache_enabled:
                file_hash = self.generate_file_hash(file_path)
                if file_hash in self._cache:
                    self.logger.debug(f"使用缓存: {file_path.name}")
                    return self._cache[file_hash]

            # 提取PDF内容
            pdf_content = self._extract_pdf_content(file_path)

            if not pdf_content['text'].strip():
                self.logger.warning(f"PDF文件无文本内容: {file_path.name}")
                return {}

            # 解析元数据
            metadata = self._parse_pda_metadata(file_path, pdf_content)

            # 提取实体
            entities = self._extract_entities(
                pdf_content['text'],
                pdf_content['tables'],
                metadata
            )

            # 提取关系
            relationships = self._extract_relationships(
                entities,
                pdf_content['text'],
                metadata
            )

            result = {
                'file_path': str(file_path),
                'metadata': metadata.to_dict(),
                'full_text': pdf_content['text'][:10000],  # 保存前10000字符
                'entities': entities,
                'relationships': relationships,
                'page_count': pdf_content['page_count'],
                'has_tables': len(pdf_content['tables']) > 0
            }

            # 更新缓存
            if self.cache_enabled:
                with self._cache_lock:
                    self._cache[file_hash] = result

            return result

        except Exception as e:
            self.logger.error(f"提取失败 {file_path.name}: {e}", exc_info=True)
            self.extraction_stats['extraction_errors'] += 1
            return {}

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据为标准格式

        Args:
            raw_data: 原始提取数据

        Returns:
            转换后的数据
        """
        if not raw_data or 'entities' not in raw_data:
            return {'entities': [], 'relationships': []}

        # 转换实体为标准格式
        transformed_entities = []
        for entity in raw_data['entities']:
            if isinstance(entity, dict):
                transformed_entities.append(entity)
            elif hasattr(entity, 'to_dict'):
                transformed_entities.append(entity.to_dict())
            else:
                # 转换dataclass为字典
                if hasattr(entity, '__dataclass_fields__'):
                    transformed_entities.append({
                        k: v for k, v in entity.__dict__.items()
                        if not k.startswith('_')
                    })

        # 转换关系为标准格式
        transformed_relationships = []
        for rel in raw_data.get('relationships', []):
            if isinstance(rel, dict):
                transformed_relationships.append(rel)
            elif hasattr(rel, 'to_dict'):
                transformed_relationships.append(rel.to_dict())

        return {
            'entities': transformed_entities,
            'relationships': transformed_relationships,
            'metadata': raw_data.get('metadata', {})
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证数据质量

        Args:
            data: 待验证数据

        Returns:
            是否验证通过
        """
        if not isinstance(data, dict):
            return False

        if 'entities' not in data or 'relationships' not in data:
            return False

        if not isinstance(data['entities'], list):
            return False

        if not isinstance(data['relationships'], list):
            return False

        # 验证实体必需字段
        for entity in data['entities'][:5]:  # 抽样检查
            if not isinstance(entity, dict):
                continue
            if 'entity_type' not in entity or 'name' not in entity:
                self.logger.warning(f"实体缺少必需字段: {entity}")
                return False

        return True

    #===========================================================
    # PDF内容提取
    #===========================================================

    def _extract_pdf_content(self, file_path: Path) -> Dict[str, Any]:
        """
        提取PDF内容（文本和表格）

        Args:
            file_path: PDF文件路径

        Returns:
            包含文本、表格、页面数等的字典
        """
        content = {
            'text': '',
            'tables': [],
            'page_count': 0,
            'metadata': {}
        }

        # 优先使用pdfplumber（更好的表格提取）
        if PDFPLUMBER_AVAILABLE:
            content = self._extract_with_pdfplumber(file_path, content)

        # 备用PyPDF2
        elif PYPDF2_AVAILABLE:
            content = self._extract_with_pypdf2(file_path, content)

        # 如果仍然没有文本且启用OCR
        if not content['text'].strip() and self.use_ocr and TESSERACT_AVAILABLE:
            content = self._extract_with_ocr(file_path, content)

        return content

    def _extract_with_pdfplumber(self, file_path: Path, content: Dict[str, Any]) -> Dict[str, Any]:
        """使用pdfplumber提取内容"""
        try:
            with pdfplumber.open(file_path) as pdf:
                content['page_count'] = len(pdf.pages)
                content['metadata'] = pdf.metadata or {}

                full_text = []
                all_tables = []

                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文本
                    text = page.extract_text() or ''
                    full_text.append(text)

                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            all_tables.append({
                                'page': page_num,
                                'data': table
                            })

                content['text'] = '\n'.join(full_text)
                content['tables'] = all_tables

        except Exception as e:
            self.logger.warning(f"pdfplumber提取失败: {e}")

        return content

    def _extract_with_pypdf2(self, file_path: Path, content: Dict[str, Any]) -> Dict[str, Any]:
        """使用PyPDF2提取内容"""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                content['page_count'] = len(pdf_reader.pages)
                content['metadata'] = pdf_reader.metadata or {}

                full_text = []
                for page in pdf_reader.pages:
                    text = page.extract_text() or ''
                    full_text.append(text)

                content['text'] = '\n'.join(full_text)

        except Exception as e:
            self.logger.warning(f"PyPDF2提取失败: {e}")

        return content

    def _extract_with_ocr(self, file_path: Path, content: Dict[str, Any]) -> Dict[str, Any]:
        """使用OCR提取文本（扫描PDF）"""
        try:
            # 注意: 需要先安装tesseract-ocr
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)

            full_text = []
            for page in doc:
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                text = pytesseract.image_to_string(
                    img,
                    lang=self.ocr_language
                )
                full_text.append(text)

            content['text'] = '\n'.join(full_text)
            content['page_count'] = len(doc)

        except Exception as e:
            self.logger.warning(f"OCR提取失败: {e}")

        return content

    #===========================================================
    # 元数据解析
    #===========================================================

    def _parse_pda_metadata(
        self,
        file_path: Path,
        pdf_content: Dict[str, Any]
    ) -> PDAReportMetadata:
        """
        从文件名和PDF内容解析PDA报告元数据

        Args:
            file_path: PDF文件路径
            pdf_content: PDF内容

        Returns:
            PDA报告元数据
        """
        metadata = PDAReportMetadata()

        # 从文件名解析
        filename = file_path.stem

        # 提取报告编号 (如TR1, TR13)
        match = self.pda_number_pattern.search(filename)
        if match:
            tr_number = match.group(1)
            metadata.report_number = f"TR{tr_number}"
            metadata.category = self.PDA_CATEGORIES.get(
                metadata.report_number,
                'general'
            )

        # 提取年份
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', filename)
        if year_match:
            metadata.year = int(year_match.group(1))

        # 提取修订版
        revision_match = re.search(
            r'\b(?:Rev|Revision|Revised)\s*(\d+[a-z]?)\b',
            filename,
            re.IGNORECASE
        )
        if revision_match:
            metadata.revision = revision_match.group(1)

        # 从PDF元数据提取标题
        pdf_metadata = pdf_content.get('metadata', {})
        title = pdf_metadata.get('/Title') or pdf_metadata.get('Title')
        if title:
            metadata.title = title.strip()
        else:
            # 从文件名生成标题
            metadata.title = filename.replace('-', ' ').replace('_', ' ')

        # 检测语言
        if '(CN)' in filename or '中文' in filename:
            metadata.language = 'zh'

        return metadata

    #===========================================================
    # 实体提取
    #===========================================================

    def _extract_entities(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """
        从文本和表格中提取所有实体

        Args:
            text: PDF文本内容
            tables: 提取的表格
            metadata: PDA报告元数据

        Returns:
            实体列表
        """
        entities = []

        # 提取各类实体
        entities.extend(self._extract_facility_entities(text, tables, metadata))
        entities.extend(self._extract_manufacturer_entities(text, tables, metadata))
        entities.extend(self._extract_standard_entities(text, tables, metadata))
        entities.extend(self._extract_assay_entities(text, tables, metadata))
        entities.extend(self._extract_process_entities(text, tables, metadata))

        self.extraction_stats['total_entities'] = len(entities)

        return entities

    def _extract_facility_entities(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """提取设施实体"""
        facilities = []
        seen = set()

        # 从文本提取
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            # 匹配设施类型
            for pattern in self.facility_type_patterns:
                matches = pattern.finditer(sentence)
                for match in matches:
                    facility_type = match.group(1)
                    facility_key = f"{facility_type}_{sentence[:50]}"

                    if facility_key in seen:
                        continue

                    # 提取环境要求
                    env_reqs = self._extract_environmental_requirements(sentence)

                    # 提取洁净度分级
                    classification = self._extract_cleanroom_classification(sentence)

                    # 创建实体
                    facility = {
                        'entity_type': 'sc:Facility',
                        'name': f"{facility_type} ({metadata.report_number})",
                        'facility_type': facility_type,
                        'classification': classification,
                        'environmental_requirements': env_reqs,
                        'design_criteria': {},
                        'intended_use': self._infer_intended_use(sentence),
                        'data_source': f'PDA_{metadata.report_number}',
                        'source_file': metadata.report_number,
                        'confidence': 0.75
                    }

                    facilities.append(facility)
                    seen.add(facility_key)

        # 从表格提取（表格通常包含详细规格）
        for table in tables:
            facilities.extend(
                self._extract_facilities_from_table(table, metadata)
            )

        return facilities

    def _extract_manufacturer_entities(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """提取设备制造商实体"""
        manufacturers = []
        seen = set()

        # 从文本提取设备制造商
        for pattern in self.manufacturer_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                company_name = match.group(1).strip()

                # 过滤
                if (len(company_name) < 5 or
                    company_name.lower() in ['parenteral drug association', 'pda'] or
                    company_name in seen):
                    continue

                # 查找附近的设备信息
                context_start = max(0, match.start() - 200)
                context_end = min(len(text), match.end() + 200)
                context = text[context_start:context_end]

                equipment_name = self._extract_equipment_name(context)
                equipment_type = self._extract_equipment_type(context)

                manufacturer = {
                    'entity_type': 'sc:Manufacturer',
                    'manufacturer_name': company_name,
                    'equipment_name': equipment_name,
                    'equipment_type': equipment_type,
                    'specifications': self._extract_specifications(context),
                    'validation_requirements': [],
                    'data_source': f'PDA_{metadata.report_number}',
                    'source_file': metadata.report_number,
                    'confidence': 0.70
                }

                manufacturers.append(manufacturer)
                seen.add(company_name)

        return manufacturers

    def _extract_standard_entities(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """提取质量标准实体"""
        standards = []
        seen = set()

        # 提取各类标准
        for std_type, pattern in self.standard_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                if std_type == 'iso':
                    standard_name = f"ISO {match.group(1)}"
                    standard_type = 'international'

                elif std_type == 'eu_gmp':
                    try:
                        annex = match.group(1) if match.lastindex and match.lastindex >= 1 else ''
                    except (AttributeError, IndexError):
                        annex = ''
                    standard_name = f"EU GMP {f'Annex {annex}' if annex else ''}"
                    standard_type = 'regional'

                elif std_type == 'fda':
                    standard_name = f"FDA Guideline"
                    standard_type = 'regulatory'

                elif std_type == 'usp':
                    try:
                        num = match.group(1) if match.lastindex and match.lastindex >= 1 else ''
                    except (AttributeError, IndexError):
                        num = ''
                    standard_name = f"USP {f'<{num}>' if num else ''}"
                    standard_type = 'pharmacopoeia'

                elif std_type == 'ep':
                    try:
                        version = match.group(1) if match.lastindex and match.lastindex >= 1 else ''
                    except (AttributeError, IndexError):
                        version = ''
                    standard_name = f"European Pharmacopoeia {version}"
                    standard_type = 'pharmacopoeia'

                elif std_type == 'astm':
                    try:
                        num = match.group(1) if match.lastindex and match.lastindex >= 1 else ''
                    except (AttributeError, IndexError):
                        num = ''
                    standard_name = f"ASTM {num}"
                    standard_type = 'testing'

                else:
                    continue

                if standard_name in seen:
                    continue

                # 提取标准要求
                context_start = max(0, match.start() - 500)
                context_end = min(len(text), match.end() + 500)
                context = text[context_start:context_end]

                standard = {
                    'entity_type': 'sc:QualityStandard',
                    'standard_name': standard_name.strip(),
                    'standard_type': standard_type,
                    'requirements': self._extract_requirements(context),
                    'acceptance_criteria': self._extract_acceptance_criteria(context),
                    'monitoring_parameters': self._extract_monitoring_parameters(context),
                    'data_source': f'PDA_{metadata.report_number}',
                    'source_file': metadata.report_number,
                    'confidence': 0.95
                }

                standards.append(standard)
                seen.add(standard_name)

        return standards

    def _extract_assay_entities(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """提取检测方法实体"""
        assays = []
        seen = set()

        # 从文本提取检测方法
        sentences = re.split(r'[.!?;]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue

            # 匹配检测类型
            for pattern in self.assay_type_patterns:
                matches = pattern.finditer(sentence)
                for match in matches:
                    assay_type = match.group(1)
                    assay_key = f"{assay_type}_{sentence[:50]}"

                    if assay_key in seen:
                        continue

                    # 提取检测名称
                    assay_name = self._extract_assay_name(sentence, assay_type)

                    # 提取采样计划
                    sampling_plan = self._extract_sampling_plan(sentence)

                    # 提取验收标准
                    acceptance_criteria = self._extract_acceptance_criteria(sentence)

                    # 提取检测频率
                    frequency = self._extract_frequency(sentence)

                    assay = {
                        'entity_type': 'rd:Assay',
                        'assay_name': assay_name,
                        'assay_type': assay_type,
                        'test_method': sentence[:100],
                        'sampling_plan': sampling_plan,
                        'acceptance_criteria': acceptance_criteria,
                        'limits': {},
                        'frequency': frequency,
                        'data_source': f'PDA_{metadata.report_number}',
                        'source_file': metadata.report_number,
                        'confidence': 0.80
                    }

                    assays.append(assay)
                    seen.add(assay_key)

        return assays

    def _extract_process_entities(
        self,
        text: str,
        tables: List[Dict[str, Any]],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """提取工艺实体"""
        processes = []
        seen = set()

        # 从文本提取工艺
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            # 匹配工艺类型
            for pattern in self.process_type_patterns:
                matches = pattern.finditer(sentence)
                for match in matches:
                    process_type = match.group(1)
                    process_key = f"{process_type}_{sentence[:50]}"

                    if process_key in seen:
                        continue

                    # 提取工艺名称
                    process_name = self._extract_process_name(sentence, process_type)

                    # 提取关键参数
                    critical_params = self._extract_critical_parameters(sentence)

                    # 提取验证方法
                    validation_approach = self._extract_validation_approach(sentence)

                    process = {
                        'entity_type': 'sc:Process',
                        'process_name': process_name,
                        'process_type': process_type,
                        'critical_parameters': critical_params,
                        'validation_approach': validation_approach,
                        'acceptance_criteria': [],
                        'data_source': f'PDA_{metadata.report_number}',
                        'source_file': metadata.report_number,
                        'confidence': 0.75
                    }

                    processes.append(process)
                    seen.add(process_key)

        return processes

    #===========================================================
    # 关系提取
    #===========================================================

    def _extract_relationships(
        self,
        entities: List[Dict[str, Any]],
        text: str,
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """
        提取实体间的关系

        Args:
            entities: 提取的实体列表
            text: 文本内容
            metadata: 元数据

        Returns:
            关系列表
        """
        relationships = []

        # 按类型分组实体
        facilities = [e for e in entities if e.get('entity_type') == 'sc:Facility']
        manufacturers = [e for e in entities if e.get('entity_type') == 'sc:Manufacturer']
        standards = [e for e in entities if e.get('entity_type') == 'sc:QualityStandard']
        assays = [e for e in entities if e.get('entity_type') == 'rd:Assay']
        processes = [e for e in entities if e.get('entity_type') == 'sc:Process']

        # Facility -> QualityStandard (REQUIRES_STANDARD)
        for facility in facilities:
            matching_standards = self._find_related_standards(facility, standards, text)
            for standard in matching_standards[:3]:  # 限制数量
                relationships.append({
                    'from': facility['name'],
                    'to': standard['standard_name'],
                    'relationship_type': 'rel:REQUIRES_STANDARD',
                    'properties': {
                        'requirement_level': 'mandatory',
                        'data_source': f'PDA_{metadata.report_number}'
                    },
                    'source': 'pda_pdf_extraction',
                    'confidence': 0.75
                })

        # Facility -> Assay (TEST_QUALITY)
        for facility in facilities:
            matching_assays = self._find_related_assays(facility, assays, text)
            for assay in matching_assays[:5]:
                relationships.append({
                    'from': assay['assay_name'],
                    'to': facility['name'],
                    'relationship_type': 'rel:TEST_QUALITY',
                    'properties': {
                        'test_purpose': 'quality_control',
                        'data_source': f'PDA_{metadata.report_number}'
                    },
                    'source': 'pda_pdf_extraction',
                    'confidence': 0.70
                })

        # Facility -> Manufacturer (EQUIPPED_WITH)
        for facility in facilities:
            matching_manufacturers = self._find_related_manufacturers(
                facility, manufacturers, text
            )
            for manufacturer in matching_manufacturers[:3]:
                relationships.append({
                    'from': facility['name'],
                    'to': manufacturer['manufacturer_name'],
                    'relationship_type': 'rel:EQUIPPED_WITH',
                    'properties': {
                        'equipment_type': manufacturer.get('equipment_type', ''),
                        'data_source': f'PDA_{metadata.report_number}'
                    },
                    'source': 'pda_pdf_extraction',
                    'confidence': 0.65
                })

        # Process -> Assay (VALIDATED_BY)
        for process in processes:
            matching_assays = self._find_related_assays(process, assays, text)
            for assay in matching_assays[:2]:
                relationships.append({
                    'from': process['process_name'],
                    'to': assay['assay_name'],
                    'relationship_type': 'rel:VALIDATED_BY',
                    'properties': {
                        'validation_type': 'process_validation',
                        'data_source': f'PDA_{metadata.report_number}'
                    },
                    'source': 'pda_pdf_extraction',
                    'confidence': 0.70
                })

        return relationships

    #===========================================================
    # 辅助提取方法
    #===========================================================

    def _extract_environmental_requirements(self, text: str) -> Dict[str, Any]:
        """提取环境要求"""
        requirements = {}

        # 温度
        temp_match = re.search(r'(\d{2})\s*[°-]?\s*C\b', text)
        if temp_match:
            requirements['temperature_c'] = temp_match.group(1)

        # 湿度
        humidity_match = re.search(r'(\d+)\s*%?\s*RH?\b', text)
        if humidity_match:
            requirements['humidity_percent'] = humidity_match.group(1)

        # 微生物限度
        microbial_match = re.search(
            r'(?:≥|>=|not more than)\s*(\d+)\s*CFU/(m³|ft³)',
            text,
            re.IGNORECASE
        )
        if microbial_match:
            requirements['microbial_limit_cfu'] = microbial_match.group(1)

        # 换气次数
        ach_match = re.search(
            r'(\d+)\s*(?:air changes|ACH)\b',
            text,
            re.IGNORECASE
        )
        if ach_match:
            requirements['air_changes_per_hour'] = ach_match.group(1)

        # 压差
        pressure_match = re.search(
            r'(\d+(?:\.\d+)?)\s*Pa(?:scal)?\b',
            text
        )
        if pressure_match:
            requirements['pressure_differential_pa'] = pressure_match.group(1)

        return requirements

    def _extract_cleanroom_classification(self, text: str) -> str:
        """提取洁净室分级"""
        for pattern in self.cleanroom_class_patterns:
            match = pattern.search(text)
            if match:
                if 'ISO' in match.group(0).upper():
                    return f"ISO {match.group(1) if match.lastindex >= 0 else ''}"
                elif 'GMP' in match.group(0).upper():
                    return f"EU GMP Grade {match.group(2) if match.lastindex >= 1 else ''}"
                elif 'Grade' in match.group(0):
                    return f"Grade {match.group(1)}"

        return ""

    def _infer_intended_use(self, text: str) -> str:
        """推断设施用途"""
        text_lower = text.lower()

        if 'aseptic' in text_lower or 'sterile' in text_lower:
            return 'aseptic_processing'
        elif 'manufacturing' in text_lower or 'production' in text_lower:
            return 'manufacturing'
        elif 'packaging' in text_lower:
            return 'packaging'
        elif 'storage' in text_lower or 'warehous' in text_lower:
            return 'storage'
        elif 'changing' in text_lower or 'gown' in text_lower:
            return 'personnel_facility'
        else:
            return 'general'

    def _extract_equipment_name(self, context: str) -> str:
        """从上下文提取设备名称"""
        # 查找常见的设备名称模式
        patterns = [
            r'([A-Z][a-zA-Z]+\s+(?:autoclave|sterilizer|filter|filler|machine|system))',
            r'((?:[A-Z][a-zA-Z]+\s+){1,3}(?:Equipment|System|Unit))',
        ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_equipment_type(self, context: str) -> str:
        """提取设备类型"""
        context_lower = context.lower()

        if 'autoclave' in context_lower or 'sterilizer' in context_lower:
            return 'sterilization_equipment'
        elif 'filter' in context_lower:
            return 'filtration_equipment'
        elif 'fill' in context_lower:
            return 'filling_equipment'
        elif 'lyophiliz' in context_lower:
            return 'lyophilization_equipment'
        elif 'inspection' in context_lower:
            return 'inspection_equipment'
        elif 'clean' in context_lower:
            return 'cleaning_equipment'
        else:
            return 'general_equipment'

    def _extract_specifications(self, context: str) -> Dict[str, Any]:
        """提取设备规格"""
        specs = {}

        # 容量
        capacity_match = re.search(
            r'capacity[:\s]+(\d+(?:\.\d+)?)\s*(L|ml|m³|kg)',
            context,
            re.IGNORECASE
        )
        if capacity_match:
            specs['capacity'] = f"{capacity_match.group(1)} {capacity_match.group(2)}"

        # 尺寸
        dimension_match = re.search(
            r'(\d+)\s*[x×]\s*(\d+)\s*[x×]?\s*(\d+)?\s*(mm|m|cm)',
            context,
            re.IGNORECASE
        )
        if dimension_match:
            dims = [dimension_match.group(i) for i in range(1, 4) if dimension_match.group(i)]
            specs['dimensions'] = f"{' x '.join(dims)} {dimension_match.group(4)}"

        # 材质
        if 'stainless steel' in context.lower() or '316l' in context.lower():
            specs['material'] = 'Stainless Steel 316L'
        elif 'ptfe' in context.lower():
            specs['material'] = 'PTFE'

        return specs

    def _extract_requirements(self, context: str) -> List[str]:
        """提取标准要求"""
        requirements = []

        # 查找要求关键词后的句子
        patterns = [
            r'(?:shall|must|required|requirement)[:\s]+([^.!?]+)',
            r'(?:specification|spec)[:\s]+([^.!?]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                req = match.group(1).strip()
                if len(req) > 10 and len(req) < 200:
                    requirements.append(req)

        return requirements[:5]  # 限制数量

    def _extract_acceptance_criteria(self, context: str) -> List[str]:
        """提取验收标准"""
        criteria = []

        patterns = [
            r'(?:acceptance criteria|acceptable|limit)[:\s]+([^.!?]+)',
            r'(?:not more than|≤|<=|≤)\s+([^,.!?]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                criterion = match.group(1).strip()
                if len(criterion) > 5 and len(criterion) < 150:
                    criteria.append(criterion)

        return criteria[:3]

    def _extract_monitoring_parameters(self, context: str) -> List[str]:
        """提取监控参数"""
        params = []

        keywords = ['temperature', 'humidity', 'pressure', 'particle', 'microbial', 'air flow']
        context_lower = context.lower()

        for keyword in keywords:
            if keyword in context_lower:
                params.append(keyword)

        return list(set(params))

    def _extract_assay_name(self, sentence: str, assay_type: str) -> str:
        """提取检测名称"""
        # 生成简洁的检测名称
        return f"{assay_type} Test".strip()

    def _extract_sampling_plan(self, sentence: str) -> str:
        """提取采样计划"""
        if 'per batch' in sentence.lower():
            return 'per_batch'
        elif 'each shift' in sentence.lower():
            return 'per_shift'
        elif 'daily' in sentence.lower():
            return 'daily'
        elif 'weekly' in sentence.lower():
            return 'weekly'
        else:
            return 'as_required'

    def _extract_frequency(self, sentence: str) -> str:
        """提取检测频率"""
        for pattern in self.frequency_patterns:
            match = pattern.search(sentence)
            if match:
                return match.group(1).lower().replace(' ', '_')
        return 'as_required'

    def _extract_process_name(self, sentence: str, process_type: str) -> str:
        """提取工艺名称"""
        return f"{process_type} Process".strip()

    def _extract_critical_parameters(self, sentence: str) -> List[str]:
        """提取关键参数"""
        params = []

        # 查找数值参数
        numeric_matches = re.finditer(
            r'(\d+(?:\.\d+)?)\s*([°C%FPa|m³|L|min]+)\b',
            sentence
        )
        for match in numeric_matches:
            params.append(f"{match.group(1)} {match.group(2)}")

        return params[:5]

    def _extract_validation_approach(self, sentence: str) -> str:
        """提取验证方法"""
        sentence_lower = sentence.lower()

        if 'media fill' in sentence_lower or 'process simulation' in sentence_lower:
            return 'media_fill_simulation'
        elif 'challenge study' in sentence_lower:
            return 'challenge_study'
        elif 'worst case' in sentence_lower:
            return 'worst_case_validation'
        elif 'parametric release' in sentence_lower:
            return 'parametric_release'
        else:
            return 'standard_validation'

    def _extract_facilities_from_table(
        self,
        table: Dict[str, Any],
        metadata: PDAReportMetadata
    ) -> List[Dict[str, Any]]:
        """从表格中提取设施信息"""
        facilities = []

        # 表格数据结构分析
        # 这里需要根据实际表格格式进行调整
        table_data = table.get('data', [])

        if not table_data or len(table_data) < 2:
            return facilities

        # 假设第一行是表头
        headers = [str(cell).lower() if cell else '' for cell in table_data[0]]

        # 查找相关列
        type_col = -1
        class_col = -1
        req_col = -1

        for i, header in enumerate(headers):
            if 'type' in header or 'area' in header:
                type_col = i
            elif 'class' in header or 'grade' in header:
                class_col = i
            elif 'requirement' in header or 'criteria' in header:
                req_col = i

        # 提取数据行
        for row in table_data[1:]:
            if not row:
                continue

            facility = {
                'entity_type': 'sc:Facility',
                'name': '',
                'facility_type': '',
                'classification': '',
                'environmental_requirements': {},
                'design_criteria': {},
                'intended_use': 'manufacturing',
                'data_source': f'PDA_{metadata.report_number}',
                'source_file': metadata.report_number,
                'confidence': 0.85
            }

            if type_col >= 0 and type_col < len(row):
                facility['facility_type'] = str(row[type_col]).strip()
                facility['name'] = f"{facility['facility_type']} (Table)"

            if class_col >= 0 and class_col < len(row):
                facility['classification'] = str(row[class_col]).strip()

            if req_col >= 0 and req_col < len(row):
                req_text = str(row[req_col])
                facility['environmental_requirements'] = (
                    self._extract_environmental_requirements(req_text)
                )

            if facility['facility_type']:
                facilities.append(facility)

        return facilities

    #===========================================================
    # 关系匹配辅助方法
    #===========================================================

    def _find_related_standards(
        self,
        facility: Dict[str, Any],
        standards: List[Dict[str, Any]],
        text: str
    ) -> List[Dict[str, Any]]:
        """查找与设施相关的标准"""
        related = []

        # 根据洁净室分级匹配
        classification = facility.get('classification', '')
        if 'ISO' in classification:
            iso_num = re.search(r'\d+', classification)
            if iso_num:
                for standard in standards:
                    if f'ISO {iso_num.group()}' in standard['standard_name']:
                        related.append(standard)

        # 根据用途匹配
        intended_use = facility.get('intended_use', '')
        if 'aseptic' in intended_use:
            for standard in standards:
                if 'Annex 1' in standard['standard_name'] or 'GMP' in standard['standard_name']:
                    related.append(standard)

        return related

    def _find_related_assays(
        self,
        entity: Dict[str, Any],
        assays: List[Dict[str, Any]],
        text: str
    ) -> List[Dict[str, Any]]:
        """查找相关的检测方法"""
        related = []
        entity_text = str(entity.get('name', '')).lower()

        # 根据用途匹配检测方法
        if 'aseptic' in entity_text or 'sterile' in entity_text:
            for assay in assays:
                assay_type = assay.get('assay_type', '').lower()
                if any(word in assay_type for word in ['microbial', 'sterility', 'endotoxin']):
                    related.append(assay)

        elif 'clean' in entity_text or 'room' in entity_text:
            for assay in assays:
                assay_type = assay.get('assay_type', '').lower()
                if 'particle' in assay_type:
                    related.append(assay)

        return related

    def _find_related_manufacturers(
        self,
        facility: Dict[str, Any],
        manufacturers: List[Dict[str, Any]],
        text: str
    ) -> List[Dict[str, Any]]:
        """查找相关的设备制造商"""
        # 简单实现：返回前几个制造商
        # 在实际应用中，可能需要更复杂的关联分析
        return manufacturers[:3]

    #===========================================================
    # 批量处理和保存
    #===========================================================

    def process_batch(
        self,
        file_paths: List[Path],
        output_dir: Optional[Path] = None
    ) -> ProcessingResult:
        """
        批量处理PDA TR PDF文件

        Args:
            file_paths: PDF文件路径列表
            output_dir: 输出目录

        Returns:
            处理结果
        """
        self.logger.info(f"批量处理 {len(file_paths)} 个PDA TR PDF文件")

        start_time = datetime.now()
        all_entities = []
        all_relationships = []
        processed_files = []
        failed_files = []

        # 分类收集实体
        facilities = []
        manufacturers = []
        standards = []
        assays = []
        processes = []

        for i, file_path in enumerate(file_paths):
            try:
                self.logger.info(f"处理 {i+1}/{len(file_paths)}: {file_path.name}")

                result = self.extract(file_path)
                if not result:
                    failed_files.append(str(file_path))
                    continue

                # 分类收集实体
                for entity in result.get('entities', []):
                    entity_type = entity.get('entity_type', '')

                    if entity_type == 'sc:Facility':
                        facilities.append(entity)
                    elif entity_type == 'sc:Manufacturer':
                        manufacturers.append(entity)
                    elif entity_type == 'sc:QualityStandard':
                        standards.append(entity)
                    elif entity_type == 'rd:Assay':
                        assays.append(entity)
                    elif entity_type == 'sc:Process':
                        processes.append(entity)

                    all_entities.append(entity)

                all_relationships.extend(result.get('relationships', []))
                processed_files.append(str(file_path))

            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                failed_files.append(str(file_path))

        # 保存分类文件
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 保存分类实体文件
            self._save_entity_file(output_dir / f'pda_facilities_{timestamp}.json', facilities)
            self._save_entity_file(output_dir / f'pda_manufacturers_{timestamp}.json', manufacturers)
            self._save_entity_file(output_dir / f'pda_standards_{timestamp}.json', standards)
            self._save_entity_file(output_dir / f'pda_assays_{timestamp}.json', assays)
            self._save_entity_file(output_dir / f'pda_processes_{timestamp}.json', processes)
            self._save_entity_file(output_dir / f'pda_relationships_{timestamp}.json', all_relationships)

            # 保存汇总统计
            summary = {
                'processor': self.PROCESSOR_NAME,
                'timestamp': timestamp,
                'statistics': {
                    'total_files': len(file_paths),
                    'processed_files': len(processed_files),
                    'failed_files': len(failed_files),
                    'facilities_extracted': len(facilities),
                    'manufacturers_extracted': len(manufacturers),
                    'standards_extracted': len(standards),
                    'assays_extracted': len(assays),
                    'processes_extracted': len(processes),
                    'total_entities': len(all_entities),
                    'total_relationships': len(all_relationships),
                },
                'processed_files': processed_files,
                'failed_files': failed_files,
                'processing_time_seconds': (datetime.now() - start_time).total_seconds()
            }

            summary_file = output_dir / f'pda_summary_{timestamp}.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            self.logger.info(f"结果已保存到: {output_dir}")
            self.logger.info(f"  设施: {len(facilities)}")
            self.logger.info(f"  制造商: {len(manufacturers)}")
            self.logger.info(f"  标准: {len(standards)}")
            self.logger.info(f"  检测: {len(assays)}")
            self.logger.info(f"  工艺: {len(processes)}")
            self.logger.info(f"  关系: {len(all_relationships)}")

        # 创建处理结果
        metrics = ProcessingMetrics(
            files_scanned=len(file_paths),
            files_processed=len(processed_files),
            files_failed=len(failed_files),
            entities_extracted=len(all_entities),
            relationships_extracted=len(all_relationships),
            processing_time_seconds=(datetime.now() - start_time).total_seconds()
        )

        return ProcessingResult(
            status=ProcessingStatus.COMPLETED if processed_files else ProcessingStatus.FAILED,
            processor_name=self.PROCESSOR_NAME,
            source_path='batch_processing',
            metrics=metrics,
            entities=all_entities,
            relationships=all_relationships,
            metadata={
                'processed_files': processed_files,
                'failed_files': failed_files,
                'extraction_stats': dict(self.extraction_stats)
            }
        )

    def _save_entity_file(self, filepath: Path, entities: List[Dict[str, Any]]):
        """保存实体文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)


#===========================================================
# 命令行接口
#===========================================================

def main():
    """命令行主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='PDA Technical Reports PDF Processor'
    )
    parser.add_argument(
        'input',
        help='PDA TR PDF文件或目录路径'
    )
    parser.add_argument(
        '-o', '--output',
        default='/root/autodl-tmp/pj-pharmaKG/data/processed/documents/pda_technical_reports',
        help='输出目录'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=0,
        help='限制处理文件数量（用于测试）'
    )
    parser.add_argument(
        '--tr',
        type=str,
        help='只处理指定的TR编号（如TR1,TR13）'
    )
    parser.add_argument(
        '--use-ocr',
        action='store_true',
        help='启用OCR处理扫描PDF'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='禁用缓存'
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建处理器
    config = {
        'use_ocr': args.use_ocr,
        'cache_enabled': not args.no_cache
    }

    processor = PDAPDFProcessor(config)

    # 扫描文件
    input_path = Path(args.input)
    files = processor.scan(input_path)

    # 过滤文件
    if args.tr:
        tr_num = args.tr.upper()
        files = [f for f in files if tr_num in f.name.upper()]

    if args.limit > 0:
        files = files[:args.limit]

    print(f"\n找到 {len(files)} 个PDF文件待处理")
    if args.tr:
        print(f"筛选: {args.tr}")

    # 批量处理
    if files:
        output_dir = Path(args.output)
        result = processor.process_batch(files, output_dir)

        print(f"\n处理完成:")
        print(f"  成功: {result.metrics.files_processed}")
        print(f"  失败: {result.metrics.files_failed}")
        print(f"  实体: {result.metrics.entities_extracted}")
        print(f"  关系: {result.metrics.relationships_extracted}")
        print(f"  耗时: {result.metrics.processing_time_seconds:.2f}秒")
    else:
        print("没有找到符合条件的PDF文件")


if __name__ == '__main__':
    main()
