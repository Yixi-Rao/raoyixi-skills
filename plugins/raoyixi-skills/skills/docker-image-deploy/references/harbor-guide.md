# Harbor 镜像仓库使用指南

## Harbor 简介

Harbor 是企业级私有 Docker 镜像仓库,提供镜像存储、管理、扫描和访问控制等功能。

## 仓库地址

**企业 Harbor 地址**: `reg-ai.chehejia.com`

## 认证方式

### LDAP 认证

Harbor 使用企业 LDAP 账号进行认证:
- **用户名**: 您的 LDAP 用户名
- **密码**: Harbor 专用密码 (不是 LDAP 登录密码)


### 获取 Harbor 密码

请通过以下方式获取 Harbor 专用密码:
1. 访问企业 IT 服务台
2. 提交 Harbor 访问权限申请
3. 获取分配的 Harbor 专用密码

## 个人镜像空间

### 空间规则

每个用户都有专属的镜像存储空间:

**个人空间路径**:
```
reg-ai.chehejia.com/<LDAP用户名>/
```

**示例**:
```
reg-ai.chehejia.com/raoyixi/pytorch:2.0.1
reg-ai.chehejia.com/raoyixi/verl:vllm012.latest
```

### 系统保留目录

**不要推送到以下目录**(系统保留):
```
reg-ai.chehejia.com/<LDAP用户名>/notebook/
```

此目录由系统自动管理,用户推送会被覆盖。

## 基本操作

### 1. 登录 Harbor

```bash
docker login reg-ai.chehejia.com -u <LDAP用户名>
```

输入 Harbor 专用密码后,显示:
```
Login Succeeded
```

### 2. 推送镜像

#### 步骤 1: 为镜像打标签

```bash
docker tag <本地镜像> reg-ai.chehejia.com/<用户名>/<镜像名>:<标签>
```

**示例**:
```bash
docker tag pytorch/pytorch:2.0.1 reg-ai.chehejia.com/raoyixi/pytorch:2.0.1
```

#### 步骤 2: 推送到 Harbor

```bash
docker push reg-ai.chehejia.com/<用户名>/<镜像名>:<标签>
```

**示例**:
```bash
docker push reg-ai.chehejia.com/raoyixi/pytorch:2.0.1
```

### 3. 拉取镜像

```bash
docker pull reg-ai.chehejia.com/<用户名>/<镜像名>:<标签>
```

**示例**:
```bash
docker pull reg-ai.chehejia.com/raoyixi/pytorch:2.0.1
```

### 4. 查看镜像列表

#### 通过 API 查看

```bash
curl -u <用户名>:<密码> \
  https://reg-ai.chehejia.com/v2/<用户名>/<镜像名>/tags/list
```

**示例响应**:
```json
{
  "name": "raoyixi/pytorch",
  "tags": ["2.0.1", "latest"]
}
```

#### 通过 Web 界面

访问: `https://reg-ai.chehejia.com`
1. 使用 LDAP 用户名和 Harbor 密码登录
2. 导航到"项目"→"个人项目"
3. 查看镜像列表和详情

## 镜像管理

### 镜像标签规范

推荐的标签命名规范:

1. **版本号标签**
   ```
   reg-ai.chehejia.com/raoyixi/pytorch:2.0.1
   reg-ai.chehejia.com/raoyixi/pytorch:2.0.1-cuda11.8
   ```

2. **日期标签**
   ```
   reg-ai.chehejia.com/raoyixi/myapp:2026-02-13
   ```

3. **Git 提交标签**
   ```
   reg-ai.chehejia.com/raoyixi/myapp:git-abc1234
   ```

4. **latest 标签**(谨慎使用)
   ```
   reg-ai.chehejia.com/raoyixi/myapp:latest
   ```

### 删除镜像

#### 通过 Web 界面删除

1. 登录 Harbor Web 界面
2. 导航到对应的镜像仓库
3. 选择要删除的标签
4. 点击"删除"按钮

#### 通过 API 删除

```bash
curl -X DELETE -u <用户名>:<密码> \
  https://reg-ai.chehejia.com/v2/<用户名>/<镜像名>/manifests/<标签>
```

**注意**: 删除操作不可逆,请谨慎操作。

### 镜像扫描

Harbor 支持自动扫描镜像漏洞:

1. 在 Web 界面中,导航到镜像详情页
2. 点击"扫描"按钮
3. 查看扫描结果,包括 CVE 漏洞列表
4. 根据严重程度评估是否需要更新镜像

## 配额管理

### 查看配额

在 Harbor Web 界面中:
1. 导航到"项目"→"个人项目"
2. 查看"存储配额"信息
3. 监控已用空间和剩余空间

