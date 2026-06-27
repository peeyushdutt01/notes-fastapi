from sqlalchemy import create_engine, select, delete, or_, and_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from datetime import date, datetime
import uuid


class Base(DeclarativeBase):
    pass

class Note(Base):
    __tablename__ = "Notes"
    
    id : Mapped[int] = mapped_column(primary_key=True)
    title : Mapped[str] = mapped_column(nullable=False)
    content : Mapped[str] = mapped_column(nullable=False)
    modified_at : Mapped[datetime] = mapped_column(default= datetime.now, onupdate=datetime.now)
    created_at : Mapped[datetime] = mapped_column(default= datetime.now)
    is_pinned : Mapped[bool] = mapped_column(default = False)
    is_archived : Mapped[bool] = mapped_column(default = False)

class User(Base):
    __tablename__ = "user"
    
    id: Mapped[str] = mapped_column(
        primary_key=True, 
        default= lambda: str(uuid.uuid4())
        )
    username : Mapped[str] = mapped_column(unique=True, nullable=False)
    email : Mapped[str] = mapped_column(unique=True, nullable=False)
    password : Mapped[str] = mapped_column(nullable=False)

engine = create_engine("sqlite:///notes.db")

Base.metadata.create_all(bind=engine)

def get_note(note_id):
    if note_id:
        with Session(engine) as session:
            statement = select(Note).where(Note.id == note_id)
            note = session.scalars(statement).all()
            return note
    else:
        with Session(engine) as session:
            statement = select(Note)
            notes = session.scalars(statement).all()
            return notes

def add_note(data : Note):
    with Session(engine) as session:
        session.add(data)
        session.commit()

def delete_note_by_id(note_id : int):
    with Session(engine) as session:
        statement = delete(Note).where(Note.id == note_id)
        result = session.execute(statement)
        session.commit()
        
        return result.rowcount > 0
            
def update_note_by_id(note_id : int, data:Note):
    with Session(engine) as session:
        statement = select(Note).where(Note.id == note_id)
        note = session.scalars(statement).one_or_none()
        if note == None :
            return note
        note.title = data.title
        note.content = data.content
    
        session.commit()
        
def show_users():
    with Session(engine) as session:
        statement = select(User)
        users = session.scalars(statement).all()
        return users
    
def register(data:User):
    with Session(engine) as session:
        already_user = session.execute(
            select(User).
            where(
            or_(
                User.id == data.id,
                User.email == data.email
                )
            )
        )
        if already_user:
            return None
        session.add(data)
        session.commit()
        return data
    
def login(data:User):
    with Session(engine) as session:
        statement = select(User).where(
            and_(
                User.username == data.username,
                User.email == data.email
                )
            )
        success = session.scalars(statement).first()
        return success

         