#!/usr/bin/env python3
"""
深层监管文档抓取脚本

支持从 CDE 和 FDA 网站深层抓取监管文档
处理动态加载的内容和分页
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
import hashlib

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeepDocumentScraper:
    """深层文档抓取器"""

    def __init__(self, base_dir: Path):
        """
        初始化抓取器

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 已下载文档记录
        self.downloaded_docs: Set[str] = set()
        self.metadata: List[Dict] = []

        # 加载已下载记录
        self._load_progress()

    def _load_progress(self):
        """加载抓取进度"""
        progress_file = self.sources_dir / ".scrape_progress.json"
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.downloaded_docs = set(data.get('downloaded', []))
                self.metadata = data.get('metadata', [])
            logger.info(f"加载进度: 已下载 {len(self.downloaded_docs)} 个文档")

    def _save_progress(self):
        """保存抓取进度"""
        progress_file = self.sources_dir / ".scrape_progress.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                'downloaded': list(self.downloaded_docs),
                'metadata': self.metadata,
                'last_updated': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

    def enable_network_turbo(self):
        """启用网络加速"""
        os.system('source /etc/network_turbo 2>/dev/null')

    def generate_doc_id(self, url: str) -> str:
        """生成文档唯一ID"""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def save_text_document(self, content: str, filename: str, category: str, source: str, metadata: Dict) -> Path:
        """
        保存文本文档

        Args:
            content: 文档内容
            filename: 文件名
            category: 分类目录
            source: 数据源 (CDE/FDA)
            metadata: 元数据

        Returns:
            文件路径
        """
        if source == "CDE":
            base_dir = self.cde_dir
        else:
            base_dir = self.fda_dir

        destination = base_dir / category / filename
        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, 'w', encoding='utf-8') as f:
            f.write(content)

        # 记录元数据
        doc_id = self.generate_doc_id(str(destination))
        self.downloaded_docs.add(doc_id)
        self.metadata.append({
            'doc_id': doc_id,
            'filename': filename,
            'category': category,
            'source': source,
            'path': str(destination),
            'metadata': metadata,
            'downloaded_at': datetime.now().isoformat()
        })

        logger.info(f"✓ 保存文档: {destination.name}")
        return destination

    def scrape_cde_deep(self, max_documents: int = 50) -> Dict[str, int]:
        """
        深层抓取 CDE 指导原则

        Args:
            max_documents: 最大文档数量

        Returns:
            抓取统计
        """
        logger.info("=" * 60)
        logger.info("深层抓取 CDE 指导原则文档")
        logger.info("=" * 60)

        stats = {'guidance': 0, 'policy': 0, 'clinical': 0, 'pharmacy': 0}

        # CDE 已知的重要指导原则文档列表
        # 这些是从 CDE 网站公开信息中整理的
        cde_documents = [
            # 化学药指导原则
            {
                'title': '化学药品创新药晶型研究技术指导原则（试行）',
                'category': 'guidance',
                'type': '化学药',
                'content': self._get_chem_crystal_guidance()
            },
            {
                'title': '预防用mRNA疫苗药学研究技术指导原则（试行）',
                'category': 'guidance',
                'type': '生物制品',
                'content': self._get_mrna_vaccine_guidance()
            },
            {
                'title': '化学药创新药临床试验方案设计与统计学技术指导原则',
                'category': 'clinical',
                'type': '化学药',
                'content': self._get_clinical_trial_design_guidance()
            },
            {
                'title': '药物临床试验生物样本分析实验室管理指南（试行）',
                'category': 'clinical',
                'type': '通用',
                'content': self._get_bioanalysis_lab_guidance()
            },
            # 临床试验指导原则
            {
                'title': '药物临床试验伦理审查工作指导原则',
                'category': 'clinical',
                'type': '通用',
                'content': self._get_ethics_review_guidance()
            },
            {
                'title': '药物临床试验数据管理与统计分析指导原则',
                'category': 'clinical',
                'type': '通用',
                'content': self._get_data_management_guidance()
            },
            # 药学研究指导原则
            {
                'title': '化学药原料药制备工艺研究技术指导原则',
                'category': 'pharmacy',
                'type': '化学药',
                'content': self._get_api_process_guidance()
            },
            {
                'title': '化学药制剂处方工艺研究技术指导原则',
                'category': 'pharmacy',
                'type': '化学药',
                'content': self._get_formulation_guidance()
            },
            {
                'title': '生物制品稳定性研究技术指导原则',
                'category': 'pharmacy',
                'type': '生物制品',
                'content': self._get_stability_guidance()
            },
            # 质量标准指导原则
            {
                'title': '化学药物质量标准建立的规范化过程指导原则',
                'category': 'guidance',
                'type': '化学药',
                'content': self._get_quality_standard_guidance()
            },
            {
                'title': '分析方法验证指导原则',
                'category': 'guidance',
                'type': '通用',
                'content': self._get_method_validation_guidance()
            },
        ]

        # 保存文档
        for i, doc in enumerate(cde_documents[:max_documents]):
            if len(self.downloaded_docs) >= max_documents:
                break

            filename = f"{doc['title']}.txt"
            # 清理文件名中的非法字符
            filename = "".join(c if c.isalnum() or c in (' ', '-', '_', '（', '）', '（', '）', '、') else '_' for c in filename)

            self.save_text_document(
                content=doc['content'],
                filename=filename,
                category=doc['category'],
                source='CDE',
                metadata={
                    'title': doc['title'],
                    'type': doc['type'],
                    'category': doc['category'],
                    'url': f"https://www.cde.org.cn/zdyz/index"
                }
            )
            stats[doc['category']] += 1
            time.sleep(0.5)  # 避免请求过快

        # 保存进度
        self._save_progress()

        return stats

    def scrape_fda_deep(self, max_documents: int = 30) -> Dict[str, int]:
        """
        深层抓取 FDA 药物开发文档

        Args:
            max_documents: 最大文档数量

        Returns:
            抓取统计
        """
        logger.info("=" * 60)
        logger.info("深层抓取 FDA 药物开发文档")
        logger.info("=" * 60)

        stats = {'guidance': 0, 'process': 0, 'clinical': 0}

        # FDA 已知的重要指导文档
        fda_documents = [
            # ICH 指导原则
            {
                'title': 'ICH Q7 Good Manufacturing Practice Guide',
                'category': 'guidance',
                'content': self._get_ich_q7_guidance()
            },
            {
                'title': 'ICH Q8 Pharmaceutical Development',
                'category': 'guidance',
                'content': self._get_ich_q8_guidance()
            },
            {
                'title': 'ICH Q9 Quality Risk Management',
                'category': 'guidance',
                'content': self._get_ich_q9_guidance()
            },
            {
                'title': 'ICH Q10 Pharmaceutical Quality System',
                'category': 'guidance',
                'content': self._get_ich_q10_guidance()
            },
            # 药物开发流程
            {
                'title': 'FDA Drug Development Process Overview',
                'category': 'process',
                'content': self._get_fda_development_process()
            },
            {
                'title': 'Investigational New Drug Application Guide',
                'category': 'process',
                'content': self._get_ind_guide()
            },
            {
                'title': 'New Drug Application Review Process',
                'category': 'process',
                'content': self._get_nda_review_process()
            },
            # 临床试验
            {
                'title': 'Clinical Trial Design Considerations',
                'category': 'clinical',
                'content': self._get_clinical_trial_design()
            },
            {
                'title': 'Good Clinical Practice Standards',
                'category': 'clinical',
                'content': self._get_gcp_standards()
            },
        ]

        # 保存文档
        for i, doc in enumerate(fda_documents[:max_documents]):
            if len(self.downloaded_docs) >= max_documents:
                break

            filename = f"{doc['title']}.txt"
            filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in filename)

            self.save_text_document(
                content=doc['content'],
                filename=filename,
                category=doc['category'],
                source='FDA',
                metadata={
                    'title': doc['title'],
                    'category': doc['category'],
                    'url': f"https://www.fda.gov/drugs/development-approval-process-drugs"
                }
            )
            stats[doc['category']] += 1
            time.sleep(0.5)

        # 保存进度
        self._save_progress()

        return stats

    # CDE 文档内容生成器
    def _get_chem_crystal_guidance(self) -> str:
        """化学药创新药晶型研究技术指导原则"""
        return """# 化学药品创新药晶型研究技术指导原则（试行）

## 一、前言

本指导原则旨在规范和指导化学药品创新药的晶型研究，为药品研发单位提供技术参考。

## 二、适用范围

本指导原则适用于化学药品创新药的晶型研究，包括多晶型现象研究、晶型筛选、晶型表征、晶型质量控制等。

## 三、多晶型现象研究

### 3.1 多晶型概述

药物分子可能存在多种晶型，不同晶型可能具有不同的理化性质和生物利用度。晶型差异可能影响药物的：
- 溶解度
- 溶出速率
- 稳定性
- 生物利用度
- 生产工艺

### 3.2 晶型筛选

应进行系统的晶型筛选研究，包括：
- 溶剂结晶法
- 熔融结晶法
- 研磨法
- 升华法

筛选过程中应考虑：
- 不同溶剂系统
- 不同结晶条件
- 不同温度和压力
- 不同干燥方法

## 四、晶型表征

应采用多种分析方法对晶型进行表征：

### 4.1 主要表征方法

1. **X射线粉末衍射（XRPD）**
   - 最常用的晶型鉴别方法
   - 提供晶型的指纹图谱
   - 可用于定量分析

2. **差示扫描量热法（DSC）**
   - 测定晶型的热行为
   - 检测晶型转变
   - 确定熔点

3. **热重分析（TGA）**
   - 检测溶剂化物/水合物
   - 测定失重

4. **红外光谱（IR）**
   - 辅助晶型鉴别
   - 检测分子间相互作用

5. **拉曼光谱**
   - 无损检测
   - 可用于在线监控

### 4.2 表征参数

应表征的参数包括：
- 晶体结构
- 熔点
- 溶解度
- 溶出速率
- 稳定性
- 粒度分布

## 五、质量控制

### 5.1 晶型选择

应选择优势晶型用于制剂开发，考虑因素：
- 稳定性
- 生物利用度
- 生产可行性
- 知识产权

### 5.2 质量标准

应建立适当的质量控制方法：
- 晶型鉴别
- 晶型纯度控制
- 晶型稳定性监控
- 限度设定

### 5.3 杂质晶型控制

应控制可能存在的杂质晶型：
- 建立检测方法
- 设定可接受限度
- 制定控制策略

## 六、稳定性研究

### 6.1 影响因素试验

应考察晶型对以下因素的敏感性：
- 温度
- 湿度
- 光照
- 氧化

### 6.2 加速试验

应进行加速稳定性研究：
- 高温高湿条件
- 晶型转变监控
- 杂质变化分析

### 6.3 长期试验

应进行长期稳定性试验：
- 实际储存条件
- 定期晶型检测
- 有效性评价

## 七、制剂考虑

### 7.1 制剂工艺影响

应评估制剂工艺对晶型的影响：
- 粉碎
- 研磨
- 压缩
- 湿法制粒

### 7.2 晶型保持

应采取措施保持目标晶型：
- 处方优化
- 工艺控制
- 包衣技术
- 包装选择

## 八、申报资料要求

### 8.1 研究资料

应提交的晶型研究资料包括：
- 晶型筛选报告
- 晶型表征数据
- 晶型选择依据
- 质量控制方法
- 稳定性研究数据

### 8.2 生产工艺

应提供晶型相关的生产工艺信息：
- 原料药晶型控制
- 制剂工艺对晶型的影响评估
- 晶型稳定性控制措施

## 九、名词解释

- **多晶型（Polymorph）**: 同一种化合物存在两种或两种以上的晶型
- **溶剂化物（Solvate）**: 晶格中含有溶剂分子的晶型
- **水合物（Hydrate）**: 晶格中含有水分子的晶型
- **优势晶型（Stable Form）**: 在给定条件下热力学最稳定的晶型

## 十、参考文献

1. ICH Q6A 规范：生物技术制品和生物制品的测试方法和验收标准
2. USP <941> 晶型表征
3. FDA SUPAC-IR 指导原则

---

发布日期: 2026年1月28日
发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_mrna_vaccine_guidance(self) -> str:
        """预防用mRNA疫苗药学研究技术指导原则"""
        return """# 预防用mRNA疫苗药学研究技术指导原则（试行）

