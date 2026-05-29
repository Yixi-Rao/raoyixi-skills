---
name: docker-image-deploy
description: 将 Docker Hub 镜像部署到企业 Harbor 私有镜像仓库。当用户说"部署镜像到 Harbor"、"上传 Docker 镜像"、"镜像迁移"、"推送到 reg-ai.chehejia.com"或"Docker Hub 到 Harbor"时使用。支持跨架构部署(ARM到AMD64)。
license: MIT
metadata:
  author: Internal DevOps Team
  version: 1.0.0
  category: infrastructure
  tags: [docker, harbor, deployment, container]
  compatibility: 需要 Colima、Docker CLI、docker-buildx。仅支持 macOS。需要企业 VPN 访问 Harbor (reg-ai.chehejia.com)。
---

# Docker 镜像部署到 Harbor 技能

## 功能概述

此技能提供完整的 Docker 镜像部署流程,用于将公共镜像仓库(如 Docker Hub)的镜像迁移到企业私有 Harbor 仓库。

**核心功能**:
1. ✅ 环境检查与依赖安装(需用户确认)
2. ✅ 从源镜像仓库拉取镜像
3. ✅ 为镜像打上 Harbor 标签
4. ✅ 推送镜像到 Harbor 仓库
5. ✅ 验证部署成功并生成部署文档

## 使用方法

### 基本调用

```bash
# 启动镜像部署流程
$docker-image-deploy
```

技能会自动引导您完成整个部署流程。

### 使用场景

1. **从 Docker Hub 迁移镜像到 Harbor**
   ```bash
   $docker-image-deploy
   # 然后输入源镜像信息和 Harbor 凭证
   ```

2. **跨架构部署**(如 ARM Mac 部署 AMD64 镜像)
   ```bash
   $docker-image-deploy
   # 技能会自动检测并使用 --platform 参数
   ```

## 前置要求

### 必需工具

执行部署前,系统需要安装以下工具:

| 工具 | 用途 | 安装命令 (macOS) |
|-----|------|-----------------|
| Docker CLI | Docker 命令行工具 | `brew install docker` |
| Colima | Docker 运行时环境 | `brew install colima` |
| docker-buildx | 跨架构构建支持 | `brew install docker-buildx` |

**重要**: 技能会自动检测缺失的工具,并在征得您同意后统一安装。

### 网络要求

- **Docker Hub 访问**: 需要稳定的网络连接
- **Harbor 访问**: 需要企业内网访问(通常需要 VPN)
- **代理配置**: 如需代理,请在任务开始前手动配置

### 所需信息

技能会主动收集以下信息(如未提供):

1. **源镜像信息**
   - Docker Hub 镜像完整链接或名称
   - 镜像架构(如 linux/amd64)

2. **Harbor 凭证**
   - LDAP 用户名
   - Harbor 专用密码

3. **目标配置**
   - Harbor 仓库地址(默认: reg-ai.chehejia.com)
   - 目标镜像标签

## 部署流程详解

### 第 1 步: 环境检查

技能会自动检查:

1. **工具安装状态**
   ```bash
   # 检查 docker
   which docker

   # 检查 colima
   which colima

   # 检查 docker-buildx
   which docker-buildx
   ```

2. **Docker 运行状态**
   ```bash
   docker ps
   ```

3. **磁盘空间**
   ```bash
   df -h
   ```

**如果检测到缺失工具**,技能会:
- 列出所有需要安装的工具清单
- 说明每个工具的用途
- **征得您的明确同意后**才执行安装
- 使用 Homebrew 统一安装

示例输出:
```
检测到以下工具未安装:
  ❌ docker - Docker 命令行工具
  ❌ colima - 容器运行时环境
  ❌ docker-buildx - 跨架构构建工具

建议安装命令:
  brew install docker colima docker-buildx

是否现在安装? (需要您的确认)
```

### 第 2 步: 收集部署信息

技能会通过 `AskUserQuestion` 工具主动询问:

**问题 1: 源镜像信息**
```
请提供源镜像信息:
□ Docker Hub 链接 (如: https://hub.docker.com/layers/verlai/verl/...)
□ 或镜像名称 (如: verlai/verl:vllm012.latest)
```

**问题 2: Harbor 凭证**
```
请提供 Harbor 登录凭证:
□ LDAP 用户名: _______
□ Harbor 专用密码: _______
```

**问题 3: 目标配置**(可选)
```
目标配置 (可选):
□ Harbor 地址: [默认 reg-ai.chehejia.com]
□ 目标标签: [默认与源镜像相同]
```

### 第 3 步: 启动 Colima 运行时

```bash
# 启动 Colima
colima start
```

检查启动状态:
```bash
INFO[0000] using docker runtime
INFO[0000] starting colima
INFO[0019] provisioning ...                context=vm
INFO[0020] starting ...                    context=docker
INFO[0021] done
```

### 第 4 步: 登录 Harbor

```bash
docker login reg-ai.chehejia.com -u <LDAP用户名> -p <Harbor密码>
```

预期输出:
```
Login Succeeded
```

**安全提示**: 密码不会记录在日志或部署文档中。

