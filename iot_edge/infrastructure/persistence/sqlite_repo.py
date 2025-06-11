import sqlite3
from iot_edge.domain.models.access_event import AccessEvent

class SQLiteAccessRepository:
    def __init__(self, db_path="access_events.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS access_events (
                user_id TEXT,
                timestamp TEXT,
                result TEXT,
                method TEXT
            )        
        ''')
        self.conn.commit()

    def save(self, event: AccessEvent):
        self.conn.execute(
            "INSERT INTO access_events VALUES (?, ?, ?, ?)",
            (event.user_id, event.timestamp, event.result, event.method)
        )
        self.conn.commit()