from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api.pubg_routes import router as pubg_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PUBG Battle Analytics", version="1.0.0")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[MIDDLEWARE] {request.method} {request.url}")
    response = await call_next(request)
    print(f"[MIDDLEWARE] Response: {response.status_code}")
    return response

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(pubg_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search")
async def search_player(player_name: str = Form(...)):
    """플레이어 검색 폼 처리"""
    return RedirectResponse(url=f"/player/{player_name}", status_code=303)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)