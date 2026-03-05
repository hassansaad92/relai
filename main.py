from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import csv
from pathlib import Path

app = FastAPI(title="Scheduling Assistant API")

DATA_DIR = Path("data")
FRONTEND_DIST = Path("frontend/dist")


def read_csv(filename: str) -> list[dict]:
    """Read CSV file and return as list of dictionaries"""
    filepath = DATA_DIR / filename
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


# API routes
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


@app.get("/api/assignments")
async def get_assignments():
    """Get all current assignments"""
    return read_csv("assignments.csv")


@app.get("/api/assignment-history")
async def get_assignment_history():
    """Get full SCD2 assignment history"""
    return read_csv("assignment_history.csv")


# Serve frontend static files in production
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Serve React app for all non-API routes"""
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
