from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.auth.auth import router as auth_router
from app.api.v1.classes.classes import router as classes_router
from app.api.v1.homeworks.routes import router as homeworkes_router
from app.api.v1.parents.routes import router as parents_router
from app.api.v1.students.students import router as students_router
from app.api.v1.subjects.subjects import router as subjects_router
from app.api.v1.teachers.teachers import router as teacheres_router
from app.config import settings
from app.dependencies.tg import client
from app.site.auth import router as site_auth_router
from app.site.main import router as site_main_router

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await client.connect()
    await client.sign_in(bot_token=settings.BOT_TOKEN)
    yield
    client.disconnect()


# Set all CORS enabled origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(classes_router, prefix="/api/v1/classes", tags=["Classes"])
app.include_router(
    students_router, prefix="/api/v1/students", tags=["Sturdents"]
)
app.include_router(parents_router, prefix="/api/v1/parents", tags=["Parents"])
app.include_router(
    subjects_router, prefix="/api/v1/subjects", tags=["Subjects"]
)
app.include_router(
    teacheres_router, prefix="/api/v1/teachers", tags=["Teachers"]
)
app.include_router(
    homeworkes_router, prefix="/api/v1/homeworks", tags=["Homework"]
)
app.include_router(site_auth_router, tags=["Site"])
app.include_router(site_main_router, tags=["Site"])
