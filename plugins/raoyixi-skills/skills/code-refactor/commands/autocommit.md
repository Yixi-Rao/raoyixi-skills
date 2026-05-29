# 自动化代码总结与提交指南

## 概述
本指南结合了两个文件的内容，提供了一个完整的自动化代码变更总结和提交流程，适用于大模型实现自动化代码管理。

## 配置参数
```
变更记录目录: ./changelog
文档命名格式: CodeChange_{年月日时分}_{git_user}.md
```

## 第一阶段：代码变更分析与记录

### 环境检查和基础信息收集
1. **检查当前分支和远程分支关系**
   ```bash
   git branch -r                    # 查看远程分支列表
   git branch                       # 确认当前分支
   ```

2. **确定对比基础节点**
   - 优先对比远程同名分支：`git merge-base {current_branch} origin/{current_branch}`
   - 如果远程不存在同名分支，则对比master分支：`git merge-base {current_branch} origin/master`
   - 记录基础commit hash作为对比起点

3. **获取时间和用户信息**
   ```bash
   cur_date=$(date '+%Y%m%d%H%M')   # 格式：年月日时分
   git_user=$(git config user.name) # 获取git用户名
   ```

### 代码变更分析
1. **获取变更文件列表**
   ```bash
   git status --porcelain | grep -v "changelog/"  # 排除changelog目录
   ```

2. **获取具体变更内容**
   - 对于修改文件：`git diff {file_path}`
   - 对于新增文件：使用find命令列出文件结构
   - 对于删除文件：记录删除状态

3. **应用过滤规则**
   - 根据.gitignore规则排除不必要的文件
   - 排除changelog/目录内的所有文件
   - 排除__pycache__/、.claude/、bak/、prompts/等目录

### 生成变更记录文档
创建文件：`{变更记录目录}/CodeChange_{cur_date}_{git_user}.md`

**文档结构模板：**
````markdown
# 代码变更记录

**变更时间**: {cur_date}  
**变更人员**: {git_user}  
**对比基础**: {base_commit_hash} (说明对比基础的来源)  
**当前分支**: {current_branch}  

## 变更总览

本次变更主要包含以下内容：
1. [概述变更类型和范围]
2. [主要功能模块变化]
3. [配置文件调整]
4. [新增/删除文件说明]

## 详细变更内容

### 1. {文件路径} 文件变更

**文件路径**: `{relative_file_path}`  
**变更类型**: {修改(M)/新增(??)/删除(D)}  
**变更目的**: {说明变更的业务目的和技术目标}

**变更内容**:
```diff
{具体的diff内容}
```

**变更说明**:
- [逐条说明每个变更块的作用]
- [解释技术实现细节]
- [说明对系统的影响]

### 2. 新增文件和目录

#### 2.1 {目录名称}/ 目录
**变更类型**: 新增 (??)  
**变更目的**: {说明新增目录的用途和价值}

**新增文件**:
- `{file_name}` - {文件功能说明}
- [列出主要文件及其作用]

## 变更影响分析

1. **功能影响**: {分析对现有功能的影响}
2. **性能影响**: {分析对系统性能的影响}
3. **兼容性影响**: {分析向前/向后兼容性}
4. **部署影响**: {分析对部署流程的影响}

## 总结

{总结本次变更的整体价值和意义，以及可能的风险点}
````

## 第二阶段：自动化提交流程

