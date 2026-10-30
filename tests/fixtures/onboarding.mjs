// Shared fake Tizen boundary for modern and historical browser tests. Never contacts a TV.
export function installOnboarding(seed) {
  if(!sessionStorage.getItem('seeded')){if(seed)localStorage.setItem('cleanhome.home.v1',JSON.stringify(seed));sessionStorage.setItem('seeded','yes');}
  const original=Storage.prototype.setItem;window.__failSave=false;
  Storage.prototype.setItem=function(k,v){if(window.__failSave&&k==='cleanhome.home.v1')throw new DOMException('Full','QuotaExceededError');return original.call(this,k,v);};
  window.__launches=[];
  window.tizen={application:{getAppsInfo(ok){setTimeout(()=>ok([
   {id:'AppOne0001.Main',name:'Alpha',show:true},{id:'AppTwo0002.Main',name:'Beta',show:true},
   {id:'AppThree03.Main',name:'Gamma',show:true},{id:'ExtraFour1.Main',name:'Delta',show:true},{id:'ExtraFive1.Main',name:'Epsilon',show:true},{id:'ExtraSix01.Main',name:'Zeta',show:true},{id:'ExtraSeven.Main',name:'Eta',show:true},{id:'VideoTV001.Video',name:'YouTube',show:true},{id:'MusicTV001.Player',name:'Spotify',show:true}
  ]),20);},launch(id,ok){__launches.push(id);ok();},getCurrentApplication(){return {appInfo:{id:'D5Q60BHome.CleanHome'}};}}};
 
 window.fetch=function(){return Promise.reject(new Error("Offline compatibility test"));};
}
