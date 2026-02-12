# NMPA Spider 状态报告

## 测试时间
2026-02-12

## 网站分析

### 反爬虫保护

NMPA官网（www.nmpa.gov.cn）使用了**阿里云 Anti-Bot** 反爬虫保护系统，特征：

- **HTTP 412 响应**: Precondition Failed
- **Cookie 验证**: 设置 `acw_tc` 和 `NfBCSins2OywS` cookies
- **JavaScript 挑战**: 需要执行JavaScript才能获取真实内容
- **TLS 指纹验证**: 检测请求的TLS特征

### 测试结果

| 方法 | 结果 | 说明 |
|------|------|------|
| curl (无UA) | HTTP 412 | 被拦截 |
| curl (带UA) | HTTP 412 | 被拦截 |
| curl (带Cookie) | HTTP 412 | 仍被拦截 |
| Scrapy | HTTP 412 | 被拦截 |
| Playwright (headless) | HTTP 412 | 被拦截 |

## 技术分析

阿里云 Anti-Bot 保护的检测维度：

1. **User-Agent 检测**: 检查常见的爬虫UA
2. **Cookie 验证**: 需要完成Cookie握手
3. **JavaScript 执行**: 必须执行JS才能生成有效Cookie
4. **TLS 指纹**: 检测是否为真实浏览器
5. **请求头一致性**: 检查各请求头的合理性

## 解决方案

### 方案1: 使用成熟的商业爬虫服务

推荐服务:
- **Scrapy Cloud**: https://www.zyte.com/scrapy-cloud
- **ScraperAPI**: https://www.scraperapi.com/
- **ZenRows**: https://www.zenrows.com/

优点:
- 无需处理反爬虫逻辑
- 稳定可靠
- 支持JavaScript渲染

### 方案2: 使用浏览器自动化（需进一步测试）

当前 Playwright 测试失败，可能需要：
```python
# 使用非 headless 模式
browser = await p.chromium.launch(
    headless=False,  # 显示浏览器窗口
    args=[
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
    ]
)
```

### 方案3: 寻找替代数据源

NMPA 数据可能可以从其他渠道获取：

| 来源 | 说明 |
|------|------|
| 国家药监局数据开放平台 | https://data.nmpa.gov.cn/ |
| 政府数据开放平台 | https://www.data.gov.cn/ |
| 第三方医药数据库 | 需要调研 |

## 建议

1. **短期方案**: 使用商业爬虫服务快速获取数据
2. **中期方案**: 研究使用非 headless Playwright 或 Selenium
3. **长期方案**: 与NMPA沟通获取官方API或数据授权

## 已创建的爬虫代码

虽然当前无法直接爬取NMPA官网，但爬虫代码已完成，可用于：

- 其他反爬虫保护较弱的网站
- 内网环境（无外网保护）
- 获得授权后访问NMPA

## 项目文件

- `processors/nmpa/spiders/nmpa_list_spider.py` - Scrapy版本
- `processors/nmpa/spiders/nmpa_playwright_spider.py` - Playwright版本
- `scripts/run_spider_standalone.py` - 独立运行器
- `docs/nmpa-spider-quickstart.md` - 使用指南
