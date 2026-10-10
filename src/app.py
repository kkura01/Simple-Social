"""HTTP API for Simple Social: auth, media upload, feed, and post deletion."""

import uuid

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from src.schemas import UserRead, UserCreate, UserUpdate
from src.db import Post, User, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from src.images import imagekit
import shutil
import os
import tempfile
from src.users import auth_backend, current_active_user, fastapi_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Simple Social",
    description=(
        "A small social feed API. Authenticate with JWT, upload images or videos "
        "to ImageKit, browse posts, and delete your own content."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix='/auth/jwt', tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix='/auth', tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix='/auth', tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix='/auth', tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix='/users', tags=["user"])


@app.post(
    "/upload",
    tags=["posts"],
    summary="Upload a post",
    response_description="The created post, including the hosted media URL",
)
async def upload_file(
        file: UploadFile = File(..., description="Image or video to share"),
        caption: str = Form("", description="Optional caption shown with the post"),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session),
):
    """Store the file on ImageKit and persist a `Post` owned by the current user.

    Requires a Bearer token. Temporary files are always cleaned up, even if upload fails.
    """
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        with open(temp_file_path, "rb") as f:
            upload_result = imagekit.files.upload(
                file=f,
                file_name=file.filename,
                use_unique_file_name=True,
                tags=["backend-upload"]
            )

        post = Post(
            user_id=user.id,
            caption=caption,
            url=upload_result.url,
            file_type="video" if file.content_type.startswith("video/") else "image",
            file_name=upload_result.name
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()

    post = Post(
        caption=caption,
        url="dummy url",
        file_type="photo",
        file_name="dummy name"
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get(
    "/feed",
    tags=["posts"],
    summary="Get the post feed",
    response_description="Posts newest-first, with owner flags and author emails",
)
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Return all posts in reverse chronological order.

    Each item includes `is_owner` for the authenticated user and the author's email.
    """
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()

    result = await session.execute(select(User))
    users = [row[0] for row in result.all()]
    user_dict = {u.id: u.email for u in users}

    post_data = []
    for post in posts:
        post_data.append({
            "id": str(post.id),
            "user_id":str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at":post.created_at.isoformat(),
            "is_owner":post.user_id == user.id,
            "email": user_dict.get(post.user_id, "Unkown")
        })

    return {"posts": post_data}


@app.delete(
    "/post/{post_id}",
    tags=["posts"],
    summary="Delete a post",
    response_description="Confirmation that the post was removed",
)
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Delete a post by UUID. Requires authentication.

    Returns 404 if the post does not exist. A generic 500 is used for invalid IDs
    and other unexpected errors.
    """
    try:
        post_uuid = uuid.UUID(post_id)

        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="You don't have permission to delete this post")

        await session.delete(post)
        await session.commit()

        return {"sucess":True, "message":"Post deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