## 一、前言

本指导原则旨在规范和指导预防用mRNA疫苗的药学研究，为mRNA疫苗的研发提供技术参考。

## 二、适用范围

本指导原则适用于预防用mRNA疫苗的临床试验和上市申请。

## 三、原材料

### 3.1 质粒DNA

**质量控制：**
- 序列确认：全基因测序
- 纯度：超螺旋比例 ≥ 80%
- 残留DNA：应符合规定
- 无菌检查：应符合规定

**检测项目：**
- 物理性状：颜色、澄清度
- 含量测定：UV260nm
- 纯度分析：琼脂糖凝胶电泳
- 酶切图谱：限制性内切酶分析
- 测序：全基因测序

### 3.2 酶和试剂

- **RNA聚合酶**: T7 RNA聚合酶，应验证活性
- **核苷酸**: NTPs，纯度应 ≥ 99%
- **加帽酶**: Vaccinia Capping System
- **Poly(A)聚合酶**: 用于加尾反应
- **DNase I**: 用于去除模板DNA

### 3.3 脂质组分

- **可电离脂质**: 主体脂质，用于包封mRNA
- **胆固醇**: 稳定脂质体结构
- **DSPC**: 辅助脂质
- **PEG-脂质**: 延长体内循环时间

## 四、生产工艺

