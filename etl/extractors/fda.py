#===========================================================
# PharmaKG ETL - FDA Drugs@FDA 数据抽取器
# Pharmaceutical Knowledge Graph - FDA Drugs Extractor
#===========================================================
# 版本: v1.0
# 描述: 从 FDA Drugs@FDA 数据产品抽取批准和申报信息
#===========================================================

import logging
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Generator, Dict, Optional, List
from datetime import datetime
from .base import FileBasedExtractor


logger = logging.getLogger(__name__)


class FDAExtractors(FileBasedExtractor):
    """
    FDA 数据抽取器

    从 FDA 数据产品抽取：
    - Drugs@FDA 产品批准信息
    - Orange Book 数据
    - NDA/ANDA 申报数据
    """

    def __init__(self, data_dir: str = "data/raw/fda"):
        """
        初始化 FDA 抽取器

        Args:
            data_dir: FDA 数据文件目录
        """
        super().__init__(
            name="FDA",
            rate_limit=0  # 本地文件读取
        )
        self.data_dir = data_dir

    #===========================================================
    # 文件解析实现
    #===========================================================

    def get_file_paths(self) -> List[str]:
        """
        获取 FDA 数据文件路径

        Returns:
            文件路径列表
        """
        if not os.path.exists(self.data_dir):
            logger.warning(f"FDA data directory not found: {self.data_dir}")
            return []

        files = []

        # 查找 XML 和 ZIP 文件
        for file in os.listdir(self.data_dir):
            if file.endswith((".xml", ".zip")):
                files.append(os.path.join(self.data_dir, file))

        return sorted(files)

    def _parse_file(self, file_path: str) -> Generator[Dict, None, None]:
        """
        解析 FDA 数据文件

        Args:
            file_path: 文件路径

        Yields:
            产品/批准数据记录
        """
        logger.info(f"Parsing FDA file: {file_path}")

        # 处理 ZIP 文件
        if file_path.endswith(".zip"):
            yield from self._parse_zip_file(file_path)
        else:
            yield from self._parse_xml_file(file_path)

    def _parse_zip_file(self, zip_path: str) -> Generator[Dict, None, None]:
        """
        解析 FDA ZIP 文件

        Args:
            zip_path: ZIP 文件路径

        Yields:
            产品数据记录
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找 XML 文件
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]

                for xml_file in xml_files:
                    logger.info(f"Processing {xml_file} from ZIP")

                    # 从 ZIP 中读取 XML
                    with zip_ref.open(xml_file) as file:
                        yield from self._parse_xml_content(file, xml_file)

        except Exception as e:
            logger.error(f"Failed to parse ZIP file {zip_path}: {e}")
            raise

    def _parse_xml_file(self, xml_path: str) -> Generator[Dict, None, None]:
        """
        解析 FDA XML 文件

        Args:
            xml_path: XML 文件路径

        Yields:
            产品数据记录
        """
        with open(xml_path, 'rb') as file:
            yield from self._parse_xml_content(file, os.path.basename(xml_path))

    def _parse_xml_content(self, content, source: str) -> Generator[Dict, None, None]:
        """
        解析 XML 内容

        Args:
            content: 文件内容对象
            source: 来源文件名

        Yields:
            产品数据记录
        """
        try:
            context = ET.iterparse(content, events=("start", "end"))

            for event, elem in context:
                if event == "end":
                    # 处理不同类型的 FDA 数据
                    if elem.tag == "product":
                        yield self._parse_product(elem)
                    elif elem.tag == "application":
                        yield self._parse_application(elem)
                    elif elem.tag == "tecode":
                        yield self._parse_tecode(elem)

                    elem.clear()

        except ET.ParseError as e:
            logger.error(f"Failed to parse XML from {source}: {e}")
            raise

    def _parse_product(self, product_elem: ET.Element) -> Dict:
        """
        解析产品信息（Drugs@FDA 格式）

        Args:
            product_elem: 产品 XML 元素

        Returns:
            标准化的产品数据
        """
        return {
            "application_number": self._get_elem_text(product_elem, "application-number"),
            "product_number": self._get_elem_text(product_elem, "product-number"),
            "form": self._get_elem_text(product_elem, "dosage-form"),
            "strength": self._get_elem_text(product_elem, "strength"),
            "reference_drug": self._get_elem_text(product_elem, "reference-drug"),
            "reference_standard": self._get_elem_text(product_elem, "reference-standard"),
            "brand_name": self._get_elem_text(product_elem, "brand-name"),
            "active_ingredients": self._parse_active_ingredients(product_elem),
            "marketing_status": self._get_elem_text(product_elem, "marketing-status"),
            "te_code": self._get_elem_text(product_elem, "te-code"),
            "approval_date": self._get_elem_text(product_elem, "approval-date"),
            "rld": self._get_elem_text(product_elem, "rld") == "Yes"
        }

    def _parse_application(self, app_elem: ET.Element) -> Dict:
        """
        解析申报信息

        Args:
            app_elem: 申报 XML 元素

        Returns:
            标准化的申报数据
        """
        app_number = self._get_elem_text(app_elem, "application-number")

        # 确定申报类型
        app_type = "NDA"
        if app_number.startswith("ANDA"):
            app_type = "ANDA"
        elif app_number.startswith("BLA"):
            app_type = "BLA"
        elif app_number.startswith("sNDA"):
            app_type = "sNDA"

        return {
            "application_number": app_number,
            "application_type": app_type,
            "submission_date": self._get_elem_text(app_elem, "submission-date"),
            "submission_type": self._get_elem_text(app_elem, "submission-type"),
            "sponsor_applicant": self._get_elem_text(app_elem, "sponsor-applicant"),
            "products": self._parse_app_products(app_elem),
            "approvals": self._parse_app_approvals(app_elem)
        }

    def _parse_tecode(self, tecode_elem: ET.Element) -> Dict:
        """
        解析治疗等效性代码信息

        Args:
            tecode_elem: TE Code XML 元素

        Returns:
            标准化的 TE Code 数据
        """
        return {
            "application_number": self._get_elem_text(tecode_elem, "application-number"),
            "product_number": self._get_elem_text(tecode_elem, "product-number"),
            "te_code": self._get_elem_text(tecode_elem, "te-code"),
            "rld": self._get_elem_text(tecode_elem, "rld") == "Yes",
            "rld_parent": self._get_elem_text(tecode_elem, "rld-parent")
        }

    def _get_elem_text(self, elem: ET.Element, tag: str) -> Optional[str]:
        """安全获取元素文本"""
        child = elem.find(tag)
        return child.text if child is not None else None

    def _parse_active_ingredients(self, product_elem: ET.Element) -> List[Dict]:
        """解析活性成分"""
        ingredients = []

        for ing_elem in product_elem.findall("active-ingredients/active-ingredient"):
            ingredients.append({
                "name": self._get_elem_text(ing_elem, "name"),
                "strength": self._get_elem_text(ing_elem, "strength")
            })

        return ingredients

    def _parse_app_products(self, app_elem: ET.Element) -> List[Dict]:
        """解析申报的产品"""
        products = []

        for prod_elem in app_elem.findall("products/product"):
            products.append({
                "product_number": self._get_elem_text(prod_elem, "product-number"),
                "form": self._get_elem_text(prod_elem, "dosage-form"),
                "brand_name": self._get_elem_text(prod_elem, "brand-name"),
                "active_ingredients": self._parse_active_ingredients(prod_elem)
            })

        return products

    def _parse_app_approvals(self, app_elem: ET.Element) -> List[Dict]:
        """解析申报的批准信息"""
        approvals = []

        for appr_elem in app_elem.findall("approvals/approval"):
            approvals.append({
                "approval_date": self._get_elem_text(appr_elem, "approval-date"),
                "type": self._get_elem_text(appr_elem, "type"),
                "action_date": self._get_elem_text(appr_elem, "action-date"),
                "submission_class": self._get_elem_text(appr_elem, "submission-class"),
                "review_class": self._get_elem_text(appr_elem, "review-class")
            })

        return approvals

    #===========================================================
    # 抽取记录实现
    #===========================================================

    def _fetch_records(self) -> Generator[Dict, None, None]:
        """从所有文件抽取记录"""
        for file_path in self.get_file_paths():
            for record in self._parse_file(file_path):
                yield record

    def get_total_count(self) -> Optional[int]:
        """
        获取产品总数

        Returns:
            产品总数
        """
        total = 0
        for file_path in self.get_file_paths():
            try:
                if file_path.endswith(".zip"):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                        for xml_file in xml_files:
                            with zip_ref.open(xml_file) as file:
                                tree = ET.parse(file)
                                total += len(list(tree.iter("product")))
                else:
                    tree = ET.parse(file_path)
                    total += len(list(tree.iter("product")))
            except Exception as e:
                logger.error(f"Failed to count products in {file_path}: {e}")

        return total if total > 0 else None

    #===========================================================
    # 特定抽取方法
    #===========================================================

    def extract_products_by_sponsor(
        self,
        sponsor_name: str
    ) -> List[Dict]:
        """
        按赞助方抽取产品

        Args:
            sponsor_name: 赞助方名称

        Returns:
            产品列表
        """
        products = []

        for record in self._fetch_records():
            if record.get("sponsor_applicant") == sponsor_name:
                products.append(record)

        return products

    def extract_approvals_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        按日期范围抽取批准

        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            批准列表
        """
        approvals = []

        for record in self._fetch_records():
            approval_date = record.get("approval_date")
            if approval_date and start_date <= approval_date <= end_date:
                approvals.append(record)

        return approvals

    def extract_ndas(self) -> Generator[Dict, None, None]:
        """
        只抽取 NDA 产品

        Yields:
            NDA 产品记录
        """
        for record in self._fetch_records():
            app_number = record.get("application_number", "")
            if app_number.startswith("NDA"):
                yield record

    def extract_andas(self) -> Generator[Dict, None, None]:
        """
        只抽取 ANDA 产品

        Yields:
            ANDA 产品记录
        """
        for record in self._fetch_records():
            app_number = record.get("application_number", "")
            if app_number.startswith("ANDA"):
                yield record


# 便捷函数
def extract_fda_data(
    data_dir: str = "data/raw/fda",
    limit: Optional[int] = None
) -> Dict[str, List[Dict]]:
    """
    便捷函数：抽取 FDA 数据

    Args:
        data_dir: FDA 数据文件目录
        limit: 记录数限制

    Returns:
        FDA 数据字典
    """
    extractor = FDAExtractors(data_dir=data_dir)

    try:
        result = {
            "products": [],
            "applications": [],
            "tecodes": [],
            "ndas": [],
            "andas": []
        }

        count = 0
        for record in extractor._fetch_records():
            result["products"].append(record)

            # 分类存储
            app_number = record.get("application_number", "")
            if app_number.startswith("NDA"):
                result["ndas"].append(record)
            elif app_number.startswith("ANDA"):
                result["andas"].append(record)

            count += 1
            if limit and count >= limit:
                break

        return result
    finally:
        extractor.close()
