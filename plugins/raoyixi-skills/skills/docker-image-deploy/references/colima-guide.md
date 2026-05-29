# 镜像管理工具 --- Colima

**作者：** 王旭\
**更新时间：** 2025年7月31日

------------------------------------------------------------------------

## 📦 Colima 介绍

**Colima（Container On Linux Is Made Accessible）**
是一个开源的容器运行环境，用于在 **macOS 和 Linux** 上高效运行容器和
Kubernetes。

它的目标是提供一种轻量级、快速和跨平台的替代方案，以替代 **Docker
Desktop** 或类似工具。

------------------------------------------------------------------------

# 使用指南

在初始启动时，Colima 默认使用指定的 Docker runtime 启动。\
因此系统首先需要安装 Docker。

``` bash
brew install docker
```

------------------------------------------------------------------------

# 安装启动

## 🖥 MAC OS

使用 Homebrew 安装：

``` bash
brew install colima
```

------------------------------------------------------------------------

## 🐧 Arch Linux

安装依赖：

``` bash
sudo pacman -S qemu-base go docker
```

安装 Lima 和 Colima：

``` bash
yay -S lima-bin colima-bin
```

------------------------------------------------------------------------

## 📦 Binary 安装

下载并安装：

``` bash
# 下载 binary
curl -LO https://github.com/abiosoft/colima/releases/latest/download/colima-$(uname)-$(uname -m)

# 安装到 PATH
sudo install colima-$(uname)-$(uname -m) /usr/local/bin/colima
```

------------------------------------------------------------------------

# 🚀 使用

## 启动 Colima

``` bash
colima start
```

启动完成后，原 Docker 命令可以继续使用。

------------------------------------------------------------------------

# 🏗 使用跨架构构建（需要 docker-buildx）

## 安装 buildx

``` bash
brew install docker-buildx
```

------------------------------------------------------------------------

## 构建镜像（与本机系统一致）

``` bash
docker build -t reg-ai.chehejia.com/notebook/xxx:tag .
```

------------------------------------------------------------------------

## 跨架构构建

``` bash
docker-buildx build -t reg-ai.chehejia.com/notebook/xxx:tag --platform=linux/amd64 .
```

------------------------------------------------------------------------

# 常见问题

如果出现以下报错：

``` bash
$ docker ps
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

解决方式：

``` bash
colima start
```

示例输出：

``` text
INFO[0000] using docker runtime
INFO[0000] starting colima
INFO[0019] provisioning ...                context=vm
INFO[0020] starting ...                    context=docker
INFO[0021] done
```

然后再次执行：

``` bash
docker ps
```

------------------------------------------------------------------------

# ⚠️ 注意事项

-   如果之前安装过 **Docker Desktop**
-   卸载后可能会遗留证书或配置残留
-   可能导致 Docker 运行异常
-   建议清理相关残留配置
