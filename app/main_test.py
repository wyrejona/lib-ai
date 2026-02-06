from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path

app = FastAPI()
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat")
async def chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/files")
async def files(request: Request):
    return templates.TemplateResponse("files.html", {"request": request})

@app.get("/api/engine-status")
async def status():
    return JSONResponse({
        "chatModel": "llama2:7b",
        "embeddingModel": "nomic-embed-text",
        "vectorStore": "Ready",
        "ollamaStatus": "Connected"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
