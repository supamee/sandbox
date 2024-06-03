#!/usr/bin/env bash
echo $(date --utc)
echo $(date)
echo "unix:$(date +%s)"
echo "lora:"
sqlite3 /sentry/vault/data/lora/store.db "SELECT deviceid, gps_timestamp, time_created, latitude, MAX(ROWID
) FROM gps GROUP BY deviceid;"

echo "wifi:"
sqlite3 /sentry/vault/data/wifi_store.db "SELECT mac, last_timestamp, MAX(ROWID) FROM wifi;"

echo "GPS:"
sqlite3 /sentry/vault/data/GPS/store.db "SELECT gps_timestamp, latitude, time_created, MAX(ROWID
) FROM gps;"


echo "Audio:"
sqlite3 /sentry/vault/data/Audio/store.db "SELECT end_time, MAX(ROWID
) FROM audio_data;"

ls /sentry/vault/data/Audio/blobs -lt --time-style=long-iso | grep '^-' | head -n 1 | awk '{print $6, $7}'