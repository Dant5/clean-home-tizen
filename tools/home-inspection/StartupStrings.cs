// Read-only, bounded inspection of startup-specific firmware strings.
// No vendor binary is copied into this repository or modified on the television.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
internal static class StartupStrings {
 [DllImport("libvconf.so.0")] static extern int vconf_get_int(string key,out int value);
 [DllImport("libvconf.so.0")] static extern int vconf_get_bool(string key,out int value);
 public static object Query() {
  int boolValue,intValue;int boolCode=vconf_get_bool("db/menu/app_booting",out boolValue);int intCode=vconf_get_int("db/menu/app_booting",out intValue);var lastApp=new{key="db/menu/app_booting",boolCode,boolValue,intCode,intValue};
  var rows=new List<object>();
  foreach(string path in new[]{"/usr/bin/app-boot-manager","/usr/bin/app-context-manager","/usr/lib/libapp-context-manager-common.so"}) {
   try {
    var info=new FileInfo(path);if(info.Length>32*1024*1024)throw new Exception("File exceeds inspection bound");
    var selected=new SortedSet<string>();var keys=new SortedSet<string>();var buffer=new StringBuilder();
    Action flush=()=>{if(buffer.Length>=5 && buffer.Length<=256){string text=buffer.ToString();foreach(Match match in Regex.Matches(text,@"(?:db|memory)/[A-Za-z0-9_./-]+"))keys.Add(match.Value);if(Regex.IsMatch(text,"boot|last.?app|auto.?run|auto_start|home.app|first.screen",RegexOptions.IgnoreCase))selected.Add(text);}buffer.Clear();};
    using(var stream=File.OpenRead(path)){int value;while((value=stream.ReadByte())!=-1){if(value>=32 && value<=126){if(buffer.Length<=256)buffer.Append((char)value);}else flush();}flush();}
    var settings=new List<object>();foreach(string key in keys.Where(x=>Regex.IsMatch(x,"last|auto_start|autorun",RegexOptions.IgnoreCase)).Take(30)){int value;int code=vconf_get_int(key,out value);settings.Add(new{key,code,value=code==0?(int?)value:null});}
    rows.Add(new{path,bytes=info.Length,keys=keys.Take(200).ToArray(),strings=selected.Take(160).ToArray(),settings});
   }catch(Exception error){rows.Add(new{path,error=error.GetType().Name});}
  }
  return new{readOnly=true,scope="Three named startup components; strings and selected integer/boolean getters only",lastApp,rows};
 }
}
