# Kubernetes 部署指南

本目录包含了 MCP SQL Vector DB 项目的 Kubernetes 部署配置文件。

## 目录结构

```
deploy/
├── README.md          # 本文件
├── myscale.yaml       # MyScale 向量数据库部署
├── pgvector.yaml      # PgVector 向量数据库部署
├── mcp-server.yaml    # MCP Server 服务部署
└── dify.yaml          # Dify AI 应用部署
```

## 组件说明

### 1. MyScale (myscale.yaml)
- **用途**: 基于 ClickHouse 的向量数据库
- **镜像**: `origin-hub-ai-registry.cn-shanghai.cr.aliyuncs.com/component/mqdb:24.8.8.1-61d35943-release`
- **端口**: 8123 (HTTP), 9000 (Native)
- **存储**: 20Gi PVC

### 2. PgVector (pgvector.yaml)
- **用途**: PostgreSQL + pgvector 扩展的向量数据库
- **镜像**: `pgvector/pgvector:pg16`
- **端口**: 5432
- **存储**: 10Gi PVC
- **特性**: 包含初始化脚本，自动创建示例表和索引

### 3. MCP Server (mcp-server.yaml)
- **用途**: Model Context Protocol 服务器
- **镜像**: `origin-hub-ai-registry.cn-shanghai.cr.aliyuncs.com/component/mcp-sqlvectordb:0.0.1`
- **端口**: 4200
- **副本数**: 2
- **健康检查**: `/health` 端点

### 4. Dify (dify.yaml)
- **用途**: AI 应用开发平台
- **镜像**: `langgenius/dify-api:0.6.13`, `langgenius/dify-web:0.6.13`
- **组件**:
  - dify-postgres: PostgreSQL 数据库
  - dify-redis: Redis 缓存
  - dify-api: API 服务 (2 副本)
  - dify-worker: 后台任务处理 (2 副本)
  - dify-web: Web 前端 (2 副本)
  - dify-nginx: 反向代理 (2 副本)

## 部署步骤

### 前置要求

1. 一个运行中的 Kubernetes 集群 (v1.19+)
2. 配置好的 `kubectl` 命令行工具
3. 集群中已安装 StorageClass (默认使用 `standard`)
4. (可选) 安装了 cert-manager 用于自动 TLS 证书管理
5. (可选) 安装了 Nginx Ingress Controller

### 1. 创建命名空间

所有服务都部署在 `mcp-system` 命名空间中：

```bash
kubectl create namespace mcp-system
```

### 2. 部署数据库服务

首先部署数据库服务，因为其他服务依赖它们：

```bash
# 部署 MyScale
kubectl apply -f myscale.yaml

# 部署 PgVector
kubectl apply -f pgvector.yaml
```

等待数据库服务就绪：

```bash
kubectl wait --for=condition=ready pod -l app=myscale -n mcp-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=pgvector -n mcp-system --timeout=300s
```

### 3. 部署 MCP Server

```bash
kubectl apply -f mcp-server.yaml
```

等待 MCP Server 就绪：

```bash
kubectl wait --for=condition=ready pod -l app=mcp-server -n mcp-system --timeout=120s
```

### 4. 部署 Dify

```bash
kubectl apply -f dify.yaml
```

等待所有 Dify 组件就绪：

```bash
kubectl wait --for=condition=ready pod -l app=dify-postgres -n mcp-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=dify-redis -n mcp-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=dify-api -n mcp-system --timeout=180s
kubectl wait --for=condition=ready pod -l app=dify-web -n mcp-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=dify-nginx -n mcp-system --timeout=120s
```

## 验证部署

### 检查所有 Pod 状态

```bash
kubectl get pods -n mcp-system
```

预期输出应该显示所有 Pod 都处于 `Running` 状态。

### 检查服务

```bash
kubectl get svc -n mcp-system
```

### 测试 MCP Server

```bash
# 端口转发
kubectl port-forward svc/mcp-server 4200:4200 -n mcp-system

# 在另一个终端测试健康检查
curl http://localhost:4200/health
```

### 测试 Dify

```bash
# 端口转发
kubectl port-forward svc/dify-nginx 8080:80 -n mcp-system

# 在浏览器中访问
# http://localhost:8080
```

## 配置 Ingress

### MCP Server Ingress

编辑 `mcp-server.yaml` 中的 Ingress 配置：

```yaml
spec:
  tls:
  - hosts:
    - mcp-server.yourdomain.com  # 修改为你的域名
    secretName: mcp-server-tls
  rules:
  - host: mcp-server.yourdomain.com  # 修改为你的域名
```

### Dify Ingress

编辑 `dify.yaml` 中的 Ingress 配置和环境变量：

```yaml
# 在 dify-config ConfigMap 中更新
NEXT_PUBLIC_PUBLIC_API_URL: "https://dify.yourdomain.com"  # 修改为你的域名

# 在 Ingress 中更新
spec:
  tls:
  - hosts:
    - dify.yourdomain.com  # 修改为你的域名
```

重新应用配置：

```bash
kubectl apply -f mcp-server.yaml
kubectl apply -f dify.yaml
```

## 持久化存储

所有服务都使用 PersistentVolumeClaim (PVC) 来持久化数据：

- **myscale-data-pvc**: 20Gi
- **pgvector-data-pvc**: 10Gi
- **dify-postgres-pvc**: 5Gi
- **dify-redis-pvc**: 2Gi
- **dify-storage-pvc**: 10Gi

