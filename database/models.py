from sqlalchemy import Date, ForeignKey, String, Text, BigInteger,Boolean,Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date
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
    associations: Mapped[list["Association"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class Event(MyBase):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    point: Mapped[int] = mapped_column(BigInteger, default=0)
    description: Mapped[str] = mapped_column(Text)
    state: Mapped[bool] = mapped_column(Boolean, default=True)
    event_date: Mapped[date] = mapped_column(Date)
    limit: Mapped[int]=mapped_column(BigInteger,nullable=True)
    required_age: Mapped[int]=mapped_column(Integer,nullable=True)
    city: Mapped[str] = mapped_column(String(200))
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