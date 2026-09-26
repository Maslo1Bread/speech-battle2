import sqlite3

c = sqlite3.connect("speech_battle.db")
print("tables", c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("users", c.execute("select id, role, status, age from users").fetchall())
print("count", c.execute("select count(*) from users").fetchone())
