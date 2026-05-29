# AutoSummary 使用指南

## 概述

本指南用于分析并总结某个分支与现有 master 分支的变更记录，帮助开发者快速了解分支中的修改内容、影响范围和关键变更点。

## 目录

- [前置准备](#前置准备)
- [基本用法](#基本用法)
- [变更分析流程](#变更分析流程)
- [总结报告生成](#总结报告生成)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 前置准备

### 环境要求

- Git 版本 >= 2.20
- Python 3.8+（如果使用自动化脚本）
- 对目标仓库的读取权限

### 初始化设置

```bash
# 确保在项目根目录
cd /path/to/your/project

# 更新所有分支信息
git fetch --all

# 确保 master 分支是最新的
git checkout master
git pull origin master
```

---

## 基本用法

### 1. 查看分支差异

#### 查看文件变更列表

```bash
# 查看当前分支相对于 master 的所有变更文件
git diff master...your-branch --name-only

# 查看详细的文件变更统计
git diff master...your-branch --stat

# 查看具体的代码变更
git diff master...your-branch
```

#### 查看提交历史

```bash
# 查看分支上的所有提交
git log master..your-branch --oneline

# 查看详细的提交信息
git log master..your-branch --pretty=format:"%h - %an, %ar : %s"

# 查看每个提交的文件变更
git log master..your-branch --name-status
```

### 2. 按文件类型分类

```bash
# 查看所有修改的 Python 文件
git diff master...your-branch --name-only | grep '\.py$'

# 查看所有修改的 JavaScript/TypeScript 文件
git diff master...your-branch --name-only | grep '\.\(js\|ts\)$'

# 查看所有修改的配置文件
git diff master...your-branch --name-only | grep '\.\(json\|yaml\|yml\|toml\|ini\)$'
```

### 3. 统计变更量

```bash
# 统计代码行数变化
git diff master...your-branch --shortstat

# 按作者统计变更
git shortlog master..your-branch

# 详细的变更统计
git diff master...your-branch --numstat
```

---

## 变更分析流程

### 步骤 1: 识别变更类型

对变更进行分类，常见类型包括：

- **新功能 (Feature)**: 新增的功能模块或特性
- **Bug 修复 (Bugfix)**: 修复已知问题
- **重构 (Refactor)**: 代码结构优化，不改变功能
- **性能优化 (Performance)**: 提升性能的修改
- **文档 (Documentation)**: 文档更新
- **测试 (Test)**: 测试代码的添加或修改
- **配置 (Config)**: 配置文件的变更
- **依赖 (Dependencies)**: 第三方依赖的更新

### 步骤 2: 分析影响范围

#### 识别核心模块变更

```bash
# 查看目录级别的变更分布
git diff master...your-branch --dirstat

# 查看每个目录的变更文件数
git diff master...your-branch --name-only | cut -d/ -f1 | sort | uniq -c
```

#### 识别关键文件变更

关注以下类型的文件变更：

- API 接口文件
- 数据库模型/迁移文件
- 配置文件
- 核心业务逻辑文件
- 公共工具类/函数

### 步骤 3: 提取变更细节

```bash
# 查看特定文件的详细变更
git diff master...your-branch -- path/to/file

# 查看函数级别的变更
git diff master...your-branch -U10 -- path/to/file

# 使用更友好的差异格式
git diff master...your-branch --word-diff -- path/to/file
```

### 步骤 4: 识别潜在风险

检查以下方面：

- **破坏性变更**: API 接口变更、数据结构变更
- **安全问题**: 认证、授权相关的修改
- **性能风险**: 大量数据处理、循环嵌套等
- **兼容性问题**: 依赖版本升级、配置格式变更

---

## 总结报告生成

### 报告模板

```markdown
# 分支变更总结报告

**分支名称**: feature/your-branch-name
**基准分支**: master
**分析时间**: YYYY-MM-DD
**分析人员**: Your Name

---

## 一、变更概览

### 统计数据
- 总提交数: X 个
- 变更文件数: Y 个
- 新增代码行: +A 行
- 删除代码行: -B 行
- 净增代码行: N 行

### 变更分布
| 目录/模块 | 变更文件数 | 新增行数 | 删除行数 |
|----------|-----------|---------|---------|
| module_a | X | +A | -B |
| module_b | Y | +C | -D |

---

## 二、主要变更内容

### 2.1 新功能
1. **功能名称**: 功能描述
   - 涉及文件: `file1.py`, `file2.py`
   - 关键变更: 简要说明

2. **功能名称**: 功能描述
   - 涉及文件: `file3.js`
   - 关键变更: 简要说明

### 2.2 Bug 修复
1. **问题描述**: 修复了什么问题
   - 影响范围: 哪些模块/功能
   - 修复方式: 如何修复

### 2.3 重构与优化
1. **重构内容**: 重构说明
   - 优化效果: 性能提升/代码质量提升

### 2.4 配置与依赖变更
- 新增依赖: `package@version`
- 更新依赖: `old-package@1.0` → `new-package@2.0`
- 配置变更: 说明配置项的变化

---

## 三、关键变更详解

### 3.1 API 接口变更
| 接口路径 | 变更类型 | 说明 |
|---------|---------|------|
| /api/v1/users | 新增 | 新增用户管理接口 |
| /api/v1/auth | 修改 | 更新认证逻辑 |

### 3.2 数据库变更
- 新增表: `table_name`
- 修改表结构: `table_name` - 新增字段 `field_name`
- 数据迁移: 描述迁移内容

### 3.3 核心逻辑变更
详细说明核心业务逻辑的变更内容和原因。

---

## 四、风险评估

### 4.1 破坏性变更
- [ ] 无破坏性变更
- [ ] 存在破坏性变更（需要说明）

### 4.2 潜在风险点
1. **风险描述**: 具体风险内容
   - 影响范围: 
   - 缓解措施:

### 4.3 测试覆盖
- 单元测试: 已添加/已更新
- 集成测试: 已添加/已更新
- 手动测试: 已完成

---

## 五、部署注意事项

### 5.1 前置条件
- 数据库迁移命令: `command here`
- 环境变量配置: 新增/修改的环境变量
- 依赖安装: `npm install` / `pip install -r requirements.txt`

### 5.2 部署步骤
1. 步骤一
2. 步骤二
3. 步骤三

### 5.3 回滚方案
说明如何回滚到之前的版本。

---

## 六、审查建议

### 6.1 重点审查文件
- `critical/file1.py` - 核心业务逻辑变更
- `critical/file2.js` - API 接口变更

### 6.2 审查要点
- [ ] 代码规范检查
- [ ] 安全性检查
- [ ] 性能影响评估
- [ ] 测试覆盖率检查

---

## 七、附录

### 7.1 完整提交列表
```
commit_hash1 - Author, Date: Commit message
commit_hash2 - Author, Date: Commit message
```

### 7.2 完整文件变更列表
```
M  modified_file1.py
A  added_file1.js
D  deleted_file1.old
```
```

---

## 最佳实践

### 1. 定期同步 master 分支

```bash
# 在功能分支上定期合并 master
git checkout your-branch
git merge master

# 或使用 rebase (保持提交历史整洁)
git rebase master
```

### 2. 使用有意义的提交信息

```bash
# 推荐的提交信息格式
<type>(<scope>): <subject>

# 示例
feat(auth): add JWT token authentication
fix(api): resolve null pointer exception in user endpoint
docs(readme): update installation instructions
```

### 3. 分阶段提交

- 每个提交应该是一个逻辑完整的单元
- 避免混合多种类型的变更在同一个提交中
- 大功能应该拆分为多个小提交

### 4. 使用标签和里程碑

```bash
# 为重要的版本打标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 查看所有标签
git tag -l
```

### 5. 自动化总结脚本

可以创建自动化脚本来生成变更总结：

```bash
#!/bin/bash
# auto-summary.sh

BRANCH=${1:-$(git rev-parse --abbrev-ref HEAD)}
BASE_BRANCH=${2:-master}

echo "# 分支变更总结报告"
echo ""
echo "**分支名称**: $BRANCH"
echo "**基准分支**: $BASE_BRANCH"
echo "**分析时间**: $(date +%Y-%m-%d)"
echo ""
echo "## 统计数据"
echo ""
git diff $BASE_BRANCH...$BRANCH --shortstat
echo ""
echo "## 变更文件列表"
echo ""
git diff $BASE_BRANCH...$BRANCH --name-status
echo ""
echo "## 提交历史"
echo ""
git log $BASE_BRANCH..$BRANCH --oneline
```

使用方法：

```bash
# 分析当前分支
./auto-summary.sh

# 分析指定分支
./auto-summary.sh feature/my-feature

# 指定基准分支
./auto-summary.sh feature/my-feature develop
```

---

## 常见问题

### Q1: 如何比较两个非直接相关的分支？

```bash
# 使用三点语法找到共同祖先后的变更
git diff branch1...branch2

# 或使用 merge-base
git diff $(git merge-base branch1 branch2) branch2
```

### Q2: 如何查看已删除文件的内容？

```bash
# 查看删除的文件列表
git diff master...your-branch --diff-filter=D --name-only

# 查看删除文件的最后内容
git show master:path/to/deleted/file
```

### Q3: 如何忽略空白字符的变更？

```bash
# 忽略空白字符变更
git diff master...your-branch -w

# 忽略行尾空白字符
git diff master...your-branch --ignore-space-at-eol
```

### Q4: 如何生成可分享的变更报告？

```bash
# 生成 HTML 格式的差异报告
git diff master...your-branch > changes.diff
git diff master...your-branch --stat > changes-stat.txt

# 使用 git log 生成格式化的提交历史
git log master..your-branch --pretty=format:"%h - %an, %ar : %s" > commits.txt
```

### Q5: 如何处理大型分支的变更分析？

对于包含大量变更的分支：

1. **按模块拆分分析**: 逐个目录进行分析
2. **使用可视化工具**: 如 GitKraken, SourceTree
3. **分阶段审查**: 按时间顺序或功能模块分批审查
4. **自动化工具**: 使用 CI/CD 集成的代码审查工具

---

## 扩展工具推荐

### 命令行工具

- **tig**: 终端下的 Git 可视化工具
- **diff-so-fancy**: 更美观的 diff 输出
- **git-extras**: 提供额外的 Git 命令

### 在线服务

- **GitHub Pull Request**: 提供完整的变更审查界面
- **GitLab Merge Request**: 类似功能
- **Bitbucket Pull Request**: 类似功能

### IDE 集成

- **VSCode**: Git Graph, GitLens 插件
- **IntelliJ IDEA**: 内置强大的 Git 集成
- **Sublime Merge**: 专业的 Git 客户端

---

## 总结

通过系统化的变更分析和总结流程，可以：

1. ✅ 快速了解分支的所有变更内容
2. ✅ 识别潜在的风险和问题
3. ✅ 为代码审查提供清晰的指引
4. ✅ 确保变更的可追溯性和文档化
5. ✅ 提高团队协作效率

建议根据项目的具体情况调整和完善这个流程，使其更符合团队的工作方式。