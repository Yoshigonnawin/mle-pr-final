from sklearn.compose import ColumnTransformer
import pandas as pd


def create_id_mapping(
    transformer: ColumnTransformer,
    user_item_ratings: pd.DataFrame,
    visitoridx_name: str = "visitoridx",
    itemidx_name: str = "itemidx",
) -> tuple[dict, dict]:
    # Извлекаем оригинальные id из трансформера для категориальных признаков
    visitorid_transformer_id = list(
        transformer.named_transformers_["cats"].categories_[0]
    )
    itemid_transformer_id = list(transformer.named_transformers_["cats"].categories_[2])

    # Получаем уникальные индексы из тестового набора
    visitoridx = user_item_ratings[visitoridx_name].unique().tolist()
    itemidx = user_item_ratings[itemidx_name].unique().tolist()

    # Сортируем индексы для корректного сопоставления
    visitoridx.sort()
    itemidx.sort()

    # Создаём словари {внутренний_индекс: оригинальный_id}
    cross_visitoridx = {
        internal_idx: original_id
        for internal_idx, original_id in zip(visitoridx, visitorid_transformer_id)
    }
    cross_itemidx = {
        internal_idx: original_id
        for internal_idx, original_id in zip(itemidx, itemid_transformer_id)
    }

    return cross_visitoridx, cross_itemidx
