import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
import scipy.sparse as sp
from sklearn.preprocessing import LabelEncoder


class StupidRecommender:
    def init(self) -> None:
        pass

    def fit(self):
        pass

    def predict(self, user_id, users, items, interactions, k=1):
        users_fav_categories = users.loc[user_id, 'categories'].split(";")
        if users.loc[user_id, 'kids_flag'] == 1:
            users_fav_categories.append('Товары для детей')
        if users.loc[user_id, 'pets_flag'] == 1:
            users_fav_categories.append('Товары для животных')

        items_from_fav_categ = items.loc[items['category'].isin(users_fav_categories), 'item_id'].values.tolist()
        rest_items = items.loc[~items['category'].isin(users_fav_categories), 'item_id'].values.tolist()
        n_fav = len(items_from_fav_categ)
        n_rest = len(items) - n_fav

        probs = [2] * n_fav + [1] * n_rest
        probs = probs / np.sum(probs)

        sampled_items = np.random.choice(items_from_fav_categ + rest_items, size=k+1, p=probs, replace=False)
        used_items = interactions.loc[interactions['user_id'] == user_id, 'item_id'].values
        filtered_items = np.setdiff1d(sampled_items, used_items, assume_unique=True)

        if k == 1:
            return filtered_items[0] if len(filtered_items) else None
        else:
            return filtered_items[:k]


class EASE:
    def __init__(self, reg: float = 0.01) -> None:
        self.reg = reg
        self.trained = False
        self.item_similarity = None
        self.interaction_matrix = None
        self.user_encoder = None
        self.item_encoder = None

    def fit(
            self, df, items, item_col='item_id', user_col="user_id"
    ) -> None:
        # user_ids = df[user_col].unique()
        # item_ids = df[item_col].unique()

        self.user_encoder = LabelEncoder().fit(df[user_col].unique())
        self.item_encoder = LabelEncoder().fit(items[item_col])
        user_ids = self.user_encoder.transform(df[user_col])
        item_ids = self.item_encoder.transform(df[item_col])

        counts = np.ones(len(df))

        matrix_shape = len(user_ids), len(items)

        X = csr_matrix((counts, (user_ids, item_ids)), shape=matrix_shape)

        G = X.T @ X
        G += self.reg * sp.identity(G.shape[0]).astype(np.float32)
        G = G.todense()
        P = np.linalg.inv(G)
        B = P / (-np.diag(P))
        np.fill_diagonal(B, 0.0)

        self.item_similarity = B
        self.interaction_matrix = X
        self.trained = True

    def predict(self, user_id, interactions, k=1):
        assert self.trained

        encoded_user_id = self.user_encoder.transform([user_id])[0]
        scores = self.interaction_matrix[encoded_user_id, :] @ self.item_similarity
        ids = np.argsort(-scores, axis=-1)
        orig_item_ids = self.item_encoder.inverse_transform(np.array(ids)[0])

        used_items = interactions.loc[interactions['user_id'] == user_id, 'item_id'].values
        filtered_items = np.setdiff1d(orig_item_ids, used_items, assume_unique=True)

        if k == 1:
            return filtered_items[0] if len(filtered_items) else None
        else:
            return filtered_items[:k]
