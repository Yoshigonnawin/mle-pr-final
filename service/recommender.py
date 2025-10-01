from catboost import CatBoostRanker, Pool
import pandas as pd
from typing import List, Tuple


class Recommender:
    """Класс для генерации ранжированных рекомендаций"""

    def __init__(self, model: CatBoostRanker):
        self.model = model
        self.features = model.feature_names_
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
            if c in self.features
        ]

    def _predict(
        self, features_data: Tuple[pd.DataFrame, List[str]], topn: int = 10
    ) -> pd.DataFrame:
        """Returns DataFrame with top N predictions"""
        X, candidate_ids = features_data

        if X.empty or not candidate_ids:
            print("No candidates to rank")
            return pd.DataFrame()

        used_features = [f for f in self.features if f in X.columns]
        if not used_features:
            print("No valid features found")
            return X.head(topn)

        try:
            test_pool = Pool(
                X[used_features],
                group_id=X["group_id"],
                cat_features=[c for c in used_features if c in self.cat_features],
            )
            predictions = self.model.predict(test_pool)
            X["prediction"] = predictions
            return X.nlargest(topn, "prediction")

        except Exception as e:
            print(f"Prediction error: {e}")
            return X.head(topn)

    def recommend(
        self, features_data: Tuple[pd.DataFrame, List[str]], topn: int = 10
    ) -> List[str]:
        data = self._predict(features_data, topn)
        return data["itemid"].tolist() if not data.empty else []

    def recommend_with_scores(
        self, features_data: Tuple[pd.DataFrame, List[str]], topn: int = 10
    ) -> List[Tuple[str, float]]:
        data = self._predict(features_data, topn)
        if data.empty or "prediction" not in data.columns:
            return []
        return list(zip(data["itemid"], data["prediction"]))
