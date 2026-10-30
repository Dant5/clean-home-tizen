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
