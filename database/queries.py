from sqlalchemy import select,delete,update,insert,func
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker
from datetime import date,timedelta
from .models import Event,Association,User
#user counter
async def orm_count_users(session: AsyncSession,event_id: int):
    stmt = select(func.count()).select_from(Association).where(Association.event_id==event_id)
    result=await session.scalar(stmt)
    return result
#events related queries
async def orm_read_events_user(session: AsyncSession):
    stmt=select(Event).where(Event.event_date >= date.today()).order_by(Event.event_date.desc())
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_read_events_admin(session: AsyncSession, admin_id: int):
    stmt=select(Event).where(Event.event_date >= date.today(),Event.creator_id==admin_id).order_by(Event.event_date.desc())
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_read_tommorow_events(session: AsyncSession):
    tomorrow = date.today() + timedelta(days=1)
    stmt = select(Event).where(Event.event_date == tomorrow)
    result = await session.scalars(stmt)
    return result.all()
            
async def orm_read_search_events(session: AsyncSession,data: dict):
    conditions = []
    for field, value in data.items():
        column= getattr(Event, field)
        if value == "gay":
            conditions.append(column == None)
        elif value is not None:
            conditions.append(column == value)
    stmt=select(Event).where(*conditions).order_by(Event.event_date.desc())
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_read_past_events_admin(session: AsyncSession, admin_id: int):
    stmt=select(Event).where(Event.event_date <= date.today(),Event.state==True,Event.creator_id==admin_id).order_by(Event.event_date.desc())
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_read_event_limit(session: AsyncSession,event_id: int):
    stmt=select(Event.limit).where(Event.id == event_id)
    return await session.scalar(stmt)

async def orm_read_event_point(session: AsyncSession,event_id: int):
    stmt=select(Event.point).where(Event.id == event_id)
    return await session.scalar(stmt)

async def orm_read_event_age_limit(session: AsyncSession,event_id: int):
    stmt=select(Event.required_age).where(Event.id == event_id)
    return await session.scalar(stmt)

async def orm_read_event_state(session: AsyncSession,event_id: int):
    stmt=select(Event.state).where(Event.id == event_id)
    return await session.scalar(stmt)

async def orm_add_event(session: AsyncSession,data: dict[str]):
    obj=Event(
        name=data["event_name"],
        point=data["event_point"],
        description=data["event_description"],
        city=data["event_city"],
        event_date=data["event_date"],
        limit=data["event_limit"],
        required_age=data["event_age"],
        creator_id=data["creator_id"],
        album=data["event_media"]
        )
    session.add(obj)
    await session.commit()

async def orm_delete_event(session: AsyncSession,event_id: int):
    stmt=delete(Event).where(Event.id==event_id)
    await session.execute(stmt)
    await session.commit()

async def orm_read_event_name(session: AsyncSession,event_id: int):
    stmt=select(Event.name).where(Event.id == event_id)
    return await session.scalar(stmt)

async def orm_update_event(session: AsyncSession,data: dict[str]):
    stmt=update(Event).where(Event.id==data["id"]).values(
        name = data["event_name"],
        point=data["event_point"],
        description=data["event_description"],
        city=data["event_city"],
        event_date=data["event_date"],
        limit=data["event_limit"],
        required_age=data["event_age"],
        album=data["event_media"]
        )
    await session.execute(stmt)
    await session.commit()

async def orm_cancel_event(session: AsyncSession,event_id):
    stmt=update(Event).where(Event.id==event_id).values(
        state=False
        )
    await session.execute(stmt)
    await session.commit()

async def orm_read_event(session: AsyncSession,event_id: int):
    stmt=select(Event).where(Event.id == event_id)
    return await session.scalar(stmt)

#users related queries
async def orm_read_user(session: AsyncSession,user_id: int):
    stmt=select(User).where(User.user_id == user_id)
    return await session.scalar(stmt)

async def orm_add_user(session: AsyncSession,data: dict[str]):
    obj=User(
        user_id=data["user_id"],
        name=data["user_name"],
        surname=data["user_surname"],
        fathers_name=data["user_fname"],
        birth_date=data["user_date"],
        phone_number=data["user_number"]
        )
    session.add(obj)
    await session.commit()

async def orm_update_user(session: AsyncSession,data: dict[str]):
    stmt=update(User).where(User.user_id==data["user_id"]).values(
        name=data["user_name"],
        surname=data["user_surname"],
        fathers_name=data["user_fname"],
        birth_date=data["user_date"],
        phone_number=data["user_number"]
        )
    await session.execute(stmt)
    await session.commit()

async def orm_delete_user(session: AsyncSession,user_id: int):
    stmt=delete(User).where(User.user_id==user_id)
    await session.execute(stmt)
    await session.commit()

#associations-users related queries

async def orm_register(session: AsyncSession,user_id: int,event_id: int):
    obj=Association(
        user_id=user_id,
        event_id=event_id
        )
    session.add(obj)
    await session.commit()

async def orm_deregister(session: AsyncSession,user_id: int,event_id: int):
    stmt=delete(Association).where(Association.event_id==event_id,Association.user_id==user_id)
    await session.execute(stmt)
    await session.commit()

async def orm_read_association(session: AsyncSession,user_id: int,event_id: int):
    stmt= select(Association).where(Association.user_id==user_id,Association.event_id==event_id)
    return await session.scalar(stmt)

async def orm_users_past_events(session: AsyncSession,user_id: int):
    stmt=select(Event,Association.was_there).join(Association).where(Association.user_id==user_id,Association.was_there==True,Event.state==True,Event.event_date <= date.today()).order_by(Event.event_date.desc())
    result=await session.execute(stmt)
    return result.all()

async def orm_users_future_events(session: AsyncSession,user_id: int):
    stmt=select(Event,Association.was_there).join(Association).where(Association.user_id==user_id,Association.was_there==None,Event.event_date >= date.today()).order_by(Event.event_date.desc())
    result=await session.execute(stmt)
    return result.all()

#associations-events related queries

async def orm_user_list(session: AsyncSession,event_id: int):
    stmt=select(User).join(Association).where(Association.event_id==event_id)
    result=await session.scalars(stmt)
    return result.all()

async def orm_update_status(session: AsyncSession,association: Association,state: bool):
    association.was_there = state
    await session.commit()

async def orm_update_balance(session: AsyncSession,user_id: int,number: int):
    user = await session.get(User,user_id)
    user.balance += number
    await session.commit()