### 查看 PVC

```bash
kubectl get pvc -n mcp-system
```

### 修改存储大小

如果需要更大的存储空间，编辑对应的 yaml 文件中的存储请求：

```yaml
spec:
  resources:
    requests:
      storage: 50Gi  # 修改为所需大小
```

## 资源配额

### 当前配置

| 服务 | CPU 请求 | CPU 限制 | 内存请求 | 内存限制 |
|------|----------|----------|----------|----------|
| MyScale | 1000m | 2000m | 2Gi | 4Gi |
| PgVector | 500m | 1000m | 1Gi | 2Gi |
| MCP Server | 200m | 500m | 256Mi | 512Mi |
| Dify API | 250m | 1000m | 512Mi | 2Gi |
| Dify Worker | 250m | 1000m | 512Mi | 2Gi |
| Dify Web | 100m | 500m | 256Mi | 512Mi |
| Dify Nginx | 100m | 200m | 128Mi | 256Mi |

### 调整资源

根据实际负载，可以在各个 Deployment 中调整资源配额：

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

## 扩容

### 水平扩容

```bash
# 扩展 MCP Server
kubectl scale deployment mcp-server --replicas=5 -n mcp-system

# 扩展 Dify API
kubectl scale deployment dify-api --replicas=4 -n mcp-system
```

### 自动扩容 (HPA)

创建 HorizontalPodAutoscaler：

```bash
# MCP Server 自动扩容
kubectl autoscale deployment mcp-server \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n mcp-system

# Dify API 自动扩容
kubectl autoscale deployment dify-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n mcp-system
```

## 监控和日志

### 查看日志

```bash
# MCP Server 日志
kubectl logs -f deployment/mcp-server -n mcp-system

# Dify API 日志
kubectl logs -f deployment/dify-api -n mcp-system

# MyScale 日志
kubectl logs -f deployment/myscale -n mcp-system
```

### 查看事件

```bash
kubectl get events -n mcp-system --sort-by='.lastTimestamp'
```

## 备份和恢复

### 备份数据库

```bash
# 备份 PgVector
kubectl exec -it deployment/pgvector -n mcp-system -- \
  pg_dump -U postgres vectordb > pgvector_backup.sql

# 备份 Dify PostgreSQL
kubectl exec -it deployment/dify-postgres -n mcp-system -- \
  pg_dump -U postgres dify > dify_backup.sql
```

### 恢复数据库

```bash
# 恢复 PgVector
cat pgvector_backup.sql | kubectl exec -i deployment/pgvector -n mcp-system -- \
  psql -U postgres vectordb

# 恢复 Dify PostgreSQL
cat dify_backup.sql | kubectl exec -i deployment/dify-postgres -n mcp-system -- \
  psql -U postgres dify
```

## 清理

### 删除所有部署

```bash
kubectl delete -f dify.yaml
kubectl delete -f mcp-server.yaml
kubectl delete -f pgvector.yaml
kubectl delete -f myscale.yaml
```

### 删除命名空间 (会删除所有资源，包括 PVC)

```bash
kubectl delete namespace mcp-system
```

⚠️ **警告**: 删除 PVC 会永久删除所有数据！

## 故障排查

### Pod 无法启动

```bash
# 查看 Pod 详情
kubectl describe pod <pod-name> -n mcp-system

# 查看 Pod 日志
kubectl logs <pod-name> -n mcp-system
```

### 服务连接问题

```bash
# 测试服务连接
kubectl run -it --rm debug --image=busybox --restart=Never -n mcp-system -- sh

# 在 debug pod 中测试
nc -zv myscale.mcp-system.svc.cluster.local 8123
nc -zv pgvector.mcp-system.svc.cluster.local 5432
nc -zv mcp-server.mcp-system.svc.cluster.local 4200
```

### PVC 挂载问题

```bash
# 检查 PVC 状态
kubectl get pvc -n mcp-system

# 检查 StorageClass
kubectl get storageclass
```

## 安全建议

1. **修改默认密码**: 在生产环境中，务必修改所有默认密码
2. **使用 Secrets**: 将敏感信息从 ConfigMap 迁移到 Secrets
3. **网络策略**: 配置 NetworkPolicy 限制 Pod 之间的通信
4. **TLS 加密**: 为所有服务启用 TLS
5. **RBAC**: 配置适当的角色和权限

### 示例: 创建 Secret

```bash
# 创建 PgVector 密码 Secret
kubectl create secret generic pgvector-secret \
  --from-literal=password=your-strong-password \
  -n mcp-system

# 在 Deployment 中使用
env:
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: pgvector-secret
      key: password
```

## 性能优化

1. **数据库连接池**: 配置适当的连接池大小
2. **缓存策略**: 利用 Redis 缓存频繁访问的数据
3. **索引优化**: 为常用查询创建合适的索引
4. **资源限制**: 根据实际负载调整资源配额
5. **水平扩展**: 使用 HPA 自动扩展服务

## 更新策略

所有 Deployment 默认使用 RollingUpdate 策略：

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

这确保了零停机时间的更新。

## 支持

如有问题，请：
1. 检查日志和事件
2. 参考故障排查部分
3. 提交 Issue 到项目仓库

## 许可证

请参考项目根目录的 LICENSE 文件。

