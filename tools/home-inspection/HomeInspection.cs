// Read-only adaptation of CleanFrame / chaosmanage's native query, MIT.
// Copyright (c) 2026 Nathan Clark. Root LICENSE and THIRD_PARTY_NOTICES.md apply.
// No TV transport, staging, app launch, setters, privilege escalation or restore.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.RegularExpressions;

internal static class HomeInspection {
    private const string Target = "D5Q60BHome.CleanHome";
    private static readonly string[] Keys = {
        "db/appfw/home_appid", "db/appfw/startup_appid",
        "db/appfw/booting_appid_backup", "db/first_screen/type"
    };
    [DllImport("libc")] private static extern uint getuid();
    [DllImport("libc")] private static extern void free(IntPtr pointer);
    [DllImport("libbundle.so.0")] private static extern IntPtr bundle_create();
    [DllImport("libbundle.so.0")] private static extern void bundle_free(IntPtr bundle);
    // This sets only the operation field in our newly allocated in-memory bundle.
    [DllImport("libaul.so.0")] private static extern int aul_svc_set_operation(IntPtr bundle, string operation);
    [DllImport("libaul.so.0")] private static extern int aul_get_default_app(IntPtr bundle, out IntPtr app);
    [DllImport("libvconf.so.0")] private static extern IntPtr vconf_get_str(string key);
    [DllImport("libvconf.so.0")] private static extern int vconf_get_int(string key, out int value);
    [DllImport("libapp-context-manager-common.so")] private static extern byte util_is_appbooting_supported_webapp_byappid(string app);

    private static object Read(Func<object> operation) {
        try { return new { ok = true, value = operation() }; }
        catch (Exception error) { return new { ok = false, error = error.GetType().Name }; }
    }
    private static string ReadString(string key) {
        var pointer = vconf_get_str(key);
        if (pointer == IntPtr.Zero) throw new InvalidOperationException("Unavailable key");
        try { return Marshal.PtrToStringAnsi(pointer); }
        finally { free(pointer); }
    }
    private static string ReadHome() {
        var bundle = bundle_create();
        if (bundle == IntPtr.Zero) throw new InvalidOperationException("Unavailable bundle");
        try {
            if (aul_svc_set_operation(bundle, "http://tizen.org/appcontrol/operation/main") != 0)
                throw new InvalidOperationException("Unable to initialise query bundle");
            if (aul_get_default_app(bundle, out var pointer) != 0 || pointer == IntPtr.Zero)
                throw new InvalidOperationException("Unavailable default application");
            try { return Marshal.PtrToStringAnsi(pointer); }
            finally { free(pointer); }
        } finally { bundle_free(bundle); }
    }
    public static int Main(string[] args) {
        if (args.Length == 1 && args[0] == "--describe") {
            Console.WriteLine(JsonSerializer.Serialize(new {
                readOnly = true, target = Target, expectedArchitecture = "ARM32",
                expectedFirmwareFamily = "T-NKLBUABC", expectedFirmwareVersion = "1720.7",
                expectedSdkUid = 901, buildTarget = AppContext.TargetFrameworkName,
                transportIncluded = false, describeDoesNotContactDevice = true
            }));
            return 0;
        }
        if (args.Length != 1 || (args[0] != "--query" && args[0] != "--startup-strings")) {
            Console.Error.WriteLine("Use --describe offline. --query requires separately reviewed device staging; no transport is included.");
            return 2;
        }
        try {
            if (IntPtr.Size != 4 || RuntimeInformation.ProcessArchitecture != Architecture.Arm)
                throw new InvalidOperationException("Query restricted to ARM32");
            var version = File.ReadLines("/etc/prd_info.ini").FirstOrDefault(line => line.StartsWith("Version=", StringComparison.Ordinal));
            if (version != "Version=T-NKLBUABC-1720.7;")
                throw new InvalidOperationException("Unverified firmware; native queries were not called");
            uint uid = getuid();
            if (uid != 901) throw new InvalidOperationException("Expected developer SDK UID 901; native queries were not called");
            if(args[0]=="--startup-strings"){Console.WriteLine(JsonSerializer.Serialize(StartupStrings.Query()));return 0;}
            var values = new Dictionary<string, object>();
            foreach (var key in Keys) values[key] = Read(() => ReadString(key));
            var autostart = Read(() => {
                if (vconf_get_int("db/menu/smart_hub/ontvsetting/auto_start", out int value) != 0)
                    throw new InvalidOperationException("Unavailable autostart key");
                return value;
            });
            var lastApp = Read(() => {
                if (vconf_get_int("db/menu/app_booting", out int value) != 0 || (value != 0 && value != 1))
                    throw new InvalidOperationException("Unavailable Last App preference");
                return value;
            });
            Console.WriteLine(JsonSerializer.Serialize(new {
                readOnly = true, target = Target, uid, firmware = version,
                homeOperation = Read(() => ReadHome()), keys = values, autostart, lastApp,
                bootSupported = Read(() => util_is_appbooting_supported_webapp_byappid(Target))
            }));
            return 0;
        } catch (Exception error) {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }
}
