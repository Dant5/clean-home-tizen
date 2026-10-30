// Q60B-only SDK control; only the named Home/startup and last-app preferences are writable.
// Retain root MIT licence and THIRD_PARTY_NOTICES.md with this separate helper.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using CleanHome.Native;
internal sealed class NativePlatform:IPlatform {
 const string Operation="http://tizen.org/appcontrol/operation/main";
 const string AutoKey="db/menu/smart_hub/ontvsetting/auto_start";
 [DllImport("libc")] static extern uint getuid();
 [DllImport("libc")] static extern void free(IntPtr value);
 [DllImport("libbundle.so.0")] static extern IntPtr bundle_create();
 [DllImport("libbundle.so.0")] static extern void bundle_free(IntPtr value);
 [DllImport("libaul.so.0")] static extern int aul_svc_set_operation(IntPtr bundle,string operation);
 [DllImport("libaul.so.0")] static extern int aul_get_default_app(IntPtr bundle,out IntPtr value);
 [DllImport("libvconf.so.0")] static extern IntPtr vconf_get_str(string key);
 [DllImport("libvconf.so.0")] static extern int vconf_get_int(string key,out int value);
 [DllImport("libvconf.so.0")] static extern int vconf_set_str(string key,string value);
 [DllImport("libvconf.so.0")] static extern int vconf_set_int(string key,int value);
 [DllImport("libcapi-appfw-app-operation-tv.so.0")] static extern int app_operation_set_current_app(string operation,string app);
 [DllImport("libapp-context-manager-common.so")] static extern byte util_is_appbooting_supported_webapp_byappid(string app);
 [DllImport("libcapi-appfw-app-manager.so.0")] static extern int app_manager_get_app_info(string app,out IntPtr info);
 [DllImport("libcapi-appfw-app-manager.so.0")] static extern int app_info_destroy(IntPtr info);
 public static void Guard() {
  if(IntPtr.Size!=4 || RuntimeInformation.ProcessArchitecture!=Architecture.Arm)throw new Exception("ARM32 required; no native settings called");
  if(getuid()!=901)throw new Exception("SDK UID 901 required; root is refused");
  if(!File.ReadLines("/etc/prd_info.ini").Any(x=>x=="Version=T-NKLBUABC-1720.7;"))throw new Exception("Exact Q60B firmware guard failed");
  foreach(var entry in new[]{new[]{"libcapi-appfw-app-operation-tv.so.0","app_operation_set_current_app"},new[]{"libvconf.so.0","vconf_set_str","vconf_set_int"},new[]{"libcapi-appfw-app-manager.so.0","app_manager_get_app_info","app_info_destroy"}}) {
   IntPtr library=NativeLibrary.Load(entry[0]);
   try {for(int index=1;index<entry.Length;index++)if(!NativeLibrary.TryGetExport(library,entry[index],out var address) || address==IntPtr.Zero)throw new Exception("Native compatibility export unavailable: "+entry[index]);}
   finally {NativeLibrary.Free(library);}
  }
 }
 static void Check(int code){if(code!=0)throw new Exception("Native return code "+code);}
 static string ReadString(string key) {
  IntPtr value=vconf_get_str(key);if(value==IntPtr.Zero)throw new Exception("Required setting unavailable: "+key);
  try{return Marshal.PtrToStringAnsi(value);}finally{free(value);}
 }
 public Snapshot Read() {
  IntPtr bundle=bundle_create();if(bundle==IntPtr.Zero)throw new Exception("Query bundle unavailable");
  string main;
  try {Check(aul_svc_set_operation(bundle,Operation));IntPtr value;Check(aul_get_default_app(bundle,out value));if(value==IntPtr.Zero)throw new Exception("Main operation unavailable");try{main=Marshal.PtrToStringAnsi(value);}finally{free(value);}}
  finally{bundle_free(bundle);}
  var strings=new Dictionary<string,string>();foreach(string key in Policy.Keys)strings[key]=ReadString(key);
  int auto;Check(vconf_get_int(AutoKey,out auto));return new Snapshot{Main=main,Strings=strings,AutoStart=auto};
 }
 public bool Eligible() {
  IntPtr info;int code=app_manager_get_app_info(Policy.Target,out info);
  try {return code==0 && info!=IntPtr.Zero && util_is_appbooting_supported_webapp_byappid(Policy.Target)==1;}
  finally{if(info!=IntPtr.Zero)Check(app_info_destroy(info));}
 }
 public void SetMain(string value){if(value!=Policy.Target && value!=Policy.Samsung)throw new Exception("Unsupported Home target");Check(app_operation_set_current_app(Operation,value));}
 public void SetString(string key,string value){if(Array.IndexOf(Policy.Keys,key)<0)throw new Exception("Setting outside Home scope");Check(vconf_set_str(key,value));}
 public static int ReadLastApp(){int value;Check(vconf_get_int(StartupOption.Key,out value));return value;}
 public static void SetLastApp(int value){if(value!=0 && value!=1)throw new Exception("Invalid last-app value");Check(vconf_set_int(StartupOption.Key,value));}
 public void SetAuto(int value){if(value!=0 && value!=1)throw new Exception("Invalid autostart");Check(vconf_set_int(AutoKey,value));}
}
internal sealed class NativeStartupOption:IStartupOption {
 public int Read()=>NativePlatform.ReadLastApp();
 public void Write(int value)=>NativePlatform.SetLastApp(value);
}
internal static class NativeControl {
 public static int Main(string[] args) {
  try {
   if((args.Length!=2 && args.Length!=3) || new FileInfo(args[1]).Length>8192)throw new Exception("Expected a scoped action and small baseline file");
   var original=JsonSerializer.Deserialize<Snapshot>(File.ReadAllText(args[1]));
   NativePlatform.Guard();
   using(var guard=new FileStream("/home/owner/share/tmp/sdk_tools/.cleanhome-native-control.lock",FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None)) {
    if(args[0]=="apply-all" || args[0]=="restore-all") {
     if(args.Length!=3 || (args[2]!="0" && args[2]!="1"))throw new Exception("Recorded Last App baseline required");
     var setup=SetupPolicy.Execute(new NativePlatform(),new NativeStartupOption(),original,int.Parse(args[2]),args[0]);
     Console.WriteLine(JsonSerializer.Serialize(setup));return setup.Success?0:1;
    }
    if(args[0]=="verify-option" || args[0]=="disable-last-app" || args[0]=="restore-last-app") {
     if(args.Length!=3 || (args[2]!="0" && args[2]!="1"))throw new Exception("Recorded last-app baseline required");
     Policy.Validate(original);
     if(args[0]=="disable-last-app") {
      var state=new NativePlatform().Read();
      if(state.Main!=Policy.Target || state.Strings[Policy.HomeKey]!=Policy.Target || state.AutoStart!=1)throw new Exception("Native Home and autorun must already be configured");
     }
     var option=StartupOption.Execute(new NativeStartupOption(),int.Parse(args[2]),args[0]);
     Console.WriteLine(JsonSerializer.Serialize(option));return option.Success?0:1;
    }
    if(args.Length!=2)throw new Exception("Unexpected extra argument");
    var result=Policy.Execute(new NativePlatform(),original,args[0]);
    Console.WriteLine(JsonSerializer.Serialize(result));return result.Success?0:1;
   }
  }catch(Exception error){Console.WriteLine(JsonSerializer.Serialize(new Result{Error=error.Message}));return 1;}
 }
}
