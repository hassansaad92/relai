from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import csv
from pathlib import Path

app = FastAPI(title="Scheduling Assistant API")

DATA_DIR = Path("data")


def read_csv(filename: str) -> list[dict]:
    """Read CSV file and return as list of dictionaries"""
    filepath = DATA_DIR / filename
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("index.html")


@app.get("/overview")
async def overview():
    """Serve the main HTML page for overview route"""
    return FileResponse("index.html")


@app.get("/mechanics")
async def mechanics_page():
    """Serve the main HTML page for mechanics route"""
    return FileResponse("index.html")


@app.get("/projects")
async def projects_page():
    """Serve the main HTML page for projects route"""
    return FileResponse("index.html")


@app.get("/skills")
async def skills_page():
    """Serve the main HTML page for skills route"""
    return FileResponse("index.html")


@app.get("/api/mechanics")
async def get_mechanics():
    """Get all mechanics"""
    return read_csv("mechanics.csv")


@app.get("/api/projects")
async def get_projects():
    """Get all projects"""
    return read_csv("projects.csv")


@app.get("/api/skills")
async def get_skills():
    """Get all skills"""
    return read_csv("skills.csv")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
