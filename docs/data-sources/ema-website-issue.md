# EMA网站问题诊断报告

## 测试时间
2026-02-12 10:45

## 问题分析

### EMA网站访问限制

| 测试URL | 状态码 | 说明 |
|---------|--------|------|
| 主页面 overview/guidelines | 404 | 无法访问 |
| 分类页面 guidelines | 404 | 无法访问 |
| 具体指南页面 | 未测试 | 可能受限制 |
| 搜索功能 | 未测试 | 可能受限制 |

### 可能原因

1. **IP限制**: EMA可能检测到自动化访问并限制
2. **Cookies要求**: 可能需要有效的会话Cookie
3. **User-Agent检测**: 不接受标准的Python/User-Agent
4. **TLS指纹**: 检测请求的TLS特征
5. **地区限制**: 只允许欧盟地区访问

### 当前EMA采集器问题

| 问题 | 状态 |
|------|------|
| URL配置 | 使用 `/en/search` API | ❌ 返回404 |
| 抓取逻辑 | 使用BeautifulSoup解析HTML | ❌ 页面可能动态加载 |
| 数据提取 | 未获取到实际指南文档 | ❌ 返回0文档 |

### 建议解决方案

#### 方案1：使用非Headless浏览器模式
```python
# 修改采集器使用非headless模式
browser = await p.chromium.launch(headless=False)
```

#### 方案2：添加请求Header模拟真实浏览器
```python
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.ema.europa.eu/',
}
```

#### 方案3：寻找替代数据源
- FDA官方数据库（已可用）
- 其他公开数据集
- 药典API集成

## 结论

EMA网站有**严格的反爬虫保护**，直接HTTP请求无法获取数据。需要使用更高级的浏览器自动化方案或考虑替代数据源。

### 推荐数据源（按优先级）

1. **FDA Guidance Database** ✅（已验证可用）
2. **ClinicalTrials.gov** ✅
3. **其他公开医学数据库**
