"""分享大锅饭 - 帖子 CRUD"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import Post, User
from app.schemas.common import ok

router = APIRouter(prefix="/api/posts", tags=["posts"])


class PostCreate(BaseModel):
    title: str
    content: str = ""
    tags: Optional[str] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None


@router.get("")
def list_posts(
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Post).order_by(Post.created_at.desc())
    if keyword:
        q = q.filter(Post.title.contains(keyword))
    posts = q.all()
    result = []
    for p in posts:
        author = db.query(User).filter(User.id == p.author_id).first()
        result.append({
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "tags": p.tags,
            "author_id": p.author_id,
            "author_name": author.name if author else "未知",
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })
    return result


@router.post("")
def create_post(
    body: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = Post(
        author_id=current_user.id,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return ok({"id": post.id})


@router.get("/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "帖子不存在")
    author = db.query(User).filter(User.id == post.author_id).first()
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "tags": post.tags,
        "author_id": post.author_id,
        "author_name": author.name if author else "未知",
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@router.patch("/{post_id}")
def update_post(
    post_id: int,
    body: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "帖子不存在")
    if post.author_id != current_user.id and not current_user.is_platform_admin:
        raise HTTPException(403, "只能编辑自己的帖子")
    if body.title is not None:
        post.title = body.title
    if body.content is not None:
        post.content = body.content
    if body.tags is not None:
        post.tags = body.tags
    db.commit()
    return ok()


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "帖子不存在")
    if post.author_id != current_user.id and not current_user.is_platform_admin:
        raise HTTPException(403, "只能删除自己的帖子")
    db.delete(post)
    db.commit()
    return ok()