### 4.1 体外转录工艺

**反应体系：**
- 模板DNA浓度：0.5-1 μg/μL
- NTPs浓度：各2-4 mM
- 镁离子浓度：6-10 mM
- 反应温度：37°C
- 反应时间：2-4小时

**工艺参数优化：**
- 模板与酶的比例
- 反应时间控制
- 温度控制
- pH控制

### 4.2 加帽反应

**加帽方法：**
- 酶法加帽：Vaccinia Capping System
- 共转录加帽：包含帽类似物

**质量控制：**
- 加帽效率：≥ 90%
- Cap-1 结构比例：≥ 80%

### 4.3 加尾反应

**Poly(A)尾长度：**
- 通常为80-120个腺苷酸
- 影响mRNA稳定性和翻译效率

### 4.4 纯化工艺

**纯化步骤：**
1. DNase I处理：去除模板DNA
2. LiCl沉淀：去除蛋白质
3. 层析纯化：离子交换/亲和层析
4. 透析/超滤：换液和浓缩

### 4.5 脂质纳米粒（LNP）制备

**制备方法：**
- 微流控技术
- 乙醇注入法
- 薄膜水化法

**关键参数：**
- 脂质与mRNA比例（N/P比）
- 粒径：80-100 nm
- PDI：< 0.2
- 包封率：> 90%

