#===========================================================
# PharmaKG 临床CRL PDF数据处理器
# Pharmaceutical Knowledge Graph - Clinical CRL PDF Processor
#===========================================================
# 版本: v1.0
# 描述: 处理FDA CRL PDF文档，提取实体和关系
#===========================================================

import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from collections import defaultdict

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from processors.base import BaseProcessor, ProcessingResult, ProcessingStatus, ProcessingMetrics
from extractors.named_entity import NamedEntityExtractor
from extractors.relationship import RelationshipExtractor
from extractors.attribute import AttributeExtractor
from extractors.base import EntityType, ExtractedEntity, ExtractedRelationship, RelationshipType
from mappers.entity_mapper import EntityMapper
from extractors import entity_enhancer

logger = logging.getLogger(__name__)


class PDFCRLProcessor(BaseProcessor):
    """
    CRL PDF数据处理器

    处理FDA Complete Response Letter PDF文档
    """

    PROCESSOR_NAME = "PDFCRLProcessor"
    SUPPORTED_FORMATS = ['.pdf']
    OUTPUT_SUBDIR = "clinical_crl_pdf"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        super().__init__(config)

        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")

        # 初始化提取器
        self.entity_extractor = NamedEntityExtractor(config)
        self.relationship_extractor = RelationshipExtractor(config)
        self.attribute_extractor = AttributeExtractor(config)
        self.entity_mapper = EntityMapper(config)

        # 正则表达式模式
        self._init_patterns()

    def _init_patterns(self):
        """初始化正则表达式模式"""
        # 申请号模式: NDA/BLA + 6位数字
        self.app_number_pattern = re.compile(r'\b(NDA|BLA)\s*(\d{6})\b', re.IGNORECASE)

        # 日期模式: MM/DD/YYYY or DD/MM/YYYY
        self.date_pattern = re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b')

        # FDA机构模式
        self.fda_agency_patterns = [
            re.compile(r'(Center for [^.]+?\.?)', re.IGNORECASE),
            re.compile(r'(Office of [^.]+?\.?)', re.IGNORECASE),
            re.compile(r'(Division of [^.]+?\.?)', re.IGNORECASE),
            re.compile(r'(Directorate of [^.]+?\.?)', re.IGNORECASE),
        ]

        # 公司名称模式 - 扩展多种模式
        self.company_patterns = [
            re.compile(r'(?:To:|Applicant:|Company:|Submitted by:|Applicant\s*)\s*([A-Z][A-Za-z0-9\s&\-,\.]+(?:Inc|LLC|Ltd|Corp|Pharma|Therapeutics|Laboratories|Sciences|Biotech|Bio|Genetics)?)(?:\s|$|,)', re.IGNORECASE),
            re.compile(r'([A-Z][A-Za-z0-9\s&\-,\.]+\s+(?:Inc|LLC|Ltd|Corp|Pharma|Therapeutics|Laboratories))', re.IGNORECASE),
        ]

        # 药物名称模式 - 匹配常见药物命名模式
        self.drug_patterns = [
            re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b', re.MULTILINE),
        ]

    def scan(self, source_path: Union[str, Path]) -> List[Path]:
        """扫描源目录"""
        source_path = Path(source_path)

        if source_path.is_file():
            return [source_path] if source_path.suffix in self.SUPPORTED_FORMATS else []

        files = []
        for ext in self.SUPPORTED_FORMATS:
            files.extend(source_path.rglob(f"*{ext}"))

        # 排除已处理的文件
        unprocessed_files = [f for f in files if not self.is_processed(f)]

        return unprocessed_files

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """从CRL PDF文件中提取数据"""
        self.logger.debug(f"提取文件: {file_path}")

        try:
            # 读取PDF文件
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # 提取元数据
                metadata = self._extract_metadata(file_path, pdf_reader)

                # 提取全部文本
                full_text = self._extract_full_text(pdf_reader)

                if not full_text.strip():
                    self.logger.warning(f"PDF文件无文本内容: {file_path}")
                    return {}

                # 解析CRL信息
                crl_info = self._parse_crl_document(file_path, full_text, metadata)

                return {
                    'file_path': str(file_path),
                    'metadata': metadata,
                    'full_text': full_text[:5000],  # 保存前5000字符用于分析
                    **crl_info
                }

        except Exception as e:
            self.logger.error(f"处理PDF文件失败 {file_path}: {e}")
            return {}

    def _extract_full_text(self, pdf_reader) -> str:
        """提取PDF全部文本"""
        full_text = ""
        for page in pdf_reader.pages:
            try:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            except Exception as e:
                self.logger.warning(f"提取页面文本失败: {e}")
                continue
        return full_text

    def _extract_metadata(self, file_path: Path, pdf_reader) -> Dict[str, Any]:
        """提取PDF元数据"""
        # 从文件名提取信息
        filename_info = self._parse_filename(file_path)

        metadata = {
            'filename': file_path.name,
            'page_count': len(pdf_reader.pages),
            'is_encrypted': pdf_reader.is_encrypted,
        }

        # PDF元数据
        if pdf_reader.metadata:
            metadata.update({
                'title': pdf_reader.metadata.get('/Title', ''),
                'author': pdf_reader.metadata.get('/Author', ''),
                'subject': pdf_reader.metadata.get('/Subject', ''),
                'creator': pdf_reader.metadata.get('/Creator', ''),
                'producer': pdf_reader.metadata.get('/Producer', ''),
            })

        # 文件名信息
        metadata.update(filename_info)

        return metadata

    def _parse_filename(self, file_path: Path) -> Dict[str, Any]:
        """从文件名解析信息"""
        filename = file_path.stem  # 不包含扩展名

        info = {
            'app_number': '',
            'app_type': '',
            'date_str': ''
        }

        # 模式: CRL_NDA123456_YYYYMMDD.pdf 或 CRL_BLA123456_YYYYMMDD.pdf
        match = re.search(r'(NDA|BLA)?_?(\d{6})[_-](\d{8})', filename, re.IGNORECASE)
        if match:
            app_type = match.group(1) or ''
            app_number = match.group(2)
            date_str = match.group(3)

            info['app_type'] = app_type.upper()
            info['app_number'] = f"{app_type.upper()}{app_number}" if app_type else app_number
            info['date_str'] = date_str

            # 转换日期
            try:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                info['date_iso'] = f"{year}-{month}-{day}"
            except:
                pass

        return info

    def _parse_crl_document(self, file_path: Path, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """解析CRL文档内容"""
        entities = []
        relationships = []

        # 1. 提取申请号实体
        app_number = metadata.get('app_number', '')
        if not app_number:
            # 从文本中提取申请号
            matches = self.app_number_pattern.findall(text)
            if matches:
                app_type, app_num = matches[0]
                app_number = f"{app_type.upper()}{app_num}"

        if app_number:
            app_entity = ExtractedEntity(
                entity_type=EntityType.REGULATORY_SUBMISSION,
                text=app_number,
                confidence=1.0,
                properties={
                    'submission_number': app_number,
                    'submission_type': app_number[:3] if len(app_number) > 3 else 'NDA',
                    'data_source': 'FDA_CRL_PDF',
                    'source_file': file_path.name
                },
                identifiers={'submission_number': app_number},
                source='pdf_filename'
            )
            entities.append(app_entity)

        # 2. 日期信息保存到文档属性中（不创建单独的日期实体）
        date_str = metadata.get('date_str', '')
        if date_str:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                # 日期将作为文档属性保存，不创建单独实体
            except:
                pass

        # 3. 提取FDA机构实体
        fda_agencies = self._extract_fda_agencies(text)
        for agency_name in fda_agencies[:3]:  # 限制数量
            agency_entity = ExtractedEntity(
                entity_type=EntityType.REGULATORY_AGENCY,
                text=agency_name,
                confidence=0.85,
                properties={
                    'name': agency_name,
                    'data_source': 'FDA_CRL_PDF',
                    'source_file': file_path.name
                },
                source='pdf_text_extraction'
            )
            entities.append(agency_entity)

        # 添加FDA顶级机构
        fda_entity = ExtractedEntity(
            entity_type=EntityType.REGULATORY_AGENCY,
            text='FDA',
            confidence=1.0,
            properties={
                'name': 'Food and Drug Administration',
                'abbreviation': 'FDA',
                'data_source': 'FDA_CRL_PDF'
            },
            source='pdf_fda_default'
        )
        entities.append(fda_entity)

        # 4. 提取公司/申请人实体
        companies = self._extract_companies(text)
        for company_name in companies[:2]:  # 限制数量
            company_entity = ExtractedEntity(
                entity_type=EntityType.COMPANY,
                text=company_name,
                confidence=0.8,
                properties={
                    'name': company_name,
                    'data_source': 'FDA_CRL_PDF',
                    'source_file': file_path.name
                },
                source='pdf_text_extraction'
            )
            entities.append(company_entity)

        # 5. 提取药物/化合物实体（使用命名实体提取器）
        drug_entities = self.entity_extractor.extract_entities(
            text=text[:2000],  # 使用前2000字符
            extract_types=[EntityType.COMPOUND]
        )
        entities.extend(drug_entities[:5])  # 限制数量

        # 6. 创建关系（使用字典格式）
        document_id = f"Document-{file_path.stem}"

        # 创建文档实体
        doc_entity = ExtractedEntity(
            entity_type=EntityType.DOCUMENT,
            text=document_id,
            confidence=1.0,
            properties={
                'primary_id': document_id,
                'document_type': 'CRL',
                'source_file': file_path.name,
                'app_number': app_number,
                'date': metadata.get('date_iso', ''),
                'data_source': 'FDA_CRL_PDF'
            },
            source='pdf_document'
        )
        entities.append(doc_entity)

        # 创建关系: 使用简单字典格式
        # 文档 -> 申请号
        if app_number:
            relationships.append({
                'from': document_id,
                'to': app_number,
                'relationship_type': 'ABOUT',
                'properties': {
                    'data_source': 'FDA_CRL_PDF'
                },
                'source': 'pdf_extraction',
                'confidence': 1.0
            })

        # FDA -> 文档
        relationships.append({
            'from': 'FDA',
            'to': document_id,
            'relationship_type': 'ISSUED',
            'properties': {
                'data_source': 'FDA_CRL_PDF'
            },
            'source': 'pdf_extraction',
            'confidence': 1.0
        })

        return {
            'entities': entities,
            'relationships': relationships,
            'app_number': app_number,
            'date': metadata.get('date_iso', '')
        }

    def _extract_fda_agencies(self, text: str) -> List[str]:
        """从文本中提取FDA机构"""
        agencies = []
        seen = set()

        for pattern in self.fda_agency_patterns:
            matches = pattern.findall(text)
            for match in matches:
                agency = match.strip()
                if agency and len(agency) > 5 and agency not in seen:
                    # 过滤掉非机构名称
                    if any(word in agency.lower() for word in ['center', 'office', 'division', 'directorate']):
                        agencies.append(agency)
                        seen.add(agency)

        return agencies

    def _extract_companies(self, text: str) -> List[str]:
        """从文本中提取公司名称"""
        companies = []
        seen = set()

        for pattern in self.company_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    company = match[0] if match[0] else match[1] if len(match) > 1 else ''
                else:
                    company = match

                company = company.strip()

                # 过滤条件
                if (company and
                    len(company) > 3 and
                    company not in seen and
                    not any(word in company.lower() for word in ['food', 'drug', 'administration', 'fda', 'page', 'section'])):
                    companies.append(company)
                    seen.add(company)

        return companies

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换提取的数据

        Args:
            raw_data: 原始提取数据

        Returns:
            转换后的数据
        """
        # 如果数据已经是实体和关系格式，直接返回
        if 'entities' in raw_data and 'relationships' in raw_data:
            return raw_data

        # 否则返回空数据
        return {
            'entities': [],
            'relationships': [],
            'metadata': raw_data.get('metadata', {})
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证数据

        Args:
            data: 待验证数据

        Returns:
            是否验证通过
        """
        # 基本验证
        if not isinstance(data, dict):
            return False

        # 必须包含entities和relationships
        if 'entities' not in data or 'relationships' not in data:
            return False

        # entities和relationships必须是列表
        if not isinstance(data['entities'], list) or not isinstance(data['relationships'], list):
            return False

        return True

    def process_batch(self, file_paths: List[Path], batch_size: int = 10) -> ProcessingResult:
        """批量处理PDF文件"""
        self.logger.info(f"开始批量处理 {len(file_paths)} 个PDF文件")

        all_entities = []
        all_relationships = []
        processed_files = []
        failed_files = []

        for i, file_path in enumerate(file_paths):
            try:
                self.logger.debug(f"处理 {i+1}/{len(file_paths)}: {file_path.name}")

                result = self.extract(file_path)

                if result:
                    entities = result.get('entities', [])
                    relationships = result.get('relationships', [])

                    all_entities.extend(entities)
                    all_relationships.extend(relationships)
                    processed_files.append(str(file_path))

                else:
                    failed_files.append(str(file_path))

            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                failed_files.append(str(file_path))

        # 创建处理结果
        metrics = ProcessingMetrics(
            files_processed=len(processed_files),
            files_failed=len(failed_files),
            entities_extracted=len(all_entities),
            relationships_extracted=len(all_relationships)
        )

        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED if processed_files else ProcessingStatus.FAILED,
            processor_name=self.PROCESSOR_NAME,
            source_path='batch_processing',
            metrics=metrics,
            entities=all_entities,
            relationships=all_relationships,
            metadata={
                'processed_files': processed_files,
                'failed_files': failed_files
            }
        )

        return result

    def save_results(self, result: ProcessingResult, output_dir: Path) -> None:
        """保存处理结果"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 映射实体
        mapped_entities = self.entity_mapper.map_entities(result.entities)

        # 处理关系 - 直接转换为字典格式
        mapped_relationships = []
        for rel in result.relationships:
            if isinstance(rel, dict):
                # 已经是字典格式
                mapped_relationships.append(rel)
            elif hasattr(rel, 'to_dict'):
                # ExtractedRelationship对象
                mapped_relationships.append(rel.to_dict())
            else:
                # 其他格式，尝试转换
                mapped_relationships.append({
                    'from': getattr(rel, 'from', getattr(rel, 'from_entity', '')),
                    'to': getattr(rel, 'to', getattr(rel, 'to_entity', '')),
                    'relationship_type': str(getattr(rel, 'relationship_type', 'RELATED_TO')),
                    'properties': getattr(rel, 'properties', {}),
                    'source': getattr(rel, 'source', ''),
                    'confidence': getattr(rel, 'confidence', 0.0)
                })

        # 保存实体
        entities_file = output_dir / f'entities_{timestamp}.json'
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(mapped_entities, f, ensure_ascii=False, indent=2)

        # 保存关系
        relationships_file = output_dir / f'relationships_{timestamp}.json'
        with open(relationships_file, 'w', encoding='utf-8') as f:
            json.dump(mapped_relationships, f, ensure_ascii=False, indent=2)

        # 保存摘要
        summary = {
            'processor': self.PROCESSOR_NAME,
            'timestamp': timestamp,
            'entities_count': len(mapped_entities),
            'relationships_count': len(mapped_relationships),
            'files_processed': result.metrics.files_processed,
            'files_failed': result.metrics.files_failed,
            'metadata': result.metadata
        }

        summary_file = output_dir / f'summary_{timestamp}.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.logger.info(f"结果已保存到: {output_dir}")
        self.logger.info(f"  实体: {entities_file.name}")
        self.logger.info(f"  关系: {relationships_file.name}")
        self.logger.info(f"  摘要: {summary_file.name}")
