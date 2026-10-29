# Temporary Web Inspector access for the installed Clean Home app only.
# Explicit TV address/inspector port; no TV discovery, install, pair, root or Home changes.
# The caller starts only its own app in debug mode and closes the session after testing.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$script:cdpId=0
$script:cdpEvents=New-Object System.Collections.ArrayList
function Connect-CleanHomeInspector([string]$tvAddress,[int]$port){
 $targets=Invoke-RestMethod -Uri ('http://'+$tvAddress+':'+ $port +'/json') -TimeoutSec 5
 $target=@($targets | Where-Object {$_.title -eq 'Clean Home'})
 if($target.Count -ne 1){throw 'Exactly one Clean Home inspector target is required'}
 $path=([uri]$target[0].webSocketDebuggerUrl).PathAndQuery
 $script:cdpSocket=New-Object System.Net.WebSockets.ClientWebSocket
 $script:cdpSocket.Options.Proxy=$null
 $cts=New-Object System.Threading.CancellationTokenSource
 $cts.CancelAfter(8000)
 try{$null=$script:cdpSocket.ConnectAsync([uri]('ws://'+$tvAddress+':'+ $port + $path),$cts.Token).GetAwaiter().GetResult()}finally{$cts.Dispose()}
 $identity=Invoke-Cdp 'Runtime.evaluate' @{expression='JSON.stringify({id:tizen.application.getCurrentApplication().appInfo.id,version:tizen.application.getCurrentApplication().appInfo.version})';returnByValue=$true}
 $id=ConvertFrom-Json $identity.result.value
 if($id.id -ne 'D5Q60BHome.CleanHome'){throw 'Inspector target is not our launcher; no control allowed'}
 return $id
}
function Invoke-Cdp([string]$method,$parameters){
 $script:cdpId++;$id=$script:cdpId
 $json=@{id=$id;method=$method;params=$parameters}|ConvertTo-Json -Compress -Depth 12
 $bytes=[Text.Encoding]::UTF8.GetBytes($json);$cts=New-Object System.Threading.CancellationTokenSource;$cts.CancelAfter(10000)
 try{
  $null=$script:cdpSocket.SendAsync([ArraySegment[byte]]::new($bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,$cts.Token).GetAwaiter().GetResult()
  while($true){
   $memory=New-Object System.IO.MemoryStream
   try{
    do{$buf=New-Object byte[] 32768;$received=$script:cdpSocket.ReceiveAsync([ArraySegment[byte]]::new($buf),$cts.Token).GetAwaiter().GetResult();if($received.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close){throw 'Inspector socket closed'};$memory.Write($buf,0,$received.Count)}while(-not $received.EndOfMessage)
    $reply=[Text.Encoding]::UTF8.GetString($memory.ToArray())|ConvertFrom-Json
   }finally{$memory.Dispose()}
   if($reply.id -eq $id){if($reply.error){throw ($reply.error|ConvertTo-Json -Compress)};return $reply.result}
   if($reply.method){$null=$script:cdpEvents.Add($reply)}
  }
 }finally{$cts.Dispose()}
}
function Read-CleanHome([string]$expression){
 $r=Invoke-Cdp 'Runtime.evaluate' @{expression=$expression;returnByValue=$true;awaitPromise=$true}
 if($r.exceptionDetails){throw ('Clean Home evaluation failed: '+$r.exceptionDetails.text)}
 return $r.result.value
}
function Close-CleanHomeInspector{
 if($script:cdpSocket){$script:cdpSocket.Dispose()}
}
