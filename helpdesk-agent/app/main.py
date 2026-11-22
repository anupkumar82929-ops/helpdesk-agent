from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .agent import HelpdeskService

service = HelpdeskService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.start()
    yield
    await service.stop()


app = FastAPI(title="HR/IT Helpdesk Agent", lifespan=lifespan)


class ChatIn(BaseModel):
    message: str


@app.post("/chat")
async def chat(body: ChatIn):
    r = await service.ask(body.message)
    return {"answer": r.answer, "status": r.status, "redactions": r.redactions}


@app.get("/health")
async def health():
    return {"ok": True}


PAGE = """<!doctype html><meta charset=utf-8><title>HR/IT Helpdesk</title>
<style>
body{font-family:system-ui;max-width:720px;margin:2rem auto;padding:0 1rem}
#log{border:1px solid #ccc;border-radius:8px;padding:1rem;height:60vh;overflow:auto;white-space:pre-wrap}
.u{color:#0645ad;margin-top:.8rem}.a{margin-top:.2rem}.s{font-size:.75rem;color:#888}
form{display:flex;gap:.5rem;margin-top:1rem}input{flex:1;padding:.6rem}button{padding:.6rem 1rem}
</style>
<h2>Acme HR/IT Helpdesk</h2><div id=log></div>
<form id=f><input id=q placeholder="e.g. How many leave days does E102 have left?" autofocus><button>Send</button></form>
<script>
const log=document.getElementById('log');
function add(c,t){const d=document.createElement('div');d.className=c;d.textContent=t;log.appendChild(d);log.scrollTop=log.scrollHeight;return d}
f.onsubmit=async e=>{e.preventDefault();const m=q.value.trim();if(!m)return;q.value='';
add('u','You: '+m);const w=add('a','...');
const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});
const j=await r.json();w.textContent=j.answer;
add('s','status: '+j.status+(j.redactions.length?' | redacted: '+j.redactions.join(', '):''))}
</script>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return PAGE
