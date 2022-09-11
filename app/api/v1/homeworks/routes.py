from uuid import UUID

import orjson
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import allow_access, get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import FullUser
from app.server.router import TrailingSlashAPIRouter

from ....schemas.homeworks import (
    CreateHomeworkPayload,
    Homework,
    HomeworksList,
    UpdateHomeworkPayload,
)

router = TrailingSlashAPIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_homeworks(
    payload: CreateHomeworkPayload,
    db_client=Depends(get_db),
    _=Depends(allow_access(teacher=True)),
) -> HomeworksList:
    try:
        created_homeworks = await db_client.query_json(
            """
            with new_homeworks := (

            with student_ids_unpacked := array_unpack(<array<uuid>>$student_ids)
                for student_id in student_ids_unpacked union (
                    INSERT Homework {
                        assigned_by := (
                            select Teacher filter .id = <uuid>$teacher_id
                            ),
                        assigned_to := (
                            select Student filter .id = student_id
                            ),
                        assignment := <str>$assignment,
                        subject := (
                            select Subject filter .id = <uuid>$subject_id
                            ),
                        deadline := <datetime>$deadline,
                        }
                    )
                ),
            SELECT new_homeworks {
                id,
                updated_at,
                created_at,
                deadline,
                assignment,
                done_by_student,
                grade,
                assigned_to: {
                    id,
                    updated_at,
                    created_at,
                    user: {
                        id,
                        first_name,
                        last_name,
                        username,
                        status
                    },
                    class: {
                        id,
                        updated_at,
                        created_at,
                        name,
                        year
                    }
                },
                assigned_by: {
                    id,
                    updated_at,
                    created_at,
                    user: {
                        id,
                        first_name,
                        last_name,
                        username,
                        status
                    },
                    subjects: {
                        id,
                        updated_at,
                        created_at,
                        name,
                    },
                    classes: {
                        id,
                        updated_at,
                        created_at,
                        name,
                        year,
                        },
                },
                subject: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
            };
            """,
            subject_id=payload.subject_id,
            student_ids=payload.assigned_to,
            teacher_id=payload.assigned_by,
            deadline=payload.deadline,
            assignment=payload.assignment,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    return HomeworksList(data=orjson.loads(created_homeworks))


@router.get("/")
async def get_homeworkss(
    db_client=Depends(get_db), _: FullUser = Depends(get_current_active_user)
) -> HomeworksList:
    homeworkes = await db_client.query_json(
        """
            SELECT Homework {
                id,
                updated_at,
                created_at,
                deadline,
                assignment,
                done_by_student,
                grade,
                assigned_to: {
                    id,
                    updated_at,
                    created_at,
                    user: {
                        id,
                        first_name,
                        last_name,
                        username,
                        status
                    },
                    class: {
                        id,
                        updated_at,
                        created_at,
                        name,
                        year
                    }
                },
                assigned_by: {
                    id,
                    updated_at,
                    created_at,
                    user: {
                        id,
                        first_name,
                        last_name,
                        username,
                        status
                    },
                    subjects: {
                        id,
                        updated_at,
                        created_at,
                        name,
                    },
                    classes: {
                        id,
                        updated_at,
                        created_at,
                        name,
                        year,
                        },
                },
                subject: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
            };
            """
    )
    homework_data = orjson.loads(homeworkes)
    return HomeworksList(data=homework_data)


@router.get("/{homeworks_id}")
async def get_homeworks_by_id(
    homeworks_id: UUID,
    db_client=Depends(get_db),
    user: FullUser = Depends(allow_access(teacher=True, student=True)),
) -> Homework:
    homework = await db_client.query_single_json(
        """
            SELECT Homework {
                id,
                updated_at,
                created_at,
                deadline,
                assignment,
                done_by_student,
                grade,
                assigned_to: {
                    id,
                    updated_at,
                    created_at,
                    user: {
                        id,
                        first_name,
                        last_name,
                        username,
                        status
                    },
                    class: {
                        id,
                        updated_at,
                        created_at,
                        name,
                        year
                    }
                },
                assigned_by: {
                    id,
                    updated_at,
                    created_at,
                    user: {
                        id,
                        first_name,
                        last_name,
                        username,
                        status
                    },
                    subjects: {
                        id,
                        updated_at,
                        created_at,
                        name,
                    },
                    classes: {
                        id,
                        updated_at,
                        created_at,
                        name,
                        year,
                        },
                },
                subject: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
            }
            filter
                .id = <uuid>$homeworks_id and
                (.assigned_to.user.id = <uuid>$user_id or
                        .assigned_by.user.id = <uuid>$user_id)


            """,
        homeworks_id=homeworks_id,
        user_id=user.id,
    )
    if homework == "null":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return Homework(**orjson.loads(homework))


@router.patch("/{homework_id}")
async def update_homework_by_id(
    payload: UpdateHomeworkPayload,
    homework_id: UUID,
    db_client=Depends(get_db),
    user: FullUser = Depends(allow_access(teacher=True, student=True)),
) -> Homework:
    errors = []
    if user.is_teacher is False:
        if payload.grade is not None:
            errors.append("Student can't set grade")
        if payload.assignment is not None:
            errors.append("Student can't change assignment")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="; ".join(errors)
        )
    if query_args := payload.model_dump(exclude_none=True):
        query = """
            update Homework filter
                .id = <uuid>$homework_id and
                (.assigned_to.user.id = <uuid>$user_id or
                        .assigned_by.user.id = <uuid>$user_id)
            set {
        """
        if payload.grade is not None:
            query += """
                grade := <optional int32>$grade,
            """
        if payload.done_by_student is not None:
            query += """
                done_by_student := <optional bool>$done_by_student,
            """
        if payload.assignment is not None:
            query += """
                assignment := <optional str>$assignment,
            """
        query += "}"

        await db_client.query_single_json(
            query, homework_id=homework_id, user_id=user.id, **query_args
        )
    homework = await db_client.query_single_json(
        """
        SELECT Homework {
            id,
            updated_at,
            created_at,
            deadline,
            assignment,
            done_by_student,
            grade,
            assigned_to: {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                },
                class: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year
                }
            },
            assigned_by: {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                },
                subjects: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
                classes: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year,
                    },
            },
            subject: {
                id,
                updated_at,
                created_at,
                name,
            },
            }

            filter
                .id = <uuid>$homework_id and
                (.assigned_to.user.id = <uuid>$user_id or
                        .assigned_by.user.id = <uuid>$user_id)
            ;
            """,
        user_id=user.id,
        homework_id=homework_id,
    )

    return Homework(**orjson.loads(homework))
