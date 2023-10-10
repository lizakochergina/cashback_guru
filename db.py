import sqlite3 as sql
import pandas as pd
import datetime
import numpy as np


db = sql.connect('recsys.db')
cursor = db.cursor()

async def db_connect():
    # global db, cursor
    # db = sql.connect('recsys.db')
    # cursor = db.cursor()
    query = "CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY, age INTEGER, gender TEXT, preferences TEXT," \
            "time_added TEXT, kids_flag TEXT, pets_flag TEXT, feedback INTEGER)"
    query2 = "CREATE TABLE IF NOT EXISTS items(item_id TEXT PRIMARY KEY, category TEXT, brand TEXT, " \
             "percent INTEGER, first_time INTEGER, text_info TEXT, days_left INTEGER, img_url TEXT)"
    query3 = "CREATE TABLE IF NOT EXISTS interactions(user_id TEXT PRIMARY KEY, item_id TEXT, feedback TEXT, timestamp TEXT)"
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
                "INSERT INTO users (user_id, age, gender, preferences, time_added, kids_flag, pets_flag,"
                "feedback) VALUES(?, ?, ?,'', ?, ?, ?, 0)",
                (user_id, data['age'], data["gender"], data["creation_time"], data["kids_flag"], data["pets_flag"]))
            db.commit()
    else:
        pass


async def get_categories(user_id):
    fav_categories = cursor.execute(
        "SELECT preferences FROM users WHERE user_id == '{key}'".format(
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
        "UPDATE users SET preferences = '{}' WHERE user_id = '{}'".format(
            new_categories, user_id))
    db.commit()


def load_users_data():
    df = pd.read_sql_query(
        "SELECT * FROM users",
        db,
        dtype={'user_id': np.uint64, 'age': np.uint64, 'gender': str, 'time_added': str,
               'kids_flag': str, 'pets_flag': str, 'feedback': np.uint64}
    )
    return df


def load_items_data():
    # df = pd.read_sql_query(
    #     "SELECT * FROM items",
    #     db,
    #     dtype={'item_id': np.uint64, 'category': str, 'brand': str, 'percent': np.uint64,
    #            'first_time': np.uint64, 'text_info': str, 'days_left': np.uint64 ,'img_url': str
    # })
    df = pd.read_csv('items.csv', dtype={'item_id': np.uint64, 'category': str, 'brand': str,
                                         'percent': np.uint64, 'first_time': np.uint64, 'text_info': str,
                                         'days_left': np.uint64 ,'img_url': str}).set_index('item_id')
    return df


def load_interactions_data():
    df = pd.read_sql_query(
        "SELECT * FROM interactions",
        db,
        dtype={'user_id': np.uint64, 'item_id': np.uint64, 'feedback': np.uint64, 'timestamp': str})
    return df
