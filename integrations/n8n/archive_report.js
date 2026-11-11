// Separate branch after HTML, alongside the original email branch.
// Bind N8N_WEBHOOK_SECRET in n8n; allow built-in crypto.
// Normalize seat/stage from the trigger and set the live session label.
const crypto=require('crypto');
const secret=$env.OBE_REPORT_WEBHOOK_SECRET;
if(!secret||secret.length<32)throw new Error('Report signing is not configured');
return $input.all().map((item,index)=>{
 const body={event_id:String($execution.id)+':'+index,issued_at:Math.floor(Date.now()/1000),report:{
  session:'CONFIGURE_LIVE_SESSION_LABEL',seat:item.json.seat,attempt:1,
  stage:item.json.stage,filename:item.json.seat+'_'+item.json.stage+'.html',
  extension:'html',content_base64:Buffer.from(item.json.html,'utf8').toString('base64')}};
 const rawBody=JSON.stringify(body);
 return {json:{rawBody,signature:crypto.createHmac('sha256',secret).update(rawBody).digest('hex')}};
});
// HTTP Request POST /integrations/n8n/report/; raw JSON body rawBody;
// X-OBE-Signature header signature. Grading and email nodes stay unchanged.
