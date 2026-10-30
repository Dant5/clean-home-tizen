// Settings-read-only compatibility checks. No setters or device transport.
using System;
using System.Collections.Generic;

internal static class CompatibilityChecks {
    internal static readonly string[] Reads = {"homeOperation","homePreference","startupPreference","bootingPreference","firstScreen","autoStart","lastApp","appBoot"};
    internal static Dictionary<string,string[]> Run(uint uid, string architecture, Func<string,string> read) {
        var checks = new Dictionary<string,string[]>();
        checks["identity"] = uid != 0 ? new[]{"pass","OK",uid == 901 ? "SDK" : "Other"} : new[]{"fail","ROOT_REFUSED","Unknown"};
        bool supported = architecture == "ARM32" || architecture == "ARM64";
        checks["architecture"] = supported ? new[]{"pass","OK","None"} : new[]{"fail","ARCH_UNSUPPORTED","Unknown"};
        foreach (var name in Reads) {
            if (uid == 0 || !supported) {checks[name] = new[]{"skipped","NOT_RUN","None"};continue;}
            try {
                string observation = read(name);
                if (Array.IndexOf(new[]{"Samsung","CleanHome","Other","On","Off","Available","Unavailable"}, observation)<0)
                    checks[name] = new[]{"fail","UNEXPECTED_VALUE","Unknown"};
                else checks[name] = new[]{"pass","OK",observation};
            } catch (Exception error) {
                string code = error is DllNotFoundException ? "MISSING_LIBRARY" : error is EntryPointNotFoundException ? "MISSING_SYMBOL" : error is BadImageFormatException ? "ARCH_UNSUPPORTED" : error is UnauthorizedAccessException ? "ACCESS_DENIED" : "READ_FAILED";
                checks[name] = new[]{"unavailable",code,"None"};
            }
        }
        return checks;
    }
}
