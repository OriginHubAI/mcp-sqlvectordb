# Kubernetes 部署指南

本目录包含了 MCP SQL Vector DB 项目的 Kubernetes 部署配置文件。

## 目录结构

```
deploy/
├── README.md          # 本文件
├── myscale.yaml       # MyScale 向量数据库部署
└── mcp-server.yaml    # MCP Server 服务部署
```

## 组件说明

### 1. MyScale (myscale.yaml)
- **用途**: 基于 ClickHouse 的向量数据库
- **镜像**: `origin-hub-ai-registry.cn-shanghai.cr.aliyuncs.com/component/mqdb:24.8.8.1-61d35943-release`
- **端口**: 8123 (HTTP), 9000 (Native)
- **存储**: 20Gi PVC


### 3. MCP Server (mcp-server.yaml)
- **用途**: Model Context Protocol 服务器
- **镜像**: `origin-hub-ai-registry.cn-shanghai.cr.aliyuncs.com/component/mcp-sqlvectordb:0.0.6`
- **端口**: 4200
- **副本数**: 2
- **健康检查**: `/health` 端点

## 部署步骤

### 前置要求

1. 一个运行中的 Kubernetes 集群 (v1.19+)
2. 配置好的 `kubectl` 命令行工具

### 1. 创建命名空间

所有服务都部署在 `mcp-sqlvdb` 命名空间中：

```bash
kubectl create namespace mcp-sqlvdb
```
### 2. 创建配置文件 configmap

TextToVectrorSql 需要使用 Api 访问，我们需要将一些敏感信息配置到 config map 中

```bash
kubectl apply -f secrets.yaml
```

### 2. 部署数据库服务

首先部署数据库服务，因为其他服务依赖它们：

```bash
# 部署 MyScale
kubectl apply -f myscale.yaml
```

等待数据库服务就绪

### 3. 部署 MCP Server

```bash
kubectl apply -f mcp-server.yaml
```

## 验证部署

### 测试 MCP Server

```bash
# 查看 Mcp server ip 信息
kubectl get svc -n mcp-sqlvdb

# 检测 Mcp server 是否可用
curl http://x.x.x.x:4200/health
```

验证 Mcp Server 可用之后，即可在 dify 中注册 mcp 服务，注册地址为：`http://x.x.x.x:4200/mcp`