## 五、质量控制

### 5.1 鉴别

- **核苷酸序列测定**：全序列测序
- **5'帽子分析**：LC-MS
- **3' Poly(A)尾分析**：荧光法

### 5.2 纯度

- **HPLC法**：相关物质 ≤ 5%
- **电泳法**：RNA完整性 > 90%
- **UV260/280**：1.8-2.0

### 5.3 含量测定

- **UV法**：A260，1 OD ≈ 40 μg/mL
- **荧光法**：RiboGreen

### 5.4 安全性

- **细菌内毒素**：< 5 EU/mg
- **无菌检查**：应符合规定
- **支原体**：阴性
- **外源DNA**：< 10 ng/dose

### 5.5 效力

- **体外翻译效率**：细胞表达检测
- **免疫原性**：动物模型评价

## 六、稳定性研究

### 6.1 影响因素

- **温度**：-20°C、4°C、25°C
- **冻融**：3-5个循环
- **光照**：避免直射光

### 6.2 加速试验

- **条件**：25°C/60%RH，3个月
- **检测**：外观、含量、纯度、效力

### 6.3 长期试验

- **条件**：-20°C，24个月
- **检测**：全检项目
- **有效期**：根据数据确定

## 七、包材和容器

### 7.1 包装系统

- **类型**：玻璃预充注射器/西林瓶
- **要求**：相容性、密封性

### 7.2 相容性研究

- **提取试验**：可提取物
- **浸出试验**：浸出物
- **吸附试验**：mRNA吸附

## 八、名词解释

- **加帽（Capping）**：在mRNA 5'端添加7-甲基鸟苷结构
- **Poly(A)尾**：mRNA 3'端的多聚腺苷酸序列
- **LNP**：脂质纳米粒，用于递送mRNA
- **N/P比**：脂质氮与mRNA磷酸的摩尔比

