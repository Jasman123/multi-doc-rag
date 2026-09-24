import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, *, email: str, hashed_password: str, role: UserRole = UserRole.user) -> User:
    user = User(email=email, hashed_password=hashed_password, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def bump_token_version(db: AsyncSession, user: User) -> None:
    user.token_version += 1
    await db.commit()

async def list_user(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User))
    return list(result.scalars().all())