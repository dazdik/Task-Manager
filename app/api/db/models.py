from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import (DeclarativeBase, Mapped, declared_attr,
                            mapped_column, relationship)


class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"


class TaskStatus(PyEnum):
    CREATED = "created"
    AT_WORK = "at work"
    ON_CHECK = "on check"
    FROZEN = "frozen"
    CANCEL = "cancel"
    FINISHED = "finished"


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls):
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)


class UserTasksAssociation(Base):
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "task_id",
            name="unique_user_task",
        ),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))

    user: Mapped["User"] = relationship(back_populates="user_detail")
    task: Mapped["Task"] = relationship(back_populates="task_detail")


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default=datetime.now,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER.name, server_default="USER"
    )
    user_detail: Mapped[list["UserTasksAssociation"]] = relationship(
        back_populates="user"
    )


class Task(Base):
    name: Mapped[str] = mapped_column(String(155))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default=datetime.now,
    )
    urgency: Mapped[bool] = mapped_column(default=False, server_default="false")
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.CREATED.name, server_default="CREATED"
    )

    task_detail: Mapped[list["UserTasksAssociation"]] = relationship(
        back_populates="task"
    )
