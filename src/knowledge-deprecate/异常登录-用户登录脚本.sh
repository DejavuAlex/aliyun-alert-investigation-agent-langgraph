#!/usr/bin/env bash

MODULE_NAME="03_general"
date=$(date +%Y%m%d-%H%M%S)
base="/tmp/Ashro_${date}_${MODULE_NAME}"

log_dir="$base/log"
danger_dir="$base/danger"

mkdir -p "$log_dir" "$danger_dir"

MODULE_LOG="${log_dir}/${MODULE_NAME}.log"
MODULE_DANGER="${danger_dir}/${MODULE_NAME}.danger"

echo "" > "$MODULE_LOG"
echo "" > "$MODULE_DANGER"

echo "************ 用户与密码安全 ************" | tee -a "$MODULE_LOG"

echo "------------ 登录用户 ------------" | tee -a "$MODULE_LOG"
who | tee -a "$MODULE_LOG"

echo "------------ passwd 信息 ------------" | tee -a "$MODULE_LOG"
cat /etc/passwd | tee -a "$MODULE_LOG"

# 检查超级用户
echo "------------ 检查超级用户 --------------" | tee -a "$MODULE_LOG"
Superuser=$(awk -F: '$3 == 0 && $1 != "root" { print $1 }' /etc/passwd)
if [ -n "$Superuser" ]; then
    echo "[!!!] 除 root 外发现 UID=0 用户:" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    echo "$Superuser" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

# 检查空口令账户
echo "------------ 空口令账户 --------------" | tee -a "$MODULE_LOG"
empty_password_accounts=$(awk -F: '($2 == "") {print $1}' /etc/shadow)
if [ -n "$empty_password_accounts" ]; then
    echo "[!!!] 发现空口令账户:" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    echo "$empty_password_accounts" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

# 检查 sudo NOPASSWD
echo "------------ 检查 sudo NOPASSWD --------------" | tee -a "$MODULE_LOG"
sudoers_users=$(visudo -c 2>&1 | grep -E '^[^#]*[[:space:]]ALL=.*NOPASSWD' | awk '{print $1}')
if [ -n "$sudoers_users" ]; then
    echo "[!!!] 存在免密 sudo 用户:" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    echo "$sudoers_users" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
fi

# 检查 SSH 公钥登录
echo "------------ 检查 SSH 公钥登录 --------------" | tee -a "$MODULE_LOG"
home_dirs=$(getent passwd | cut -d: -f6)
for dir in $home_dirs; do
    if [ -f "$dir/.ssh/authorized_keys" ]; then
        echo "[!!!] 用户目录 $dir 存在 authorized_keys：" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
        cat "$dir/.ssh/authorized_keys" | tee -a "$MODULE_LOG" | tee -a "$MODULE_DANGER"
    fi
done

echo "检查结束！！！" | tee -a "$MODULE_LOG"
