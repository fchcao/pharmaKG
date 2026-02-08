# PDA PDF Processor - Quick Start Guide / 快速开始指南

## 快速开始 / Quick Start

### 1. 安装依赖 / Install Dependencies

```bash
pip install pdfplumber PyPDF2
```

### 2. 运行测试 / Run Tests

```bash
# 快速测试（单个文件）
python scripts/test_pda_pdf_processor.py --quick

# 完整测试套件
python scripts/test_pda_pdf_processor.py
```

### 3. 处理PDA TR文档 / Process PDA TR Documents

```bash
# 处理单个PDF
python -m processors.pda_pdf_processor "/root/autodl-tmp/pj-pharmaKG/data/sources/documents/PDA TR 全集/PDA TR13-Fundamentals of an Environmental Monitoring Program(Revised2014）.pdf"

# 处理整个目录（前10个文件测试）
python -m processors.pda_pdf_processor "/root/autodl-tmp/pj-pharmaKG/data/sources/documents/PDA TR 全集" -l 10

# 处理特定TR编号
python -m processors.pda_pdf_processor "/root/autodl-tmp/pj-pharmaKG/data/sources/documents/PDA TR 全集" --tr TR13
```

### 4. 查看输出 / View Output

输出文件保存在: `/root/autodl-tmp/pj-pharmaKG/data/processed/documents/pda_technical_reports/`

```bash
ls -lh /root/autodl-tmp/pj-pharmaKG/data/processed/documents/pda_technical_reports/*.json
```

### 5. Python API使用 / Python API Usage

```python
from pathlib import Path
from processors.pda_pdf_processor import PDAPDFProcessor

# 创建处理器
processor = PDAPDFProcessor()

# 处理单个文件
result = processor.extract(Path('/path/to/PDA TR13.pdf'))
print(f"提取实体: {len(result['entities'])}")
print(f"提取关系: {len(result['relationships'])}")

# 批量处理
files = processor.scan(Path('/path/to/PDA TR 全集'))
batch_result = processor.process_batch(files, Path('/output/dir'))
```

---

## 文件结构 / File Structure

```
pharmakg/
├── processors/
│   └── pda_pdf_processor.py          # 核心处理器 (1300+ lines)
├── scripts/
│   └── test_pda_pdf_processor.py     # 测试脚本
├── examples/
│   └── usage_pda_pdf_processor.py    # 使用示例
├── docs/
│   ├── PDA_PDF_PROCESSOR.md          # 完整文档
│   └── PDA_PDF_PROCESSOR_IMPLEMENTATION_SUMMARY.md  # 实现总结
└── data/
    ├── sources/documents/
    │   └── PDA TR 全集/              # PDA PDF源文件 (197 files)
    └── processed/documents/
        └── pda_technical_reports/    # 输出目录
            ├── pda_facilities_*.json
            ├── pda_manufacturers_*.json
            ├── pda_standards_*.json
            ├── pda_assays_*.json
            ├── pda_processes_*.json
            ├── pda_relationships_*.json
            └── pda_summary_*.json
```

---

## 提取的实体 / Extracted Entities

| 实体类型 | 描述 | 示例 |
|---------|------|------|
| sc:Facility | 设施 | 洁净室、生产区、包装区 |
| sc:Manufacturer | 设备制造商 | SP Scientific, Getinge |
| sc:QualityStandard | 质量标准 | ISO 14644, EU GMP Annex 1 |
| rd:Assay | 检测方法 | 微生物检测、无菌检查 |
| sc:Process | 工艺 | 湿热灭菌、过滤工艺 |

---

## 提取的关系 / Extracted Relationships

| 关系类型 | 描述 | 示例 |
|---------|------|------|
| rel:REQUIRES_STANDARD | 设施需要标准 | 洁净室 → ISO 14644 |
| rel:TEST_QUALITY | 检测方法 | 粒子计数 → 洁净室 |
| rel:EQUIPPED_WITH | 设备配备 | 洁净室 → 制造商 |
| rel:VALIDATED_BY | 工艺验证 | 灭菌 → 生物指示剂 |

---

## 测试结果示例 / Test Results Example

```
处理文件: PDA TR1 (158页)
处理时间: 21秒

提取结果:
  rd:Assay: 224个
  sc:Facility: 3个
  sc:Manufacturer: 25个
  sc:Process: 97个
  sc:QualityStandard: 13个
  总实体: 362个
  总关系: 9个
```

---

## 常见问题 / FAQ

### Q: 如何处理扫描版PDF？
A: 启用OCR功能：
```python
processor = PDAPDFProcessor({'use_ocr': True})
```

### Q: 如何限制处理文件数量？
A: 使用 `-l` 参数：
```bash
python -m processors.pda_pdf_processor /path/to/dir -l 10
```

### Q: 如何只处理特定TR编号？
A: 使用 `--tr` 参数：
```bash
python -m processors.pda_pdf_processor /path/to/dir --tr TR13
```

### Q: 处理速度慢怎么办？
A: 1) 启用缓存（默认开启）2) 减小批处理大小 3) 使用SSD存储

---

## 更多信息 / More Information

- 完整文档: `/root/autodl-tmp/pj-pharmaKG/docs/PDA_PDF_PROCESSOR.md`
- 实现总结: `/root/autodl-tmp/pj-pharmaKG/docs/PDA_PDF_PROCESSOR_IMPLEMENTATION_SUMMARY.md`
- 使用示例: `/root/autodl-tmp/pj-pharmaKG/examples/usage_pda_pdf_processor.py`

---

**版本**: 1.0 | **更新**: 2026-02-08
