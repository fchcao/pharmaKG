#!/usr/bin/env python3
"""
示例监管文档下载脚本
从已知 URL 下载重要的监管法规文档作为示例

这些文档可用于测试文档 ETL 管道
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
except ImportError:
    print("请安装依赖: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 示例监管文档 URL 列表
SAMPLE_REGULATORY_DOCUMENTS = {
    "CDE": {
        "指导原则": [
            # 化学药品指导原则
            ("化学药创新药晶型研究技术指导原则", "https://www.cde.org.cn/main/att/download/f31f6b3a0eb3429b8c4e5e8f8a4b3c2e"),
            ("预防用mRNA疫苗药学研究技术指导原则", "https://www.cde.org.cn/main/att/download/1234567890abcdef"),
        ]
    },
    "FDA": {
        "指导原则": [
            # FDA 指导文档（使用已知公开文档）
            ("Q7A Good Manufacturing Practice Guidance", "https://www.fda.gov/media/71012/download"),
            ("Q8(R2) Pharmaceutical Development", "https://www.fda.gov/media/71026/download"),
            ("Q9 Quality Risk Management", "https://www.fda.gov/media/71028/download"),
            ("Q10 Pharmaceutical Quality System", "https://www.fda.gov/media/71030/download"),
        ],
        "药物开发": [
            ("Content and Format of INDs", "https://www.fda.gov/media/150354/download"),
            ("Providing Clinical Evidence of Effectiveness", "https://www.fda.gov/media/146632/download"),
        ]
    }
}


class SampleDocumentDownloader:
    """示例文档下载器"""

    def __init__(self, base_dir: Path):
        """
        初始化下载器

        Args:
            base_dir: 项目基础目录
        """
        self.base_dir = base_dir
        self.sources_dir = base_dir / "data" / "sources" / "regulatory"
        self.sources_dir.mkdir(parents=True, exist_ok=True)

        # 创建分类目录
        self.cde_dir = self.sources_dir / "CDE"
        self.fda_dir = self.sources_dir / "FDA"
        self.cde_dir.mkdir(parents=True, exist_ok=True)
        self.fda_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download_file(self, url: str, destination: Path, title: str) -> bool:
        """
        下载文件

        Args:
            url: 文件URL
            destination: 目标路径
            title: 文档标题

        Returns:
            是否成功
        """
        try:
            if destination.exists():
                logger.debug(f"文件已存在，跳过: {destination.name}")
                return True

            logger.info(f"下载: {title}")

            # 使用网络加速
            os.system('source /etc/network_turbo 2>/dev/null')

            response = self.session.get(url, stream=True, timeout=120)
            response.raise_for_status()

            # 确保目录存在
            destination.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = destination.stat().st_size / 1024  # KB
            logger.info(f"✓ 下载完成: {destination.name} ({file_size:.1f} KB)")
            return True

        except Exception as e:
            logger.error(f"✗ 下载失败 {title}: {e}")
            return False

    def download_fda_samples(self) -> Dict[str, bool]:
        """下载 FDA 示例文档"""
        logger.info("=" * 60)
        logger.info("下载 FDA 示例文档")
        logger.info("=" * 60)

        results = {}

        for category, documents in SAMPLE_REGULATORY_DOCUMENTS.get("FDA", {}).items():
            category_dir = self.fda_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)

            for title, url in documents:
                # 生成安全的文件名
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
                filename = f"{safe_title}.pdf"
                destination = category_dir / filename

                results[title] = self.download_file(url, destination, title)

        return results

    def create_sample_text_document(self, content: str, filename: str, category: str) -> Path:
        """
        创建示例文本文档

        Args:
            content: 文档内容
            filename: 文件名
            category: 分类目录

        Returns:
            文件路径
        """
        destination = self.cde_dir / category / filename
        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✓ 创建示例文档: {destination}")
        return destination

    def create_cde_sample_documents(self) -> List[Path]:
        """创建 CDE 示例文档"""
        logger.info("=" * 60)
        logger.info("创建 CDE 示例文档")
        logger.info("=" * 60)

        documents = []

        # 示例文档1: 化学药指导原则
        content1 = """# 化学药品创新药晶型研究技术指导原则（试行）

## 一、前言

本指导原则旨在规范化学药品创新药晶型研究，为药品研发单位提供技术参考。

## 二、适用范围

本指导原则适用于化学药品创新药的晶型研究。

## 三、研究内容

### 3.1 多晶型现象研究

药物分子可能存在多种晶型，不同晶型可能具有不同的理化性质和生物利用度。

### 3.2 晶型筛选

应进行系统的晶型筛选研究，包括但不限于：
- 溶剂结晶
- 熔融结晶
- 研磨法

### 3.3 晶型表征

应采用多种分析方法对晶型进行表征：
- X射线粉末衍射（XRPD）
- 差示扫描量热法（DSC）
- 热重分析（TGA）
- 红外光谱（IR）

## 四、质量控制

应建立适当的质量控制方法，确保药品的晶型一致性。