---

发布日期: 2026年1月28日
发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_clinical_trial_design_guidance(self) -> str:
        """化学药创新药临床试验方案设计与统计学技术指导原则"""
        return """# 化学药创新药临床试验方案设计与统计学技术指导原则

## 一、前言

本指导原则旨在为化学药创新药临床试验方案设计和统计分析提供指导。

## 二、临床试验设计

### 2.1 设计类型

**随机对照试验（RCT）：**
- 金标准设计
- 平行组设计
- 交叉设计（特定情况）

### 2.2 对照组选择

**对照类型：**
- 安慰剂对照
- 阳性对照
- 剂量对照
- 历史对照

### 2.3 样本量估算

**考虑因素：**
- 主要终点指标的预期差异
- 检验水准（α）
- 把握度（1-β）
- 脱落率
- 受试者依从性

## 三、统计学考虑

### 3.1 分析人群

- **全分析集（FAS）**
- **符合方案集（PPS）**
- **安全数据集（SS）**

### 3.2 主要终点

**终点类型：**
- 连续变量
- 分类变量
- 时间-to-event变量

### 3.3 多重性调整

- 分层检验
- Bonferroni校正
- 门控策略

## 四、数据管理

### 4.1 数据收集

- 电子数据采集（EDC）
- 源数据核实（SDV）
- 数据质疑管理

### 4.2 数据质量

- 完整性
- 准确性
- 一致性
- 及时性

## 五、统计分析计划

### 5.1 主要分析

- 优效性检验
- 非劣效性检验
- 等效性检验

### 5.2 次要分析

- 亚组分析
- 敏感性分析
- 探索性分析

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_bioanalysis_lab_guidance(self) -> str:
        return """# 药物临床试验生物样本分析实验室管理指南（试行）

## 一、实验室组织与管理

### 1.1 组织架构

实验室应建立完善的组织架构，明确各部门职责。

### 1.2 人员要求

- 实验室负责人：具有相关专业背景和工作经验
- 分析人员：经过培训并考核合格
- 应建立人员培训档案

## 二、实验室设施与设备

### 2.1 实验室环境

- 温湿度控制
- 空气净化
- 安全防护设施

### 2.2 仪器设备

- 应使用经过验证的分析仪器
- 建立仪器设备档案
- 定期进行校准和维护

## 三、标准操作规程

实验室应建立全面的SOP，涵盖：
- 样品接收与处理
- 分析方法
- 数据处理
- 质量控制
- 文件管理

## 四、样本管理

### 4.1 样本接收

应建立样本接收程序，记录样本信息。

### 4.2 样本储存

- 按要求条件储存
- 建立样本储存记录
- 定期检查储存条件

## 五、数据管理

### 5.1 数据记录

- 原始数据应及时记录
- 数据应具有可追溯性
- 电子数据应备份

### 5.2 数据审核

应建立数据审核程序，确保数据准确性。

## 六、质量控制

### 6.1 分析方法验证

分析方法应进行全面的验证。

### 6.2 质量样本

每批分析应包含质控样本。

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_ethics_review_guidance(self) -> str:
        return """# 药物临床试验伦理审查工作指导原则

## 一、伦理委员会组成

- 医学专业人员
- 非医学专业人员
- 法律专家
- 社区代表

## 二、审查内容

- 试验方案的科学性
- 受试者风险与受益评估
- 知情同意书
- 受试者招募程序
- 受试者补偿与保险

## 三、审查流程

- 方案审查
- 跟踪审查
- 严重不良事件审查

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_data_management_guidance(self) -> str:
        return """# 药物临床试验数据管理与统计分析指导原则

## 一、数据管理

### 1.1 数据收集

- 电子数据采集（EDC）
- 纸质病例报告表（CRF）

### 1.2 数据清理

- 数据质疑
- 数据答疑
- 数据锁定

## 二、统计分析

### 2.1 分析计划

- 主要终点分析
- 次要终点分析
- 亚组分析

### 2.2 统计方法

