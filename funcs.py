import pandas as pd
import numpy as np
from db import load_users_data, load_items_data, load_interactions_data


class DataManager:
    def __init__(self):
        """
            need to load data from database

            users = pd.DataFrame(cols={user_id, age, gender, preferences, time_added, kids_flag, pets_flag, feedback})
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

    def get_first_recs(self, user_id, k=1):
        users_fav_categories = self.users.loc[user_id, 'preferences'].split(";")
        if self.users.loc[user_id, 'kids_flag'] == "Да":
            users_fav_categories.append('Товары для детей')
        if self.users.loc[user_id, 'pets_flag'] == "Да":
            users_fav_categories.append('Товары для животных')

        items_from_fav_categ = self.items.loc[
            self.items['category'].isin(users_fav_categories), 'item_id'].values.tolist()
        rest_items = self.items.loc[~self.items['category'].isin(users_fav_categories), 'item_id'].values.tolist()
        n_fav = len(items_from_fav_categ)
        n_rest = self.n_items - n_fav

        probs = [2] * n_fav + [1] * n_rest
        probs = probs / np.sum(probs)

        sampled_items = np.random.choice(items_from_fav_categ + rest_items, size=k + 1, p=probs, replace=False)
        used_items = self.interactions.loc[self.interactions['user_id'] == user_id, 'item_id'].values
        print(probs)
        print('sampled', sampled_items)
        print('used', used_items)

        clean_sampled_items = []
        for item in sampled_items:
            if item not in used_items:
                clean_sampled_items.append(item)
        print('clean', clean_sampled_items)
        if not clean_sampled_items:
            return []
        elif k == 1:
            return clean_sampled_items[0]
        else:
            return clean_sampled_items[:k]

    def get_item_data(self, item_id):
        row = self.items.loc[self.items['item_id'] == item_id]
        print(row)
        return row['img_url'].values[0], row['category'].values[0], row['text_info'].values[0]

    def add_interaction(self, user_id, item_id, feedback, timestamp):
        n = len(self.interactions)
        self.interactions.loc[n] = [user_id, item_id, feedback, timestamp]