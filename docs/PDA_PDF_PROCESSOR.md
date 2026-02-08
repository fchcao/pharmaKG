# PDA Technical Reports PDF Processor / PDA技术报告PDF处理器

## 版本 / Version

v1.0 (2026-02-08)

## 概述 / Overview

PDA PDF处理器是PharmaKG项目的一部分，专门用于处理PDA (Parenteral Drug Association) 发布的技术报告PDF文档。该处理器从制药制造领域的专业技术文档中提取实体和关系，构建知识图谱。

The PDA PDF Processor is part of the PharmaKG project, specifically designed to process technical report PDF documents published by PDA (Parenteral Drug Association). It extracts entities and relationships from professional pharmaceutical manufacturing documents to build a knowledge graph.

## 目录 / Table of Contents

1. [功能特性](#功能特性)
2. [系统架构](#系统架构)
3. [安装配置](#安装配置)
4. [使用方法](#使用方法)
5. [数据模型](#数据模型)
6. [输出格式](#输出格式)
7. [API参考](#api参考)
8. [最佳实践](#最佳实践)
9. [故障排除](#故障排除)
10. [更新日志](#更新日志)

---

## 功能特性 / Features

### 核心功能 / Core Features

- **PDF内容提取**：使用pdfplumber或PyPDF2提取文本和表格
- **OCR支持**：可选的OCR功能处理扫描PDF（使用pytesseract）
- **智能解析**：自动识别PDA报告编号、标题、版本等信息
- **实体提取**：提取5类实体（设施、制造商、标准、检测、工艺）
- **关系提取**：识别实体间的6种关系类型
- **批量处理**：支持批量处理大量PDF文件
- **缓存机制**：文件级缓存避免重复处理
- **进度跟踪**：详细的处理统计和错误报告

### 支持的实体类型 / Supported Entity Types

1. **sc:Facility** - 设施实体
   - 洁净室 (Clean Room)
   - 生产区 (Manufacturing Area)
   - 包装区 (Packaging Area)
   - 更衣室 (Changing Room)
   - 仓储区 (Storage Area)
   - 无菌区 (Aseptic Area)

2. **sc:Manufacturer** - 设备制造商实体
   - 设备名称和类型
   - 制造商信息
   - 设备规格
   - 验证要求

3. **sc:QualityStandard** - 质量标准实体
   - ISO标准 (如ISO 14644)
   - EU GMP指南 (如Annex 1)
   - USP章节
   - FDA指南

4. **rd:Assay** - 检测方法实体
   - 微生物检测
   - 无菌检查
   - 内毒素检测
   - 粒子计数
   - 生物负荷

5. **sc:Process** - 工艺实体
   - 湿热灭菌
   - 干热灭菌
   - 辐照灭菌
   - 过滤工艺
   - 灌装工艺
   - 培养基模拟

### 支持的关系类型 / Supported Relationship Types

1. **rel:REQUIRES_STANDARD** - 设施需要符合的标准
2. **rel:TEST_QUALITY** - 检测方法用于设施质量控制
3. **rel:EQUIPPED_WITH** - 设施配备的设备制造商
4. **rel:VALIDATED_BY** - 工艺通过检测方法验证
5. **rel:MANUFACTURES** - 制造商生产的产品（待实现）
6. **rel:SUBJECT_TO_INSPECTION** - 制造商接受检查（待实现）

---

## 系统架构 / Architecture

### 处理流程 / Processing Flow

```
输入PDF文件
    ↓
[扫描阶段] → 识别PDF文件，过滤已处理文件
    ↓
[提取阶段] → 提取文本、表格、元数据
    ↓
[解析阶段] → 实体识别、关系提取
    ↓
[转换阶段] → 标准化数据格式
    ↓
[验证阶段] → 数据质量检查
    ↓
[保存阶段] → 分类保存实体和关系
```

### 组件架构 / Component Architecture

```
PDAPDFProcessor
    ├── BaseProcessor (继承)
    │   ├── 扫描 (scan)
    │   ├── 提取 (extract)
    │   ├── 转换 (transform)
    │   └── 验证 (validate)
    │
    ├── PDF内容提取器
    │   ├── pdfplumber (优先)
    │   ├── PyPDF2 (备用)
    │   └── OCR (扫描PDF)
    │
    ├── 实体提取器
    │   ├── 设施提取器 (_extract_facility_entities)
    │   ├── 制造商提取器 (_extract_manufacturer_entities)
    │   ├── 标准提取器 (_extract_standard_entities)
    │   ├── 检测提取器 (_extract_assay_entities)
    │   └── 工艺提取器 (_extract_process_entities)
    │
    ├── 关系提取器
    │   └── 关系匹配器 (_extract_relationships)
    │
    └── 辅助工具
        ├── 正则表达式模式库
        ├── 元数据解析器
        └── 环境参数提取器
```

---

## 安装配置 / Installation & Configuration

### 系统要求 / System Requirements

- Python 3.8+
- 内存: 至少4GB（处理大型PDF时需要更多）
- 磁盘: 每个PDF约100-500MB临时空间

### 依赖安装 / Dependencies Installation

```bash
# 基础依赖（必需）
pip install pdfplumber PyPDF2

# OCR支持（可选）
pip install pytesseract pillow
# 需要安装tesseract-ocr:
# Ubuntu/Debian: apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装

# 测试依赖
pip install pytest pytest-cov
```

### 配置选项 / Configuration Options

```python
config = {
    'use_ocr': False,              # 是否启用OCR
    'ocr_language': 'eng',          # OCR语言（eng/chi_sim等）
    'batch_size': 10,               # 批处理大小
    'min_confidence': 0.6,          # 最小置信度阈值
    'cache_enabled': True,          # 是否启用缓存
    'parallel_workers': 1,          # 并行工作进程数
}

processor = PDAPDFProcessor(config)
```

---

## 使用方法 / Usage

### 基本用法 / Basic Usage

#### 1. 命令行模式 / Command Line

```bash
# 处理单个PDF
python -m processors.pda_pdf_processor /path/to/file.pdf

# 处理整个目录
python -m processors.pda_pdf_processor /path/to/pda/tr/directory

# 限制处理数量（测试用）
python -m processors.pda_pdf_processor /path/to/dir -l 10

# 只处理特定TR编号
python -m processors.pda_pdf_processor /path/to/dir --tr TR13

# 启用OCR处理扫描PDF
python -m processors.pda_pdf_processor /path/to/dir --use-ocr

# 禁用缓存
python -m processors.pda_pdf_processor /path/to/dir --no-cache

# 详细输出
python -m processors.pda_pdf_processor /path/to/dir -v
```

#### 2. Python脚本模式 / Python Script

```python
from pathlib import Path
from processors.pda_pdf_processor import PDAPDFProcessor

# 创建处理器
processor = PDAPDFProcessor({
    'cache_enabled': True,
    'batch_size': 20
})

# 处理单个文件
file_path = Path('/path/to/PDA TR13.pdf')
result = processor.extract(file_path)

# 查看结果
print(f"提取实体数: {len(result['entities'])}")
print(f"提取关系数: {len(result['relationships'])}")

# 批量处理
files = list(Path('/path/to/dir').glob('PDA*.pdf'))
output_dir = Path('/output/directory')
batch_result = processor.process_batch(files, output_dir)
```

#### 3. 使用测试脚本 / Using Test Script

```bash
# 运行完整测试套件
python scripts/test_pda_pdf_processor.py

# 快速测试单个文件
python scripts/test_pda_pdf_processor.py --quick

# 快速测试指定文件
python scripts/test_pda_pdf_processor.py --quick --file /path/to/file.pdf

# 详细输出
python scripts/test_pda_pdf_processor.py --verbose
```

### 高级用法 / Advanced Usage

#### 自定义实体提取 / Custom Entity Extraction

```python
class CustomPDAProcessor(PDAPDFProcessor):
    def _extract_facility_entities(self, text, tables, metadata):
        # 调用父类方法
        facilities = super()._extract_facility_entities(text, tables, metadata)

        # 添加自定义逻辑
        # 例如: 识别特定类型的设施

        return facilities
```

#### 过滤和筛选 / Filtering

```python
# 只处理特定类别的PDA报告
categories = ['sterilization', 'environmental_monitoring']
files = [f for f in processor.scan(source_dir)
         if any(cat in f.name for cat in categories)]

# 按文件大小筛选
max_size_mb = 50
files = [f for f in files
         if f.stat().st_size / (1024*1024) <= max_size_mb]
```

---

## 数据模型 / Data Models

### 实体数据模型 / Entity Data Models

#### Facility Entity / 设施实体

```json
{
  "entity_type": "sc:Facility",
  "name": "clean room (TR13)",
  "facility_type": "clean room",
  "classification": "ISO Class 5",
  "environmental_requirements": {
    "temperature_c": "20",
    "humidity_percent": "45",
    "microbial_limit_cfu": "1",
    "air_changes_per_hour": "20",
    "pressure_differential_pa": "15"
  },
  "design_criteria": {},
  "intended_use": "aseptic_processing",
  "data_source": "PDA_TR13",
  "source_file": "TR13",
  "confidence": 0.75
}
```

#### QualityStandard Entity / 质量标准实体

```json
{
  "entity_type": "sc:QualityStandard",
  "standard_name": "ISO 14644-1",
  "standard_type": "international",
  "requirements": [
    "Particle concentration limits shall be as specified",
    "Monitoring frequency shall be determined by risk assessment"
  ],
  "acceptance_criteria": [
    "Not more than 100 particles/m³ for ≥0.5µm",
    "Not more than 1 CFU for ≥5µm settle plate"
  ],
  "monitoring_parameters": [
    "temperature",
    "humidity",
    "pressure",
    "particle"
  ],
  "data_source": "PDA_TR13",
  "source_file": "TR13",
  "confidence": 0.95
}
```

#### Assay Entity / 检测方法实体

```json
{
  "entity_type": "rd:Assay",
  "assay_name": "Microbiological Test",
  "assay_type": "microbiological examination",
  "test_method": "Membrane filtration method...",
  "sampling_plan": "per_batch",
  "acceptance_criteria": [
    "Not more than 10 CFU/100ml"
  ],
  "limits": {},
  "frequency": "per_batch",
  "data_source": "PDA_TR13",
  "source_file": "TR13",
  "confidence": 0.80
}
```

### 关系数据模型 / Relationship Data Models

```json
{
  "from": "clean room (TR13)",
  "to": "ISO 14644-1",
  "relationship_type": "rel:REQUIRES_STANDARD",
  "properties": {
    "requirement_level": "mandatory",
    "data_source": "PDA_TR13"
  },
  "source": "pda_pdf_extraction",
  "confidence": 0.75
}
```

---

## 输出格式 / Output Format

### 文件结构 / File Structure

处理完成后，在输出目录生成以下文件：

```
output_directory/
├── pda_facilities_20260208_120000.json      # 设施实体
├── pda_manufacturers_20260208_120000.json   # 制造商实体
├── pda_standards_20260208_120000.json       # 质量标准实体
├── pda_assays_20260208_120000.json          # 检测方法实体
├── pda_processes_20260208_120000.json       # 工艺实体
├── pda_relationships_20260208_120000.json   # 所有关系
└── pda_summary_20260208_120000.json         # 处理摘要
```

### 摘要文件格式 / Summary File Format

```json
{
  "processor": "PDAPDFProcessor",
  "timestamp": "20260208_120000",
  "statistics": {
    "total_files": 108,
    "processed_files": 105,
    "failed_files": 3,
    "facilities_extracted": 342,
    "manufacturers_extracted": 87,
    "standards_extracted": 156,
    "assays_extracted": 423,
    "processes_extracted": 198,
    "total_entities": 1206,
    "total_relationships": 856
  },
  "processed_files": [
    "/path/to/PDA TR1.pdf",
    "/path/to/PDA TR13.pdf",
    ...
  ],
  "failed_files": [
    "/path/to/corrupted.pdf",
    ...
  ],
  "processing_time_seconds": 2345.67
}
```

---

## API参考 / API Reference

### 类: PDAPDFProcessor

#### 构造函数 / Constructor

```python
PDAPDFProcessor(config: Optional[Dict[str, Any]] = None)
```

**参数 / Parameters:**
- `config` (dict, optional): 配置字典
  - `use_ocr` (bool): 是否启用OCR，默认False
  - `ocr_language` (str): OCR语言，默认'eng'
  - `batch_size` (int): 批处理大小，默认10
  - `min_confidence` (float): 最小置信度，默认0.6
  - `cache_enabled` (bool): 是否启用缓存，默认True
  - `parallel_workers` (int): 并行工作进程数，默认1

#### 主要方法 / Main Methods

##### scan()

```python
scan(source_path: Union[str, Path]) -> List[Path]
```

扫描源目录，查找待处理的PDF文件。

**参数 / Parameters:**
- `source_path`: 源目录或文件路径

**返回 / Returns:**
- `List[Path]`: PDF文件路径列表

##### extract()

```python
extract(file_path: Path) -> Dict[str, Any]
```

从单个PDF文件提取数据。

**参数 / Parameters:**
- `file_path`: PDF文件路径

**返回 / Returns:**
- `dict`: 包含entities、relationships、metadata的字典

##### process_batch()

```python
process_batch(
    file_paths: List[Path],
    output_dir: Optional[Path] = None
) -> ProcessingResult
```

批量处理PDF文件。

**参数 / Parameters:**
- `file_paths`: PDF文件路径列表
- `output_dir`: 输出目录路径

**返回 / Returns:**
- `ProcessingResult`: 处理结果对象

#### 辅助方法 / Helper Methods

##### _extract_cleanroom_classification()

```python
_extract_cleanroom_classification(text: str) -> str
```

从文本中提取洁净室分级。

##### _extract_environmental_requirements()

```python
_extract_environmental_requirements(text: str) -> Dict[str, Any]
```

提取环境要求（温度、湿度、压差等）。

##### _extract_frequency()

```python
_extract_frequency(sentence: str) -> str
```

提取检测频率。

---

## 最佳实践 / Best Practices

### 1. 处理大量文件 / Processing Large Numbers of Files

```python
# 分批处理，避免内存溢出
files = processor.scan(source_dir)
batch_size = 20

for i in range(0, len(files), batch_size):
    batch = files[i:i+batch_size]
    result = processor.process_batch(batch, output_dir)
    logger.info(f"处理进度: {min(i+batch_size, len(files))}/{len(files)}")
```

### 2. 错误处理 / Error Handling

```python
# 记录并跳过损坏的文件
for file_path in files:
    try:
        result = processor.extract(file_path)
        if not result or not result.get('entities'):
            logger.warning(f"文件无有效数据: {file_path.name}")
            continue
    except Exception as e:
        logger.error(f"处理失败 {file_path}: {e}")
        # 将失败文件移到错误目录
        file_path.rename(error_dir / file_path.name)
```

### 3. 质量控制 / Quality Control

```python
# 验证提取质量
def validate_extraction_quality(result):
    entity_count = len(result.get('entities', []))
    relationship_count = len(result.get('relationships', []))

    # 基本数量检查
    if entity_count < 5:
        logger.warning(f"实体数量偏少: {entity_count}")

    # 置信度检查
    low_confidence = [e for e in result.get('entities', [])
                     if e.get('confidence', 1.0) < 0.7]
    if len(low_confidence) > entity_count * 0.3:
        logger.warning(f"低置信度实体比例过高: {len(low_confidence)}/{entity_count}")
```

### 4. 性能优化 / Performance Optimization

```python
# 使用SSD存储临时文件
# 增加并行处理（如果内存足够）
config = {
    'parallel_workers': 4,
    'cache_enabled': True
}

# 对于超大文件，分页处理
# （需要修改处理器以支持分页处理）
```

---

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. PDF提取无文本内容

**问题**: PDF提取返回空文本

**原因**:
- PDF是扫描版
- PDF使用图像格式
- PDF有密码保护

**解决方案**:
```python
# 启用OCR
config = {'use_ocr': True, 'ocr_language': 'eng'}
processor = PDAPDFProcessor(config)
```

#### 2. 内存不足

**问题**: 处理大型PDF时内存溢出

**解决方案**:
```python
# 减小批处理大小
config = {'batch_size': 5}
# 或分批处理文件
```

#### 3. 处理速度慢

**问题**: 处理时间过长

**解决方案**:
- 启用缓存避免重复处理
- 增加并行工作进程
- 限制OCR使用（仅对必要文件）
- 使用SSD存储

#### 4. 实体识别准确率低

**问题**: 提取的实体不准确或不完整

**解决方案**:
- 调整min_confidence阈值
- 添加自定义正则表达式模式
- 对特定TR编号添加专门规则

---

## 支持的PDA技术报告 / Supported PDA Technical Reports

### 按类别分类 / By Category

#### 灭菌 / Sterilization (灭菌)
- TR1: Moist Heat Sterilization
- TR11: Gamma Radiation Sterilization
- TR16: Effects of Gamma Irradiation
- TR26: Liquid Chemical Sterilants
- TR30: EtO Sterilization
- TR51: Dry Heat Sterilization
- TR69: Radiation Sterilization
- TR78: Steam Sterilization
- TR87: EtO Residuals

#### 环境监测 / Environmental Monitoring (环境监测)
- TR13: Environmental Monitoring Program

#### 工艺验证 / Process Validation (工艺验证)
- TR22: Process Simulation (Media Fills)
- TR34: Aseptic Processing

#### 过滤 / Filtration (过滤)
- TR15: Tangential Flow Filtration
- TR26: Sterilizing Filtration
- TR44: Liquid Filter Integrity Testing

#### 检测 / Inspection (检测)
- TR29: Visual Inspection
- TR98: Visual Inspection of Injectables

#### 清洁 / Cleaning (清洁)
- TR54: Cleaning and Sanitization
- TR70: Cleaning and Sanitization

---

## 更新日志 / Changelog

### v1.0 (2026-02-08)

**新增功能 / New Features:**
- 初始版本发布
- 支持pdfplumber和PyPDF2
- 5类实体提取
- 6种关系类型
- 批量处理支持
- 缓存机制
- OCR支持（可选）
- 命令行接口
- 测试套件

**已知限制 / Known Limitations:**
- 表格解析需要针对特定格式优化
- OCR准确率取决于扫描质量
- 某些复杂布局可能导致识别错误
- 中英文混合文档处理有待改进

**计划改进 / Planned Improvements:**
- 支持更多PDF布局格式
- 改进表格提取准确率
- 添加更多实体类型
- 支持图表和图像内容提取
- 改进中英文混合处理
- 添加机器学习模型辅助识别

---

## 许可证 / License

本处理器是PharmaKG项目的一部分，遵循项目许可证。

---

## 联系方式 / Contact

如有问题或建议，请通过以下方式联系：

- 项目仓库: [PharmaKG GitHub](https://github.com/your-org/pharmakg)
- 问题反馈: [GitHub Issues](https://github.com/your-org/pharmakg/issues)

---

## 附录 / Appendix

### A. 正则表达式模式参考

#### 洁净室分级模式
```python
r'\bISO\s*Class\s*(\d+)\b'
r'\bEU\s*GMP\s*(Grade\s*([A-D]))\b'
r'\bClass\s*(\d{3,6})\b'
```

#### 质量标准模式
```python
r'\bISO\s*(\d+(?:-\d+)?)\b'
r'\bEU\s*GMP\s*(?:Annex\s+(\d+|[A-Z]))?\b'
r'\b(?:USP|<(\d+(?:-\d+)?)>)\b'
```

### B. 环境参数单位参考

| 参数 | 常用单位 | 说明 |
|------|----------|------|
| 温度 | °C, °F, K | 摄氏度、华氏度、开尔文 |
| 湿度 | %RH | 相对湿度 |
| 压力 | Pa, bar, psi | 帕斯卡、巴、磅每平方英寸 |
| 菌落 | CFU/m³, CFU/plate | 菌落形成单位 |
| 换气 | ACH, /h | 每小时换气次数 |
| 粒径 | µm, micron | 微米 |
| 粒子数 | particles/m³ | 每立方米粒子数 |

### C. PDA报告编号速查表

| TR编号 | 标题 | 类别 |
|--------|------|------|
| TR1 | Moist Heat Sterilization | 灭菌 |
| TR13 | Environmental Monitoring | 环境监测 |
| TR22 | Process Simulation | 工艺验证 |
| TR26 | Liquid Chemical Sterilants | 灭菌 |
| TR29 | Visual Inspection | 检测 |
| TR30 | EtO Sterilization | 灭菌 |
| TR34 | Aseptic Processing | 工艺验证 |
| TR41 | Risk Assessment | 风险评估 |
| TR49 | Biotechnology | 生物技术 |
| TR54 | Cleaning and Sanitization | 清洁 |
| TR70 | Cleaning and Sanitization | 清洁 |
| TR78 | Steam Sterilization | 灭菌 |

---

**文档版本**: v1.0
**最后更新**: 2026-02-08
**维护者**: PharmaKG Development Team
