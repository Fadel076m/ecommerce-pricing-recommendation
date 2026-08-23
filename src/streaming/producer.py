"""
Producteur Kafka de démonstration (streaming simulé, brief section 3).

Rejoue data/sample/fact_web_events_sample.parquet (échantillon RetailRocket
versionné, cf. scripts/data_generator.py) sur le topic ecommerce.web_events,
un message toutes les DELAY_SECONDS secondes, pour simuler l'arrivée continue
d'événements de navigation en plus du chargement batch (Jalon 3/4).

Ne fait PAS partie de `make demo` : ce n'est pas nécessaire pour consulter le
dashboard/l'API. Usage (nécessite `docker compose --profile streaming up -d kafka`) :
    python -m src.streaming.producer [--max-messages N] [--delay SECONDS]
"""
import argparse
import os
import time
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer

from src.streaming.events import BOOTSTRAP_SERVERS_DEFAULT, TOPIC, event_to_message

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_PATH = REPO_ROOT / "data" / "sample" / "fact_web_events_sample.parquet"


def produce(max_messages: int | None = None, delay_seconds: float = 0.2) -> int:
    df = pd.read_parquet(SAMPLE_PATH)
    if max_messages:
        df = df.head(max_messages)

    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", BOOTSTRAP_SERVERS_DEFAULT)
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    sent = 0
    try:
        for sequence, row in enumerate(df.to_dict("records")):
            message = event_to_message(row, sequence)
            producer.send(TOPIC, message)
            sent += 1
            print(f"[producer] envoyé {sent}/{len(df)} -> topic={TOPIC}")
            time.sleep(delay_seconds)
        producer.flush()
    finally:
        producer.close()
    return sent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-messages", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.2, help="secondes entre deux messages")
    args = parser.parse_args()
    total = produce(max_messages=args.max_messages, delay_seconds=args.delay)
    print(f"[producer] terminé : {total} événements envoyés.")
