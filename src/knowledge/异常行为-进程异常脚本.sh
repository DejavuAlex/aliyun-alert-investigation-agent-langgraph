#!/usr/bin/env bash

MODULE_NAME="02_process_abnormal"
date=$(date +%Y%m%d-%H%M%S)
base="/tmp/Ashro_${date}_${MODULE_NAME}"

log_dir="$base/log"
danger_dir="$base/danger"
bin_dump_dir="$base/bin_dump"

mkdir -p "$log_dir" "$danger_dir" "$bin_dump_dir"

MODULE_LOG="${log_dir}/${MODULE_NAME}.log"
MODULE_DANGER="${danger_dir}/${MODULE_NAME}.danger"

echo "" > "$MODULE_LOG"
echo "" > "$MODULE_DANGER"

if [ "$(id -u)" != "0" ]; then
    echo "必须 root 才能执行"
    exit 1
fi

echo "************ 进程异常分析 ************" | tee -a "$MODULE_LOG"

echo "------------ 系统进程 ------------" | tee -a "$MODULE_LOG"
ps aux | tee -a "$MODULE_LOG"

echo "------------ CPU TOP5 ------------" | tee -a "$MODULE_LOG"
ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head -n 5 | tee -a "$MODULE_LOG"

echo "------------ 内存 TOP5 ------------" | tee -a "$MODULE_LOG"
ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%mem | head -n 5 | tee -a "$MODULE_LOG"

echo "------------ 反弹 shell 进程扫描 ------------" | tee -a "$MODULE_LOG"
shell_processes=$(ps aux | grep -E "nc|ncat|socat|bash -i|python -c|perl -e|curl|wget" | grep -v grep)
if [ -n "$shell_processes" ]; then
    echo "[!!!] 发现可疑反弹 shell:" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    echo "$shell_processes" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

echo "------------ 隐藏进程检查 ------------" | tee -a "$MODULE_LOG"
hidden=$(ps aux | awk '{if($8=="S"||$8=="D") print $0}')
if [ -n "$hidden" ]; then
    echo "[!!!] 发现隐藏进程：" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    echo "$hidden" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

echo "------------ 可疑可执行文件导出 ------------" | tee -a "$MODULE_LOG"
pids=$(pgrep -d ' ' -f .)
for pid in $pids; do
    exe=$(readlink -f /proc/$pid/exe 2>/dev/null)
    if [ -f "$exe" ]; then
        cp "$exe" "$bin_dump_dir/$(basename $exe)-$pid" 2>/dev/null
    fi
done

echo "[*] 可执行文件已导出到 $bin_dump_dir" | tee -a "$MODULE_LOG"

echo "检查结束！！！" | tee -a "$MODULE_LOG"

echo "日志输出路径:   $MODULE_LOG"
echo "危险项输出路径: $MODULE_DANGER"
echo "可疑可执行 dump 输出路径: $bin_dump_dir"
