FROM itzg/minecraft-server:java21-multiarch

ENV REMOVE_OLD_MODS=true \
    REMOVE_OLD_MODS_INCLUDE="Ban-Plugin-*.jar,lobby-plugin-*.jar" \
    REMOVE_OLD_MODS_DEPTH=1 \
    TYPE=PAPER \
    VERSION=1.21.1 \
    MEMORY=384M \
    ENABLE_ROLLING_LOG=true \
    ALLOW_FLIGHT=true \
    ONLINE_MODE=false \
    ENFORCE_SECURE_PROFILE=false

COPY plugins/*.jar /plugins/
