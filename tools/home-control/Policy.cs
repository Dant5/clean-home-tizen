// Native snapshot/readback pattern adapted from AeroTizen (Hamza El Alaoui, MIT).
// Q60B policy: no watcher, root, package management or general-purpose settings API.
using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
namespace CleanHome.Native {
 public sealed class Snapshot {
  public string Main {get;set;}
  public Dictionary<string,string> Strings {get;set;}
  public int AutoStart {get;set;}
  public Snapshot Copy() => new Snapshot {Main=Main,Strings=new Dictionary<string,string>(Strings),AutoStart=AutoStart};
 }
 public interface IPlatform {
  Snapshot Read(); bool Eligible();
  void SetMain(string app); void SetString(string key,string value); void SetAuto(int value);
 }
 public sealed class Result {
  public bool Success {get;set;} public bool RolledBack {get;set;}
  public string Error {get;set;} public Snapshot After {get;set;}
 }
 public static class Policy {
  public const string Target="D5Q60BHome.CleanHome";
  public const string Samsung="com.samsung.tv.csfs";
  public const string HomeKey="db/appfw/home_appid";
  public const string FirstScreen="db/first_screen/type";
  public static readonly string[] Keys={HomeKey,"db/appfw/startup_appid","db/appfw/booting_appid_backup",FirstScreen};
  public static void Validate(Snapshot value) {
   if(value==null || value.Strings==null || value.Strings.Count!=4 || (value.AutoStart!=0 && value.AutoStart!=1)) throw new Exception("Incomplete or invalid Home snapshot");
   foreach(string key in Keys) if(!value.Strings.ContainsKey(key) || !AppId(value.Strings[key]))throw new Exception("Invalid or missing Home setting: "+key);
   if(!AppId(value.Main))throw new Exception("Invalid Home owner");
  }
  static bool AppId(string value)=>value!=null && Regex.IsMatch(value,@"^[A-Za-z0-9_.-]{1,128}$");
  public static bool Same(Snapshot left,Snapshot right) {
   if(left.Main!=right.Main || left.AutoStart!=right.AutoStart)return false;
   foreach(string key in Keys)if(left.Strings[key]!=right.Strings[key])return false;
   return true;
  }
  public static Snapshot HomeOnly(Snapshot original) {
   var value=original.Copy();value.Main=Target;value.Strings[HomeKey]=Target;return value;
  }
  // Samsung updates booting_appid_backup during normal foreground transitions.
  // Permit only this recorded startup id or the baseline/target value during boot apply.
  static bool KnownBootBackup(Snapshot live,Snapshot original) {
   string value=live.Strings["db/appfw/booting_appid_backup"];
   return value==original.Strings["db/appfw/booting_appid_backup"] || value==original.Strings["db/appfw/startup_appid"] || value==Target;
  }
  static bool HomeReadyForBoot(Snapshot live,Snapshot original) {
   var expected=HomeOnly(original);
   expected.Strings["db/appfw/booting_appid_backup"]=live.Strings["db/appfw/booting_appid_backup"];
   return Same(live,expected) && KnownBootBackup(live,original);
  }
  static void Write(IPlatform platform,Snapshot desired) {
   if(platform.Read().Main!=desired.Main){platform.SetMain(desired.Main);if(platform.Read().Main!=desired.Main)throw new Exception("Home-operation readback mismatch");}
   // Native Home assignment may derive other values; restore all unrelated baseline fields.
   foreach(string key in Keys)if(platform.Read().Strings[key]!=desired.Strings[key]) {
    platform.SetString(key,desired.Strings[key]);if(platform.Read().Strings[key]!=desired.Strings[key])throw new Exception("Home-setting readback mismatch: "+key);
   }
   if(platform.Read().AutoStart!=desired.AutoStart){platform.SetAuto(desired.AutoStart);if(platform.Read().AutoStart!=desired.AutoStart)throw new Exception("Autostart readback mismatch");}
   if(!Same(platform.Read(),desired))throw new Exception("Final Home snapshot mismatch");
  }
  public static Result Execute(IPlatform platform,Snapshot original,string action) {
   Validate(original);
   if(original.Main!=Samsung || original.Strings[HomeKey]!=Samsung)throw new Exception("Baseline must record this TV's original Samsung Home owner");
   if(action!="verify" && action!="apply-home" && action!="apply-boot" && action!="restore" && action!="restore-boot")throw new Exception("Unsupported native action");
   var before=platform.Read();Validate(before);
   if(action=="verify") {
    if(!Same(before,original))throw new Exception("Live state differs from the saved original; no writes attempted");
    return new Result {Success=true,After=before};
   }
   if(action=="apply-home" && !Same(before,original))throw new Exception("Live state changed; Home apply refused");
   if(action=="apply-boot" && !HomeReadyForBoot(before,original))throw new Exception("Boot requires the verified Home-only state");
   if(action.StartsWith("apply",StringComparison.Ordinal) && !platform.Eligible())throw new Exception("Installed launcher is not eligible; no writes attempted");
   if(action.StartsWith("restore",StringComparison.Ordinal)) {
    if((before.Main!=original.Main && before.Main!=Target) || (before.Strings[HomeKey]!=original.Strings[HomeKey] && before.Strings[HomeKey]!=Target) || before.Strings[FirstScreen]!=original.Strings[FirstScreen])throw new Exception("Unrelated Home ownership or first-screen change; restore refused");
    if(action=="restore" && before.AutoStart!=original.AutoStart)throw new Exception("Use the recorded boot restore procedure for changed autostart");
   }
   try {
    if(action=="apply-home")Write(platform,HomeOnly(original));
    else if(action=="apply-boot") {
     platform.SetAuto(1);
     var after=platform.Read();Validate(after);
     if(after.Main!=Target || after.Strings[HomeKey]!=Target || after.AutoStart!=1 || after.Strings[FirstScreen]!=original.Strings[FirstScreen])throw new Exception("Native boot readback mismatch");
     foreach(string key in Keys)if(after.Strings[key]!=original.Strings[key] && after.Strings[key]!=Target && !(key=="db/appfw/booting_appid_backup" && KnownBootBackup(after,original)))throw new Exception("Unexpected derived boot setting: "+key);
    } else Write(platform,original);
    return new Result {Success=true,After=platform.Read()};
   } catch(Exception error) {
    try {Write(platform,before);return new Result {RolledBack=true,Error=error.Message,After=platform.Read()};}
    catch(Exception recovery){return new Result {Error="Native change failed: "+error.Message+"; rollback incomplete: "+recovery.Message};}
   }
  }
 }
}
