from sqlalchemy import Column, BLOB
from sqlmodel import SQLModel, Field

class TagValue(SQLModel, table=True):
    __tablename__ = 'tag_value'

    name: str = Field(index=True, primary_key=True)
    value: bytes = Field(sa_column=Column(BLOB))
    disabled: bool  | None = Field(default=False, nullable=True)
