from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    missing = [k for k, v in {"SUPABASE_RELAI_URL": SUPABASE_URL, "SUPABASE_RELAI_SECRET_KEY": SUPABASE_KEY}.items() if not v]
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Scheduling Assistant API")


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/overview")
async def overview():
    return FileResponse("index.html")


@app.get("/mechanics")
async def mechanics_page():
    return FileResponse("index.html")


@app.get("/projects")
async def projects_page():
    return FileResponse("index.html")


@app.get("/skills")
async def skills_page():
    return FileResponse("index.html")


@app.get("/api/mechanics")
async def get_mechanics():
    response = supabase.table("mechanics").select("*").execute()
    return response.data


@app.get("/api/projects")
async def get_projects():
    response = supabase.table("projects").select("*").execute()
    return response.data


@app.get("/api/skills")
async def get_skills():
    response = supabase.table("skills").select("*").execute()
    return response.data


@app.get("/api/assignments")
async def get_assignments():
    response = supabase.table("assignments").select("*").execute()
    return response.data


class MechanicCreate(BaseModel):
    name: str
    skills: str
    availability_status: str
    available_date: str


class ProjectCreate(BaseModel):
    name: str
    required_skills: str
    num_elevators: int
    start_date: str
    duration_weeks: int
    status: str


class SkillCreate(BaseModel):
    skill: str


@app.post("/api/mechanics")
async def create_mechanic(mechanic: MechanicCreate):
    response = supabase.table("mechanics").insert(mechanic.model_dump()).execute()
    print("INSERT mechanics response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create mechanic")
    return response.data[0]


@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    response = supabase.table("projects").insert(project.model_dump()).execute()
    print("INSERT projects response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create project")
    return response.data[0]


@app.post("/api/skills")
async def create_skill(skill: SkillCreate):
    response = supabase.table("skills").insert(skill.model_dump()).execute()
    print("INSERT skills response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create skill")
    return response.data[0]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
