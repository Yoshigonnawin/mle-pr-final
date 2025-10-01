import logging
from fastapi import FastAPI, HTTPException
from .events_store import EventStore
from .recommendations_service import RecommendationService
from contextlib import asynccontextmanager


logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса

    # Создаем экземпляр RecommendationService
    recommendation_service = RecommendationService()

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
