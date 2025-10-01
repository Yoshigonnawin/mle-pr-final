from .recommender_repository import RecommenderRepository
from .feature_generator import FeatureGenerator
from .recommender import Recommender


class RecommendationService:
    def __init__(
        self,
        model_path: str = "models/catboost_ranker.cbm",
        props_path: str = "range_features/item_props_last.parquet",
        als_assets_path: str = "ALS_assets",
        top_rated_path: str = "features_assets",
        last_k: int = 5,
        n_als: int = 20,
        n_sim: int = 10,
        topn: int = 10,
    ):
        self.recommender_repository = RecommenderRepository(
            model_path, props_path, als_assets_path, top_rated_path
        )

        self.feature_generator = FeatureGenerator(
            self.recommender_repository, last_k, n_als, n_sim
        )

        self.recommender = Recommender(self.recommender_repository.model)
        self.topn = topn

    def _cold_start(self) -> list:
        return self.recommender_repository.top_ratings

    def _range_recommendations(
        self, userid: str, recent_items: list[str], with_score: bool
    ):
        if with_score:
            return self.recommender.recommend_with_scores(
                features_data=self.feature_generator.build_features(
                    userid, recent_items
                ),
                topn=self.topn,
            )
        else:
            return self.recommender.recommend(
                features_data=self.feature_generator.build_features(
                    userid, recent_items
                ),
                topn=self.topn,
            )

    def get_recommedations(
        self, userid: str, recent_items: list[str], with_score: bool
    ):
        if not self.recommender_repository.get_user_idx(userid) and not recent_items:
            return self._cold_start()
        else:
            return self._range_recommendations(userid, recent_items, with_score)
