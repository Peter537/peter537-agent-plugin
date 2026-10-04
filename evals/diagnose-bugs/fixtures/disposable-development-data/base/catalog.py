import sqlite3


def refresh(connection):
    if connection.execute("PRAGMA user_version").fetchone()[0]:
        return
    connection.execute("CREATE TABLE teams(name TEXT PRIMARY KEY)")
    connection.executemany("INSERT INTO teams VALUES (?)", [("North",), ("South",)])
    connection.execute("PRAGMA user_version = 2")


def old_database():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE teams(name TEXT PRIMARY KEY)")
    connection.execute("INSERT INTO teams VALUES ('North')")
    connection.execute("CREATE TABLE notes(body TEXT)")
    connection.execute("INSERT INTO notes VALUES ('Synthetic saved note')")
    connection.execute("PRAGMA user_version = 1")
    return connection
