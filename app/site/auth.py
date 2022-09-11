import base64
import hashlib
import secrets

import httpx
from edgedb import AsyncIOClient
from fastapi import (
    APIRouter,
    Cookie,
    Form,
    HTTPException,
    Request,
    Response,
)
from fastapi.param_functions import Depends
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings
from app.dependencies.db import get_db
from app.dependencies.db_queries.create_parent_with_identity_async_edgeql import (
    create_parent_with_identity,
)
from app.dependencies.db_queries.get_email_from_current_identity_async_edgeql import (
    get_email_from_current_identity,
)

SERVER_PORT = 3000

router = APIRouter()

auth_client = httpx.AsyncClient(base_url=settings.EDGEDB_AUTH_BASE_URL)


def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def generate_pkce():
    verifier = secrets.token_urlsafe(32)
    challenge = hashlib.sha256(verifier.encode()).digest()
    challenge = base64url_encode(challenge)
    return {"verifier": verifier, "challenge": challenge}


@router.post("/auth/signup")
async def handle_sign_up(
    db: AsyncIOClient = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    provider: str = Form(...),
):
    pkce = generate_pkce()
    register_response = await auth_client.post(
        "/register",
        json={
            "challenge": pkce["challenge"],
            "email": email,
            "password": password,
            "provider": provider,
            "verify_url": f"http://localhost:{settings.SERVER_PORT}/auth/verify",
        },
    )

    if register_response.status_code != 201:
        raise HTTPException(
            status_code=400,
            detail=f"Error from the auth server: {register_response.text}",
        )
    create_parent_response = await create_parent_with_identity(
        db,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )

    # Set cookie and return response
    response = Response(status_code=200, content="Email have been sent")
    response.set_cookie(
        key="edgedb_pkce_verifier",
        value=pkce["verifier"],
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response


@router.post("/auth/signup/parent", response_class=HTMLResponse)
async def handle_sign_up_parent(
    db: AsyncIOClient = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
):
    # check token
    identity = await get_email_from_current_identity(db)
    if identity is None:
        # TODO redirect to login
        raise HTTPException(
            status_code=400,
            detail="Could not find identity for current user",
        )

    await create_parent_with_identity(
        db,
        first_name=first_name,
        last_name=last_name,
        email=identity.email,
    )

    return Response(status_code=302, headers={"Location": "/"})


@router.post("/auth/signin")
async def handle_sign_in(
    email: str = Form(...),
    password: str = Form(...),
    provider: str = Form(...),
):
    pkce = generate_pkce()
    authenticate_response = await auth_client.post(
        "/authenticate",
        json={
            "challenge": pkce["challenge"],
            "email": email,
            "password": password,
            "provider": provider,
        },
    )
    if authenticate_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Error from the auth server: {authenticate_response.text}",
        )

    code = authenticate_response.json().get("code")
    token_response = await auth_client.get(
        "/token", params={"code": code, "verifier": pkce["verifier"]}
    )
    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Error from the auth server: {token_response.text}",
        )

    auth_token = token_response.json().get("auth_token")
    # TODO: return template or redirect to index
    response = Response(status_code=302, headers={"Location": "/"})
    response.set_cookie(
        key="edgedb_auth_token",
        value=auth_token,
        httponly=True,
        path="/",
        secure=True,
        samesite="strict",
    )
    return response


