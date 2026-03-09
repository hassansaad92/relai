from fastapi import FastAPI
from fastapi.responses import FileResponse

from api import router

app = FastAPI(title="Scheduling Assistant API")

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


@app.get("/skills")
async def skills_page():
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
