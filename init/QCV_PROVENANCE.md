The SoC detection script `init.qti.qcv.sh` is retained byte-for-byte from the
user-provided C5.0-260902-1559 Android 17 stock vendor image. Its SHA-256 is
`e9fc94cd134eeb03ba59827f097afbde883a4753c19cbdac3d53e15092a19f12`.
The independently verified Evolution X reference vendor contains identical bytes.

The connected FroggerPro reports SoC ID 659 and machine KERA. The script maps
that ID to `ro.vendor.qti.soc_name=kera`. The boot configuration selects the same
KERA vendor manifest before HAL startup. `sun` is the shared build platform,
but is not this device's vendor SKU.
