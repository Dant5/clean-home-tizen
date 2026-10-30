import {env} from "cloudflare:workers";
import {validateReport} from "./report-schema.mjs";

const cors = {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"POST, OPTIONS","Access-Control-Allow-Headers":"Content-Type","Cache-Control":"no-store"};
const reply = (data: object, status=200) => Response.json(data,{status,headers:cors});
export function OPTIONS() {return new Response(null,{status:204,headers:cors});}
export function GET() {return reply({service:"Clean Home TV feedback",schema:1,ready:!!env.DB});}
export async function POST(request: Request) {
  const database=env.DB;
  let body="";
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  try {
    reader=request.body?.getReader(); if (!reader) return reply({error:"Empty report"},400);
    const chunks: Uint8Array[]=[]; let length=0;
    const deadline=Date.now()+5000;
    while (true) {
      const remaining=deadline-Date.now(); if(remaining<=0) throw new Error("Body timeout");
      let timer: ReturnType<typeof setTimeout> | undefined;
      let part: ReadableStreamReadResult<Uint8Array>;
      try {part=await Promise.race([reader.read(),new Promise<never>((_,reject)=>{timer=setTimeout(()=>reject(new Error("Body timeout")),remaining);})]);}
      finally {clearTimeout(timer);}
      if(part.done)break;length+=part.value.length;
      if(length>8192){await reader.cancel();return reply({error:"Report too large"},413);}
      chunks.push(part.value);
    }
    if (length>2048) return reply({error:"Report too large"},413);
    if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) return reply({error:"Expected JSON"},415);
    const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    body=new TextDecoder("utf-8",{fatal:true}).decode(bytes);
  } catch {try {await reader?.cancel();}catch {}return reply({error:"Invalid report"},400);}
  let report;
  try {report=validateReport(JSON.parse(body));} catch {return reply({error:"Invalid report"},400);}
  if (!report) return reply({error:"Invalid report"},400);
  if (!database) return reply({error:"Reporting unavailable"},503);
  const id="CH-"+crypto.randomUUID(),now=Date.now(),dayStart=Math.floor(now/86400000)*86400000;
  try {
    const results=await database.batch([
      database.prepare("DELETE FROM tv_reports WHERE created_at < ?").bind(now-90*86400000),
      database.prepare("INSERT INTO tv_reports (id, created_at, report) SELECT ?, ?, ? WHERE (SELECT COUNT(*) FROM tv_reports WHERE created_at >= ?) < 500 AND (SELECT COUNT(*) FROM tv_reports WHERE created_at >= ?) < 30").bind(id,now,JSON.stringify(report),dayStart,now-60000)
    ]);
    if (results[1].meta.changes!==1) return reply({error:"Reports busy. Please try later."},429);
    return reply({accepted:true,id},201);
  } catch {return reply({error:"Reporting unavailable"},503);}
}