### 第 5 步: 拉取源镜像

```bash
docker pull <源镜像名称> --platform <架构>
```

**进度监控**:
- 技能会实时报告下载进度
- 显示已完成层数和剩余层数
- 大型镜像可能需要 10-30 分钟

示例输出:
```
【拉取进度】
✅ 已完成: 15/37 层 (40.5%)
🔄 正在下载: layer abc123... (256MB)
⏱️ 预计剩余时间: 8 分钟
```

### 第 6 步: 打标签

```bash
docker tag <源镜像> reg-ai.chehejia.com/<用户名>/<镜像名>:<标签>
```

验证标签:
```bash
docker images | grep <镜像名>
```

### 第 7 步: 推送到 Harbor

```bash
docker push reg-ai.chehejia.com/<用户名>/<镜像名>:<标签>
```

**进度监控**:
- 实时显示上传进度
- 显示已推送层数
- 估算剩余时间

示例输出:
```
【推送进度】
✅ 已完成: 28/37 层 (75.7%)
🔄 正在推送: layer def456... (512MB)
⏱️ 预计剩余时间: 5 分钟
```

### 第 8 步: 验证部署

1. **检查 Harbor API**
   ```bash
   curl -s -u <用户名>:<密码> \
     https://reg-ai.chehejia.com/v2/<用户名>/<镜像名>/tags/list
   ```

2. **验证 Digest**
   - 确认推送的 digest 与源镜像一致

3. **生成部署文档**
   - 自动生成详细的部署记录
   - 包含镜像信息、部署流程、故障排查等

### 第 9 步: 生成部署文档

技能会自动在工作目录生成 `部署记录.md`,包含:

- ✅ 部署信息汇总
- ✅ 源镜像和目标镜像详情
- ✅ 完整的部署命令
- ✅ 验证结果
- ✅ 使用方法说明
- ✅ 故障排查指南

## Examples

### Example 1: 部署标准 Docker Hub 镜像

**用户说**: "帮我把 verlai/verl:vllm012.latest 这个镜像部署到 Harbor"

**执行步骤**:
1. 检测环境(docker, colima, docker-buildx)
2. 询问 LDAP 用户名和 Harbor 密码
3. 启动 Colima
4. 登录 Harbor (reg-ai.chehejia.com)
5. 拉取镜像: `docker pull verlai/verl:vllm012.latest --platform linux/amd64`
6. 打标签: `docker tag verlai/verl:vllm012.latest reg-ai.chehejia.com/raoyixi/verl:vllm012.latest`
7. 推送: `docker push reg-ai.chehejia.com/raoyixi/verl:vllm012.latest`
8. 验证 Digest 匹配
9. 生成部署记录文档

**结果**: 镜像成功推送到 `reg-ai.chehejia.com/raoyixi/verl:vllm012.latest`,生成详细部署文档。

### Example 2: 跨架构部署(ARM Mac 到 AMD64)

**用户说**: "我在 M1 Mac 上,需要部署 pytorch/pytorch:2.0.1 到 Harbor,目标是 AMD64 架构"

**执行步骤**:
1. 检测系统架构(ARM64)
2. 自动添加 `--platform linux/amd64` 参数
3. 使用 Colima 的跨架构支持
4. 拉取 AMD64 版本镜像
5. 打标签并推送到 Harbor
6. 验证架构正确(linux/amd64)

**结果**: 成功部署适用于 LPAI 平台的 AMD64 镜像。

### Example 3: 首次使用(需要安装工具)

**用户说**: "部署 Docker 镜像到 Harbor"

**执行步骤**:
1. 检测环境,发现缺少 docker, colima, docker-buildx
2. 列出安装清单:
   ```
   需要安装的工具:
   ❌ docker - Docker 命令行工具
   ❌ colima - 容器运行时环境
   ❌ docker-buildx - 跨架构构建工具

   建议安装命令:
   brew install docker colima docker-buildx
   ```
3. 等待用户确认
4. 用户确认后执行安装
5. 安装完成后继续部署流程

**结果**: 工具安装完成,镜像成功部署。

## 参考文档

### Colima 使用指南

需要 Colima 细节时读取 `references/colima-guide.md`。

### Harbor 使用说明

需要 Harbor 细节时读取 `references/harbor-guide.md`。

## 配置管理

### 默认配置

技能使用以下默认配置:

```yaml
# ./config/defaults.yaml
harbor:
  registry: reg-ai.chehejia.com

docker:
  default_platform: linux/amd64
  pull_timeout: 3600  # 秒
  push_timeout: 3600  # 秒

colima:
  cpu: 2
  memory: 2  # GB
  disk: 100  # GB
```

### 自定义配置

您可以创建 `./config/custom.yaml` 覆盖默认配置:

```yaml
harbor:
  registry: custom-registry.example.com

docker:
  default_platform: linux/arm64
```

## 常见问题排查

### 问题 1: Docker daemon 未运行

**错误信息**:
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**解决方案**:
```bash
# 启动 Colima
colima start

# 验证
docker ps
```

### 问题 2: 镜像拉取超时

**错误信息**:
```
error pulling image: net/http: TLS handshake timeout
```

