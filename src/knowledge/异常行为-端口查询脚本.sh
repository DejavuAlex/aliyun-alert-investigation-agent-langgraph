#!/usr/bin/env bash

MODULE_NAME="01_port_connection"
date=$(date +%Y%m%d-%H%M%S)
base="/tmp/Ashro_${date}_${MODULE_NAME}"

log_dir="$base/log"
danger_dir="$base/danger"

mkdir -p "$log_dir" "$danger_dir"

MODULE_LOG="${log_dir}/${MODULE_NAME}.log"
MODULE_DANGER="${danger_dir}/${MODULE_NAME}.danger"

echo "" > "$MODULE_LOG"
echo "" > "$MODULE_DANGER"

if [ "$(id -u)" != "0" ]; then
    echo "必须 root 才能执行"
    exit 1
fi

echo "************ 端口 & 连接 ************" | tee -a "$MODULE_LOG"

echo "------------ 监听端口 --------------" | tee -a "$MODULE_LOG"
listening_ports=$(netstat -tuln | awk 'NR>2{print $4}' | awk -F':' '{print $NF}' | sort -u)
echo "$listening_ports" | tee -a "$MODULE_LOG"

echo "------------ 已建立连接 --------------" | tee -a "$MODULE_LOG"
est=$(netstat -tun | grep ESTABLISHED)
if [ -n "$est" ]; then
    echo "[!!!] 存在已建立连接：" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    echo "$est" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

echo "检查结束！！！" | tee -a "$MODULE_LOG"

echo "日志输出路径:   $MODULE_LOG"
echo "危险项输出路径: $MODULE_DANGER"
