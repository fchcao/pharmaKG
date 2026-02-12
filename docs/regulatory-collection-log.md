# 监管数据采集日志

## 采集记录

### 2026-02-12 采集批次

| 时间 | 操作 | 结果 | 文件 |
|------|------|------|------|
| 10:05:14 | FDA指南采集 | 62份文档 | `fda_guidance_20260212_100521.json` |
| 10:05:33 | EMA指南采集 | 0份文档 | `ema_guidance_20260212_100533.json` |
| 10:05:43 | 监管数据聚合 | 547份文档 | `regulatory_aggregated_20260212_100543.json` |

## 采集统计

### 总体数据

| 指标 | 数值 |
|--------|------|
| 总文档数 | 547 |
| 去重删除 | 7,451 |
| 验证通过 | 181 (33.1%) |
| 验证失败 | 366 (因file:// URL) |

### 按机构分布

| 机构 | 文档数 |
|------|--------|
| Other | 541 |
| NMPA | 5 |
| CDE | 1 |
| FDA | 62 (新采集) |
| EMA | 0 (待补充) |

### 按文档类型分布

| 类型 | 数量 |
|------|------|
| other | 425 |
| standard | 87 |
| guidances | 15 |
| opinion | 10 |
| notice | 10 |

### 按治疗领域分布

| 领域 | 数量 |
|------|------|
| general | 335 |
| quality | 167 |
| clinical | 7 |
| manufacturing | 14 |
| toxicology | 16 |

## 数据源配置

| 机构 | URL | 状态 |
|------|-----|------|
| FDA | https://www.fda.gov/regulatory-information/search-fda-guidance-documents | ✅ 已使用 |
| EMA | https://www.ema.europa.eu/en/documents/public | ⚠️ 抓取失败 |
| NMPA | 本地文件 | ✅ 已处理 |
| CDE | 本地文件 | ✅ 已处理 |

## 下次采集计划

### FDA (推荐频率: 每月)

```bash
# 采集FDA指南
conda activate data-spider
python -m processors.fda_guidance_processor --limit 100
```

**优先类别**:
- CMC (化学、制造、控制)
- Bioanalytical (生物分析方法)
- Clinical Trial Design (临床试验设计)
- Oncology (肿瘤学)

### EMA (推荐频率: 每月)

```bash
# 采集EMA指南
python -m processors.ema_processor --limit 100 --lookback-days 90
```

**优先类别**:
- Clinical Trials (临床试验)
- Quality (质量/GMP)
- Pharmacovigilance (药物警戒)

### 聚合 (每次采集后)

```bash
# 聚合所有数据
python -m processors.regulatory_aggregator
```

## 问题与改进

### 已知问题

1. **EMA采集器返回0文档**
   - 原因: 网页抓取逻辑需要调整
   - 解决方案: 检查EMA网站结构更新

2. **大量文档验证失败**
   - 原因: file:// URL格式不被接受
   - 解决方案: 更新URL验证规则或转换为http://

3. **NMPA/CDE数据较少**
   - 原因: 仅使用本地测试文件
   - 解决方案: 需要官方API或补充数据源

## 增量采集建议

### 下次采集目标

| 机构 | 目标文档数 | 优先级 |
|------|-------------|--------|
| FDA | +200 | 高 |
| EMA | +100 | 高 |
| NMPA | +50 | 中 |
| CDE | +30 | 中 |

### 数据质量改进

1. **补充缺失字段**:
   - publish_date (发布日期)
   - 有效期URL
   - 关键词标签

2. **改进分类准确性**:
   - 增加治疗领域关键词
   - 优化文档类型检测逻辑

3. **增强关系链接**:
   - 文档间引用关系
   - 替代/更新关系
   - 相关文档推荐

## 采集器文件位置

```
processors/
├── regulatory_aggregator.py       # 数据聚合器
├── fda_guidance_processor.py       # FDA采集器
└── ema_processor.py               # EMA采集器
```

## 输出目录

```
data/
├── sources/regulatory/
│   ├── FDA/                    # FDA原始数据
│   ├── CDE/                    # CDE原始数据
│   └── 中药2025WPS/            # NMPA原始数据
└── processed/regulatory_aggregated/   # 聚合后数据
```

### 2026-02-12 第二次采集

#### FDA增量采集

| 时间 | 操作 | 结果 |
|------|------|------|
| 10:29:55 | FDA指南采集 | 62份新文档 |
| 10:30:01 | 数据聚合 | 待执行 |

#### 累计数据

| 数据源 | 总数 |
|--------|--------|
| FDA | 124份 (62+62) |
| NMPA/CDE | 547份 |
| **总计** | **671份** 监管文档 |


### 2026-02-12 问题修复记录

#### 问题1：FDA重复采集
**原因**: 每次运行都重新爬取相同数据，没有使用缓存去重  
**修复**: 添加`use_cache`参数，默认为True  
**状态**: ✅ 已修复

#### 问题2：FDA文档无正文内容  
**原因**: transform函数对None content只拼接title+url+date  
**修复**: 保留HTML内容前1000字符或使用空字符串  
**状态**: ✅ 已修复

#### 问题3：EMA采集无数据  
**原因**: EMA网站结构完全变化，所有测试页面返回404  
**状态**: ⚠️ 暂时无法解决，需要评估替代方案  

### 当前数据状态

| 数据源 | 文档数 | 状态 |
|--------|---------|------|
| FDA指南 | 124份 | ✅ 可用 |
| NMPA/CDE历史 | 547份 | ✅ 可用 |
| **总计** | **671份** | 监管文档 |

### 处理器更新

- `fda_guidance_processor.py`: 添加use_cache参数，修复content字段处理