**解决方案**:
1. 检查网络连接
2. 如需代理,配置 Docker 代理设置
3. 增加超时时间
4. 使用 `colima restart` 重新加载配置

### 问题 3: Harbor 认证失败

**错误信息**:
```
unauthorized: authentication required
```

**解决方案**:
1. 确认使用的是 Harbor 专用密码(不是 LDAP 密码)
2. 重新登录:
   ```bash
   docker logout reg-ai.chehejia.com
   docker login reg-ai.chehejia.com -u <用户名>
   ```

### 问题 4: 磁盘空间不足

**错误信息**:
```
no space left on device
```

**解决方案**:
1. 清理无用镜像:
   ```bash
   docker image prune -a
   ```
2. 扩展 Colima 磁盘(需重建):
   ```bash
   colima stop
   colima start --disk 200
   ```

### 问题 5: 架构不匹配

**错误信息**:
```
exec format error
```

**解决方案**:
- 确保使用 `--platform` 参数指定正确架构
- 对于 AMD64 镜像,必须使用:
  ```bash
  docker pull <镜像> --platform linux/amd64
  ```

## 安全最佳实践

### 1. 凭证管理

- ❌ **不要**在命令历史中保存密码
- ✅ **使用**环境变量或密钥管理工具
- ✅ Harbor 密码使用专用密码,定期轮换

### 2. 镜像验证

- ✅ 始终验证 Digest 匹配
- ✅ 检查镜像签名(如适用)
- ✅ 扫描已知漏洞

### 3. 网络安全

- ✅ Harbor 访问走企业内网,不走公网代理
- ✅ 使用 HTTPS 连接
- ✅ 启用 VPN 访问企业内网资源

### 4. 权限控制

- ✅ 推送到个人空间 `<用户名>/`
- ❌ 不要推送到系统保留目录 `<用户名>/notebook/`
- ✅ 只授予必要的最小权限

## 性能优化

### 1. 并行层传输

Docker 默认并行传输多个层,无需额外配置。

### 2. 镜像缓存

- 相同的层只需拉取/推送一次
- 增量更新只传输变更的层

### 3. 网络优化

- 使用稳定的网络连接
- 对于超大镜像(>20GB),考虑分批部署
- 在非高峰时段执行大型部署

## 任务清单模板

技能会使用 `TodoWrite` 工具跟踪进度:

```
☐ 1. 环境检查与工具安装
☐ 2. 收集部署信息(源镜像、Harbor凭证)
☐ 3. 启动 Colima 运行时
☐ 4. 登录 Harbor 镜像仓库
☐ 5. 从源仓库拉取镜像
☐ 6. 为镜像打上 Harbor 标签
☐ 7. 推送镜像到 Harbor 仓库
☐ 8. 验证部署成功
☐ 9. 生成部署文档
```

每完成一步,技能会自动更新任务状态。

## 日志记录

所有操作会记录到:
```
~/.codex/skills/docker-image-deploy/deploy-history.log
```

日志格式:
```
[2026-02-13 03:17:00] 开始部署: verlai/verl:vllm012.latest
[2026-02-13 03:17:05] 环境检查完成
[2026-02-13 03:17:10] 登录 Harbor 成功
[2026-02-13 03:17:15] 开始拉取镜像 (37 层, 13.18 GB)
[2026-02-13 03:37:20] 镜像拉取完成
[2026-02-13 03:37:25] 开始推送到 Harbor
[2026-02-13 04:07:15] 推送完成
[2026-02-13 04:07:20] 部署验证成功
[2026-02-13 04:07:25] 部署文档已生成
```

## 扩展功能

### 批量部署

如需部署多个镜像,可创建镜像清单:

```yaml
# ./config/images.yaml
images:
  - source: verlai/verl:vllm012.latest
    platform: linux/amd64
    target: reg-ai.chehejia.com/raoyixi/verl:vllm012.latest

  - source: pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime
    platform: linux/amd64
    target: reg-ai.chehejia.com/raoyixi/pytorch:2.0.1
```

然后调用:
```bash
$docker-image-deploy --batch ./config/images.yaml
```

### 定时同步

使用 cron 定期同步镜像更新:

```bash
# 每天凌晨 2 点同步
0 2 * * * cd /path/to/skill && ./scripts/sync-images.sh
```

## 限制和注意事项

1. **磁盘空间**: 确保至少有镜像大小 3 倍的可用空间
2. **网络稳定性**: 大型镜像传输需要稳定的网络
3. **架构兼容性**: ARM Mac 拉取 AMD64 镜像需要额外时间
4. **Harbor 配额**: 注意个人空间的存储配额限制
5. **时间要求**: 10GB+ 镜像可能需要 1-2 小时完成部署

## 相关资源

- Colima 官方文档: https://github.com/abiosoft/colima
- Docker 官方文档: https://docs.docker.com
- Harbor 使用手册: 内部文档链接

## 技术支持

- 查看部署历史: `cat ~/.codex/skills/docker-image-deploy/deploy-history.log`
- 调试模式: 设置 `SKILL_DEBUG=1` 环境变量
- 问题反馈: 联系 DevOps 团队或创建工单
