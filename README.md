# Kafka-ELK Stack Setup

This repository contains a complete setup for integrating Apache Kafka with the ELK (Elasticsearch, Logstash, and Kibana) stack using Docker Compose.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Setup](#running-the-setup)
- [Verifying the Setup](#verifying-the-setup)
- [Stopping and Cleaning Up](#stopping-and-cleaning-up)

---

## Overview
This project sets up:
1. **Kafka** (with Zookeeper & Kafka Manager)
2. **ELK Stack** (Elasticsearch, Logstash, Kibana)
3. **Kafka Producer** (Python script to generate sample data)

Kafka is used for message streaming, and Logstash processes Kafka messages before storing them in Elasticsearch. Kibana is used for visualization.

---

## Architecture

```
Kafka Producer → Kafka → Logstash → Elasticsearch → Kibana
```

---

## Prerequisites

- Docker & Docker Compose installed
- Python 3 installed (for Kafka Producer)
- Internet access to pull required Docker images

---

## Installation

### Clone the Repository
```sh
git clone <repo-url>
cd <repo-directory>
```

### Start Kafka Cluster
```sh
docker-compose -f kafka-docker-compose.yaml up -d
```

### Start ELK Stack
```sh
docker-compose -f elastic-search-kibana-docker-compose.yaml up -d
```

---

## Configuration

### Kafka Configuration (`kafka-docker-compose.yaml`)
```yaml
version: "3"
services:
  zookeeper:
    image: zookeeper
    restart: always
    container_name: zookeeper
    hostname: zookeeper
    ports:
      - 2181:2181
    environment:
      ZOO_MY_ID: 1

  kafka:
    image: wurstmeister/kafka
    container_name: kafka
    ports:
      - 9092:9092
    environment:
      KAFKA_ADVERTISED_HOST_NAME: "54.227.194.172"
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181

  kafka_manager:
    image: hlebalbau/kafka-manager:stable
    container_name: kakfa-manager
    restart: always
    ports:
      - "9000:9000"
    depends_on:
      - zookeeper
      - kafka
    environment:
      ZK_HOSTS: "zookeeper:2181"
      APPLICATION_SECRET: "random-secret"
      command: -Dpidfile.path=/dev/null
```

### ELK Configuration (`elastic-search-kibana-docker-compose.yaml`)
```yaml
version: '3.7'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.4.0
    container_name: elasticsearch
    restart: always
    environment:
      - xpack.security.enabled=false
      - discovery.type=single-node
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    cap_add:
      - IPC_LOCK
    volumes:
      - elasticsearch-data-volume:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      - "9300:9300"

  kibana:
    container_name: kibana
    image: docker.elastic.co/kibana/kibana:7.4.0
    restart: always
    environment:
      - ELASTICSEARCH_HOSTS=http://54.227.194.172:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:7.4.0
    container_name: logstash
    restart: always
    environment:
      - LOGSTASH_ELASTICSEARCH_HOST=http://54.227.194.172:9200
    ports:
      - "5044:5044"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data-volume:
    driver: local
```

### Logstash Configuration (`logstash/pipeline/logstash.conf`)
```yaml
input {
  kafka {
    bootstrap_servers => "54.227.194.172:9092"
    topics => ["registered_user"]
    codec => "json"
  }
}

filter {
  # Add filters here to parse or enrich the data if needed
}

output {
  elasticsearch {
    hosts => ["54.227.194.172:9200"]
    index => "logstash-%{+YYYY.MM.dd}"
  }
}
```

### Kafka Producer (`producer.py`)
```python
from confluent_kafka import Producer
from faker import Faker
import json
import time

fake = Faker()

# Kafka Producer configuration
producer = Producer({'bootstrap.servers': '54.227.194.172:9092'})

# Generate a fake registered user
def get_registered_user():
    return {
        "name": fake.name(),
        "address": fake.address(),
        "created_at": fake.date_time().isoformat()
    }

# Delivery report callback
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

if __name__ == "__main__":
    while True:
        registered_user = get_registered_user()
        print(f"Producing message: {registered_user}")

        producer.produce(
            "registered_user",
            key=registered_user["name"].encode("utf-8"),
            value=json.dumps(registered_user).encode("utf-8"),
            callback=delivery_report
        )

        producer.flush()
        time.sleep(4)
```

---

## Running the Setup

### Start Kafka
```sh
docker-compose -f kafka-docker-compose.yaml up -d
```

### Start ELK Stack
```sh
docker-compose -f elastic-search-kibana-docker-compose.yaml up -d
```

### Run the Kafka Producer
```sh
python3 producer.py
```

---

## Verifying the Setup

- Open **Kafka Manager** at `http://<server-ip>:9000`
- Open **Elasticsearch** at `http://<server-ip>:9200`
- Open **Kibana** at `http://<server-ip>:5601`

---

## Stopping and Cleaning Up
```sh
docker-compose -f kafka-docker-compose.yaml down
docker-compose -f elastic-search-kibana-docker-compose.yaml down
```

This will stop all services and remove associated containers.

---

## Conclusion
This setup enables streaming data from Kafka to Elasticsearch using Logstash and visualizing it in Kibana. 🚀
