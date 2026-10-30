// A single guarded transaction for the optional public companion, with exact Undo.
using System;
namespace CleanHome.Native {
 public sealed class SetupResult {
  public bool Success {get;set;} public bool RolledBack {get;set;}
  public string Error {get;set;} public Snapshot After {get;set;}
  public int? LastApp {get;set;}
 }
 public static class SetupPolicy {
  static void Require(Result result) {if(!result.Success)throw new Exception(result.Error ?? "Native Home transaction failed");}
  static void Require(OptionResult result) {if(!result.Success)throw new Exception(result.Error ?? "Last App transaction failed");}
  public static SetupResult Execute(IPlatform platform,IStartupOption option,Snapshot original,int lastApp,string action) {
   Policy.Validate(original);
   if(lastApp!=0 && lastApp!=1)throw new Exception("Invalid original Last App value");
   if(action!="apply-all" && action!="restore-all")throw new Exception("Unsupported setup action");
   if(original.Main!=Policy.Samsung || original.Strings[Policy.HomeKey]!=Policy.Samsung)throw new Exception("Original Samsung Home baseline required");
   var before=platform.Read();Policy.Validate(before);
   int beforeOption=option.Read();
   if(beforeOption!=0 && beforeOption!=1)throw new Exception("Unknown Last App value");
   // Validate ownership BEFORE changing either preference, including during Undo.
   if(before.Main!=original.Main && before.Main!=Policy.Target)throw new Exception("Another launcher owns Home; no changes attempted");
   if(before.Strings[Policy.HomeKey]!=original.Strings[Policy.HomeKey] && before.Strings[Policy.HomeKey]!=Policy.Target)throw new Exception("Another launcher owns the Home setting");
   if(before.Strings[Policy.FirstScreen]!=original.Strings[Policy.FirstScreen])throw new Exception("First screen changed; no changes attempted");
   if(action=="apply-all") {
    if(!Policy.Same(before,original) || beforeOption!=lastApp)throw new Exception("Saved original no longer matches; no changes attempted");
    if(!platform.Eligible())throw new Exception("Install the Clean Home app before setting up Home");
   }
   try {
    if(action=="apply-all") {
     Require(Policy.Execute(platform,original,"apply-home"));
     Require(Policy.Execute(platform,original,"apply-boot"));
     Require(StartupOption.Execute(option,lastApp,"disable-last-app"));
     var after=platform.Read();Policy.Validate(after);
     if(after.Main!=Policy.Target || after.Strings[Policy.HomeKey]!=Policy.Target || after.AutoStart!=1 || option.Read()!=0)throw new Exception("Combined setup verification failed");
    } else {
     // Restore the Last App preference before relinquishing native Home.
     Require(StartupOption.Execute(option,lastApp,"restore-last-app"));
     Require(Policy.Execute(platform,original,"restore-boot"));
     if(!Policy.Same(platform.Read(),original) || option.Read()!=lastApp)throw new Exception("Undo verification failed");
    }
    return new SetupResult {Success=true,After=platform.Read(),LastApp=option.Read()};
   } catch(Exception error) {
    // Apply errors restore the complete original; Undo errors restore its original
    // Last App integer and leave Home restoration available for explicit recovery.
    bool restored=false;string detail="";
    try {
     Require(StartupOption.Execute(option,lastApp,"restore-last-app"));
     Require(Policy.Execute(platform,original,"restore-boot"));
     restored=Policy.Same(platform.Read(),original) && option.Read()==lastApp;
    }catch(Exception recovery){detail="; recovery incomplete: "+recovery.Message;}
    return new SetupResult {Error=error.Message+detail,RolledBack=restored,After=platform.Read(),LastApp=option.Read()};
   }
  }
 }
}
