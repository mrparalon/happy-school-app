from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.auth.auth import router as auth_router
from app.api.v1.classes.classes import router as classes_router

app = FastAPI()

# Set all CORS enabled origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, tags=["auth"])
app.include_router(classes_router, tags=["classes"])
