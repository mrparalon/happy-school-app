import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated

import orjson
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Form,
    Header,
    Response,
)
from fastapi.responses import HTMLResponse
from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic.dataclasses import dataclass

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import FullUser

from .db_queries.select_students_by_parent_id_async_edgeql import (
    select_students_by_parent_id,
)

env = Environment(
    loader=PackageLoader("app.site.main"), autoescape=select_autoescape()
)

router = APIRouter()


class UserRole(str, Enum):
    teacher = "teacher"
    parent = "parent"


@dataclass
class ReviewCreateRequest:
    comment: str = Form(..., min_length=1)
    engagement: int = Form(..., gte=1, lte=5)
    focus: int = Form(..., gte=1, lte=5)


USERS = {
    "teacher@example.com": {"password": "password", "role": UserRole.teacher},
    "parent@example.com": {
        "password": "password",
        "role": UserRole.parent,
        "children_ids": ["1"],
    },
}

STUDENTS = [
    {
        "id": "1",
        "name": "John Doe",
        "grade": "4",
        "teacher": "Mrs. Smith",
    },
    {
        "id": "2",
        "name": "Jane Doe",
        "grade": "4",
        "teacher": "Mrs. Smith",
    },
]

REVIEWS = [
    {
        "student_id": "1",
        "created_at": "2023-12-30T20:17:07.651118",
        "comment": """ Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean sit amet molestie erat, non condimentum odio. Vivamus ex ex, sollicitudin eget arcu in, ornare varius neque. Lorem ipsum dolor sit amet, consectetur adipiscing elit. In sollicitudin ipsum sit amet magna egestas, a pharetra felis auctor. Duis a magna vitae massa lobortis gravida. Nunc bibendum eleifend ex eget faucibus. Maecenas vitae lectus id velit aliquam sagittis. Integer at dui pretium justo mattis fringilla a vehicula ipsum. Proin pretium dui ut odio fringilla, eu viverra mi cursus. Cras in varius sapien, quis malesuada nibh. Nam fermentum maximus pellentesque. Donec odio lacus, mollis sit amet lacus a, malesuada efficitur risus. Praesent mollis laoreet pharetra. Mauris laoreet metus a sagittis gravida. Ut consectetur aliquet placerat. Pellentesque venenatis nisl vitae orci aliquam, sit amet rhoncus sem pulvinar.

Nullam iaculis ullamcorper velit, id varius erat elementum ac. Pellentesque dapibus sollicitudin dignissim. Pellentesque porta bibendum massa sollicitudin vestibulum. Vivamus a risus ultricies, volutpat mauris ut, ornare turpis. Donec tellus felis, sollicitudin ultrices augue in, semper pellentesque diam. Maecenas mollis est purus, non tempor sapien maximus a. Vivamus sit amet pellentesque ex. Aenean tristique leo et velit dictum suscipit. Proin elementum nec risus vitae efficitur. Vivamus vitae nisl non elit viverra aliquam. """,
        "engagement": 3,
        "focus": 3,
    },
    {
        "student_id": "1",
        "created_at": "2023-11-30T20:17:07.651118",
        "comment": "\n    real review",
        "engagement": 2,
        "focus": 4,
    },
    {
        "student_id": "1",
        "created_at": "2023-10-30T20:17:07.651118",
        "comment": """ Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean sit amet molestie erat, non condimentum odio. Vivamus ex ex, sollicitudin eget arcu in, ornare varius neque. Lorem ipsum dolor sit amet, consectetur adipiscing elit. In sollicitudin ipsum sit amet magna egestas, a pharetra felis auctor. Duis a magna vitae massa lobortis gravida. Nunc bibendum eleifend ex eget faucibus. Maecenas vitae lectus id velit aliquam sagittis. Integer at dui pretium justo mattis fringilla a vehicula ipsum. Proin pretium dui ut odio fringilla, eu viverra mi cursus. Cras in varius sapien, quis malesuada nibh. Nam fermentum maximus pellentesque. Donec odio lacus, mollis sit amet lacus a, malesuada efficitur risus. Praesent mollis laoreet pharetra. Mauris laoreet metus a sagittis gravida. Ut consectetur aliquet placerat. Pellentesque venenatis nisl vitae orci aliquam, sit amet rhoncus sem pulvinar.

Nullam iaculis ullamcorper velit, id varius erat elementum ac. Pellentesque dapibus sollicitudin dignissim. Pellentesque porta bibendum massa sollicitudin vestibulum. Vivamus a risus ultricies, volutpat mauris ut, ornare turpis. Donec tellus felis, sollicitudin ultrices augue in, semper pellentesque diam. Maecenas mollis est purus, non tempor sapien maximus a. Vivamus sit amet pellentesque ex. Aenean tristique leo et velit dictum suscipit. Proin elementum nec risus vitae efficitur. Vivamus vitae nisl non elit viverra aliquam. """,
        "engagement": 5,
        "focus": 4,
    },
    {
        "student_id": "1",
        "created_at": "2023-09-30T20:17:07.651118",
        "comment": "\n    real review",
        "engagement": 4,
        "focus": 3,
    },
    {
        "student_id": "2",
        "created_at": "2023-08-30T20:17:07.651118",
        "comment": "\n    review for parent not exist",
        "engagement": 3,
        "focus": 3,
    },
]
USER_SESSIONS = {}


