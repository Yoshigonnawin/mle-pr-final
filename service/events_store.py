from typing import List


class EventStore:
    def __init__(self, max_events_per_user: int = 10) -> None:
        self.events = {}
        self.max_events_per_user = max_events_per_user

    def put(self, user_id: str, item_id: str, event: str) -> None:
        """
        Сохраняет событие
        """
        user_events = self.events.get(user_id, [])
        self.events[user_id] = [{item_id: event}] + user_events[
            : self.max_events_per_user
        ]

    def get(self, user_id: str, k: int) -> List[str]:
        """
        Возвращает события для пользователя
        """
        user_events = [list(item.keys())[0] for item in self.events.get(user_id, [])][
            :k
        ]
        return user_events