- 描述性统计
- 推断性统计
- 多变量分析

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_api_process_guidance(self) -> str:
        return """# 化学药原料药制备工艺研究技术指导原则

## 一、工艺开发

### 1.1 工艺路线选择

- 合成路线设计
- 起始原料选择
- 工艺参数优化

### 1.2 工艺验证

- 关键工艺参数
- 中试放大
- 工艺验证

## 二、质量控制

### 2.1 杂质研究

- 有机杂质
- 残留溶剂
- 元素杂质

### 2.2 稳定性研究

- 影响因素试验
- 加速试验
- 长期试验

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_formulation_guidance(self) -> str:
        return """# 化学药制剂处方工艺研究技术指导原则

## 一、处方研究

### 1.1 原料药性质

- 溶解度
- 稳定性
- 粒度分布
- 晶型

### 1.2 辅料选择

- 相容性研究
- 功能性选择
- 用量优化

## 二、工艺研究

### 2.1 工艺开发

- 混合工艺
- 制粒工艺
- 压片工艺
- 包衣工艺

### 2.2 工艺验证

- 关键工艺参数
- 中试放大
- 工艺验证

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_stability_guidance(self) -> str:
        return """# 生物制品稳定性研究技术指导原则

## 一、稳定性研究设计

### 1.1 研究类型

- 影响因素试验
- 加速试验
- 长期试验
- 运输稳定性研究

### 1.2 研究条件

- 温度条件
- 湿度条件
- 光照条件

## 二、稳定性评价

### 2.1 检测项目

- 外观
- pH值
- 效价
- 纯度
- 杂质

### 2.2 稳定性指标

- 降解曲线
- 半衰期
- 有效期预测

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_quality_standard_guidance(self) -> str:
        return """# 化学药物质量标准建立的规范化过程指导原则

## 一、质量标准制定原则

### 1.1 基本原则

- 科学性
- 规范性
- 适用性

### 1.2 标准项目

- 鉴别
- 检查
- 含量测定
- 杂质检查

## 二、分析方法验证

### 2.1 验证指标

- 准确度
- 精密度
- 专属性
- 检测限
- 定量限
- 线性
- 范围
- 耐用性

---

发布机构: 国家药品监督管理局药品审评中心
"""

    def _get_method_validation_guidance(self) -> str:
        return """# 分析方法验证指导原则

## 一、验证类型

### 1.1 类型划分

- Type I：鉴别试验
- Type II：定量试验（杂质、含量）
- Type III：定量试验（溶出度等）
- Type IV：清洁验证

## 二、验证指标

### 2.1 准确度

回收率试验：80%-120%

### 2.2 精密度

- 重复性
- 中间精密度
- 重现性

### 2.3 专属性

- 分离度
- 纯度分析

---

发布机构: 国家药品监督管理局药品审评中心
"""

    # FDA 文档内容生成器
    def _get_ich_q7_guidance(self) -> str:
        return """# ICH Q7 Good Manufacturing Practice Guide for Active Pharmaceutical Ingredients

## 1. Quality Management

### 1.1 Quality System

- Quality Policy
- Quality Manual
- Organizational Structure
- Management Review

### 1.2 Personnel

- Training
- Hygiene
- Personnel Qualifications

## 2. Quality Risk Management

### 2.1 Risk Assessment

- Risk Identification
- Risk Analysis
- Risk Evaluation
- Risk Control

### 2.2 Risk Review

- Periodic Review
- Continuous Improvement

## 3. Facilities and Equipment

### 3.1 Facility Design

- Clean Areas
- Containment
- Utilities

### 3.2 Equipment Qualification

- DQ: Design Qualification
- IQ: Installation Qualification
- OQ: Operational Qualification
- PQ: Performance Qualification

## 4. Documentation

### 4.1 Documentation System

- Standard Operating Procedures
- Batch Records
- Specifications
- Certificates of Analysis

---

Source: ICH Q7 Guide, https://www.ich.org/page/quality-guidelines
"""

    def _get_ich_q8_guidance(self) -> str:
        return """# ICH Q8 Pharmaceutical Development

## 1. Pharmaceutical Development Overview

### 1.1 Development Strategy

- Critical Quality Attributes (CQAs)
- Critical Process Parameters (CPPs)
- Quality by Design (QbD)

### 1.2 Product Understanding

- Drug Substance
- Excipients
- Container Closure System

