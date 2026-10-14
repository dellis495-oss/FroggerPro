libcamera_metadata.so was retrieved from the working phone's vendor overlay on
2026-10-12. It is byte-for-byte identical to the CP2A-built
out/target/product/FroggerPro/system/lib64/libcamera_metadata.so.
SHA-256: f3e2723a2d6fd16d180694d29c5628128bc393a909c99c92990d992ab049587c
The vendor library's SONAME is libcamera_metadata.so. ELF dependencies are
liblog.so, libc++.so, libc.so, libm.so and libdl.so. The prebuilt module preserves
its working vendor placement. Recheck compatibility when updating platform
camera metadata; do not replace this with an arbitrary stock-version library.