### 执行流程
```bash
# 1. 获取工程目录和基础信息
pwd  # 获取当前待提交代码的仓库，记为{工程目录}
git_commit_message="根据代码变更生成的提交信息"
git_local_branch=$(git rev-parse --abbrev-ref HEAD)
global_user=$(git config --global user.name)

# 2. 执行提交流程
cd {工程目录}

# 显示本地分支与远程分支差异
echo "=== 检查本地分支与远程分支差异 ==="
git fetch origin {git_local_branch}
git diff HEAD origin/{git_local_branch} --stat
echo "=== 详细差异 ==="
git diff HEAD origin/{git_local_branch}

# 添加所有更改
git add .

# 提交更改（使用Conventional Commits规范）
git commit -m "{git_commit_message}

Co-authored-by: {global_user} <{global_user}@lixiang.com>
Co-authored-by: anthropic <anthropic@lixiang.com>"

# 如果提交失败，自动修复pre-commit发现的问题
if [ $? -ne 0 ]; then
    echo "=== pre-commit检查失败，尝试自动修复 ==="
    git add .
    git commit -m "{git_commit_message}

Co-authored-by: {global_user} <{global_user}@lixiang.com>
Co-authored-by: anthropic <anthropic@lixiang.com>"
fi

# 推送到远程分支
git push origin {git_local_branch}:{git_local_branch}
```

## 规范要求

### Conventional Commits规范
- **格式**: `type: description`
- **简洁性**: commit message要简单，言简意赅，只保留关键信息，最多不超过20个字
- **类型**: 使用标准类型如feat、fix、docs、style、refactor、test、chore等

### 协作者信息
- 使用标准的Co-authored-by格式添加协作者信息，放在commit body部分
- 格式：`Co-authored-by: 用户名 <邮箱>`

### 质量检查
- commit过程中如果pre-commit发现格式问题、import冗余问题，必须完全修复后才能提交
- 不允许使用--no-verify跳过任何hooks检查
- 如果push失败，分析原因并尝试修复，禁止使用`git push --force origin xxx`

## 常见问题处理

### 1. ruff检查失败
- 自动删除未使用的import
- 修复格式问题
- 重新add和commit

### 2. conventional-commit检查失败
- 调整commit message格式直到符合规范
- 确保使用正确的type和description格式

### 3. push被拒绝
- 检查是否需要先pull合并远程更改
- 解决冲突后重新提交

## 大文件清理功能

当遇到 Git 推送失败提示大文件（>100MB）问题时，参考 [clean.md](clean.md) 中的指南进行清理。

### 快速清理步骤

1. **扫描大文件**：
   ```bash
   git rev-list -n 50 HEAD | while read commit; do
       git ls-tree -r -l $commit | awk '$4 > 100000000 {print "文件:" $5, "大小:" int($4/1024/1024) "MB"}'
   done | sort -u
   ```

2. **分析文件来源**：
   ```bash
   git log --all --pretty=format:"%H %an %s" --follow -- <file_path> | tail -1
   ```

3. **执行清理**（需用户确认）：
   ```bash
   git reset --soft <previous_commit_hash>
   git rm --cached <file_path>
   rm -f <file_path>
   git add .
   git commit -m "Clean history: remove large files"
   ```

4. **强制推送**（最后确认）：
   ```bash
   git push origin <branch_name> --force
   ```

详细操作指南请参考 [clean.md](clean.md) 文件。

## 完整执行示例

```bash
# 1. 环境检查
git status
git branch -r

# 2. 生成变更记录
# [根据第一阶段流程生成CodeChange文档]

# 3. 执行自动提交
# [根据第二阶段流程执行提交]

# 4. 验证结果
ls -la ./changelog/
git log --oneline -5
```

## 注意事项

### 排除规则
- **必须排除**：.gitignore中明确列出的文件和目录
- **必须排除**：changelog/目录内的所有文件
- **建议排除**：临时文件、编译产物、IDE配置文件

### 质量要求
- **完整性**：确保所有实质性变更都被记录
- **准确性**：diff内容必须准确反映实际变更
- **可读性**：使用清晰的语言说明变更目的和影响
- **结构化**：严格按照模板格式组织内容

### 自动化建议
- 可以结合CI/CD流程自动触发变更记录生成
- 建议在每次重要提交前生成变更记录
- 可以设置定期（如每日/每周）自动生成汇总报告