## 五、稳定性研究

应考察不同晶型的稳定性，包括物理稳定性和化学稳定性。

---

发布日期: 2026年1月28日
发布机构: 国家药品监督管理局药品审评中心
"""

        doc1 = self.create_sample_text_document(content1, "化学药品创新药晶型研究技术指导原则.txt", "guidance")
        documents.append(doc1)

        # 示例文档2: 生物制品指导原则
        content2 = """# 预防用mRNA疫苗药学研究技术指导原则（试行）

## 一、前言

本指导原则旨在规范和指导预防用mRNA疫苗的药学研究。

## 二、适用范围

本指导原则适用于预防用mRNA疫苗的临床试验和上市申请。

## 三、原材料

### 3.1 质粒DNA

应建立质粒DNA的质量标准，包括：
- 序列确认
- 纯度
- 超螺旋比例

### 3.2 酶和试剂

应使用符合药典标准的酶和试剂。

## 四、生产工艺

### 4.1 体外转录工艺

应优化体外转录工艺参数：
- 核苷酸浓度
- 酶用量
- 反应时间
- 温度

### 4.2 纯化工艺

应建立有效的纯化工艺，去除杂质。

## 五、质量控制

应建立全面的质量控制体系：

### 5.1 鉴别
- 核苷酸序列测定

### 5.2 纯度
- HPLC法测定相关物质
- 电泳法测定RNA完整性

### 5.3 含量测定
- UV法测定RNA浓度

### 5.4 安全性
- 细菌内毒素
- 无菌检查

## 六、稳定性研究

应进行系统的稳定性研究，为有效期和贮存条件提供依据。

---

发布日期: 2026年1月28日
发布机构: 国家药品监督管理局药品审评中心
"""

        doc2 = self.create_sample_text_document(content2, "预防用mRNA疫苗药学研究技术指导原则.txt", "guidance")
        documents.append(doc2)

        # 示例文档3: 临床试验指导原则
        content3 = """# 药物临床试验生物样本分析实验室管理指南（试行）

## 一、前言

为规范药物临床试验生物样本分析实验室的管理，保证临床试验数据质量，制定本指南。

## 二、适用范围

本指南适用于药物临床试验中生物样本分析实验室的建设和管理。

## 三、实验室组织与管理

### 3.1 组织架构

实验室应建立完善的组织架构，明确各部门职责。

### 3.2 人员要求

- 实验室负责人应具有相关专业背景和工作经验
- 分析人员应经过培训并考核合格
- 应建立人员培训档案

## 四、实验室设施与设备

### 4.1 实验室环境

- 温湿度控制
- 空气净化
- 安全防护设施

### 4.2 仪器设备

- 应使用经过验证的分析仪器
- 建立仪器设备档案
- 定期进行校准和维护

## 五、标准操作规程

实验室应建立全面的标准操作规程（SOP），涵盖：
- 样品接收与处理
- 分析方法
- 数据处理
- 质量控制
- 文件管理

## 六、样本管理

### 6.1 样本接收

应建立样本接收程序，记录样本信息。

### 6.2 样本储存

- 按要求条件储存
- 建立样本储存记录
- 定期检查储存条件

## 七、数据管理

### 7.1 数据记录

- 原始数据应及时记录
- 数据应具有可追溯性
- 电子数据应备份

### 7.2 数据审核

应建立数据审核程序，确保数据准确性。

## 八、质量控制

### 8.1 分析方法验证

分析方法应进行全面的验证。

### 8.2 质量样本

每批分析应包含质控样本。

---

发布日期: 2026年1月
发布机构: 国家药品监督管理局药品审评中心
"""

        doc3 = self.create_sample_text_document(content3, "药物临床试验生物样本分析实验室管理指南.txt", "clinical")
        documents.append(doc3)

        return documents

    def run(self, download_fda: bool = True) -> Dict[str, any]:
        """
        运行下载和创建示例文档

        Args:
            download_fda: 是否下载FDA文档

        Returns:
            结果摘要
        """
        results = {
            'fda_downloaded': {},
            'cde_created': []
        }

        # 创建 CDE 示例文档
        results['cde_created'] = self.create_cde_sample_documents()

        # 下载 FDA 文档
        if download_fda:
            results['fda_downloaded'] = self.download_fda_samples()

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description='下载和创建示例监管文档')
    parser.add_argument(
        '--no-fda',
        action='store_true',
        help='不下载FDA文档'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default=str(Path(__file__).parent.parent),
        help='项目基础目录'
    )

    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    downloader = SampleDocumentDownloader(base_dir)

    results = downloader.run(download_fda=not args.no_fda)

    # 打印摘要
    logger.info("")
    logger.info("=" * 60)
    logger.info("操作完成")
    logger.info("=" * 60)
    logger.info(f"CDE 示例文档创建: {len(results['cde_created'])} 个")
    logger.info(f"FDA 文档下载: {len([r for r in results['fda_downloaded'].values() if r])} 个")

    return 0


if __name__ == '__main__':
    sys.exit(main())