@router.get("/")
async def index(
    current_user: Annotated[FullUser | None, Depends(get_current_active_user)],
    hx_request: str | None = Header(None),
    db_client=Depends(get_db),
):
    if current_user is None:
        template = env.get_template("login.html")
        return HTMLResponse(template.render())
    if current_user.is_teacher:
        template = env.get_template("index_teacher.html")
        headers = {}
        if hx_request:
            headers["HX-redirect"] = "/"
        return HTMLResponse(
            template.render(students=STUDENTS), headers=headers
        )
    if current_user.is_parent:
        template = env.get_template("index_parent.html")
        kids = await select_students_by_parent_id(
            db_client, parent_user_id=current_user.id
        )
        return HTMLResponse(template.render(students=kids))
    return "Error, unknown user role"


@router.get("/login")
async def get_login_form(
    current_user: Annotated[str | None, Depends(get_current_active_user)]
):
    if current_user is not None:
        # redirect to index
        return Response(status_code=302, headers={"Location": "/"})
    return HTMLResponse(env.get_template("login.html").render())


@router.get("/signup")
async def get_signup_form(
    current_user: Annotated[str | None, Depends(get_current_active_user)]
):
    if current_user is not None:
        # redirect to index
        return Response(status_code=302, headers={"Location": "/"})
    return HTMLResponse(env.get_template("signup.html").render())


@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if email not in USERS:
        return "User not found"
    if USERS[email]["password"] != password:
        return "Incorrect password"
    token = str(uuid.uuid4())
    USER_SESSIONS[token] = email
    with open("sessions.json", "w") as f:
        f.write(orjson.dumps(USER_SESSIONS).decode())
    # Set cookie and redirect to index
    response = Response()
    response.set_cookie(key="token", value=token)
    response.headers["Location"] = "/"
    response.status_code = 302
    return response


@router.get("/logout")
async def logout(token: Annotated[str | None, Cookie()] = None):
    if not token:
        template = env.get_template("login.html")
        return HTMLResponse(template.render())
    USER_SESSIONS.pop(token, None)
    with open("sessions.json", "w") as f:
        f.write(orjson.dumps(USER_SESSIONS).decode())
    response = Response()
    response.set_cookie(key="token", value="")
    response.headers["Location"] = "/"
    response.status_code = 302
    return response


@router.get("/students/{student_id}/new-review")
async def get_new_review_form(
    current_user: Annotated[str | None, Depends(get_current_active_user)],
    student_id: str,
):
    if current_user is None:
        template = env.get_template("login.html")
        return HTMLResponse(template.render())
    template = env.get_template("new_review.html")
    student = next(s for s in STUDENTS if s["id"] == student_id)
    return HTMLResponse(template.render(student=student))


@router.post("/students/{student_id}/reviews")
async def post_new_review_form(
    current_user: Annotated[str | None, Depends(get_current_active_user)],
    student_id: str,
    request: ReviewCreateRequest = Depends(),
):
    if current_user is None:
        template = env.get_template("login.html")
        return HTMLResponse(template.render())

    REVIEWS.append(
        {
            "student_id": student_id,
            "created_at": datetime.now().isoformat(),
            "comment": request.comment,
            "engagement": request.engagement,
            "focus": request.focus,
        }
    )
    print(REVIEWS)
    template = env.get_template("new_review_success_button.html")
    return HTMLResponse(template.render())


@router.get("/students/{student_id}")
async def get_student(
    current_user: Annotated[str | None, Depends(get_current_active_user)],
    student_id: str,
):
    if current_user is None:
        template = env.get_template("login.html")
        return HTMLResponse(template.render())
    student = next(s for s in STUDENTS if s["id"] == student_id)
    template = env.get_template("student.html")
    reviews = [r for r in REVIEWS if r["student_id"] == student_id]
    return HTMLResponse(
        template.render(
            student=student,
            reviews=reviews,
            reviews_json=orjson.dumps(reviews).decode(),
        )
    )
