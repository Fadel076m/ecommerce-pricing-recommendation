"""
Tests du streaming simulé (Kafka, brief section 3).

Les tests de sérialisation (event_to_message/message_to_event) ne nécessitent
aucun broker et tournent toujours. Le test d'intégration bout en bout est
skippé proprement si aucun broker Kafka n'est joignable (profil Docker Compose
"streaming" non démarré) -- même logique que les autres tests d'intégration du
projet qui dépendent d'une ressource locale optionnelle (cf. test_transformation.py).
"""
import socket
from pathlib import Path

import pytest

from src.streaming.events import STREAM_EVENT_ID_PREFIX, event_to_message, message_to_event

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = REPO_ROOT / "data" / "sample" / "fact_web_events_sample.parquet"


def _kafka_reachable(host: str = "localhost", port: int = 9092, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


SAMPLE_ROW = {
    "visitor_id": "12345",
    "item_id": "67890",
    "session_id": "12345_S0",
    "event_type": "view",
    "event_time": "2015-08-14 10:00:00",
}


def test_event_to_message_roundtrip():
    message = event_to_message(SAMPLE_ROW, sequence=7)
    event = message_to_event(message)
    assert event["event_id"] == f"{STREAM_EVENT_ID_PREFIX}7"
    assert event["visitor_id"] == "12345"
    assert event["item_id"] == "67890"
    assert event["event_type"] == "view"


def test_message_to_event_rejects_missing_fields():
    incomplete = b'{"visitor_id": "1", "item_id": "2"}'
    with pytest.raises(ValueError):
        message_to_event(incomplete)


def test_sample_file_matches_fact_web_events_schema():
    if not SAMPLE_PATH.exists():
        pytest.skip("data/sample/fact_web_events_sample.parquet absent.")
    import pandas as pd

    df = pd.read_parquet(SAMPLE_PATH)
    expected_columns = {"event_id", "visitor_id", "item_id", "session_id", "event_type", "event_time"}
    assert expected_columns.issubset(df.columns)
    assert len(df) > 0


@pytest.mark.skipif(
    not _kafka_reachable(), reason="Aucun broker Kafka joignable sur localhost:9092 (profil 'streaming' non démarré)."
)
def test_produce_and_consume_end_to_end():
    from src.streaming.producer import produce
    from src.streaming.events import TOPIC
    from kafka import KafkaConsumer

    sent = produce(max_messages=5, delay_seconds=0.0)
    assert sent == 5

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,
    )
    received = [message_to_event(message.value) for message in consumer]
    consumer.close()
    assert len(received) >= 5