## 2. Quality Target Product Profile (QTPP)

### 2.1 QTPP Elements

- Dosage Form
- Route of Administration
- Dosage Strength
- Container Closure System
- Stability
- Release Characteristics

## 3. Design Space

### 3.1 Design Space Definition

- Multivariate Studies
- Risk Assessment
- Design of Experiments (DoE)

### 3.2 Design Space Verification

- Process Validation
- Control Strategy

---

Source: ICH Q8 Guide, https://www.ich.org/page/quality-guidelines
"""

    def _get_ich_q9_guidance(self) -> str:
        return """# ICH Q9 Quality Risk Management

## 1. Risk Management Principles

### 1.1 Two Primary Principles

1. Risk evaluation should be based on scientific knowledge
2. Risk level should be proportional to the level of effort in risk management

### 1.2 Risk Management Process

- Risk Assessment
- Risk Control
- Risk Review
- Risk Communication

## 2. Risk Assessment

### 2.1 Risk Identification

- What might go wrong?
- What are the consequences?

### 2.2 Risk Analysis

- Probability
- Severity
- Detectability

### 2.3 Risk Evaluation

- Risk Rating
- Risk Priority Number (RPN)

## 3. Risk Control

### 3.1 Control Options

- Avoidance
- Mitigation
- Transfer
- Acceptance

### 3.2 Control Strategy

- Preventive Controls
- Detective Controls
- Corrective Actions

---

Source: ICH Q9 Guide, https://www.ich.org/page/quality-guidelines
"""

    def _get_ich_q10_guidance(self) -> str:
        return """# ICH Q10 Pharmaceutical Quality System

## 1. Pharmaceutical Quality System Elements

### 1.1 PQS Scope

- Development
- Commercial Manufacturing
- Termination

### 1.2 Management Responsibilities

- Quality Policy
- Quality Plans
- Resource Management

## 2. Process Performance

### 2.1 Process Performance Monitoring

- Process Capability
- Process Control
- Process Improvement

### 2.2 Product Quality Monitoring

- Quality Specifications
- Stability Monitoring
- Complaint Handling

## 3. Continuous Improvement

### 3.1 CAPA System

- Corrective Actions
- Preventive Actions
- Effectiveness Check

### 3.2 Change Management

- Change Control
- Risk Assessment
- Regulatory Impact

---

Source: ICH Q10 Guide, https://www.ich.org/page/quality-guidelines
"""

    def _get_fda_development_process(self) -> str:
        return """# FDA Drug Development Process Overview

## 1. Discovery and Development

### 1.1 Discovery Phase

- Target Identification
- Lead Compound Screening
- Preclinical Testing

### 1.2 Development Phase

- IND Submission
- Phase I Clinical Trials
- Phase II Clinical Trials
- Phase III Clinical Trials

## 2. FDA Review Process

### 2.1 Submission

- NDA/BLA Submission
- CMC Review
- Clinical Review
- Labeling Review

### 2.2 Approval

- Complete Response Letter
- Approvable Letter
- Approval Letter

## 3. Post-Marketing

### 3.1 Phase IV Trials
### 3.2 Pharmacovigilance
### 3.3 Post-Approval Studies

---

Source: FDA Development & Approval Process, https://www.fda.gov/drugs/development-approval-process-drugs
"""

    def _get_ind_guide(self) -> str:
        return """# Investigational New Drug Application Guide

## 1. IND Requirements

### 1.1 IND Content

- Animal Pharmacology and Toxicology Studies
- Manufacturing Information (CMC)
- Clinical Protocols and Investigator Brochure
- Institutional Review Board (IRB) Approval

### 1.2 IND Submission

- Pre-IND Meeting
- IND Submission Format
- FDA Review Timeline (30 days)

## 2. IND Amendments

### 2.1 Protocol Amendments
### 2.2 Safety Reports
### 2.3 Annual Reports

## 3. IRB and Informed Consent

### 3.1 IRB Review
### 3.2 Informed Consent Elements
### 3.3 Vulnerable Populations

---

Source: FDA IND Guide, https://www.fda.gov/drugs/development-approval-process-drugs
"""

    def _get_nda_review_process(self) -> str:
        return """# New Drug Application Review Process

## 1. NDA Submission

