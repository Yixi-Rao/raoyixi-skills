# Git 大文件清理指南

## 概述
本指南提供了一套完整的自动化流程，用于检测并清理 Git 仓库中的大文件（>100MB），解决因大文件导致的推送失败问题。

## 操作目标
- 自动发现最近 N 个提交中上传过的大文件（>100MB）
- 回退到大文件首次出现之前的提交（git reset --soft）
- 删除该大文件并保持现有代码不丢失
- 将所有更改合并成一个新的干净提交
- 在确认后强制推送到远程仓库

## ⚠️ 安全警告
- 所有命令必须真实可执行，不得使用伪命令或"假执行"描述
- 每个步骤输出执行结果（文件路径、commit hash 等）
- 对不可逆操作（如 push --force）必须进行确认提示
- 保证执行过程中不会丢失当前工作区代码

## 大模型执行指南

本指南专为大模型设计，提供逐步执行的命令，无需创建脚本文件。

### 🎯 执行原则
- **逐步执行**：每个步骤都要单独执行，等待结果确认后再进行下一步
- **结果验证**：每步都要检查输出结果，确保操作正确
- **安全第一**：涉及强制推送的操作必须获得用户明确确认

### 🔍 步骤1：环境检查

首先检查当前仓库状态：

```bash
echo "=== 环境检查 ==="
git status
git branch --show-current
echo "当前目录: $(pwd)"
```

### 🔍 步骤2：扫描大文件

执行扫描命令，查找最近50次提交中的大文件：

```bash
echo "=== 扫描最近50次提交中的大文件(>100MB) ==="
git rev-list -n 50 HEAD | while read commit; do
    git ls-tree -r -l $commit | awk '$4 > 100000000 {print "文件:" $5, "大小:" int($4/1024/1024) "MB", "提交:" $commit}'
done | sort -u
```

**等待结果**：
- 如果输出为空，说明没有大文件，任务结束
- 如果有输出，记录文件路径，继续下一步

### 🔍 步骤3：分析大文件详情

对每个发现的大文件，获取详细信息：

```bash
# 替换 <file_path> 为实际文件路径
echo "=== 分析文件: <file_path> ==="
echo "首次出现提交:"
git log --all --pretty=format:"%H %an %s" --follow -- <file_path> | tail -1
echo "上一个提交:"
first_commit=$(git log --all --pretty=format:"%H" --follow -- <file_path> | tail -1)
git rev-parse ${first_commit}^
```

### ⚠️ 步骤4：执行清理（需要用户确认）

**在执行清理前，必须向用户确认**：

```bash
echo "⚠️  即将执行清理操作："
echo "- 回退到上一个提交（保留代码更改）"
echo "- 移除大文件"
echo "- 重新提交更改"
# 等待用户确认后再执行下一步
```

获得确认后执行：

```bash
# 替换为实际的前一个提交hash
echo "=== 执行软回退 ==="
git reset --soft <previous_commit_hash>
echo "=== 移除大文件 ==="
git rm --cached <file_path>
rm -f <file_path>
echo "=== 验证删除 ==="
git status | grep -q "<file_path>" && echo "⚠️  文件仍在状态列表中" || echo "✓ 文件已成功移除"
```

### ✅ 步骤5：重新提交

```bash
echo "=== 重新提交清理结果 ==="
git add .
git commit -m "Clean history: remove large files and squash commits"
echo "新提交信息:"
git log --oneline -1
```

### 🚨 步骤6：强制推送（最后确认）

**强制推送前必须获得用户明确确认**：

```bash
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "=== 推送前检查 ==="
echo "当前分支: $current_branch"
echo "待推送提交数: $(git rev-list origin/$current_branch..HEAD | wc -l)"
echo ""
echo "🚨 即将执行强制推送，这会重写远程分支历史！"
echo "其他协作者将需要执行：git fetch origin && git reset --hard origin/$current_branch"
# 等待用户确认是否执行强制推送
```

用户确认后执行：

```bash
git push origin $current_branch --force
echo "✓ 强制推送完成"
```

### 🔄 应急回滚

如果清理过程中出现问题：

```bash
echo "=== 查看操作历史 ==="
git reflog -5
echo "=== 如需回滚，执行 ==="
echo "git reset --hard <之前的commit_hash>"
```