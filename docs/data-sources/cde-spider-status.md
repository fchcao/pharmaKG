# CDE Spider 状态报告

## 测试时间
2026-02-12

## 网站分析

### CDE (药品审评中心) 反爬虫保护

目标网站：
- https://www.cde.org.cn/zdyz/index - 指导原则
- https://www.cde.org.cn/main/policy/listpage/* - 政策文件

### 反爬虫特征

1. **HTTP 202 响应**: 页面持续导航，无法获取内容
2. **JavaScript 挑战**: 需要执行JS才能生成有效内容
3. **浏览器指纹检测**: 检测自动化工具特征
4. **持续重定向**: 页面不断导航，无法稳定获取内容

### 测试结果

| 方法 | 结果 | 说明 |
|------|------|------|
| curl | N/A | 无法测试JS重定向 |
| Playwright (headless) | HTTP 202 + 持续导航 | 被拦截 |
| Playwright (带指纹) | HTTP 202 + 持续导航 | 仍被拦截 |

### 测试代码

```python
# 即使使用真实浏览器指纹，仍然失败
response = await page.goto('https://www.cde.org.cn/zdyz/index')
# Status: 202
# Content: "页面持续导航中..."
```

## 替代方案

### 方案1: 使用商业医药数据API (推荐)

| 数据源 | URL | 覆盖内容 |
|--------|-----|----------|
| 药渡数据 | https://www.pharmacodia.com/ | CDE审评、指导原则 |
| 摩熵数科 | https://www.moresco.com.cn/ | 药品注册、临床试验 |
| 药智数据 | https://www.yaozh.com/ | 综合药品数据库 |
| DrugBank | https://go.drugbank.com/ | 国际药品数据 |
| Cortellis | https://www.cortellis.com/ | 综合医药情报 |

### 方案2: 使用政府数据开放平台

| 平台 | URL | 说明 |
|------|-----|------|
| 国家药监局数据开放平台 | https://data.nmpa.gov.cn/ | 可能提供API |
| 政府数据开放平台 | https://www.data.gov.cn/ | 综合数据源 |

### 方案3: 手动数据收集

对于小规模数据集（<1000条），可以：
1. 手动下载CDE网站的关键文档
2. 创建结构化录入工具
3. 使用人工辅助方式整理

### 方案4: 使用非Headless浏览器（需要VNC）

```python
browser = await p.chromium.launch(
    headless=False,  # 需要显示环境
    args=[
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
    ]
)
```

## 建议优先级

1. **短期**: 联系药渡数据/摩熵数科获取API访问
2. **中期**: 评估政府数据开放平台可用性
3. **长期**: 与CDE沟通获取官方API授权

## 已创建的爬虫代码

爬虫代码已完成，可用于：
- 其他反爬虫保护较弱的网站
- 内网环境
- 获得授权后访问CDE

## 项目文件

- `processors/cde_spider.py` - 基础版爬虫
- `processors/cde_advanced_spider.py` - 高级版爬虫（带真实指纹）
- `docs/data-collection-environment.md` - 环境配置文档
