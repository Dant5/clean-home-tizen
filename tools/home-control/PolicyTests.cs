using System;
using System.Collections.Generic;
using CleanHome.Native;
internal sealed class Fake:IPlatform {
 public Snapshot State; public bool IsEligible=true,Derive=true,FailRollback=false,SilentMismatch=false;
 public int Writes=0,FailAt=0;
 public Fake(Snapshot state){State=state.Copy();}
 public Snapshot Read()=>State.Copy();public bool Eligible()=>IsEligible;
 void Tick(){Writes++;if(FailAt==Writes || (FailRollback && Writes>=FailAt))throw new Exception("Injected native failure");}
 public void SetMain(string app){State.Main=app;if(Derive){State.Strings[Policy.HomeKey]=app;State.Strings["db/appfw/startup_appid"]=app;State.Strings[Policy.FirstScreen]=app;}Tick();}
 public void SetString(string key,string value){if(!SilentMismatch)State.Strings[key]=value;Tick();}
 public void SetAuto(int value){State.AutoStart=value;if(Derive && value==1)State.Strings["db/appfw/startup_appid"]=State.Main;Tick();}
}
internal sealed class FakeOption:IStartupOption {
 public int Value,Writes;public bool Fail,Silent,FailRollback;
 public int Read()=>Value;
 public void Write(int value){Writes++;if(!Silent)Value=value;if(Fail && (Writes==1 || FailRollback))throw new Exception("Injected option failure");}
}
internal static class Tests {
 static int passed=0;
 static Snapshot Original(int auto=0)=>new Snapshot{Main=Policy.Samsung,AutoStart=auto,Strings=new Dictionary<string,string>{{Policy.HomeKey,Policy.Samsung},{"db/appfw/startup_appid","org.tizen.tv-viewer"},{"db/appfw/booting_appid_backup",Policy.Target},{Policy.FirstScreen,Policy.Samsung}}};
 static void Assert(bool value){if(!value)throw new Exception("Assertion failed");}
 static void Run(string label,Action action){try{action();passed++;}catch(Exception error){throw new Exception(label+": "+error.Message);}}
 static void Refused(Fake fake,Snapshot original,string action){bool failed=false;try{Policy.Execute(fake,original,action);}catch{failed=true;}Assert(failed && fake.Writes==0);}
 public static void Main(){
  Run("Verify performs no writes",()=>{var o=Original();var f=new Fake(o);Assert(Policy.Execute(f,o,"verify").Success && f.Writes==0);});
  Run("Home apply preserves startup, first screen and autostart",()=>{var o=Original();var f=new Fake(o);Assert(Policy.Execute(f,o,"apply-home").Success && Policy.Same(f.State,Policy.HomeOnly(o)));});
  Run("Baseline may contain launcher in last-app backup",()=>{var o=Original();Assert(o.Strings["db/appfw/booting_appid_backup"]==Policy.Target);Policy.Validate(o);});
  Run("Exact restore rehearsal",()=>{var o=Original();var f=new Fake(o);Policy.Execute(f,o,"apply-home");Assert(Policy.Execute(f,o,"restore").Success && Policy.Same(f.State,o));});
  Run("Boot delegates startup derivation and preserves first screen",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));Assert(Policy.Execute(f,o,"apply-boot").Success && f.State.AutoStart==1 && f.State.Strings[Policy.FirstScreen]==o.Strings[Policy.FirstScreen] && f.Writes==1);});
  Run("Boot accepts observed Samsung last-app transition to saved startup",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));f.State.Strings["db/appfw/booting_appid_backup"]=o.Strings["db/appfw/startup_appid"];Assert(Policy.Execute(f,o,"apply-boot").Success);});
  Run("Boot refuses an unrelated last-app value",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));f.State.Strings["db/appfw/booting_appid_backup"]="other.App";Refused(f,o,"apply-boot");});
  Run("Boot restore returns exact original",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));Policy.Execute(f,o,"apply-boot");Assert(Policy.Execute(f,o,"restore-boot").Success && Policy.Same(f.State,o));});
  Run("Plain restore refuses unrecorded boot change",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));f.State.AutoStart=1;Refused(f,o,"restore");});
  Run("Restore supports missing launcher",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o)){IsEligible=false};Assert(Policy.Execute(f,o,"restore").Success);});
  Run("Repeated restore is a no-op",()=>{var o=Original();var f=new Fake(o);Assert(Policy.Execute(f,o,"restore").Success && f.Writes==0);});
  foreach(string action in new[]{"apply-home","verify","apply-boot"})Run("Live drift refused: "+action,()=>{var o=Original();var f=new Fake(o);f.State.Strings["db/appfw/startup_appid"]="other.App";Refused(f,o,action);});
  foreach(string action in new[]{"apply-home","apply-boot"})Run("Ineligible launcher refused: "+action,()=>{var o=Original();var f=new Fake(action=="apply-home"?o:Policy.HomeOnly(o)){IsEligible=false};Refused(f,o,action);});
  Run("Unrelated Home owner refused",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));f.State.Main="other.Home";Refused(f,o,"restore-boot");});
  Run("Unrelated first screen refused",()=>{var o=Original();var f=new Fake(Policy.HomeOnly(o));f.State.Strings[Policy.FirstScreen]="other.Screen";Refused(f,o,"restore");});
  Run("Unknown action refused",()=>{var o=Original();Refused(new Fake(o),o,"general-set");});
  Run("Foreign baseline owner refused",()=>{var o=Original();o.Main="other.Home";Refused(new Fake(o),o,"apply-home");});
  foreach(string key in Policy.Keys)Run("Missing key refused: "+key,()=>{var o=Original();var f=new Fake(o);o.Strings.Remove(key);Refused(f,o,"apply-home");});
  Run("Invalid autostart refused",()=>{var o=Original();var f=new Fake(o);o.AutoStart=2;Refused(f,o,"apply-home");});
  for(int point=1;point<=3;point++){int captured=point;Run("Apply failure rolls back after write "+point,()=>{var o=Original();var f=new Fake(o){FailAt=captured};var r=Policy.Execute(f,o,"apply-home");Assert(!r.Success && r.RolledBack && Policy.Same(f.State,o));});}
  Run("Boot failure rolls back exact pre-boot state",()=>{var o=Original();var before=Policy.HomeOnly(o);var f=new Fake(before){FailAt=1};var r=Policy.Execute(f,o,"apply-boot");Assert(!r.Success && r.RolledBack && Policy.Same(f.State,before));});
  Run("Rollback failure is reported, not success",()=>{var o=Original();var f=new Fake(o){FailAt=1,FailRollback=true};var r=Policy.Execute(f,o,"apply-home");Assert(!r.Success && !r.RolledBack && r.Error.Contains("rollback incomplete"));});
  Run("Silent write mismatch cannot report success",()=>{var o=Original();var f=new Fake(o){SilentMismatch=true};Assert(!Policy.Execute(f,o,"apply-home").Success);});
  Run("Existing autostart one is preserved by Home-only apply",()=>{var o=Original(1);var f=new Fake(o);Assert(Policy.Execute(f,o,"apply-home").Success && f.State.AutoStart==1);});
  Run("Option verify is read only",()=>{var f=new FakeOption{Value=1};Assert(StartupOption.Execute(f,1,"verify-option").Success && f.Writes==0);});
  Run("Option disable and exact restore",()=>{var f=new FakeOption{Value=1};Assert(StartupOption.Execute(f,1,"disable-last-app").Success && f.Value==0);Assert(StartupOption.Execute(f,1,"restore-last-app").Success && f.Value==1);});
  Run("Already disabled option needs no write",()=>{var f=new FakeOption{Value=0};Assert(StartupOption.Execute(f,0,"disable-last-app").Success && f.Writes==0);});
  Run("Option baseline drift refuses writes",()=>{var f=new FakeOption{Value=0};bool refused=false;try{StartupOption.Execute(f,1,"disable-last-app");}catch{refused=true;}Assert(refused && f.Writes==0);});
  Run("Option invalid value refuses writes",()=>{var f=new FakeOption{Value=2};bool refused=false;try{StartupOption.Execute(f,1,"restore-last-app");}catch{refused=true;}Assert(refused && f.Writes==0);});
  Run("Option mutation failure restores exact prior value",()=>{var f=new FakeOption{Value=1,Fail=true};var r=StartupOption.Execute(f,1,"disable-last-app");Assert(!r.Success && r.RolledBack && f.Value==1);});
  Run("Option silent mismatch cannot pass",()=>{var f=new FakeOption{Value=1,Silent=true};Assert(!StartupOption.Execute(f,1,"disable-last-app").Success);});
  Run("Option rollback failure is explicit",()=>{var f=new FakeOption{Value=1,Fail=true,FailRollback=true};var r=StartupOption.Execute(f,1,"disable-last-app");Assert(!r.Success && !r.RolledBack && r.Error.Contains("rollback incomplete"));});
  foreach(int initialAuto in new[]{0,1})foreach(int initialOption in new[]{0,1})Run("Combined setup and exact Undo "+initialAuto+initialOption,()=>{
   var o=Original(initialAuto);var f=new Fake(o);var opt=new FakeOption{Value=initialOption};
   Assert(SetupPolicy.Execute(f,opt,o,initialOption,"apply-all").Success && opt.Value==0 && f.State.Main==Policy.Target && f.State.AutoStart==1);
   Assert(SetupPolicy.Execute(f,opt,o,initialOption,"restore-all").Success && Policy.Same(f.State,o) && opt.Value==initialOption);
  });
  for(int point=1;point<=4;point++){int failure=point;Run("Combined write failure restores complete original "+failure,()=>{
   var o=Original();var f=new Fake(o){FailAt=failure};var opt=new FakeOption{Value=1};
   var r=SetupPolicy.Execute(f,opt,o,1,"apply-all");Assert(!r.Success && r.RolledBack && Policy.Same(f.State,o) && opt.Value==1);
  });}
  Run("Combined Last App failure restores Home too",()=>{var o=Original();var f=new Fake(o);var opt=new FakeOption{Value=1,Fail=true};var r=SetupPolicy.Execute(f,opt,o,1,"apply-all");Assert(!r.Success && r.RolledBack && Policy.Same(f.State,o) && opt.Value==1);});
  Run("Combined drift refuses all writes",()=>{var o=Original();var f=new Fake(o);var opt=new FakeOption{Value=0};bool refused=false;try{SetupPolicy.Execute(f,opt,o,1,"apply-all");}catch{refused=true;}Assert(refused && f.Writes==0 && opt.Writes==0);});
  Run("Undo refuses unrelated owner before changing Last App",()=>{var o=Original();var f=new Fake(o);f.State.Main="other.Home";var opt=new FakeOption{Value=0};bool refused=false;try{SetupPolicy.Execute(f,opt,o,1,"restore-all");}catch{refused=true;}Assert(refused && f.Writes==0 && opt.Writes==0);});
  Run("Combined recovery failure is explicit",()=>{var o=Original();var f=new Fake(o){FailAt=1,FailRollback=true};var opt=new FakeOption{Value=1};var r=SetupPolicy.Execute(f,opt,o,1,"apply-all");Assert(!r.Success && !r.RolledBack && r.Error.Contains("recovery incomplete"));});
  Run("Compatibility probes continue after missing getter",()=>{int calls=0;var c=CompatibilityChecks.Run(901,"ARM64",name=>{calls++;if(name=="homeOperation")throw new EntryPointNotFoundException("PRIVATE");return "Other";});Assert(calls==8 && c["homeOperation"][1]=="MISSING_SYMBOL" && c["lastApp"][0]=="pass");});
  Run("Compatibility refuses root",()=>{int calls=0;var c=CompatibilityChecks.Run(0,"ARM32",name=>{calls++;return "Other";});Assert(calls==0 && c["identity"][0]=="fail");});
  Run("Compatibility permits getter checks for other nonroot accounts",()=>{int calls=0;var c=CompatibilityChecks.Run(1000,"ARM32",name=>{calls++;return "Other";});Assert(calls==8 && c["identity"][2]=="Other");});
  Run("Compatibility refuses other architecture",()=>{int calls=0;var c=CompatibilityChecks.Run(901,"Other",name=>{calls++;return "Other";});Assert(calls==0 && c["architecture"][0]=="fail");});
  Run("Compatibility never exposes arbitrary values or errors",()=>{var c=CompatibilityChecks.Run(901,"ARM32",name=>{if(name=="homeOperation")return "PRIVATE";throw new Exception("PRIVATE");});Assert(c["homeOperation"][1]=="UNEXPECTED_VALUE" && c["lastApp"][1]=="READ_FAILED");});
  Console.WriteLine("Native Home policy checks passed: "+passed);
 }
}
