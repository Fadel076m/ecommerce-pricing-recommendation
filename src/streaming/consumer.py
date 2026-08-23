"""
Consommateur Kafka de démonstration (streaming simulé, brief section 3).

Lit le topic ecommerce.web_events et insère chaque événement dans
fact_web_events (même table que le chargement batch, cf. data/schemas/ddl.sql)
au fur et à mesure de son arrivée -- démontre la coexistence batch + streaming
demandée par le brief, sur la même cible (Data Warehouse).

S'arrête automatiquement après IDLE_TIMEOUT_MS sans nouveau message (pratique
pour une démonstration qui doit se terminer seule, pas pour un usage
production qui tournerait en continu). Usage :
    python -m src.streaming.consumer [--idle-timeout-ms 15000]
"""
import argparse
import os

from kafka import KafkaConsumer
from sqlalchemy import text

from src.streaming.events import BOOTSTRAP_SERVERS_DEFAULT, TOPIC, message_to_event
from src.transformation.load_to_postgres import get_engine

INSERT_SQL = text(
    """
    INSERT INTO fact_web_events (event_id, visitor_id, item_id, session_id, event_type, event_time)
    VALUES (:event_id, :visitor_id, :item_id, :session_id, :event_type, :event_time)
    ON CONFLICT (event_id) DO NOTHING
    """
)


def consume(idle_timeout_ms: int = 15000) -> int:
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", BOOTSTRAP_SERVERS_DEFAULT)
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="ecommerce-streaming-demo",
        consumer_timeout_ms=idle_timeout_ms,
    )
    engine = get_engine()

    received = 0
    with engine.begin() as conn:
        for message in consumer:
            event = message_to_event(message.value)
            conn.execute(INSERT_SQL, event)
            received += 1
            print(f"[consumer] inséré dans fact_web_events : {event['event_id']} ({event['event_type']})")
    consumer.close()
    return received


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--idle-timeout-ms", type=int, default=15000)
    args = parser.parse_args()
    total = consume(idle_timeout_ms=args.idle_timeout_ms)
    print(f"[consumer] terminé (inactivité) : {total} événements insérés dans fact_web_events.")
