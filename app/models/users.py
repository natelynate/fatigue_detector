# app/models/users.py
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional
from ..core.database import Base
from ..core.security import get_password_hash, verify_password

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'operation'}  # Set the schema

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    joined = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    @classmethod
    async def create(cls, db_session, email: str, password: str) -> "User":
        """
        Create a new user with hashed password
        """
        hashed_password = get_password_hash(password)
        user = cls(
            email=email,
            password=hashed_password,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @classmethod
    async def get_by_email(cls, db_session, email: str) -> Optional["User"]:
        """
        Get a user by email
        """
        return await db_session.query(cls).filter(cls.email == email).first()

    @classmethod
    async def authenticate(cls, db_session, email: str, password: str) -> Optional["User"]:
        """
        Authenticate a user by email and password
        """
        user = await cls.get_by_email(db_session, email)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def update_last_login(self, db_session):
        """
        Update the last login timestamp
        """
        self.last_login = datetime.utcnow()
        db_session.add(self)
        return self

    def __repr__(self):
        return f"<User {self.email}>"