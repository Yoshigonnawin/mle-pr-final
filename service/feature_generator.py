from .recommender_repository import RecommenderRepository
import pandas as pd
from typing import Optional, List, Dict, Tuple


class FeatureGenerator:
    """Класс для генерации признаков и кандидатов"""

    def __init__(
        self,
        data_loader: RecommenderRepository,
        last_k: int = 5,
        n_als: int = 100,
        n_sim: int = 50,
    ):
        self.data_loader = data_loader
        self.last_k = last_k
        self.n_als = n_als
        self.n_sim = n_sim

        # Получаем признаки из модели
        self.all_features = data_loader.model.feature_names_
        self.cat_features = [
            c
            for c in [
                "available",
                "categoryid",
                "root_category",
                "level_0",
                "level_1",
                "level_2",
                "level_3",
                "level_4",
                "level_5",
            ]
            if c in self.all_features
        ]

        print(
            f"FeatureGenerator initialized with LAST_K={last_k}, N_ALS={n_als}, N_SIM={n_sim}"
        )

    def generate_candidates(
        self, recent_items: List[str], als_map_user: Optional[Dict]
    ) -> List[str]:
        pool = []

        # ALS рекомендации
        if als_map_user:
            als_sorted = sorted(als_map_user.items(), key=lambda x: -x[1])[: self.n_als]
            pool.extend([iid for iid, _ in als_sorted])

        # Похожие товары
        if recent_items:
            per_item = max(1, self.n_sim // max(1, len(recent_items)))
            for it in recent_items[: self.last_k]:
                sim_items_dict = self.data_loader.sim_index.get(str(it), {})
                sorted_items = sorted(sim_items_dict.items(), key=lambda x: -x[1])[
                    :per_item
                ]
                pool.extend([sid for sid, _ in sorted_items])

        # Дедупликация
        seen = set()
        uniq = []
        for x in pool:
            if x not in seen:
                uniq.append(x)
                seen.add(x)

        return uniq

    def calculate_sim_max(self, item_id: str, recent_items: List[str]) -> float:
        best = 0.0
        for it in recent_items[: self.last_k]:
            pairs = self.data_loader.sim_index.get(str(it), {})
            for sid, sc in pairs.items():
                if str(sid) == str(item_id):
                    best = max(best, float(sc))
                    break
        return best

    def build_features(
        self, user_id: str, recent_items: List[str], session_id: Optional[str] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        # Получение ALS рекомендаций для пользователя
        user_idx = self.data_loader.get_user_idx(user_id)
        als_map_user = self.data_loader.get_als_for_user(user_idx)

        # Генерация кандидатов
        candidate_ids = self.generate_candidates(recent_items, als_map_user)

        if not candidate_ids:
            return pd.DataFrame(), []
        rows = []

        # Сессионные признаки
        sess_cnt_view = float(len(recent_items))
        sess_cnt_add = 0.0
        sess_cnt_trx = 0.0
        sess_n_items = float(len(set(recent_items)))
        sess_n_events = sess_cnt_view
        sess_duration = 0.0

        for iid in candidate_ids:
            ip = self.data_loader.props.get(str(iid), {})

            row = {
                "als_score": float(als_map_user.get(str(iid), 0.0))
                if als_map_user
                else 0.0,
                "sim_max": self.calculate_sim_max(str(iid), recent_items),
                "item_pop_w": 0.0,
                "sess_n_events": sess_n_events,
                "sess_n_items": sess_n_items,
                "sess_duration": sess_duration,
                "sess_cnt_view": sess_cnt_view,
                "sess_cnt_addtocart": sess_cnt_add,
                "sess_cnt_transaction": sess_cnt_trx,
            }

            # Категориальные свойства товара
            for prop in [
                "available",
                "categoryid",
                "root_category",
                "level_0",
                "level_1",
                "level_2",
                "level_3",
                "level_4",
                "level_5",
            ]:
                try:
                    row[prop] = int(ip.get(prop, -1)) if ip else -1
                except (ValueError, TypeError):
                    row[prop] = -1

            # Числовые свойства товара
            for prop in [
                "value_count",
                "value_mean",
                "value_std",
                "value_min",
                "value_max",
            ]:
                try:
                    row[prop] = float(ip.get(prop, 0.0)) if ip else 0.0
                except (ValueError, TypeError):
                    row[prop] = 0.0

            rows.append(row)

        X = pd.DataFrame(rows)

        # Приведение типов
        for c in self.all_features:
            if c in X.columns:
                if c in self.cat_features:
                    X[c] = X[c].fillna(-1).astype("int32")
                else:
                    X[c] = (
                        pd.to_numeric(X[c], errors="coerce")
                        .fillna(0.0)
                        .astype("float32")
                    )

        # Добавление служебных колонок
        X["visitorid"] = user_id
        X["anchor_session_id"] = session_id or "default_session"
        X["itemid"] = candidate_ids

        # Конвертация категориальных признаков в строки
        X = self._convert_categorical_to_str(X)
        X["group_id"] = (
            X["visitorid"].astype(str) + "_" + X["anchor_session_id"].astype(str)
        )

        return X, candidate_ids

    def _convert_categorical_to_str(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        for feature in self.cat_features:
            if feature in df_copy.columns:
                df_copy[feature] = df_copy[feature].astype(str)
        return df_copy
