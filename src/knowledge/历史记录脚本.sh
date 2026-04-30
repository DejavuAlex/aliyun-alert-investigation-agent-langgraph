#!/usr/bin/env bash

MODULE_NAME="02_history"
date=$(date +%Y%m%d-%H%M%S)
base="/tmp/Ashro_${date}_${MODULE_NAME}"

log_dir="$base/log"
danger_dir="$base/danger"

mkdir -p "$log_dir" "$danger_dir"

MODULE_LOG="${log_dir}/${MODULE_NAME}.log"
MODULE_DANGER="${danger_dir}/${MODULE_NAME}.danger"

echo "" > "$MODULE_LOG"
echo "" > "$MODULE_DANGER"

echo "------------ 历史命令检查 --------------" | tee -a "$MODULE_LOG"

history_file="/root/.bash_history"

if [ -s "$history_file" ]; then
    cat "$history_file" | tee -a "$MODULE_LOG"
else
    echo "[!!!] 未发现历史命令，可能已被清除" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

echo "检查结束！！！" | tee -a "$MODULE_LOG"
