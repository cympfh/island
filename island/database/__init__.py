import contextlib
import sqlite3
from typing import Iterator


class RDB:
    def __init__(self, database: str, table: str, schema: str):
        self.con = sqlite3.connect(database)
        self.table = table
        self.schema = schema
        self.initialize()

    def initialize(self):
        """テーブルの初期化"""
        q = f"CREATE TABLE IF NOT EXISTS {self.table} {self.schema}"
        with self.execute(q, ()):
            pass

    @contextlib.contextmanager
    def execute(self, query: str, params: tuple):
        cur = self.con.cursor()
        cur.execute(query, params)
        yield cur
        cur.close()
        self.con.commit()

    def to_dict(self, item):
        raise NotImplementedError

    def insert(self, item) -> bool:
        """アイテムの挿入

        Returns
        -------
        インサートできたかどうか
        """
        d = self.to_dict(item)
        names = []
        values = []
        for name, value in d.items():
            names.append(name)
            values.append(value)
        fields = ",".join(names)
        num = len(names)
        placeholder = ",".join(["?"] * num)

        q = f"INSERT INTO {self.table}({fields}) VALUES ({placeholder})"
        with self.execute(q, tuple(values)) as cur:
            return cur.rowcount > 0

    def __len__(self) -> int:
        """レコード数"""
        q = f"SELECT COUNT(*) FROM {self.table}"
        with self.execute(q, ()) as cur:
            (count,) = cur.fetchone()
            return count

    def __iter__(self) -> Iterator:
        """レコードの全列挙"""
        q = f"SELECT * FROM {self.table}"
        with self.execute(q, ()) as cur:
            return iter(cur.fetchall())


class WorkDB(RDB):
    """作品

    References
    ----------
    - https://developers.annict.com/docs/rest-api/v1/works
    """

    def __init__(self):
        schema = """
        (
            id INTEGER PRIMARY KEY NOT NULL,
            title TEXT,
            image_url TEXT,
            dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().__init__("dataset/works.db", "works", schema)

    def to_dict(self, item: dict) -> dict:
        id = item["id"]
        title = item["title"]
        image_url = item["images"]["recommended_url"]
        return {
            "id": id,
            "title": title,
            "image_url": image_url,
        }


class ReviewDB(RDB):
    """作品への記録

    References
    ----------
    - https://developers.annict.com/docs/rest-api/v1/reviews
    """

    def __init__(self):
        schema = """
        (
            id INTEGER PRIMARY KEY NOT NULL,
            user_id INTEGER NOT NULL,
            work_id INTEGER NOT NULL,
            rating_overall_state TEXT,
            dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().__init__("dataset/reviews.db", "reviews", schema)

    def to_dict(self, item) -> dict:
        id = item["id"]
        user_id = item["user"]["id"]
        work_id = item["work"]["id"]
        rating_overall_state = item["rating_overall_state"]
        return {
            "id": id,
            "user_id": user_id,
            "work_id": work_id,
            "rating_overall_state": rating_overall_state,
        }


class RecordDB(RDB):
    """エピソードへの記録

    References
    ----------
    - https://developers.annict.com/docs/rest-api/v1/records
    """

    def __init__(self):
        schema = """
        (
            id INTEGER PRIMARY KEY NOT NULL,
            user_id INTEGER NOT NULL,
            work_id INTEGER NOT NULL,
            rating_state TEXT,
            dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().__init__("dataset/records.db", "records", schema)

    def to_dict(self, item) -> dict:
        id = item["id"]
        user_id = item["user"]["id"]
        work_id = item["work"]["id"]
        rating_state = item["rating_state"]
        return {
            "id": id,
            "user_id": user_id,
            "work_id": work_id,
            "rating_state": rating_state,
        }


class StaffDB(RDB):
    """スタッフ情報

    References
    ----------
    - https://developers.annict.com/docs/rest-api/v1/staffs
    """

    def __init__(self):
        schema = """
        (
            id INTEGER PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            work_id INTEGER NOT NULL,
            dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().__init__("dataset/staffs.db", "staffs", schema)

    def to_dict(self, item) -> dict:
        id = item["id"]
        name = item["name"]
        work_id = item["work"]["id"]
        return {
            "id": id,
            "name": name,
            "work_id": work_id,
        }
