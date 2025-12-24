from sqlalchemy import Date, ForeignKey, String, Text, BigInteger,Boolean,Integer,DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date,datetime
class MyBase(DeclarativeBase):
  pass

class User(MyBase):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, primary_key=True)
    balance: Mapped[int] = mapped_column(BigInteger, default=0)
    name: Mapped[str] = mapped_column(String(150))
    surname: Mapped[str] = mapped_column(String(150))
    fathers_name: Mapped[str] = mapped_column(String(150))
    birth_date: Mapped[date] = mapped_column(Date)
    phone_number: Mapped[str] = mapped_column(String(20))
    username: Mapped[str] = mapped_column(String(33),nullable=True)
    associations: Mapped[list["Association"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class Event(MyBase):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    point: Mapped[int] = mapped_column(BigInteger, default=0)
    description: Mapped[str] = mapped_column(Text)
    state: Mapped[bool] = mapped_column(Boolean, default=True)
    event_date: Mapped[date] = mapped_column(Date)
    limit: Mapped[int]=mapped_column(BigInteger,nullable=True)
    required_age: Mapped[int]=mapped_column(Integer,nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    creator_id: Mapped[str] = mapped_column(BigInteger)
    album: Mapped[str] = mapped_column(Text,nullable=True)
    associations: Mapped[list["Association"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class Association(MyBase):
    __tablename__ = "associations"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    was_there: Mapped[bool] = mapped_column(Boolean, nullable=True)
    user: Mapped["User"] = relationship(back_populates="associations")
    event: Mapped["Event"] = relationship(back_populates="associations")

class Request(MyBase):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(String(33),nullable=True)
    album: Mapped[str] = mapped_column(Text,nullable=True)
    address: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime,default = lambda: datetime.now().replace(second=0,microsecond=0))
    status: Mapped[str] = mapped_column(String,default="В ожидании")
    phone_number: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(String,nullable=True)
    state: Mapped[bool] = mapped_column(Boolean, default=False)
    report: Mapped["Report"] = relationship(back_populates="request",uselist=False)

class Report(MyBase):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(String(33),nullable=True)
    album: Mapped[str] = mapped_column(Text,nullable=True)
    address: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    phone_number: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime,default = lambda: datetime.now().replace(second=0,microsecond=0))
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"),unique=True)
    request: Mapped["Request"] = relationship(back_populates="report")