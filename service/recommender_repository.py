from catboost import CatBoostRanker
import json
import pandas as pd
from typing import Optional, Dict
from pathlib import Path
from random import choices


class RecommenderRepository:
    """Класс для загрузки и хранения всех необходимых данных"""

    def __init__(
        self,
        model_path: str = "models/catboost_ranker.cbm",
        props_path: str = "range_features/item_props_last.parquet",
        als_assets_path: str = "ALS_assets",
        top_rated_path: str = "features_assets",
    ):
        """
        Args:
            model_path: Путь к модели CatBoost
            props_path: Путь к файлу с характеристиками товаров
            als_assets_path: Путь к директории с ALS-артефактами
        """
        self.model_path = model_path
        self.props_path = props_path
        self.als_assets_path = Path(als_assets_path)
        self.top_rated_path = Path(top_rated_path)

        # Модель
        self._model = None

        # Свойства товаров
        self.props: pd.DataFrame = None

        # Маппинги
        self.idx2user: Dict = {}
        self.idx2item: Dict = {}

        # ALS и похожие товары
        self.als_user_lookup: Dict = {}
        self.sim_index: Dict = {}
        # Загрузка высоко оцененых товаров
        self.top_ratings: list[int] = []

        # Загрузка всех данных
        self._load_all()

    def _load_all(self):
        """Загрузка всех данных"""
        print("Loading model...")
        self._load_model()

        print("Loading item properties...")
        self._load_props()

        print("Loading mappings...")
        self._load_mappings()

        print("Loading ALS recommendations...")
        self._load_als_recommendations()

        print("Loading top_ratings...")
        self._load_top_ratings()
        print("Loading similar items...")
        self._load_similar_items()

        print("Data loading completed!")

    def _load_model(self):
        """Загрузка модели"""
        self._model = CatBoostRanker()
        self._model.load_model(self.model_path)
        print(f"  Model loaded with {len(self._model.feature_names_)} features")

    def _load_props(self):
        """Загрузка свойств товаров"""
        self.props = pd.read_parquet(self.props_path)
        print(f"  Loaded properties for {len(self.props)} items")

    def _load_mappings(self):
        """Загрузка маппингов пользователей и товаров"""
        with open(self.als_assets_path / "hash_visitoridx_train.json") as f:
            self.idx2user = {
                int(float(k)): int(float(v)) for k, v in json.load(f).items()
            }

        with open(self.als_assets_path / "hash_itemidx_train.json") as f:
            self.idx2item = {
                int(float(k)): int(float(v)) for k, v in json.load(f).items()
            }

        print(f"  Loaded {len(self.idx2user)} users and {len(self.idx2item)} items")

    def _load_top_ratings(self):
        top_add = pd.read_parquet(self.top_rated_path / "top_100_addtocart.parquet")
        top_view = pd.read_parquet(self.top_rated_path / "top_100_view.parquet")
        top_transaction = pd.read_parquet(
            self.top_rated_path / "top_100_transaction.parquet"
        )

        self.top_ratings = (
            choices(top_add["itemid"].tolist(), k=6)
            + choices(top_transaction["itemid"].tolist(), k=2)
            + choices(top_view["itemid"].tolist(), k=2)
        )

        print(f"  Loaded TOP ratings with length {len(self.top_ratings)}")

    def _load_als_recommendations(self):
        """Загрузка ALS рекомендаций"""
        als_recs = pd.read_parquet(self.als_assets_path / "als_recommendations.parquet")
        als_recs["visitorid"] = als_recs["visitoridx"].map(self.idx2user)
        als_recs["itemid"] = als_recs["itemidx"].map(self.idx2item)
        als_recs = als_recs.dropna(subset=["visitorid", "itemid"])
        als_recs.rename(columns={"rating": "als_score"}, inplace=True)

        self.als_user_lookup = {
            uid: dict(zip(df_u["itemid"].astype(str), df_u["als_score"]))
            for uid, df_u in als_recs.groupby("visitorid")
        }

        print(f"  Loaded ALS recommendations for {len(self.als_user_lookup)} users")

    def _load_similar_items(self):
        """Загрузка индекса похожих товаров"""
        sim_df = pd.read_parquet(self.als_assets_path / "similar_items_df.parquet")
        sim_df["itemid"] = sim_df["items_idx"].map(self.idx2item)
        sim_df["sim_itemid"] = sim_df["sim_item_id_idx"].map(self.idx2item)
        sim_df = sim_df.dropna(subset=["itemid", "sim_itemid"])
        sim_df = sim_df[sim_df["itemid"] != sim_df["sim_itemid"]]

        self.sim_index = {
            iid: dict(zip(g["sim_itemid"], g["score"]))
            for iid, g in sim_df.groupby("itemid")
        }

        print(f"  Loaded similar items for {len(self.sim_index)} items")

    @property
    def model(self) -> CatBoostRanker:
        """Property для доступа к модели"""
        return self._model

    def get_user_idx(self, user_id: str) -> Optional[int]:
        """Получение индекса пользователя по ID"""
        return next((k for k, v in self.idx2user.items() if v == int(user_id)), None)

    def get_als_for_user(self, user_idx: Optional[int]) -> Optional[Dict]:
        """Получение ALS рекомендаций для пользователя"""
        return self.als_user_lookup.get(user_idx) if user_idx else None
