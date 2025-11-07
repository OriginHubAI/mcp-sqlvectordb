#!/bin/bash

NAMESPACE="mcp-sqlvdb"

echo "开始删除 Evicted/异常 Pod..."

# 循环删除状态为 Evicted 或 ContainerStatusUnknown 的 Pod
for pod in $(kubectl get pod -n $NAMESPACE --no-headers | awk '$3=="Evicted" || $3=="ContainerStatusUnknown" {print $1}'); do
    echo "删除 Pod: $pod"
    kubectl delete pod $pod -n $NAMESPACE
done

echo "删除完成。"

