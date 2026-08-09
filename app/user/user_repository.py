from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.user.user_schema import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        query = text("""
            SELECT email, password, username
            FROM users
            WHERE email = :email
        """)

        result = self.db.execute(
            query,
            {"email": email}
        ).mappings().first()

        if result is None:
            return None

        return User(
            email=result["email"],
            password=result["password"],
            username=result["username"]
        )

    def save_user(self, user: User) -> User:
        try:
            existing_user = self.get_user_by_email(str(user.email))

            if existing_user:
                query = text("""
                    UPDATE users
                    SET password = :password,
                        username = :username
                    WHERE email = :email
                """)
            else:
                query = text("""
                    INSERT INTO users (email, password, username)
                    VALUES (:email, :password, :username)
                """)

            self.db.execute(
                query,
                {
                    "email": str(user.email),
                    "password": user.password,
                    "username": user.username
                }
            )

            self.db.commit()
            return user

        except Exception:
            self.db.rollback()
            raise

    def delete_user(self, user: User) -> User:
        try:
            query = text("""
                DELETE FROM users
                WHERE email = :email
            """)

            self.db.execute(
                query,
                {"email": str(user.email)}
            )

            self.db.commit()
            return user

        except Exception:
            self.db.rollback()
            raise