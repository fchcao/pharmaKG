#===========================================================
# PharmaKG ETL - DrugBank 数据抽取器
# Pharmaceutical Knowledge Graph - DrugBank Extractor
#===========================================================
# 版本: v1.0
# 描述: 从 DrugBank XML 文件抽取药物数据
#===========================================================

import logging
import os
import xml.etree.ElementTree as ET
from typing import Generator, Dict, Optional, List
from datetime import datetime
from .base import FileBasedExtractor


logger = logging.getLogger(__name__)


class DrugBankExtractor(FileBasedExtractor):
    """
    DrugBank 数据抽取器

    从下载的 XML 文件中抽取：
    - 药物基本信息
    - 靶点信息
    - 通路信息
    - 适应症
    - 不良反应
    - 药物相互作用
    """

    def __init__(self, data_dir: str = "data/raw/drugbank"):
        """
        初始化 DrugBank 抽取器

        Args:
            data_dir: DrugBank XML 文件目录
        """
        super().__init__(
            name="DrugBank",
            rate_limit=0  # 本地文件读取，无需速率限制
        )
        self.data_dir = data_dir

    #===========================================================
    # 文件解析实现
    #===========================================================

    def get_file_paths(self) -> List[str]:
        """
        获取 DrugBank XML 文件路径

        Returns:
            文件路径列表
        """
        if not os.path.exists(self.data_dir):
            logger.warning(f"DrugBank data directory not found: {self.data_dir}")
            return []

        # 查找 XML 文件
        xml_files = []
        for file in os.listdir(self.data_dir):
            if file.endswith(".xml"):
                xml_files.append(os.path.join(self.data_dir, file))

        logger.info(f"Found {len(xml_files)} DrugBank XML files")
        return sorted(xml_files)

    def _parse_file(self, file_path: str) -> Generator[Dict, None, None]:
        """
        解析 DrugBank XML 文件

        Args:
            file_path: XML 文件路径

        Yields:
            药物数据记录
        """
        logger.info(f"Parsing DrugBank file: {file_path}")

        try:
            # 使用迭代解析处理大文件
            context = ET.iterparse(file_path, events=("start", "end"))

            for event, elem in context:
                if event == "end" and elem.tag == "drug":
                    yield self._parse_drug_element(elem)
                    # 清理已处理的元素以释放内存
                    elem.clear()

        except ET.ParseError as e:
            logger.error(f"Failed to parse XML file {file_path}: {e}")
            raise

    def _parse_drug_element(self, drug_elem: ET.Element) -> Dict:
        """
        解析单个药物元素

        Args:
            drug_elem: 药物 XML 元素

        Returns:
            标准化的药物数据
        """
        # 命名空间（DrugBank XML 通常使用命名空间）
        ns = {"db": "http://drugbank.ca"}

        # 基本信息
        drugbank_id = self._get_text(drug_elem, "drugbank-id", ns)
        name = self._get_text(drug_elem, "name", ns)
        description = self._get_text(drug_elem, "description", ns)
        cas_number = self._get_text(drug_elem, "cas-number", ns)
        unii = self._get_text(drug_elem, "unii", ns)
        drug_type = self._get_text(drug_elem, "drug-type", ns)
        approval = self._parse_approval(drug_elem, ns)

        # 化学结构
        properties = self._parse_properties(drug_elem, ns)

        # 分类
        categories = self._parse_categories(drug_elem, ns)

        # 靶点
        targets = self._parse_targets(drug_elem, ns)

        # 通路
        pathways = self._parse_pathways(drug_elem, ns)

        # 适应症
        indications = self._parse_indications(drug_elem, ns)

        # 不良反应
        reactions = self._parse_adverse_reactions(drug_elem, ns)

        # 药物相互作用
        interactions = self._parse_interactions(drug_elem, ns)

        return {
            # 基本信息
            "drugbank_id": drugbank_id,
            "name": name,
            "description": description,
            "cas_number": cas_number,
            "unii": unii,
            "drug_type": drug_type,
            "approval": approval,

            # 化学属性
            "properties": properties,

            # 关联数据
            "categories": categories,
            "targets": targets,
            "pathways": pathways,
            "indications": indications,
            "adverse_reactions": reactions,
            "drug_interactions": interactions,

            # 外部标识符
            "external_identifiers": self._parse_external_ids(drug_elem, ns)
        }

    def _get_text(self, elem: ET.Element, tag: str, ns: Dict) -> Optional[str]:
        """安全获取元素文本"""
        child = elem.find(f"db:{tag}", ns)
        return child.text if child is not None else None

    def _parse_approval(self, drug_elem: ET.Element, ns: Dict) -> Optional[Dict]:
        """解析批准信息"""
        approval_elem = drug_elem.find("db:approved", ns)
        if approval_elem is not None:
            return {
                "approved": approval_elem.text == "true",
                "year": self._get_text(drug_elem, "approved-year", ns),
                "flag": self._get_text(drug_elem, "approved-flag", ns)
            }
        return None

    def _parse_properties(self, drug_elem: ET.Element, ns: Dict) -> Dict:
        """解析化学属性"""
        props_elem = drug_elem.find("db:properties", ns)
        if props_elem is None:
            return {}

        return {
            "molecular_weight": self._get_text(props_elem, "molecular-weight", ns),
            "monoisotopic_mass": self._get_text(props_elem, "monoisotopic-mass", ns),
            "smiles": self._get_text(props_elem, "smiles", ns),
            "inchi": self._get_text(props_elem, "inchi", ns),
            "inchikey": self._get_text(props_elem, "inchikey", ns),
            "iupac_name": self._get_text(props_elem, "iupac-name", ns),
            "logp": self._get_text(props_elem, "logp", ns),
            "solubility": self._get_text(props_elem, "solubility", ns)
        }

    def _parse_categories(self, drug_elem: ET.Element, ns: Dict) -> List[Dict]:
        """解析药物分类"""
        categories = []
        categories_elem = drug_elem.find("db:categories", ns)

        if categories_elem is not None:
            for cat in categories_elem.findall("db:category", ns):
                categories.append({
                    "name": cat.get("name"),
                    "category": cat.get("category")
                })

        return categories

    def _parse_targets(self, drug_elem: ET.Element, ns: Dict) -> List[Dict]:
        """解析靶点信息"""
        targets = []
        targets_elem = drug_elem.find("db:targets", ns)

        if targets_elem is not None:
            for target in targets_elem.findall("db:target", ns):
                target_info = {
                    "id": self._get_text(target, "id", ns),
                    "name": self._get_text(target, "name", ns),
                    "organism": self._get_text(target, "organism", ns),
                    "actions": []
                }

                # 解析作用动作
                for action in target.findall("db:actions/db:action", ns):
                    target_info["actions"].append(action.text)

                # 解析已知作用
                known_action_elem = target.find("db:known-action", ns)
                if known_action_elem is not None:
                    target_info["known_action"] = known_action_elem.text

                targets.append(target_info)

        return targets

    def _parse_pathways(self, drug_elem: ET.Element, ns: Dict) -> List[Dict]:
        """解析通路信息"""
        pathways = []
        pathways_elem = drug_elem.find("db:pathways", ns)

        if pathways_elem is not None:
            for pathway in pathways_elem.findall("db:pathway", ns):
                pathways.append({
                    "name": self._get_text(pathway, "name", ns),
                    "category": self._get_text(pathway, "category", ns),
                    "smpdb_id": self._get_text(pathway, "smpdb-id", ns)
                })

        return pathways

    def _parse_indications(self, drug_elem: ET.Element, ns: Dict) -> List[Dict]:
        """解析适应症"""
        indications = []
        indications_elem = drug_elem.find("db:indications", ns)

        if indications_elem is not None:
            for indication in indications_elem.findall("db:indication", ns):
                ind_info = {
                    "name": self._get_text(indication, "name", ns),
                    "disease_name": indication.get("name")
                }

                # 解析适应症类别
                for cat in indication.findall("db:indication-category", ns):
                    ind_info.setdefault("categories", []).append(cat.text)

                indications.append(ind_info)

        return indications

    def _parse_adverse_reactions(self, drug_elem: ET.Element, ns: Dict) -> List[Dict]:
        """解析不良反应"""
        reactions = []
        reactions_elem = drug_elem.find("db:adverse-reactions", ns)

        if reactions_elem is not None:
            for reaction in reactions_elem.findall("db:adverse-reaction", ns):
                reactions.append({
                    "name": self._get_text(reaction, "name", ns),
                    "frequency": self._get_text(reaction, "frequency", ns)
                })

        return reactions

    def _parse_interactions(self, drug_elem: ET.Element, ns: Dict) -> List[Dict]:
        """解析药物相互作用"""
        interactions = []
        interactions_elem = drug_elem.find("db:drug-interactions", ns)

        if interactions_elem is not None:
            for interaction in interactions_elem.findall("db:drug-interaction", ns):
                interaction_info = {
                    "description": self._get_text(interaction, "description", ns)
                }

                # 解析相互作用的药物
                for drug in interaction.findall("db:drug", ns):
                    interaction_info.setdefault("interacting_drugs", []).append({
                        "name": self._get_text(drug, "name", ns),
                        "drugbank_id": self._get_text(drug, "drugbank-id", ns)
                    })

                interactions.append(interaction_info)

        return interactions

    def _parse_external_ids(self, drug_elem: ET.Element, ns: Dict) -> Dict:
        """解析外部标识符"""
        external_ids = {}
        ext_ids_elem = drug_elem.find("db:external-identifiers", ns)

        if ext_ids_elem is not None:
            for ext_id in ext_ids_elem.findall("db:external-identifier", ns):
                resource = self._get_text(ext_id, "resource", ns)
                identifier = self._get_text(ext_id, "identifier", ns)
                if resource and identifier:
                    external_ids[resource] = identifier

        return external_ids

    #===========================================================
    # 抽取记录实现
    #===========================================================

    def _fetch_records(self) -> Generator[Dict, None, None]:
        """从所有 XML 文件抽取记录"""
        for file_path in self.get_file_paths():
            for drug in self._parse_file(file_path):
                yield drug

    def get_total_count(self) -> Optional[int]:
        """
        获取药物总数

        Returns:
            药物总数
        """
        total = 0
        for file_path in self.get_file_paths():
            # 快速计算：统计 <drug> 元素数量
            try:
                tree = ET.parse(file_path)
                total += len(tree.findall(".//{http://drugbank.ca}drug"))
            except Exception as e:
                logger.error(f"Failed to count drugs in {file_path}: {e}")

        return total if total > 0 else None


# 便捷函数
def extract_drugbank_data(
    data_dir: str = "data/raw/drugbank",
    limit: Optional[int] = None
) -> List[Dict]:
    """
    便捷函数：抽取 DrugBank 数据

    Args:
        data_dir: DrugBank XML 文件目录
        limit: 记录数限制

    Returns:
        药物数据列表
    """
    extractor = DrugBankExtractor(data_dir=data_dir)

    try:
        drugs = []
        for drug in extractor._fetch_records():
            drugs.append(drug)
            if limit and len(drugs) >= limit:
                break
        return drugs
    finally:
        extractor.close()