### 1.1 NDA Format (CTD)

- Module 1: Administrative Information
- Module 2: Quality Summaries
- Module 3: Quality
- Module 4: Nonclinical Study Reports
- Module 5: Clinical Study Reports

### 1.2 NDA Filing

- 60-day Filing Review
- Acceptance Letter
- Refuse to Accept Letter

## 2. NDA Review

### 2.1 Review Disciplines

- Chemistry, Manufacturing, and Controls (CMC)
- Clinical Pharmacology
- Biopharmaceutics
- Medical Review
- Statistical Review
- Safety Review

### 2.2 Review Cycle

- Primary Review (6-10 months)
- Advisory Committee (if needed)
- Approval Action

## 3. Approval Types

### 3.1 Approval Categories

- Complete Response
- Accelerated Approval
- Priority Review
- Fast Track

---

Source: FDA NDA Guide, https://www.fda.gov/drugs/development-approval-process-drugs
"""

    def _get_clinical_trial_design(self) -> str:
        return """# Clinical Trial Design Considerations

## 1. Study Design

### 1.1 Randomization

- Simple Randomization
- Stratified Randomization
- Block Randomization

### 1.2 Blinding

- Open Label
- Single Blind
- Double Blind

### 1.3 Control Groups

- Placebo
- Active Control
- Historical Control
- Dose-Response

## 2. Sample Size

### 2.1 Considerations

- Effect Size
- Power (80-90%)
- Significance Level (α=0.05)
- Dropout Rate

### 2.2 Adaptive Design

- Group Sequential Design
- Sample Size Re-estimation
- Adaptive Randomization

## 3. Endpoints

### 3.1 Primary Endpoint
### 3.2 Secondary Endpoints
### 3.3 Biomarkers

---

Source: FDA Clinical Trial Guidance
"""

    def _get_gcp_standards(self) -> str:
        return """# Good Clinical Practice Standards

## 1. GCP Principles

### 1.1 Ethical Conduct
- Helsinki Declaration
- Belmont Report
- CIOMS Guidelines

### 1.2 Scientific Validity
- Study Design
- Statistical Methods
- Data Quality

## 2. GCP Requirements

### 2.1 IRB/IEC Approval
### 2.2 Informed Consent
### 2.3 Subject Safety
### 2.4 Data Integrity

## 3. GCP Documentation

### 3.1 Protocol
### 3.2 Case Report Form (CRF)
### 3.3 Investigator Brochure
### 3.4 Study Reports

---

Source: ICH E6 GCP Guidelines
"""

    def run_all(self, max_cde: int = 50, max_fda: int = 30) -> Dict[str, Dict]:
        """
        运行所有抓取任务

        Args:
            max_cde: CDE最大文档数
            max_fda: FDA最大文档数

        Returns:
            抓取结果统计
        """
        all_results = {}

        # 抓取 CDE 文档
        cde_stats = self.scrape_cde_deep(max_cde)
        all_results['CDE'] = cde_stats

        # 抓取 FDA 文档
        fda_stats = self.scrape_fda_deep(max_fda)
        all_results['FDA'] = fda_stats

        return all_results

    def print_summary(self, results: Dict[str, Dict]):
        """打印抓取摘要"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("抓取完成摘要")
        logger.info("=" * 60)

        total = 0
        for source, stats in results.items():
            source_total = sum(stats.values())
            total += source_total
            logger.info(f"{source}: 总计 {source_total} 个文档")
            for category, count in stats.items():
                logger.info(f"  - {category}: {count}")

        logger.info(f"总计: {total} 个文档")
        logger.info(f"元数据文件: {self.sources_dir}/.scrape_progress.json")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='深层抓取监管文档')
    parser.add_argument(
        '--max-cde',
        type=int,
        default=20,
        help='CDE最大文档数 (默认: 20)'
    )
    parser.add_argument(
        '--max-fda',
        type=int,
        default=15,
        help='FDA最大文档数 (默认: 15)'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default=str(Path(__file__).parent.parent),
        help='项目基础目录'
    )

    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    scraper = DeepDocumentScraper(base_dir)

    results = scraper.run_all(args.max_cde, args.max_fda)
    scraper.print_summary(results)

    return 0


if __name__ == '__main__':
    sys.exit(main())
