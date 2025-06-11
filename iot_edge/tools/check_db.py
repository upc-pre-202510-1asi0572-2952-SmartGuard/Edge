import sqlite3

conn = sqlite3.connect("access_events.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM access_events")
for row in cursor.fetchall():
    print(row)
