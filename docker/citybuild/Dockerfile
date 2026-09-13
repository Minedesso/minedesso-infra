FROM itzg/minecraft-server:java21-multiarch

ENV TYPE=PAPER \
    VERSION=1.21.1 \
    MEMORY=768M \
    ENABLE_ROLLING_LOG=true \
    ALLOW_FLIGHT=true \
    ONLINE_MODE=false \
    ENFORCE_SECURE_PROFILE=false

COPY plugins/*.jar /plugins/
