## Current CP2A validation status (2026-10-20)

The current framework does not expose `LightState.Builder.setFrameColors` or
`LightState.getFrameColors`. The framework-bridge results below describe the
previous working build; they do not verify this source tree. Use the standalone
`FroggerGlyphHalProbe.java` for the direct OEM HAL test on this tree. It uses the
same verified light 118 transaction, geometry, brightness, and finally-off cleanup.
The framework Matrix API/bridge still needs restoration and runtime verification.

The source-built `leds-aw20144` module is now included in vendor `modules.load`.
Confirm the actual module, Matrix sysfs node, HAL transaction, and visible output
after installing the updated OTA before claiming the hardware works.

# Glyph Matrix hardware probe

The phone must be running Android with root ADB; the existing vendor lights HAL
must expose vendor.hardware.light.ILightsExtension. This probe does not replace
the ROM framework. It draws a cross on light 118 for ten seconds at 512/4095 HAL
brightness, maps the circular 13x13 grid to 137 channels, and switches off in a
finally block. It was visibly confirmed on the reference-kernel Android session.
Watch the rear Matrix before invoking it.

From the Lineage root, after framework tools are built:

```sh
mkdir -p /tmp/frogger-glyph-visible/classes /tmp/frogger-glyph-visible/dex
javac -cp out/soong/.intermediates/frameworks/base/framework-minus-apex/android_common/combined/framework.jar -d /tmp/frogger-glyph-visible/classes device/nothing/FroggerPro/tools/FroggerGlyphVisibleTest.java
out/host/linux-x86/bin/d8 --output /tmp/frogger-glyph-visible/dex /tmp/frogger-glyph-visible/classes/FroggerGlyphVisibleTest.class
adb -s 003383663003343 push /tmp/frogger-glyph-visible/dex/classes.dex /data/local/tmp/frogger-glyph-visible.dex
adb -s 003383663003343 shell 'CLASSPATH=/data/local/tmp/frogger-glyph-visible.dex app_process /system/bin FroggerGlyphVisibleTest'
```

The framework bridge defaults to 20% brightness, converted to 819/4095 for the
HAL. persist.sys.glyph.brightness selects a percentage from 0 to 100. This is
separate from Nothing OS's Glyph Toy service; that service and third-party toy
compatibility still need implementation and validation.

The same compiled probe supports `--framework`: it opens a lights service session, sends a 169-channel LightState through the framework bridge, waits ten seconds, then closes the session. This completed successfully on the /e/OS session. Camera and direct-HAL visible Glyph cross were user-confirmed Oct15. Matrix sysfs permissions must be installed from init.froggerpro.glyph.rc; permissive SELinux does not override DAC.
