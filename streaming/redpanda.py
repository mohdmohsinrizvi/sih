from __future__ import annotations

import asyncio
import json
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

import orjson
import structlog
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from config.settings import settings

logger = structlog.get_logger(__name__)

TOPICS = {
    "raw": "weather.raw",
    "normalized": "weather.normalized",
    "validated": "weather.validated",
    "quarantine": "weather.quarantine",
    "ai": "weather.ai",
    "dedup": "weather.dedup",
    "events": "weather.events",
    "alerts": "weather.alerts",
}

TOPIC_CONFIGS = {
    "weather.raw": {"partitions": 3, "replication": 1, "retention_ms": 86400000},
    "weather.normalized": {"partitions": 3, "replication": 1, "retention_ms": 86400000},
    "weather.validated": {"partitions": 3, "replication": 1, "retention_ms": 604800000},
    "weather.quarantine": {"partitions": 1, "replication": 1, "retention_ms": 2592000000},
    "weather.ai": {"partitions": 2, "replication": 1, "retention_ms": 604800000},
    "weather.dedup": {"partitions": 2, "replication": 1, "retention_ms": 604800000},
    "weather.events": {"partitions": 3, "replication": 1, "retention_ms": 2592000000},
    "weather.alerts": {"partitions": 1, "replication": 1, "retention_ms": 604800000},
}


@dataclass
class ProducerStats:
    messages_sent: int = 0
    messages_failed: int = 0
    bytes_sent: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def messages_per_second(self) -> float:
        elapsed = time.time() - self.start_time
        return self.messages_sent / elapsed if elapsed > 0 else 0


class RedpandaProducer:
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.REDPANDA_BOOTSTRAP_SERVERS
        self._producer: Optional[Producer] = None
        self.stats = ProducerStats()

    def _get_producer(self) -> Producer:
        if self._producer is None:
            self._producer = Producer({
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "weather-producer",
                "acks": "all",
                "retries": 5,
                "retry.backoff.ms": 100,
                "linger.ms": 10,
                "batch.size": 65536,
                "compression.type": "lz4",
            })
        return self._producer

    def produce(
        self,
        topic: str,
        key: str,
        value: dict,
        on_delivery: Optional[Callable] = None,
    ) -> None:
        producer = self._get_producer()
        try:
            serialized = orjson.dumps(value).decode("utf-8")
            producer.produce(
                topic=topic,
                key=key.encode("utf-8") if key else None,
                value=serialized.encode("utf-8"),
                callback=on_delivery or self._default_callback,
            )
            producer.poll(0)
            self.stats.messages_sent += 1
            self.stats.bytes_sent += len(serialized)
        except KafkaException as e:
            self.stats.messages_failed += 1
            logger.error("produce_failed", topic=topic, key=key, error=str(e))

    async def produce_async(
        self,
        topic: str,
        key: str,
        value: dict,
    ) -> bool:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.produce, topic, key, value)
            return True
        except Exception as e:
            logger.error("produce_async_failed", topic=topic, error=str(e))
            return False

    def flush(self) -> None:
        if self._producer:
            self._producer.flush(timeout=30)

    def _default_callback(self, err, msg):
        if err:
            self.stats.messages_failed += 1
            logger.error("delivery_failed", topic=msg.topic() if msg else "unknown", error=str(err))

    def close(self) -> None:
        if self._producer:
            self._producer.flush(timeout=30)
            self._producer = None


class RedpandaConsumer:
    def __init__(
        self,
        topics: list[str],
        group_id: str,
        bootstrap_servers: Optional[str] = None,
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or settings.REDPANDA_BOOTSTRAP_SERVERS
        self._consumer: Optional[Consumer] = None
        self._running = False
        self._stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "start_time": None,
        }

    def _get_consumer(self) -> Consumer:
        if self._consumer is None:
            self._consumer = Consumer({
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
                "auto.commit.interval.ms": 5000,
                "session.timeout.ms": 30000,
                "max.poll.interval.ms": 300000,
            })
        return self._consumer

    async def consume(
        self,
        handler: Callable[[str, dict], Any],
        poll_timeout: float = 1.0,
    ) -> None:
        consumer = self._get_consumer()
        consumer.subscribe(self.topics)
        self._running = True
        self._stats["start_time"] = time.time()

        logger.info("consumer_started", topics=self.topics, group_id=self.group_id)

        try:
            while self._running:
                msg = consumer.poll(poll_timeout)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("consumer_error", error=str(msg.error()))
                    self._stats["messages_failed"] += 1
                    continue

                self._stats["messages_received"] += 1

                try:
                    key = msg.key().decode("utf-8") if msg.key() else ""
                    value = orjson.loads(msg.value().decode("utf-8"))
                    await handler(key, value)
                    self._stats["messages_processed"] += 1
                except Exception as e:
                    self._stats["messages_failed"] += 1
                    logger.error(
                        "message_processing_failed",
                        topic=msg.topic(),
                        key=msg.key(),
                        error=str(e),
                    )

        finally:
            consumer.close()
            logger.info("consumer_stopped", stats=self._stats)

    def stop(self) -> None:
        self._running = False

    @property
    def stats(self) -> dict:
        return dict(self._stats)


def create_topics(bootstrap_servers: Optional[str] = None) -> None:
    servers = bootstrap_servers or settings.REDPANDA_BOOTSTRAP_SERVERS
    admin = AdminClient({"bootstrap.servers": servers})

    existing = admin.list_topics(timeout=10).topics
    new_topics = []

    for topic_name, config in TOPIC_CONFIGS.items():
        if topic_name not in existing:
            new_topics.append(NewTopic(
                topic=topic_name,
                num_partitions=config["partitions"],
                replication_factor=config["replication"],
                config={
                    "retention.ms": str(config["retention_ms"]),
                },
            ))

    if new_topics:
        futures = admin.create_topics(new_topics)
        for topic, future in futures.items():
            try:
                future.result()
                logger.info("topic_created", topic=topic)
            except KafkaException as e:
                logger.warning("topic_creation_failed", topic=topic, error=str(e))
    else:
        logger.info("all_topics_exist")


producer = RedpandaProducer()
