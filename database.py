from sqlalchemy import create_engine, select, delete, or_, and_, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from datetime import date, datetime
import uuid


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "Notes"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    modified_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_pinned: Mapped[bool] = mapped_column(default=False)
    is_archived: Mapped[bool] = mapped_column(default=False)


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    refresh_token : Mapped[str | None] = mapped_column(nullable=True)


engine = create_engine("sqlite:///notes.db")

Base.metadata.create_all(bind=engine)


def get_note(note_id: str, user_id: str):
    if note_id:
        with Session(engine) as session:
            statement = select(Note).where(
                and_(Note.id == note_id, Note.user_id == user_id)
            )
            note = session.scalars(statement).all()
            return note
    else:
        with Session(engine) as session:
            statement = select(Note).where(Note.user_id == user_id)
            notes = session.scalars(statement).all()
            return notes


def add_note(data: Note):
    with Session(engine) as session:
        session.add(data)
        session.commit()

        return {
            "id": data.id,
            "title": data.title,
            "content": data.content,
            "modified_at": data.modified_at,
            "created_at": data.created_at,
            "is_pinned": data.is_pinned,
            "is_archived": data.is_archived,
        }


def delete_note_by_id(note_id: str, user_id: str):
    with Session(engine) as session:
        statement = delete(Note).where(
            and_(Note.id == note_id, Note.user_id == user_id)
        )
        result = session.execute(statement)
        session.commit()

        return result.rowcount > 0


def update_note_by_id(note_id: str, user_id: str, data: dict):
    with Session(engine) as session:
        statement = select(Note).where(
            and_(Note.id == note_id, Note.user_id == user_id)
        )
        note = session.scalar(statement)

        if note == None:
            return None

        for key, value in data.items():
            setattr(note, key, value)

        session.commit()
        session.refresh(note)

        return note


def show_users():
    with Session(engine) as session:
        statement = select(User)
        users = session.scalars(statement).all()
        return users


def register(data: User):
    with Session(engine) as session:
        already_user = session.scalar(
            select(User).where(or_(User.id == data.id, User.email == data.email))
        )
        if already_user != None:
            return None
        session.add(data)
        session.commit()
        return data


# def login(data: User):
#     with Session(engine) as session:
#         statement = select(User).where(
#             or_(User.username == data.username, User.email == data.email)
#         )
#         success = session.scalars(statement).first()
#         return success


def login(identifier: str):
    with Session(engine) as session:
        return session.scalar(
            select(User).where(
                or_(
                    User.username == identifier,
                    User.email == identifier
                )
            )
        )


def add_refresh_token(data : dict, refresh_token:str):
    with Session(engine) as session:
        statement = select(User).where(
            User.id == data["sub"]
        )
        user = session.scalar(statement)
        
        user.refresh_token = refresh_token
        
        session.commit()
        session.refresh(user)
        
    return refresh_token
        
def validate_refresh_token(data : dict,refresh_token:str):
    with Session(engine) as session:
        user = session.get(User, data["sub"])

        if user is None:
            return None

        if user.refresh_token == refresh_token:
            return data

        return None
    
def logout(data: dict):
    try:
        with Session(engine) as session:
            user_data = session.scalar(
                select(User).where(
                    and_(
                        User.refresh_token == data["refresh_token"],
                        User.id == data["sub"]
                    )
                )
            )
            if user_data is None:
                return None   
            user_data.refresh_token = None
            session.commit()
            return True
    except Exception as e:
        print(f"Logout error: {e}")
        return None
