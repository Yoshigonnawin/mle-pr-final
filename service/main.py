import logging
from fastapi import FastAPI, HTTPException
from .events_store import EventStore
from .recommendations_service import RecommendationService
from contextlib import asynccontextmanager
import os


logger = logging.getLogger("uvicorn.error")

model_path = os.getenv("MODEL_PATH","models/catboost_ranker.cbm")
props_path = os.getenv("PROPS_PATH","range_features/item_props_last.parquet")
als_assets_path = os.getenv("ALS_ASSETS_PATH","ALS_assets")
top_rated_path = os.getenv("TOP_RATED_PATH","features_assets")
last_k = int(os.getenv("LAST_K",5))
n_als = int(os.getenv("N_ALS",20))
n_sim = int(os.getenv("N_SIM",10))
topn = int(os.getenv("TOPN",10))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса

    # Создаем экземпляр RecommendationService
    recommendation_service = RecommendationService(
        model_path = model_path,
        props_path = props_path,
        als_assets_path = als_assets_path,
        top_rated_path = top_rated_path,
        last_k = last_k,
        n_als = n_als,
        n_sim = n_sim,
        topn = topn
    )

    # Сохраняем экземпляр в app.state для использования в endpoint'ах
    app.state.recommendation_service = recommendation_service

    logger.info("Recommendation service is ready!")
    # код ниже выполнится только один раз при остановке сервиса
    yield


# Создаем FastAPI приложение
app = FastAPI(lifespan=lifespan)

# Создаем экземпляр для работы с событиями
events_store = EventStore()


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


@app.post("/recommendations")
async def get_online_recommendations(userid: str, k: int = 10):
    """
    Получает онлайн рекомендации на основе последних событий пользователя
    """
    try:
        # Получаем последние события пользователя
        events = events_store.get(userid, k=10)

        # Получаем рекомендации на основе последнего трека
        recommendation_service = app.state.recommendation_service
        result = recommendation_service.get_recommedations(
            userid=userid, recent_items=events, with_score=True
        )
        return result

    except Exception as e:
        logger.error(f"Error getting online recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/events")
async def add_event(userid: str, itemid: str, event: str):
    """
    Добавляет событие пользователя
    """
    try:
        events_store.put(userid, itemid, event)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{userid}")
async def get_user_events(userid: str, k: int = 10):
    """
    Получает события пользователя
    """
    try:
        events = events_store.get(userid, k)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting user events: {e}")
        print(type(userid))
        raise HTTPException(status_code=500, detail=str(e))
