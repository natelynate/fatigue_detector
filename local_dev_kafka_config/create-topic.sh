#!/bin/bash

# Create session topic
docker-compose exec kafka kafka-topics.sh \
    --create \
    --bootstrap-server localhost:9092 \
    --topic session_events \
    --partitions 3 \
    --replication-factor 1

# Create frame data topic
docker-compose exec kafka kafka-topics.sh \
    --create \
    --bootstrap-server localhost:9092 \
    --topic frame_data \
    --partitions 3 \
    --replication-factor 1

# List topics to verify
docker-compose exec kafka kafka-topics.sh \
    --list \
    --bootstrap-server localhost:9092