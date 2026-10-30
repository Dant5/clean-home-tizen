const fields = ['schema','cleanHome','environment','model','firmware','tizen','chromium','viewport','spacing','appDiscovery','savedSettings','photo','errors','rejections','tvErrors','lastTVError','result'];
const choices = {
  environment:['TV API present','Browser preview'], spacing:['Margin fallback','Native gap'],
  appDiscovery:['Failed','Completed','Pending'],savedSettings:['Available','Unavailable','Not checked'],
  photo:['Loaded','Not loaded'],result:['Works on my TV','There is a problem']
};
const codes=['SecurityError','NotFoundError','InvalidValuesError','InvalidStateError','NotSupportedError','UnknownError','TypeMismatchError','TimeoutError','TVError'];
const operations=['App discovery','App launch','TV input','TV control'];
export function validateReport(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).length !== fields.length || fields.some(k=>!Object.hasOwn(value,k)) || value.schema!==1) return null;
  for (const [key,allowed] of Object.entries(choices)) if (!allowed.includes(value[key])) return null;
  for (const key of ['errors','rejections','tvErrors']) if (!Number.isInteger(value[key]) || value[key]<0 || value[key]>99) return null;
  const matches=(key,pattern)=>typeof value[key]==='string' && pattern.test(value[key]);
  if (!matches('cleanHome',/^\d{1,3}\.\d{1,3}\.\d{1,3}$/)) return null;
  if (value.model!=='Not reported' && !matches('model',/^[A-Za-z][A-Za-z0-9_-]{2,39}$/)) return null;
  if (value.firmware!=='Not reported' && (!matches('firmware',/^T-[A-Za-z][A-Za-z0-9_.-]{0,61}$/) || /(?:\d{1,3}\.){3}\d{1,3}/.test(value.firmware))) return null;
  if (value.tizen!=='Not reported' && !matches('tizen',/^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?$/)) return null;
  if (value.chromium!=='Not reported' && (!Number.isInteger(value.chromium) || value.chromium<1 || value.chromium>999)) return null;
  if (!matches('viewport',/^\d{1,5}x\d{1,5}$/) || value.viewport.split('x').some(x=>Number(x)>16384)) return null;
  if (value.lastTVError!=='None' && !operations.some(operation=>codes.some(code=>value.lastTVError===operation+': '+code))) return null;
  return Object.fromEntries(fields.map(k=>[k,value[k]]));
}

// Setup reports contain only bounded capability outcomes, never native values/logs.
const setupSteps=['metadata','developer','capabilities','nativeHelper','identity','architecture','homeOperation','homePreference','startupPreference','bootingPreference','firstScreen','autoStart','lastApp','appBoot','homeSetup'];
const setupCodes=['OK','NOT_RUN','HTTP_FAILED','NOT_SAMSUNG','SDB_FAILED','CAPS_FAILED','HELPER_FAILED','NATIVE_TOOL_MISSING','CLEANUP_UNKNOWN','INVALID_RESULT','ROOT_REFUSED','UID_UNSUPPORTED','ARCH_UNSUPPORTED','MISSING_LIBRARY','MISSING_SYMBOL','ACCESS_DENIED','READ_FAILED','UNEXPECTED_VALUE','PROFILE_NEEDED','STRICT_CHECK_FAILED','NOT_CONFIRMED'];
const setupObservations=['None','Samsung','CleanHome','Other','On','Off','Available','Unavailable','Unknown','SDK'];
export function validateSetupReport(value) {
  const fields=['schema','kind','setup','model','firmware','tizen','architecture','profile','action','phase','checks'];
  if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==fields.length||fields.some(k=>!Object.hasOwn(value,k))||value.schema!==2||value.kind!=='home-setup')return null;
  if(typeof value.setup!=='string'||!/^\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(value.setup))return null;
  if(value.model!=='Not reported'&&(typeof value.model!=='string'||!/^[A-Za-z][A-Za-z0-9_-]{2,39}$/.test(value.model)))return null;
  if(value.firmware!=='Not reported'&&(typeof value.firmware!=='string'||!/^T-[A-Za-z][A-Za-z0-9_.-]{0,61}$/.test(value.firmware)||/(?:\d{1,3}\.){3}\d{1,3}/.test(value.firmware)))return null;
  if(value.tizen!=='Not reported'&&(typeof value.tizen!=='string'||!/^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?$/.test(value.tizen)))return null;
  if(!['Not reported','ARM32','ARM64','Other'].includes(value.architecture)||!['known','needs-review','unknown'].includes(value.profile)||!['diagnose','apply','undo'].includes(value.action)||!['notChecked','original','active','unknown'].includes(value.phase))return null;
  const checks=value.checks;
  if(!checks||typeof checks!=='object'||Array.isArray(checks)||Object.keys(checks).length!==setupSteps.length||setupSteps.some(k=>!Object.hasOwn(checks,k)))return null;
  for(const entry of Object.values(checks))if(!Array.isArray(entry)||entry.length!==3||!['pass','fail','unavailable','skipped'].includes(entry[0])||!setupCodes.includes(entry[1])||!setupObservations.includes(entry[2]))return null;
  return {...Object.fromEntries(fields.filter(k=>k!=='checks').map(k=>[k,value[k]])),checks:Object.fromEntries(setupSteps.map(k=>[k,[...checks[k]]]))};
}
