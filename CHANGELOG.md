# PharmaKG 变更日志 / Change Log

本文档记录 PharmaKG 项目的所有重要变更。

## [未发布 / Unreleased]

### 2026-02-07

#### 文档 / Documentation
- **新增**: `CLAUDE.md` - 为 Claude Code 提供项目指导文档
  - 项目概述和开发命令
  - 架构概览和目录结构
  - 配置说明和代码约定
  - 重要说明和数据源

- **更新**: `api/README.md` - 添加预配置 conda 环境说明
  - AutoDL 服务器已预配置 `pharmakg-api` conda 环境
  - 添加依赖检查命令，避免不必要的重新安装

- **更新**: `deploy/QUICKSTART_AUTODL.md` - 更新 AutoDL 快速开始指南
  - Python 连接部分添加环境激活和依赖检查说明
  - 开发工作流部分添加环境激活步骤

- **更新**: `deploy/README_AUTODL.md` - 更新 AutoDL 部署指南
  - Python API 连接部分添加环境激活和依赖检查
  - 开发工作流部分添加环境激活说明
  - GPU 加速部分添加环境激活步骤

---

## 版本说明 / Versioning

本项目遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范。

版本号格式：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向下兼容的功能新增
- **PATCH**: 向下兼容的问题修复

### 版本历史 / Version History

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2025-02-06 | 初始版本，技术实施阶段 (Phase 1) |

---

## 变更类型 / Change Types

- **新增 (Added)**: 新功能
- **变更 (Changed)**: 现有功能的变更
- **弃用 (Deprecated)**: 即将移除的功能
- **移除 (Removed)**: 已移除的功能
- **修复 (Fixed)**: 问题修复
- **安全 (Security)**: 安全相关的修复或改进
- **文档 (Docs)**: 文档变更
- **测试 (Tests)**: 测试相关变更
- **重构 (Refactor)**: 代码重构
- **性能 (Performance)**: 性能优化
- **样式 (Style)**: 代码风格变更

---

## Commit 规范 / Commit Convention

本项目遵循以下 Commit Message 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: 问题修复
- `docs`: 文档变更
- `style`: 代码格式变更（不影响代码运行）
- `refactor`: 重构（既不是新增功能也不是修复问题）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `revert`: 回滚之前的 commit

### Scope 范围

- `api`: API 服务
- `etl`: ETL 系统
- `docs`: 文档
- `deploy`: 部署
- `graph`: 图分析
- `ml`: 机器学习
- `ontology`: 本体
- `config`: 配置

### Subject 标题

- 使用中文或英文
- 以动词开头，使用第一人称现在时
- 首字母小写
- 结尾不加句号

### Body 正文

- 使用中文或英文
- 说明 commit 的详细内容
- 应该说明代码变更的动机和对比

### Footer 脚注

- 关联 Issue: `Closes #123`, `Fixes #456`
- 关联 Pull Request: `PR #789`
- 协作作者: `Co-Authored-By: <name> <email>`

### 示例

```
feat(api): add compound similarity search endpoint

- 新增基于分子指纹的化合物相似度搜索
- 支持 Tanimoto 系数计算
- 添加分页和结果过滤功能

Closes #123
Co-Authored-By: Zhang San <zhangsan@example.com>
```

---

## 如何添加变更 / How to Add Changes

在发布新版本或进行重要变更时，请按以下格式添加变更记录：

```markdown
### [YYYY-MM-DD]

#### 类型 / Category
- **[Type]** `<scope>`: 简短描述
  - 详细说明（可选）
  - 关联 Issue: #123
```

---

## 相关文档 / Related Documentation

- [README.md](README.md) - 项目概述
- [CLAUDE.md](CLAUDE.md) - Claude Code 开发指导
- [docs/schema/制药行业知识图谱Schema设计文档.md](docs/schema/制药行业知识图谱Schema设计文档.md) - Schema 设计
- [docs/schema/实施路线图.md](docs/schema/实施路线图.md) - 实施路线图

---

**维护者**: PharmaKG Team
**最后更新**: 2026-02-07
