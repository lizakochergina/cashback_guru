import sqlite3 as sql
import pandas as pd
import datetime
import numpy as np

db = sql.connect('recsys.db')
cursor = db.cursor()


async def db_connect():
    query = "CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, age INTEGER, sex TEXT, categories TEXT," \
            "timestamp TEXT, kids_flag INTEGER, pets_flag INTEGER, feedback INTEGER, cur_page INTEGER, last_rec_id INTEGER, last_rec_seen INTEGER, last_msg_id INTEGER)"
    query2 = "CREATE TABLE IF NOT EXISTS items(item_id INTEGER, cashback TEXT, condition TEXT, exp_date_txt TEXT, category TEXT, brand TEXT, first_time INTEGER, text_info TEXT, img_url TEXT)"
    query3 = "CREATE TABLE IF NOT EXISTS interactions(user_id INTEGER, item_id INTEGER, feedback TEXT, timestamp TEXT," \
             "PRIMARY KEY (user_id, item_id, timestamp))"
    cursor.execute(query)
    cursor.execute(query2)
    cursor.execute(query3)
    db.commit()


async def user_exists(user_id):
    user = cursor.execute(
        "SELECT user_id FROM users WHERE user_id == '{key}'".format(key=user_id)).fetchone()
    if not user:
        return False
    return True


async def create_profile(state, user_id):
    user = cursor.execute(
        "SELECT user_id FROM users WHERE user_id == '{key}'".format(
            key=user_id)).fetchone()
    if not user:
        async with state.proxy() as data:
            cursor.execute(
                "INSERT INTO users (user_id, age, sex, categories, timestamp, kids_flag, pets_flag,"
                "feedback, cur_page, last_rec_id, last_rec_seen, last_msg_id) VALUES(?, ?, ?,'', ?, ?, ?, 0, 1, -1, -1, -1)",
                (user_id, data['age'], data["sex"], data["creation_time"], data["kids_flag"], data["pets_flag"]))
            db.commit()
    else:
        pass


async def get_categories(user_id):
    fav_categories = cursor.execute(
        "SELECT categories FROM users WHERE user_id == '{key}'".format(
            key=user_id)).fetchone()[0]
    delimiter = ';'
    if fav_categories == "":
        return list()
    fav_categories = fav_categories.split(delimiter)
    return fav_categories


async def write_categories(user_id, new_categories):
    delimiter = ';'
    new_categories = delimiter.join(new_categories)
    cursor.execute(
        "UPDATE users SET categories = '{}' WHERE user_id = '{}'".format(
            new_categories, user_id))
    db.commit()


def load_users_data():
    df = pd.read_sql_query(
        "SELECT * FROM users",
        db,
        dtype={'user_id': np.uint64, 'age': np.uint64, 'sex': str, 'timestamp': str, 'categories': str,
               'kids_flag': np.uint64, 'pets_flag': np.uint64, 'feedback': np.int64, 'cur_page': np.uint64,
               'last_rec_id': np.int64, 'last_rec_seen': np.int64, 'last_msg_id': np.int64}
    ).set_index("user_id")
    return df


def load_items_data():
    df = pd.read_sql_query(
        "SELECT * FROM items",
        db,
        dtype={'item_id': np.uint64, 'category': str, 'brand': str,
               'cashback': str, 'first_time': np.uint64, 'text_info': str,
               'exp_date_txt': str, 'img_url': str, 'condition': str})

    # df = pd.read_csv('items.csv', dtype={'item_id': np.uint64, 'category': str, 'brand': str,
    #                                      'cashback': str, 'first_time': np.uint64, 'text_info': str,
    #                                      'exp_date_txt': str, 'img_url': str, 'condition': str})
    return df


def load_interactions_data():
    df = pd.read_sql_query(
        "SELECT * FROM interactions",
        db,
        dtype={'user_id': np.uint64, 'item_id': np.uint64, 'feedback': np.int64, 'timestamp': str})
    return df


def write_feedback(user_id, item_id, reaction, timestamp):
    cursor.execute(
        "UPDATE users SET feedback = '{}' WHERE user_id = '{}'".format(
            1, user_id))
    cursor.execute(
        "INSERT INTO interactions (user_id, item_id, feedback, timestamp) VALUES(?, ?, ?, ?)",
        (user_id, item_id, reaction, timestamp))
    db.commit()


async def save_current_page(user_id, page):
    cursor.execute(
        "UPDATE users SET cur_page = '{}' WHERE user_id = '{}'".format(
            page, user_id))
    db.commit()


async def get_current_page(user_id):
    cur_page = cursor.execute(
        "SELECT cur_page FROM users WHERE user_id == '{key}'".format(
            key=user_id)).fetchone()[0]
    return cur_page


async def get_interactions(user_id):
    user_interactions = cursor.execute(
        "SELECT * FROM interactions WHERE user_id == '{key}'".format(
            key=user_id)).fetchall()
    return user_interactions


async def write_rec_id(user_id, item_id):
    cursor.execute(
        "UPDATE users SET last_rec_id = '{}', last_rec_seen = '{}' WHERE user_id = '{}'".format(
            item_id, 0, user_id))
    db.commit()


async def write_msg_id(user_id, msg_id):
    cursor.execute(
        "UPDATE users SET last_msg_id = '{}' WHERE user_id = '{}'".format(
            msg_id, user_id))
    db.commit()


async def mark_last_rec(user_id):
    cursor.execute("UPDATE users SET last_rec_seen = '{}' WHERE user_id = '{}'".format(
        1, user_id))
    db.commit()


async def check_last_seen_rec(user_id):
    last_seen_info = cursor.execute(
        "SELECT last_rec_id, last_rec_seen FROM users WHERE user_id == '{key}'".format(
            key=user_id)).fetchone()
    return last_seen_info


async def get_last_msg_id(user_id):
    last_seen_info = cursor.execute(
        "SELECT last_msg_id FROM users WHERE user_id == '{key}'".format(
            key=user_id)).fetchone()
    return last_seen_info
