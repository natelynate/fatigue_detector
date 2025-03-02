### Start container locally through yaml file
docker compose up -d

### Access container bash
docker exec -it <name> bash

### Access consumer log
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic frame_data