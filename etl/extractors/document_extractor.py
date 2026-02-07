"""
文档提取器 - 用于从本地文件系统中提取监管文档

支持 PDF、DOCX、TXT 等格式的文档解析
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import mimetypes

from .base import ExtractionResult, ExtractionMetrics

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """文档元数据"""
    file_path: str
    file_name: str
    file_size: int
    file_format: str
    mime_type: str
    checksum: str
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    accessed_time: Optional[datetime] = None


class DocumentExtractor:
    """
    文档提取器

    从本地文件系统中提取监管文档，支持多种文件格式
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文档提取器

        Args:
            config: 配置字典，可能包含：
                - base_path: 基础路径
                - supported_formats: 支持的文件格式列表
                - max_file_size: 最大文件大小（字节）
                - extract_content: 是否提取内容
                - content_max_length: 内容最大长度
        """
        self.base_path = config.get('base_path', '') if config else ''
        self.supported_formats = config.get('supported_formats', [
            '.pdf', '.docx', '.doc', '.txt'
        ]) if config else ['.pdf', '.docx', '.doc', '.txt']
        self.max_file_size = config.get('max_file_size', 100 * 1024 * 1024) if config else 100 * 1024 * 1024  # 100MB
        self.extract_content = config.get('extract_content', True) if config else True
        self.content_max_length = config.get('content_max_length', 10000) if config else 10000

    def extract(self, source: str, **kwargs) -> ExtractionResult:
        """
        提取文档

        Args:
            source: 文件路径或目录路径
            **kwargs: 额外参数
                - recursive: 是否递归处理目录（默认 False）
                - pattern: 文件名模式过滤

        Returns:
            ExtractionResult: 提取结果
        """
        try:
            path = Path(source)
            if not path.exists():
                return ExtractionResult(
                    source_name=source,
                    success=False,
                    error=f"路径不存在: {source}"
                )

            records = []
            metrics = ExtractionMetrics(source_name=source)

            if path.is_file():
                # 处理单个文件
                result = self._extract_file(path)
                if result:
                    records.append(result)
                    metrics.total_records += 1
                    metrics.successful_records += 1
            elif path.is_dir():
                # 处理目录
                recursive = kwargs.get('recursive', False)
                pattern = kwargs.get('pattern', '*')

                for file_path in self._scan_directory(path, recursive, pattern):
                    result = self._extract_file(file_path)
                    if result:
                        records.append(result)
                        metrics.total_records += 1
                        metrics.successful_records += 1

            return ExtractionResult(
                source_name=source,
                success=True,
                records=records,
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"文档提取失败: {e}")
            return ExtractionResult(
                source_name=source,
                success=False,
                error=str(e)
            )

    def _scan_directory(self, directory: Path, recursive: bool, pattern: str) -> List[Path]:
        """
        扫描目录获取支持的文件

        Args:
            directory: 目录路径
            recursive: 是否递归
            pattern: 文件名模式

        Returns:
            文件路径列表
        """
        files = []
        try:
            if recursive:
                for ext in self.supported_formats:
                    files.extend(directory.rglob(f"{pattern}{ext}"))
            else:
                for ext in self.supported_formats:
                    files.extend(directory.glob(f"{pattern}{ext}"))
        except Exception as e:
            logger.warning(f"扫描目录失败: {e}")

        return files

    def _extract_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        提取单个文件

        Args:
            file_path: 文件路径

        Returns:
            文档数据字典
        """
        try:
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                logger.warning(f"文件过大，跳过: {file_path} ({file_size} bytes)")
                return None

            # 检查文件格式
            file_ext = file_path.suffix.lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"不支持的文件格式: {file_path}")
                return None

            # 获取文件统计信息
            stat = file_path.stat()
            mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'

            # 计算校验和
            checksum = self._calculate_checksum(file_path)

            # 创建文档元数据
            metadata = DocumentMetadata(
                file_path=str(file_path.absolute()),
                file_name=file_path.name,
                file_size=file_size,
                file_format=file_ext[1:],  # 去掉点号
                mime_type=mime_type,
                checksum=checksum,
                created_time=datetime.fromtimestamp(stat.st_ctime),
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                accessed_time=datetime.fromtimestamp(stat.st_atime)
            )

            # 提取内容
            content = None
            if self.extract_content:
                content = self._extract_content(file_path, file_ext)

            # 构建结果
            result = {
                'file_path': str(file_path.absolute()),
                'file_name': file_path.name,
                'file_size': file_size,
                'file_format': file_ext[1:],
                'mime_type': mime_type,
                'checksum': checksum,
                'created_time': metadata.created_time.isoformat() if metadata.created_time else None,
                'modified_time': metadata.modified_time.isoformat() if metadata.modified_time else None,
                'content': content
            }

            return result

        except Exception as e:
            logger.error(f"提取文件失败 {file_path}: {e}")
            return None

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        计算文件 SHA256 校验和

        Args:
            file_path: 文件路径

        Returns:
            SHA256 哈希值（十六进制字符串）
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _extract_content(self, file_path: Path, file_ext: str) -> Optional[str]:
        """
        提取文件内容

        Args:
            file_path: 文件路径
            file_ext: 文件扩展名

        Returns:
            文件内容文本
        """
        try:
            if file_ext == '.txt':
                return self._extract_text_content(file_path)
            elif file_ext == '.pdf':
                return self._extract_pdf_content(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_docx_content(file_path)
            else:
                logger.warning(f"不支持的文件类型: {file_ext}")
                return None
        except Exception as e:
            logger.error(f"提取内容失败 {file_path}: {e}")
            return None

    def _extract_text_content(self, file_path: Path) -> Optional[str]:
        """提取文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > self.content_max_length:
                    content = content[:self.content_max_length]
                return content
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    if len(content) > self.content_max_length:
                        content = content[:self.content_max_length]
                    return content
            except Exception as e:
                logger.error(f"读取文本文件失败: {e}")
                return None

    def _extract_pdf_content(self, file_path: Path) -> Optional[str]:
        """提取 PDF 文件内容"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content_parts = []
                total_chars = 0

                for page in reader.pages:
                    page_text = page.extract_text()
                    if total_chars + len(page_text) > self.content_max_length:
                        remaining = self.content_max_length - total_chars
                        content_parts.append(page_text[:remaining])
                        break
                    content_parts.append(page_text)
                    total_chars += len(page_text)

                return '\n'.join(content_parts)
        except ImportError:
            logger.warning("PyPDF2 未安装，无法提取 PDF 内容")
            return None
        except Exception as e:
            logger.error(f"提取 PDF 内容失败: {e}")
            return None

    def _extract_docx_content(self, file_path: Path) -> Optional[str]:
        """提取 DOCX 文件内容"""
        try:
            from docx import Document
            doc = Document(file_path)
            content_parts = []
            total_chars = 0

            for para in doc.paragraphs:
                if total_chars + len(para.text) > self.content_max_length:
                    remaining = self.content_max_length - total_chars
                    content_parts.append(para.text[:remaining])
                    break
                content_parts.append(para.text)
                total_chars += len(para.text)

            return '\n'.join(content_parts)
        except ImportError:
            logger.warning("python-docx 未安装，无法提取 DOCX 内容")
            return None
        except Exception as e:
            logger.error(f"提取 DOCX 内容失败: {e}")
            return None

    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return self.supported_formats.copy()

    def validate_source(self, source: str) -> bool:
        """
        验证数据源是否有效

        Args:
            source: 数据源路径

        Returns:
            是否有效
        """
        path = Path(source)
        return path.exists()
