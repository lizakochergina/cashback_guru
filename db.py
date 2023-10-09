import sqlite3 as sql


async def db_connect():
    global db, cursor  # это зачем
    db = sql.connect('recsys.db')
    cursor = db.cursor()
    query = "CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY, gender TEXT, age INTEGER, preferences TEXT," \
            "time_added TEXT)"
    query2 = "CREATE TABLE IF NOT EXISTS items(item_id TEXT PRIMARY KEY, category TEXT, brand TEXT, percent INTEGER, first_time" \
             "INTEGER, text_info TEXT, days_left INTEGER)"
    cursor.execute(query)
    cursor.execute(query2)
    db.commit()


async def user_exists(user_id):
    user = cursor.execute(
        "SELECT user_id FROM users WHERE user_id == '{key}'".format(key=user_id)).fetchone()
    if not user:
        return False
    return True
