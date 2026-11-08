import android.os.IBinder;
import android.os.Binder;
import android.hardware.lights.ILightsManager;
import android.hardware.lights.LightState;
import android.os.Parcel;
import android.os.ServiceManager;
public class FroggerGlyphVisibleTest {
 static void frame(IBinder extension, boolean enabled, int[] values) throws Exception {
  Parcel in=Parcel.obtain(), out=Parcel.obtain();
  try {
   in.writeInterfaceToken("vendor.hardware.light.ILightsExtension");
   in.writeInt(118); in.writeBoolean(enabled); in.writeIntArray(values); in.writeInt(enabled?512:0);
   if(!extension.transact(2,in,out,0)) throw new IllegalStateException("Unsupported frame transaction");
   out.readException();
  } finally {in.recycle();out.recycle();}
 }
 public static void main(String[] args) throws Exception {
  if(args.length == 1 && "--framework".equals(args[0])) {
   ILightsManager manager=ILightsManager.Stub.asInterface(ServiceManager.getServiceOrThrow("lights"));
   IBinder token=new Binder();
   int[] square=new int[169];
   for(int row=0;row<13;row++) for(int col=0;col<13;col++) square[row*13+col]=(row==6||col==6)?4080:0;
   manager.openSession(token,0);
   try {
    manager.setLightStates(token,new int[]{118},new LightState[]{new LightState.Builder().setFrameColors(square).build()});
    System.out.println("Framework cross enabled: 10 seconds");Thread.sleep(10000);
   } finally {manager.closeSession(token);System.out.println("Framework session closed; matrix off");}
   return;
  }
  IBinder extension=ServiceManager.getService("android.hardware.light.ILights/default").getExtension();
  if(!"vendor.hardware.light.ILightsExtension".equals(extension.getInterfaceDescriptor())) throw new IllegalStateException("Wrong extension");
  int[] trims={4,2,1,1,0,0,0,0,0,1,1,2,4};
  int[] values=new int[137]; int pos=0;
  for(int row=0;row<13;row++) for(int col=trims[row];col<13-trims[row];col++) values[pos++]=(row==6||col==6)?4080:0;
  try {frame(extension,true,values);System.out.println("Cross enabled: 10 seconds at 12-bit brightness 512");Thread.sleep(10000);}
  finally {frame(extension,false,new int[137]);System.out.println("Matrix off");}
 }
}
