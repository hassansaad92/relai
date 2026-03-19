from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api import router
from database import init_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


app = FastAPI(title="Scheduling Assistant API", lifespan=lifespan)

app.include_router(router)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

FRONTEND_INDEX = "frontend/index.html"


@app.get("/")
async def root():
    return FileResponse(FRONTEND_INDEX)


@app.get("/overview")
async def overview():
    return FileResponse(FRONTEND_INDEX)


@app.get("/personnel")
async def personnel_page():
    return FileResponse(FRONTEND_INDEX)


@app.get("/projects")
async def projects_page():
    return FileResponse(FRONTEND_INDEX)


@app.get("/schedule")
async def schedule_page():
    return FileResponse(FRONTEND_INDEX)


@app.get("/skills")
async def skills_page():
    return FileResponse(FRONTEND_INDEX)


@app.get("/history")
async def history_page():
    return FileResponse(FRONTEND_INDEX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
