from sqlalchemy import select,delete,update,func,or_
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker
from datetime import date,timedelta
from .models import Event,Association,User,Request,Report
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
        if value is not None:
            if field == "name":
                words = value.split()
                or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                conditions.append(or_block)
            elif field == "city":
                words = value.split()
                or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                conditions.append(or_block)
            elif value == "gay":
                conditions.append(column == None)
            else:
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
        phone_number=data["user_number"],
        username=data["user_username"]
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

async def orm_update_balance(session: AsyncSession,user_id: int,number: int):
    user = await session.get(User,user_id)
    user.balance += number
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


#requests related queries

async def orm_add_request(session: AsyncSession,data: dict[str]):
    obj=Request(
        name=data["request_name"],
        description=data["request_description"],
        address=data["request_address"],
        user_id=data["user_id"],
        album=data["request_album"],
        username=data["username"],
        phone_number=data["phone_number"]
        )
    session.add(obj)
    await session.commit()

async def orm_update_request(session: AsyncSession,data: dict[str]):
    stmt=update(Request).where(Request.id==data["id"]).values(
        name=data["request_name"],
        description=data["request_description"],
        address=data["request_address"],
        album=data["request_album"],
        phone_number=data["phone_number"]
        )
    await session.execute(stmt)
    await session.commit()

async def orm_read_my_active_requests(session: AsyncSession, user_id: str):
    stmt=select(Request).where(Request.user_id==user_id, or_(Request.status=="Рассматривается",Request.status=="В ожидании"))
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_read_my_past_requests(session: AsyncSession, user_id: str):
    stmt=select(Request).where(Request.user_id==user_id, or_(Request.status=="Отклонено",Request.status=="Обработано"))
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_delete_request(session: AsyncSession, request_id: int):
    stmt=delete(Request).where(Request.id==request_id)
    await session.execute(stmt)
    await session.commit()

async def orm_read_request_name(session: AsyncSession, request_id: int):
    stmt=select(Request.name).where(Request.id == request_id)
    return await session.scalar(stmt)

async def orm_read_request(session: AsyncSession, request_id: str):
    stmt=select(Request).where(Request.id ==request_id)
    return await session.scalar(stmt)

async def orm_read_search_requests(session: AsyncSession,data: dict):
    conditions = []
    for field, value in data.items():
        column= getattr(Request, field)
        if value is not None:
            if field == "created_at":
                conditions.append(func.date(column)==value)
            elif field == "name":
                words = value.split()
                or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                conditions.append(or_block)
            elif field == "address":
                words = value.split()
                or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                conditions.append(or_block)
            else:    
                conditions.append(column == value)
    stmt=select(Request).where(*conditions).order_by(Request.created_at.desc())
    scar_result=await session.scalars(stmt)
    return scar_result.all()

async def orm_change_request_state(session: AsyncSession, state: bool, request_id: int):
    stmt=update(Request).where(Request.id==request_id).values(
        state=state
        )
    await session.execute(stmt)
    await session.commit()

async def orm_change_request_status(session: AsyncSession, status: str, request_id: int):
    stmt=update(Request).where(Request.id==request_id).values(
        status=status
        )
    await session.execute(stmt)
    await session.commit()

async def orm_change_request_comment(session: AsyncSession, data: dict[str,int]):
    stmt=update(Request).where(Request.id==data["request_id"]).values(
        comment=data["comment_text"]
        )
    await session.execute(stmt)
    await session.commit()

#raports related queries

async def orm_read_search_reports(session: AsyncSession,data: dict):
    conditions = []
    status = data.get("status")
    if status == "пропустить":
        conditions_requ = []
        conditions_repo = []
        for field, value in data.items():
            if field == "status":
                column_requ = getattr(Request, field)
                conditions_requ.append(column_requ == "Отклонено")
            else:
                column_requ = getattr(Request, field)
                column_repo = getattr(Report, field)
                if value is not None:
                    if field == "created_at":
                        conditions_repo.append(func.date(column_repo)==value)
                        conditions_requ.append(func.date(column_requ)==value)
                    elif field == "name":
                        words = value.split()
                        or_block_requ = or_(*[column_requ.ilike(f"%{word}%") for word in words])
                        or_block_repo = or_(*[column_repo.ilike(f"%{word}%") for word in words])
                        conditions_requ.append(or_block_requ)
                        conditions_repo.append(or_block_repo)
                    elif field == "address":
                        words = value.split()
                        or_block_requ = or_(*[column_requ.ilike(f"%{word}%") for word in words])
                        or_block_repo = or_(*[column_repo.ilike(f"%{word}%") for word in words])
                        conditions_requ.append(or_block_requ)
                        conditions_repo.append(or_block_repo)
                    else:    
                        conditions_requ.append(column_requ == value)
                        conditions_repo.append(column_repo == value)
        stmt_requ=select(Request).where(*conditions_requ).order_by(Request.created_at.desc())
        scar_result_requ=await session.scalars(stmt_requ)
        requ_result = scar_result_requ.all()
        stmt_repo=select(Report).where(*conditions_repo).order_by(Report.created_at.desc())
        scar_result_repo=await session.scalars(stmt_repo)
        repo_result = scar_result_repo.all()
        return [*repo_result,*requ_result]
    if status == "отчет":
        for field, value in data.items():
            if field == "status":
                continue
            column= getattr(Report, field)
            if value is not None:
                if field == "created_at":
                    conditions.append(func.date(column)==value)
                elif field == "name":
                    words = value.split()
                    or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                    conditions.append(or_block)
                elif field == "address":
                    words = value.split()
                    or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                    conditions.append(or_block)
                elif field == "status":
                    continue
                else:    
                    conditions.append(column == value)
        stmt=select(Report).where(*conditions).order_by(Report.created_at.desc())
        scar_result=await session.scalars(stmt)
        return scar_result.all()
    if status == "отказ":
        for field, value in data.items():
            column= getattr(Request, field)
            if value is not None:
                if field == "created_at":
                    conditions.append(func.date(column)==value)
                elif field == "name":
                    words = value.split()
                    or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                    conditions.append(or_block)
                elif field == "address":
                    words = value.split()
                    or_block = or_(*[column.ilike(f"%{word}%") for word in words])
                    conditions.append(or_block)
                elif value == "отказ":
                    conditions.append(column == "Отклонено")
                else:    
                    conditions.append(column == value)
        stmt=select(Request.comment).where(*conditions).order_by(Request.created_at.desc())
        scar_result=await session.scalars(stmt)
        return scar_result.all()

async def orm_add_report(session: AsyncSession,data: dict[str]):
    obj=Report(
        name=data["report_name"],
        description=data["report_description"],
        address=data["report_address"],
        user_id=data["user_id"],
        album=data["report_media"],
        username=data["username"],
        request_id=data["request_id"],
        phone_number=data["phone_number"]
        )
    session.add(obj)
    await session.commit()

async def orm_read_report(session: AsyncSession,request_id: int):
    stmt = select(Report).where(Report.request_id == int(request_id))
    return await session.scalar(stmt)

        