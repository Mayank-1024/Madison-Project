import json,uuid
js=lambda f:open('js/'+f).read().strip()
nodes=[];conns={}
SAFE={"retryOnFail":True,"maxTries":3,"waitBetweenTries":2000,"onError":"continueRegularOutput","alwaysOutputData":True}
def node(name,type_,ver,pos,params,**extra):
    n={"parameters":params,"id":str(uuid.uuid4()),"name":name,"type":type_,"typeVersion":ver,"position":pos}
    n.update(extra);nodes.append(n)
def link(a,b,idx=0):
    conns.setdefault(a,{"main":[[]]})["main"][0].append({"node":b,"type":"main","index":idx})
def hf(name,ds,pos):
    node(name,"n8n-nodes-base.httpRequest",4.2,pos,{
      "url":"https://datasets-server.huggingface.co/rows","sendQuery":True,
      "queryParameters":{"parameters":[{"name":"dataset","value":ds},{"name":"config","value":"default"},{"name":"split","value":"train"},{"name":"offset","value":"0"},{"name":"length","value":"100"}]},
      "options":{"timeout":20000}},**SAFE)
def rss(name,url,pos):
    node(name,"n8n-nodes-base.rssFeedRead",1.2,pos,{"url":url,"options":{}},**SAFE)
def code(name,f,pos,**extra):
    node(name,"n8n-nodes-base.code",2,pos,{"jsCode":js(f)},**extra)
def sticky(content,pos,w,h,color):
    node(f"Note {len(nodes)}","n8n-nodes-base.stickyNote",1,pos,{"content":content,"width":w,"height":h,"color":color})

sticky("## ① Collect\n3 sources, 6 requests. Every fetch retries 3× (2 s apart) and **continues on error**, so a slow or broken source never stops the run.",[180,-300],460,1260,7)
sticky("## ② Normalize\nEach source is mapped into the same 16-column schema. Failed/empty sources log **\"Source unavailable: …\"**.",[680,-300],440,1260,4)
sticky("## ③ Quality checks\nTrim text · dates → YYYY-MM-DD · drop records missing title/date/source · remove duplicates · flag incomplete fields.",[1160,-300],440,1260,5)
sticky("## ④ Save\nCSV of clean records + JSON quality report. Download from the node output, or find them in `/home/node/.n8n-files/`.",[1640,-300],680,1260,6)

node("Start Collection","n8n-nodes-base.manualTrigger",1,[0,380],{})
hf("Fetch Ad Copy (HuggingFace)","jaykin01/advertisement-copy",[320,-160])
hf("Fetch Campaigns (HuggingFace)","federicomoreno/marketing-campaign-performance-200k",[320,80])
feeds=[("RSS: MarTech","https://martech.org/feed/"),("RSS: Marketing Dive","https://www.marketingdive.com/feeds/news/"),("RSS: HubSpot Marketing Blog","https://blog.hubspot.com/marketing/rss.xml"),("RSS: Social Media Examiner","https://www.socialmediaexaminer.com/feed/")]
for i,(n,u) in enumerate(feeds): rss(n,u,[320,320+i*200])
code("Map Ad Copy","map_ads.js",[780,-160])
code("Map Campaigns","map_campaigns.js",[780,80])
node("Merge RSS Feeds","n8n-nodes-base.merge",3.2,[600,560],{"numberInputs":4})
code("Map RSS Articles","map_rss.js",[780,560])
node("Merge All Sources","n8n-nodes-base.merge",3.2,[1010,200],{"numberInputs":3})
code("Quality Checks & Cleaning","quality.js",[1260,200])
code("Records to Rows","to_rows.js",[1720,60])
code("Build Quality Report","report.js",[1720,380])
node("Convert to CSV","n8n-nodes-base.convertToFile",1.1,[1920,60],{"options":{"fileName":"madison_a3_records.csv"}})
node("Convert Report to JSON","n8n-nodes-base.convertToFile",1.1,[1920,380],{"operation":"toJson","options":{"fileName":"madison_a3_quality_report.json","format":True}})
node("Save CSV to Disk","n8n-nodes-base.readWriteFile",1,[2120,60],{"operation":"write","fileName":"/home/node/.n8n-files/madison_a3_records.csv","options":{}},onError="continueRegularOutput")
node("Save Report to Disk","n8n-nodes-base.readWriteFile",1,[2120,380],{"operation":"write","fileName":"/home/node/.n8n-files/madison_a3_quality_report.json","options":{}},onError="continueRegularOutput")

for n in ["Fetch Ad Copy (HuggingFace)","Fetch Campaigns (HuggingFace)"]+[f[0] for f in feeds]: link("Start Collection",n)
link("Fetch Ad Copy (HuggingFace)","Map Ad Copy"); link("Fetch Campaigns (HuggingFace)","Map Campaigns")
for i,(n,_) in enumerate(feeds): link(n,"Merge RSS Feeds",i)
link("Merge RSS Feeds","Map RSS Articles")
link("Map Ad Copy","Merge All Sources",0); link("Map Campaigns","Merge All Sources",1); link("Map RSS Articles","Merge All Sources",2)
link("Merge All Sources","Quality Checks & Cleaning")
link("Quality Checks & Cleaning","Records to Rows"); link("Quality Checks & Cleaning","Build Quality Report")
link("Records to Rows","Convert to CSV"); link("Convert to CSV","Save CSV to Disk")
link("Build Quality Report","Convert Report to JSON"); link("Convert Report to JSON","Save Report to Disk")

wf={"name":"Bhadrasen_Mayank_A3 – Madison Action Layer Data Pipeline","nodes":nodes,"connections":conns,"pinData":{},"settings":{"executionOrder":"v1"},"active":False,"meta":{"templateCredsSetupCompleted":True},"tags":[]}
out='/Users/mayank/Desktop/BrandingAI/Assignment_3/Bhadrasen_Mayank_A3_Workflow.json'
json.dump(wf,open(out,'w'),indent=2,ensure_ascii=False)
print(len([n for n in nodes if n['type']!='n8n-nodes-base.stickyNote']),'nodes ->',out)
