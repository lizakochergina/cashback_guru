import pandas as pd
import numpy as np
from db import load_users_data, load_items_data, load_interactions_data
from model import EASE, StupidRecommender


class DataManager:
    def __init__(self):
        """
            need to load data from database

            users = pd.DataFrame(cols={user_id, age, sex, categories, timestamp, kids_flag, pets_flag, feedback})
            items = pd.DataFrame(cols={item_id, category, brand, percent, first_time,
                                       text_info, days_left, img_url})
            interactions = pd.DataFrame(cols={user_id, item_id, feedback, timestamp})
        """
        self.users = load_users_data()
        self.items = load_items_data()
        self.interactions = load_interactions_data()

        self.users.to_csv('users.csv', index=False)
        self.items.to_csv('items.csv', index=False)
        self.interactions.to_csv('interactions.csv', index=False)

        self.n_items = len(self.items)
        self.n_ml_mode = 7

    def get_recs(self, user_id, k=1):
        if len(self.users) < self.n_ml_mode:
            model = StupidRecommender()
            return model.predict(user_id, self.users, self.items, self.interactions, k)
        else:
            model = EASE()
            model.fit(self.interactions)
            return model.predict(user_id)

    def get_item_data(self, item_id):
        row = self.items.loc[self.items['item_id'] == item_id]
        return row['img_url'].values[0], row['category'].values[0], row['text_info'].values[0]

    def add_interaction(self, user_id, item_id, feedback, timestamp):
        n = len(self.interactions)
        self.interactions.loc[n] = [user_id, item_id, feedback, timestamp]

    def add_categories(self, user_id, categories):
        categ = ';'.join(categories)
        self.users.loc[user_id, 'categories'] = categ

    def add_age(self, user_id, age):
        self.users.loc[user_id, 'age'] = age

    def add_sex(self, user_id, sex):
        self.users.loc[user_id, 'sex'] = sex

    def add_kids(self, user_id, kids):
        self.users.loc[user_id, 'kids_flag'] = kids

    def add_pets(self, user_id, pets):
        self.users.loc[user_id, 'pets'] = pets

    def add_time(self, user_id, timestamp):
        self.users.loc[user_id, 'timestamp'] = timestamp
