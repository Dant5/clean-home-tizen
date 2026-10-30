"""Build only our managed helpers; never download or change a TV runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotnet", default=shutil.which("dotnet"))
    args = parser.parse_args()
    if not args.dotnet: parser.error("Install a .NET SDK on this computer, or pass --dotnet PATH")
    output = ROOT / "dist/home-setup"
    if output.exists(): shutil.rmtree(output)  # Recreated build output only.
    source = ROOT / "tools/home-setup"
    shutil.copytree(source, output / "tools/home-setup", ignore=shutil.ignore_patterns("__pycache__", "payload"))
    vendor = output / "vendor/aerotizen"
    vendor.mkdir(parents=True)
    for name in ("sdb.py", "sdk.py", "transport.py", "LICENSE", "sdk-SOURCE.json"):
        shutil.copy2(ROOT / "vendor/aerotizen" / name, vendor / name)
    for name in ("LICENSE", "docs/THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, output / Path(name).name)
    shutil.copy2(ROOT / "tools/home-setup/START-WINDOWS.cmd", output / "START-WINDOWS.cmd")
    (output / "START-WINDOWS.cmd").write_text('@echo off\ncd /d "%~dp0"\npython tools\\home-setup\\setup.py\nif errorlevel 1 pause\n')
    (output / "START-LINUX.sh").write_bytes(b'#!/bin/sh\ncd "$(dirname "$0")" || exit 1\nexec python3 tools/home-setup/setup.py\n')
    os.chmod(output / "START-LINUX.sh", 0o755)
    payload = output / "tools/home-setup/payload"
    payload.mkdir()
    files = {}
    env = {**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1"}
    for project, assembly in (("home-inspection/HomeInspection.csproj", "CleanHomeReadOnlyInspection"), ("home-control/HomeControl.csproj", "CleanHomeNativeControl")):
        with tempfile.TemporaryDirectory(prefix="clean-home-build-") as temporary:
            subprocess.run([args.dotnet, "build", str(ROOT / "tools" / project), "-c", "Release", "-f", "netcoreapp3.1", "-o", temporary, "-p:UseSharedCompilation=false", "-p:DebugType=None", "-p:DebugSymbols=false", "-p:IncludeSourceRevisionInInformationalVersion=false", "-p:PathMap="+str(ROOT)+"=/_/src", "--nologo"], env=env, check=True)
            for suffix in (".dll", ".runtimeconfig.json", ".deps.json"):
                name = assembly + suffix
                data = (Path(temporary) / name).read_bytes()
                (payload / name).write_bytes(data)
                files[name] = hashlib.sha256(data).hexdigest()
    (payload / "payload.json").write_text(json.dumps({"schema": 1, "files": files}, sort_keys=True, indent=2) + "\n")
    (output / "README.txt").write_text("Clean Home optional native Home setup\n\nFirst install the Clean Home widget using your own Samsung certificates.\nThis tool then changes Home and power-on preferences only on the verified\nQA55Q60BAWXXY / T-NKLBUABC-1720.7. It refuses other models/software.\n\nWindows: install Python 3.11+ from python.org if needed, then double-click\nSTART-WINDOWS.cmd. Linux: run ./START-LINUX.sh (Python 3.11+).\nA local browser page opens. Follow Check TV, confirmation, Use Clean Home.\nNo extra Python packages, root, certificate access or background watcher.\n\nKeep your per-user CleanHome/recovery folder; use Undo on the same computer\nbefore uninstalling the widget. This tool's new end-to-end setup still needs\nphysical-TV validation; the underlying mechanism worked on our test TV.\n\nhttps://github.com/Dant5/clean-home-tizen/blob/main/docs/NATIVE-HOME.md\n")
    archive = ROOT / "dist/CleanHome-Home-Setup-experimental.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                info=zipfile.ZipInfo(path.relative_to(output).as_posix(),(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=(0o100755 if path.name.endswith('.sh') else 0o100644)<<16
                target.writestr(info,path.read_bytes())
    print("Built optional companion: " + str(archive.relative_to(ROOT)))
    print("No TV was contacted. The companion requires explicit on-screen confirmation.")


if __name__ == "__main__": main()
