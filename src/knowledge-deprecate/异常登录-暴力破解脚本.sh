#!/usr/bin/env bash

MODULE_NAME="01_bruteforce"
date=$(date +%Y%m%d-%H%M%S)
base="/tmp/Ashro_${date}_${MODULE_NAME}"

log_dir="$base/log"
danger_dir="$base/danger"

mkdir -p "$log_dir" "$danger_dir"

MODULE_LOG="${log_dir}/${MODULE_NAME}.log"
MODULE_DANGER="${danger_dir}/${MODULE_NAME}.danger"

echo "" > "$MODULE_LOG"
echo "" > "$MODULE_DANGER"

echo "------------ 暴力破解攻击检测 --------------" | tee -a "$MODULE_LOG"

check_bruteforce() {
    title="$1"
    content="$2"
    [[ -z "$content" ]] && return

    echo "[!!!] SSH 暴力破解 ($title)" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"

    echo "$content" | awk '
        /Failed password/ {
            user=$9
            ip=$(NF-3)
            key=user"@"ip
            count[key]++
        }
        END {
            for (k in count) {
                print "用户/IP: " k ", 次数: " count[k]
            }
        }
    ' | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
}

[[ -f /var/log/auth.log ]] && check_bruteforce "auth.log" "$(grep -a 'Failed password' /var/log/auth.log)"
[[ -f /var/log/secure   ]] && check_bruteforce "secure" "$(grep -a 'Failed password' /var/log/secure)"

journal_failed=$(journalctl -u ssh -u sshd --since "24 hours ago" 2>/dev/null | grep 'Failed password')
check_bruteforce "journalctl" "$journal_failed"

echo "检查结束！！！" | tee -a "$MODULE_LOG"
