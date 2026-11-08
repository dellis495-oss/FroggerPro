# FroggerPro audio integration

The KERA DSP calibration and firmware require the preserved C5.0-260902-1559 audio core. The newer source PAL/AGM/GSL set links but fails DSP graph configuration on this phone. `stock-audio-core.json` pins the complete nine-library set; do not substitute only PAL or GSL.

BoardConfig enables `froggerpro.stock_audio_core` for this product. Preferred canonical prebuilts live under `hardware/qcom-caf/sm8750/audio/frogger-audio-prebuilts`; source modules retain ownership for other products. Raw blobs are EXTRACT_ONLY entries, and extract-files.py generates filegroups with exact hash checks. Keep ELF validation enabled. Source header-provider additions preserve client compilation.

The active KERA mixer is copied from sku_sun/mixer_paths_kera_qrd.xml. Its speaker path selects Music and enables both Awinic amplifiers. Both the matched core and this route were needed for the audible hardware tone test.

Bluetooth also requires three independent pieces: ttyHS0 ownership bluetooth:net_bt 0660 in ueventd, enabled classic profiles in vendor properties, and the branch-native software audio module registered as IModule/bluetooth with its V4 VINTF declaration. Adapter ON or successful pairing does not prove audio works.

The stock voice SDK and its two consumers use private libtensorflowlite_c_nothing.so because they require versioned XNNPACK exports absent from the platform TensorFlow ABI. Extraction renames the dependency and SONAME without replacing the platform library. No undefined-symbol bypass is needed for libVoiceSdk.

Build with the safe wrapper and working kernel profile. vendorimage runs the staged inventory gate and extracts the actual EROFS image for a second audit. Validate matching AVB descriptors and rollback backups before flashing. Runtime overlays and property changes are development tests; the result is reproducible only after the built image boots and passes phone speaker, Bluetooth media, microphone/call and restart tests.

Confirmed routing correction: primary must not advertise the three A2DP output devices when the software Bluetooth module owns them. Removing those duplicate ports/routes changed the device from connected-but-silent to user-confirmed audible Bluetooth media. This correction is included in the pending true clean OTA rebuild. SCO stays in primary.