@router.get("/auth/verify")
async def handle_verify(
    verification_token: str,
    edgedb_pkce_verifier: str = Cookie(...),
):
    verify_response = await auth_client.post(
        "/verify",
        json={
            "verification_token": verification_token,
            "verifier": edgedb_pkce_verifier,
            "provider": "builtin::local_emailpassword",
        },
    )
    if verify_response.status_code != 200:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"Error from the auth server: {verify_response.text}"
            },
        )

    code = verify_response.json()["code"]
    token_response = await auth_client.get(
        "/token",
        params={"code": code, "verifier": edgedb_pkce_verifier},
    )

    if token_response.status_code != 200:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"Error from the auth server: {token_response.text}"
            },
        )

    auth_token, identity_id = (
        token_response.json()["auth_token"],
        token_response.json()["identity_id"],
    )
    # user = await select_user_by_email(
    #     email=verify_response.json()["email"],
    # )

    # select identity by id from auth token
    # than get user by email from identity
    # if exists - update user with identity id
    # else - return form with essential user fields

    response = Response(status_code=204)
    response.set_cookie(
        key="edgedb_auth_token",
        value=auth_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response


@router.get("/auth/callback")
async def handle_callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    edgedb_pkce_verifier: str | None = Cookie(None),
):
    if not code:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"OAuth callback is missing 'code'. OAuth provider responded with error: {error}"
            },
        )

    if not edgedb_pkce_verifier:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Could not find 'verifier' in the cookie store. "
                "Is this the same user agent/browser that started the authorization flow?"
            },
        )

    code_exchange_response = await auth_client.get(
        "/token", params={"code": code, "verifier": edgedb_pkce_verifier}
    )

    if code_exchange_response.status_code != 200:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"Error from the auth server: {code_exchange_response.text}"
            },
        )

    auth_token = code_exchange_response.json()["auth_token"]

    response = Response(status_code=204)
    response.set_cookie(
        key="edgedb_auth_token", value=auth_token, path="/", httponly=True
    )
    return response


@router.post("/auth/send-password-reset-email")
async def handle_send_password_reset_email(email: str = Form(...)):
    # TODO: move host to env var
    reset_url = (
        f"http://localhost:{settings.SERVER_PORT}/auth/ui/reset-password"
    )
    provider = "builtin::local_emailpassword"
    pkce = generate_pkce()

    send_reset_response = await auth_client.post(
        "/send-reset-email",
        json={
            "email": email,
            "provider": provider,
            "reset_url": reset_url,
            "challenge": pkce["challenge"],
        },
    )
    if send_reset_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Error from auth server: {send_reset_response.text}",
        )

    email_sent = await send_reset_response.json()["email_sent"]
    response = Response(
        status_code=200, content=f"Reset email sent to '{email_sent}'"
    )
    response.set_cookie(
        key="edgedb_pkce_verifier",
        value=pkce["verifier"],
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response


@router.get("/auth/ui/reset-password", response_class=HTMLResponse)
async def handle_ui_reset_password(request: Request):
    reset_token = request.query_params.get("reset_token")
    return f"""
    <html>
      <body>
        <form method="POST" action="http://localhost:{settings.SERVER_PORT}/auth/reset-password">
          <input type="hidden" name="reset_token" value="{reset_token}">
          <label>
            New password:
            <input type="password" name="password" required>
          </label>
          <button type="submit">Reset Password</button>
        </form>
      </body>
    </html>
    """


@router.post("/auth/reset-password")
async def handle_reset_password(
    reset_token: str = Form(...),
    password: str = Form(...),
    edgedb_pkce_verifier: str | None = Cookie(None),
):
    provider = "builtin::local_emailpassword"
    if not edgedb_pkce_verifier:
        raise HTTPException(
            status_code=400, detail="Verifier missing in cookie store"
        )

    reset_response = await auth_client.post(
        "/reset-password",
        json={
            "reset_token": reset_token,
            "provider": provider,
            "password": password,
        },
    )
    if reset_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Error from the auth server: {reset_response.text}",
        )

    code = reset_response.json().get("code")
    token_response = await auth_client.get(
        "/token", params={"code": code, "verifier": edgedb_pkce_verifier}
    )
    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Error from the auth server: {token_response.text}",
        )

    auth_token = token_response.json().get("auth_token")
    response = Response(status_code=204)
    response.set_cookie(
        key="edgedb_auth_token",
        value=auth_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response
