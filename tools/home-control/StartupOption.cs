// Pure policy for the separately discovered Samsung Autorun Last App integer.
using System;
namespace CleanHome.Native {
 public interface IStartupOption {int Read();void Write(int value);}
 public sealed class OptionResult {
  public bool Success {get;set;} public bool RolledBack {get;set;}
  public string Error {get;set;} public int? After {get;set;}
 }
 public static class StartupOption {
  public const string Key="db/menu/app_booting";
  public static OptionResult Execute(IStartupOption platform,int original,string action) {
   if(original!=0 && original!=1)throw new Exception("Invalid original last-app value");
   if(action!="verify-option" && action!="disable-last-app" && action!="restore-last-app")throw new Exception("Unsupported startup-option action");
   int before=platform.Read();if(before!=0 && before!=1)throw new Exception("Unexpected last-app value; no writes attempted");
   if(action=="verify-option") {if(before!=original)throw new Exception("Last-app baseline differs");return new OptionResult{Success=true,After=before};}
   if(action=="disable-last-app" && before!=original)throw new Exception("Last-app option changed since baseline");
   int desired=action=="disable-last-app"?0:original;
   try {if(before!=desired)platform.Write(desired);if(platform.Read()!=desired)throw new Exception("Last-app readback mismatch");return new OptionResult{Success=true,After=desired};}
   catch(Exception error) {
    try {if(platform.Read()!=before)platform.Write(before);if(platform.Read()!=before)throw new Exception("Last-app recovery mismatch");return new OptionResult{RolledBack=true,Error=error.Message,After=before};}
    catch(Exception recovery){return new OptionResult{Error=error.Message+"; rollback incomplete: "+recovery.Message};}
   }
  }
 }
}
