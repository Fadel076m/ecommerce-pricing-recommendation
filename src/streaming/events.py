"""
Fonctions pures (sérialisation/parsing) partagées par le producteur et le
consommateur Kafka de démonstration (streaming simulé, brief section 3).

Séparées de producer.py/consumer.py pour être testables sans broker Kafka
(tests/test_streaming.py) : la connexion réseau est le seul élément qui reste
non testable sans un cluster Kafka réellement démarré.
"""
import json

TOPIC = "ecommerce.web_events"
BOOTSTRAP_SERVERS_DEFAULT = "localhost:9092"

# Préfixe distinct de "EVT_" (batch, src/transformation/web_events.py) pour
# qu'un rejeu de la démo streaming ne puisse jamais entrer en collision avec
# la clé primaire event_id déjà chargée en base par le pipeline batch.
STREAM_EVENT_ID_PREFIX = "STREAM_EVT_"

REQUIRED_FIELDS = ["event_id", "visitor_id", "item_id", "session_id", "event_type", "event_time"]


def event_to_message(row: dict, sequence: int) -> bytes:
    """Construit le message Kafka (JSON) à partir d'une ligne fact_web_events échantillonnée."""
    payload = {
        "event_id": f"{STREAM_EVENT_ID_PREFIX}{sequence}",
        "visitor_id": str(row["visitor_id"]),
        "item_id": str(row["item_id"]),
        "session_id": str(row["session_id"]),
        "event_type": row["event_type"],
        "event_time": str(row["event_time"]),
    }
    return json.dumps(payload).encode("utf-8")


def message_to_event(message_bytes: bytes) -> dict:
    """Parse un message Kafka et vérifie la présence des champs attendus par fact_web_events."""
    payload = json.loads(message_bytes.decode("utf-8"))
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Message invalide, champs manquants : {missing}")
    return payload
