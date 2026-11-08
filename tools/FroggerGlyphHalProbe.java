import android.os.IBinder;
import android.os.Parcel;
import android.os.ServiceManager;

/** Direct OEM HAL probe; independent of optional framework Matrix APIs. */
public final class FroggerGlyphHalProbe {
    private static void frame(IBinder extension, boolean enabled, int[] values) throws Exception {
        Parcel in = Parcel.obtain();
        Parcel out = Parcel.obtain();
        try {
            in.writeInterfaceToken("vendor.hardware.light.ILightsExtension");
            in.writeInt(118);
            in.writeBoolean(enabled);
            in.writeIntArray(values);
            in.writeInt(enabled ? 512 : 0);
            if (!extension.transact(2, in, out, 0)) {
                throw new IllegalStateException("Unsupported Matrix frame transaction");
            }
            out.readException();
        } finally {
            in.recycle();
            out.recycle();
        }
    }

    public static void main(String[] args) throws Exception {
        IBinder lights = ServiceManager.getServiceOrThrow("android.hardware.light.ILights/default");
        IBinder extension = lights.getExtension();
        if (extension == null || !"vendor.hardware.light.ILightsExtension".equals(
                extension.getInterfaceDescriptor())) {
            throw new IllegalStateException("OEM Matrix extension unavailable");
        }
        int[] trims = {4, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 2, 4};
        int[] values = new int[137];
        int position = 0;
        for (int row = 0; row < 13; row++) {
            for (int col = trims[row]; col < 13 - trims[row]; col++) {
                values[position++] = row == 6 || col == 6 ? 4080 : 0;
            }
        }
        try {
            frame(extension, true, values);
            System.out.println("Matrix cross enabled for 10 seconds at 512/4095 brightness");
            Thread.sleep(10000);
        } finally {
            frame(extension, false, new int[137]);
            System.out.println("Matrix off");
        }
    }
}
