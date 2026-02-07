# PharmaKG Git 工作流指南

**文档版本**: v1.0
**创建日期**: 2026-02-07
**适用环境**: AutoDL 云服务

---

## 目录

1. [仓库配置](#一仓库配置)
2. [分支策略](#二分支策略)
3. [提交规范](#三提交规范)
4. [代码提交流程](#四代码提交流程)
5. [常用命令](#五常用命令)
6. [故障排除](#六故障排除)

---

## 一、仓库配置

### 1.1 仓库信息

```bash
远程仓库: https://github.com/fchcao/pharmaKG
默认分支: main
许可证: AGPL-3.0
```

### 1.2 本地配置

```bash
# Git 用户配置
git config user.name "PharmaKG Team"
git config user.email "pharmakg@example.com"

# 分支跟踪配置
git branch --set-upstream-to=origin/main main
```

### 1.3 网络加速（AutoDL 环境）

```bash
# 必须先启用网络加速
source /etc/network_turbo
```

> **重要**: AutoDL 环境下每次 push/pull 前都需要执行此命令！

---

## 二、分支策略

### 2.1 分支结构

```
main (默认分支)
  ├── 稳定的生产代码
  ├── 受保护，直接提交需审核
  └── Tags: v1.0, v1.1, ...
```

### 2.2 分支命名规范

| 分支类型 | 命名格式 | 示例 | 说明 |
|---------|---------|------|------|
| 主分支 | `main` | `main` | 生产代码，受保护 |
| 功能分支 | `feature/xxx` | `feature/rd-modeling` | 新功能开发 |
| 修复分支 | `fix/xxx` | `fix/api-timeout` | 问题修复 |
| 优化分支 | `refactor/xxx` | `refactor/etl-pipeline` | 代码重构 |
| 文档分支 | `docs/xxx` | `docs/api-guide` | 文档更新 |
| 发布分支 | `release/vx.x.x` | `release/v1.1` | 版本发布 |

### 2.3 分支工作流程

```
┌─────────┐     ┌──────────────┐     ┌─────────┐
│  main   │◄────│   PR/Merge   │◄────│ feature │
│ (保护)  │     │   (Code Review)  │  branch  │
└─────────┘     └──────────────┘     └─────────┘
     ▲                                    │
     │                                    ▼
  ───┴──────────────────────────────────────
              开发完成后合并
```

---

## 三、提交规范

### 3.1 Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 3.2 Type 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(api): add compound search endpoint` |
| `fix` | 问题修复 | `fix(etl): resolve ChEMBL API timeout` |
| `docs` | 文档变更 | `docs(readme): update installation guide` |
| `style` | 代码格式 | `style(api): fix indentation issues` |
| `refactor` | 重构 | `refactor(services): extract base class` |
| `perf` | 性能优化 | `perf(query): add caching for results` |
| `test` | 测试 | `test(api): add unit tests for models` |
| `chore` | 构建/工具 | `chore(deps): update neo4j driver` |

### 3.3 Scope 范围

| 范围 | 说明 |
|------|------|
| `api` | API 服务 |
| `etl` | ETL 系统 |
| `docs` | 文档 |
| `deploy` | 部署配置 |
| `graph` | 图分析 |
| `ml` | 机器学习 |
| `ontology` | 本体 |
| `config` | 配置 |

### 3.4 Subject 标题

- 使用中文或英文
- 以动词开头，使用第一人称现在时
- 首字母小写
- 结尾不加句号
- 限制在 50 个字符以内

**示例**:
```
✅ add compound search endpoint
✅ 修复 API 超时问题
✅ update installation guide
❌ Added compound search endpoint.
❌ 修复 API 超时问题。
```

### 3.5 Body 正文

详细说明 commit 的内容，解释 **what** 和 **why**，而不是 **how**。

```markdown
# 添加化合物搜索端点

- 支持按名称、SMILES、InChIKey 搜索
- 添加分页支持，默认返回 20 条结果
- 实现结果缓存，提升查询性能

Closes #123
```

### 3.6 Footer 脚注

```
Closes #123
Fixes #456
Refs #789

Co-Authored-By: Name <email>
```

### 3.7 完整示例

```bash
feat(api): add compound similarity search endpoint

新增基于分子指纹的化合物相似度搜索功能：

- 支持 Tanimoto 系数计算
- 添加分页和结果过滤功能
- 实现结果缓存机制

相关 Issue: #123

Co-Authored-By: Zhang San <zhangsan@example.com>
```

---

## 四、代码提交流程

### 4.1 日常开发流程

```bash
# 1. 开启网络加速（AutoDL 环境）
source /etc/network_turbo

# 2. 切换到 main 分支并拉取最新代码
git checkout main
git pull origin main

# 3. 创建功能分支
git checkout -b feature/your-feature-name

# 4. 进行代码修改...

# 5. 查看修改状态
git status

# 6. 添加修改的文件
git add .
# 或添加特定文件
git add path/to/file

# 7. 提交到本地
git commit -m "feat(scope): description"

# 8. 推送到远程
git push -u origin feature/your-feature-name

# 9. 创建 Pull Request (GitHub 网页操作)
```

### 4.2 快速提交流程（适合小改动）

```bash
# 一条命令完成所有步骤
source /etc/network_turbo && git add . && git commit -m "your message" && git push
```

### 4.3 修改最后一次提交

```bash
# 修改提交内容（添加更多文件）
git add forgotten_file.txt
git commit --amend

# 修改提交信息
git commit --amend -m "new commit message"

# 注意：如果已经推送到远程，需要强制推送
git push -f
```

### 4.4 查看差异

```bash
# 查看未暂存的修改
git diff

# 查看已暂存的修改
git diff --staged

# 查看特定文件的修改
git diff path/to/file

# 查看提交历史
git log --oneline -10
git log --graph --all --oneline --decorate
```

---

## 五、常用命令

### 5.1 分支操作

```bash
# 查看所有分支
git branch -a

# 查看当前分支状态
git status

# 创建新分支
git branch feature-name

# 切换分支
git checkout feature-name

# 创建并切换到新分支
git checkout -b feature-name

# 删除本地分支
git branch -d feature-name

# 删除远程分支
git push origin --delete feature-name
```

### 5.2 远程操作

```bash
# 查看远程仓库
git remote -v

# 查看远程仓库详细信息
git remote show origin

# 拉取远程更新
git pull origin main

# 推送本地分支
git push origin feature-name

# 推送所有分支
git push --all

# 设置上游分支
git branch --set-upstream-to=origin/main main
```

### 5.3 查看历史

```bash
# 查看提交历史
git log

# 简洁显示
git log --oneline

# 图形化显示
git log --graph --oneline --all

# 查看特定文件的历史
git log -- path/to/file

# 查看某次提交的详细内容
git show <commit-hash>
```

### 5.4 撤销操作

```bash
# 撤销工作区的修改
git restore path/to/file

# 撤销暂存区的修改
git restore --staged path/to/file

# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃修改）
git reset --hard HEAD~1

# 回退到指定提交
git reset --hard <commit-hash>
```

---

## 六、故障排除

### 6.1 网络问题

**问题**: 推送时出现网络超时或连接失败

**解决方案**:
```bash
# 启用网络加速
source /etc/network_turbo

# 再次尝试推送
git push
```

### 6.2 认证问题

**问题**: 推送时提示用户名或密码错误

**解决方案**:
```bash
# 使用 Personal Access Token
git push https://<TOKEN>@github.com/fchcao/pharmaKG.git main

# 或者配置 credential helper
git config credential.helper store
```

### 6.3 分支冲突

**问题**: 拉取或合并时出现冲突

**解决方案**:
```bash
# 拉取远程更新
git pull origin main

# 解决冲突后
git add .
git commit -m "fix: resolve merge conflicts"

# 推送
git push
```

### 6.4 提交历史混乱

**问题**: 提交历史不清晰或需要整理

**解决方案**:
```bash
# 交互式变基（清理最近 3 次提交）
git rebase -i HEAD~3

# 或者变基到 main 分支
git rebase main
```

---

## 七、最佳实践

### 7.1 提交频率

- ✅ **小而频繁**: 每完成一个小功能就提交
- ❌ **大而稀少**: 避免一次性提交大量修改

### 7.2 提交粒度

- ✅ **一个提交只做一件事**: 便于代码审查和回滚
- ❌ **混合多个修改**: 不同类型的修改应该分开提交

### 7.3 提交信息

- ✅ **清晰描述**: 让其他人（和未来的你）理解这次修改的目的
- ❌ **模糊不清**: "update", "fix", "修改文件" 等

### 7.4 分支管理

- ✅ **功能分支**: 每个新功能使用独立分支
- ✅ **定期同步**: 定期从 main 拉取最新代码
- ❌ **直接在 main 开发**: 避免直接在 main 分支进行开发

---

## 八、相关文档

- [CHANGELOG.md](../CHANGELOG.md) - 项目变更日志
- [README.md](../README.md) - 项目概述
- [CLAUDE.md](../CLAUDE.md) - Claude Code 开发指导
- [实施路线图](../docs/schema/实施路线图.md) - 项目路线图

---

**维护者**: PharmaKG Team
**最后更新**: 2026-02-07
