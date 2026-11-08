# FroggerPro Android 17 update

This update tracks the current FroggerPro device-tree source.
It is a source update. A complete build also needs the matching Android source
and locally extracted vendor and kernel inputs.

- Face enrollment passed on the rebuilt handset. The Settings overlay gives
  the face HAL camera ownership, and the device policy grants graphics access.
- eSIM LTE reconnected after reboot with the corrected 2G-only restriction.
  The telephony patch preserves user and carrier restrictions on LTE and NR.
- The SystemUI patch bounds-checks the slot index when rendering carrier text.
- The init and extraction changes retain the modem setup and QCRIL policy fixes.

Apply the two framework patches from the root of their respective Git projects.
The device configuration already selects the face overlay and the stock LTE/NR default.

Build from the Android root with source build/envsetup.sh, then breakfast
FroggerPro user and brunch FroggerPro user. Use m target-files-package for
the release signing input. Release keys and extracted proprietary files are
local inputs.
