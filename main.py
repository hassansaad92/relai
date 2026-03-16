from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse

from api import router
from database import init_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


app = FastAPI(title="Scheduling Assistant API", lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/overview")
async def overview():
    return FileResponse("index.html")


@app.get("/personnel")
async def personnel_page():
    return FileResponse("index.html")


@app.get("/projects")
async def projects_page():
    return FileResponse("index.html")


@app.get("/schedule")
async def schedule_page():
    return FileResponse("index.html")


@app.get("/skills")
async def skills_page():
    return FileResponse("index.html")


@app.get("/history")
async def history_page():
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
