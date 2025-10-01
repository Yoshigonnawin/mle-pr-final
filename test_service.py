import requests

BASE_URL = "http://localhost:8000"

# Проверка здоровья
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())

# События для добавления
events_data = [
    {"userid": "1", "itemid": "164941", "event": "view"},
    {"userid": "1", "itemid": "379841", "event": "add_to_cart"},
    {"userid": "1", "itemid": "355908", "event": "transaction"},
    {"userid": "2", "itemid": "164941", "event": "view"},
    {"userid": "2", "itemid": "164941", "event": "add_to_cart"},
    {"userid": "2", "itemid": "379841", "event": "view"},
    {"userid": "3", "itemid": "355908", "event": "view"},
    {"userid": "3", "itemid": "355908", "event": "add_to_cart"},
    {"userid": "3", "itemid": "355908", "event": "transaction"},
    {"userid": "1184451", "itemid": "164941", "event": "view"},
    {"userid": "1184451", "itemid": "379841", "event": "view"},
    {"userid": "1184451", "itemid": "355908", "event": "add_to_cart"},
    {"userid": "1184451", "itemid": "164941", "event": "transaction"},
]

# Добавление событий
for event in events_data:
    response = requests.post(f"{BASE_URL}/events", params=event)
    print(f"Added event: {event} -> {response.json()}")

# Получение событий пользователей
for userid in ["1", "2", "3", "1184451"]:
    response = requests.get(f"{BASE_URL}/events/{userid}", params={"k": 10})
    print(f"Events for user {userid}:", response.json())

# Получение рекомендаций
for userid in ["1", "2", "3", "1184451"]:
    response = requests.post(
        f"{BASE_URL}/recommendations", params={"userid": userid, "k": 10}
    )
    print(f"Recommendations for user {userid}:", response.json())