### 配额限制

- 个人空间默认配额: 100 GB (具体以实际分配为准)
- 如需扩容,请联系 DevOps 团队提交申请

### 清理策略

当空间不足时,可以:

1. **删除不再使用的镜像**
2. **删除旧版本标签**
3. **使用镜像压缩**(在构建时优化镜像大小)
4. **申请配额扩容**

## 网络和访问

### 网络要求

- **企业内网**: Harbor 只能通过企业内网访问
- **VPN 连接**: 远程办公时,需连接企业 VPN
- **防火墙**: 确保防火墙允许访问 reg-ai.chehejia.com

### 访问控制

- **私有项目**: 个人空间默认为私有,只有本人可访问
- **共享项目**: 如需与团队共享,可申请创建团队项目
- **只读访问**: 可以为其他用户授予只读权限

## 在 LPAI 平台使用

### 配置镜像地址

在 LPAI 平台创建任务时:

1. 在"镜像配置"中选择"自定义镜像"
2. 填写 Harbor 镜像地址:
   ```
   reg-ai.chehejia.com/<用户名>/<镜像名>:<标签>
   ```
3. 如果镜像为私有,需配置镜像拉取凭证(ImagePullSecret)

### 配置镜像拉取凭证

```bash
# 创建 Secret
kubectl create secret docker-registry harbor-secret \
  --docker-server=reg-ai.chehejia.com \
  --docker-username=<LDAP用户名> \
  --docker-password=<Harbor密码> \
  --namespace=<命名空间>
```

在部署配置中引用:
```yaml
spec:
  imagePullSecrets:
    - name: harbor-secret
```

## 最佳实践

### 1. 镜像构建

- ✅ 使用多阶段构建减小镜像体积
- ✅ 清理构建缓存和临时文件
- ✅ 使用 .dockerignore 排除不必要的文件
- ✅ 选择合适的基础镜像(如 alpine)

### 2. 标签管理

- ✅ 为每个版本创建明确的标签
- ✅ 保留必要的历史版本
- ❌ 避免频繁更新 latest 标签
- ✅ 使用语义化版本号

### 3. 安全性

- ✅ 定期扫描镜像漏洞
- ✅ 及时更新基础镜像
- ❌ 不要在镜像中保存敏感信息(密码、密钥等)
- ✅ 使用多层安全机制

### 4. 性能优化

- ✅ 合理利用 Docker 层缓存
- ✅ 将不常变化的层放在前面
- ✅ 使用 .dockerignore 减少构建上下文
- ✅ 并行构建多个镜像

## 故障排查

### 问题 1: 登录失败

**错误信息**:
```
Error response from daemon: Get https://reg-ai.chehejia.com/v2/: unauthorized
```

**可能原因**:
1. 密码错误(使用了 LDAP 密码而非 Harbor 密码)
2. 账号未激活
3. 网络无法访问 Harbor

**解决方案**:
1. 确认使用 Harbor 专用密码
2. 检查 VPN 连接
3. 联系 IT 确认账号状态

### 问题 2: 推送超时

**错误信息**:
```
error pushing image: net/http: TLS handshake timeout
```

**可能原因**:
1. 网络不稳定
2. 镜像过大
3. Harbor 服务繁忙

**解决方案**:
1. 检查网络连接稳定性
2. 分批推送(如果镜像超大)
3. 在非高峰时段重试
4. 增加 Docker 客户端超时设置

### 问题 3: 配额超限

**错误信息**:
```
Error: quota exceeded
```

**解决方案**:
1. 删除不再使用的旧镜像
2. 压缩镜像大小
3. 申请配额扩容

### 问题 4: 镜像不存在

**错误信息**:
```
Error response from daemon: manifest for ... not found
```

**可能原因**:
1. 镜像名称或标签错误
2. 镜像已被删除
3. 没有访问权限

**解决方案**:
1. 确认镜像名称和标签正确
2. 通过 Web 界面或 API 查看镜像是否存在
3. 检查访问权限

## 技术支持

### 联系方式

- **DevOps 团队**: devops@example.com
- **IT 服务台**: it-support@example.com
- **紧急热线**: 内部分机 XXXX

### 相关文档

- Harbor 官方文档: https://goharbor.io/docs/
- Docker 官方文档: https://docs.docker.com/
- 企业内部 Wiki: (内部链接)

### 问题反馈

如遇到问题或有建议,请通过以下方式反馈:
1. 企业内部工单系统
2. DevOps 邮件列表
3. 内部技术论坛

---

**最后更新**: 2026-02-13
**文档版本**: v1.0
