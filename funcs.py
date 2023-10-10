import pandas as pd
import numpy as np


class DataManager:
    def __init__(self):
        """
            need to load data from database

            users = pd.DataFrame(cols={user_id, age, sex, kids, pets, categories})
            items = pd.DataFrame(cols={item_id, name, categories, promo, text_info, img_url,
                                       first_time_only, exp_date, start_sum, restrictions})
            interactions = pd.DataFrame(cols={user_id, item_id, feedback, timestamp})
        """

        self.users = None
        self.items = None
        self.interactions = None
        self.n_items = len(self.items)
        self.fav_sum_prob = 0.65

    def get_first_recs(self, user_id, k=3):
        users_fav_categories = self.users.loc[user_id, 'categories'].split()
        if self.users.loc[self.users['user_id'] == user_id, 'kids'] == 1:
            users_fav_categories.append('Товары для детей')
        if self.users.loc[self.users['user_id'] == user_id, 'pets'] == 1:
            users_fav_categories.append('Товары для животных')

        items_from_fav_categ = self.items.loc[self.items['categories'].isin(users_fav_categories), 'item_id'].values.tolist()
        rest_items = self.items.loc[~self.items['categories'].isin(users_fav_categories), 'item_id'].values.tolist()
        n_fav = len(items_from_fav_categ)
        n_rest = self.n_items - n_fav

        probs = [2] * n_fav + [1] * n_rest
        probs = probs / np.sum(probs)

        sampled_items = np.random_choice(items_from_fav_categ + rest_items, size=k+10, p=probs, replace=False)
        used_items = self.items[self.interactions['user_id'] == user_id, 'item_id'].values

        clean_sampled_items = []
        for item in sampled_items:
            if item not in used_items:
                clean_sampled_items.append(item)
        return clean_sampled_items[:k]


