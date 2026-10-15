#!/system/bin/sh
# Temporary diagnostic profile only. Bounded snapshots; never clear kernel logs.
output=/metadata/frogger-boot-state-v4.log
exec >"$output" 2>&1
printf 'BOOT_ID='
cat /proc/sys/kernel/random/boot_id
for delay in 0 10 20; do
    sleep "$delay"
    printf '\nUPTIME '
    cat /proc/uptime
    printf '\nMODULES\n'
    cat /proc/modules
    printf '\nAUDIO CARDS\n'
    cat /proc/asound/cards
    printf '\nMOUNTS\n'
    cat /proc/mounts
    printf '\nDSP REMOTEPROC\n'
    for node in /sys/class/remoteproc/remoteproc*; do
        printf '%s ' "$node"
        cat "$node/name" "$node/state"
    done
    printf '\nKERNEL TAIL (256 KiB maximum)\n'
    dmesg | tail -c 262144
    sync
 done
