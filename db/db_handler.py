import os
from pathlib import Path

import orjson
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select, text

from models.tag_values import TagValue

DB_FOLDER = Path(__file__).resolve().parent / 'data'
DB_NAME = 'values.db'

class DBHandler:

    def __init__(
            self,
            db_folder=DB_FOLDER,
            db_name=DB_NAME
    ):
        super().__init__()

        self.db_folder = db_folder
        self.db_name = db_name

        self.engine = self.init_db()


    def init_db(self):
        os.makedirs(self.db_folder, exist_ok=True)
        db_path = self.db_folder / self.db_name
        engine = create_engine(f'sqlite:///{db_path}')

        if not os.path.exists(db_path):
            SQLModel.metadata.create_all(engine)
        return engine

    def save_data(self, data: list):
        rows_to_insert = []
        for el in data:
            name = el.get('name')
            disabled = el.get('disabled')
            if '.' in name:
                name = name.replace('.', '_')
            value = orjson.dumps({"value": el["value"]})
            item = {"name" :name, "value": value, "disabled": disabled}
            rows_to_insert.append(item)
        print(rows_to_insert)

        with self.engine.connect() as conn:
            stmt = text('''
            INSERT INTO tag_value (name, value, disabled) 
            VALUES (:name, :value, :disabled) 
            ON CONFLICT(name) DO UPDATE 
            SET value = excluded.value;
            ''')

            conn.execute(stmt, rows_to_insert)
            conn.commit()


    def get_data(self, data: dict):
        with Session(self.engine) as session:
            items = None
            if data is not None:
                items = data.get('data')

            stmt = select(TagValue)
            if items is not None:
                stmt = stmt.where(TagValue.name.in_(items))

            results = session.exec(stmt).all()

            data = []

            for row in results:
                data_dict = orjson.loads(row.value)
                value = data_dict.get('value')
                disabled = data_dict.get('disabled')
                item = {
                    "name": row.name,
                    "value": value,
                    "disabled": disabled
                }
                data.append(item)

            result = {
                "timestamp": None,
                "data": data
            }
        return result
