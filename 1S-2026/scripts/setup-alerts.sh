#!/bin/bash
# Script to configure Grafana alerts via API after startup
# This script creates alert rules for the IoT demo

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin123"

echo "Waiting for Grafana to be ready..."
until $(curl -s -o /dev/null -w '%{http_code}' ${GRAFANA_URL}/api/health | grep -q 200); do
  sleep 5
done

echo "Grafana is ready"
echo "Creating authentication header..."
AUTH="${GRAFANA_USER}:${GRAFANA_PASSWORD}"

# Get the default folder UID
echo "Getting dashboard folder info..."
FOLDER_UID=$(curl -s -u ${AUTH} ${GRAFANA_URL}/api/folders | grep -o '"uid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "   Folder UID: ${FOLDER_UID}"

# Get Redis datasource UID
echo "Getting Redis datasource UID..."
REDIS_DS_UID=$(curl -s -u ${AUTH} ${GRAFANA_URL}/api/datasources | grep -o '"uid":"[^"]*redis[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$REDIS_DS_UID" ]; then
  REDIS_DS_UID="redis-datasource"
fi
echo "   Redis DS UID: ${REDIS_DS_UID}"

echo "Creating Alert Rule: High Temperature (>30C)..."
curl -s -u ${AUTH} -X POST ${GRAFANA_URL}/api/v1/provisioning/alert-rules \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"High Temperature Alert\",
    \"condition\": \"C\",
    \"data\": [
      {
        \"refId\": \"A\",
        \"relativeTimeRange\": {
          \"from\": 300,
          \"to\": 0
        },
        \"datasourceUid\": \"${REDIS_DS_UID}\",
        \"model\": {
          \"command\": \"hget\",
          "expression": "A",
          \"field\": \"value\",
          \"keyName\": \"sensors:dht22_temperatura:latest\",
          \"type\": \"command\",
          \"refId\": \"A\"
        }
      },
      {
        \"refId\": \"C\",
        \"relativeTimeRange\": {
          \"from\": 300,
          \"to\": 0
        },
        \"datasourceUid\": \"__expr__\",
        \"model\": {
          \"type\": \"threshold\",
          \"conditions\": [
            {
              \"evaluator\": {
                \"params\": [30],
                \"type\": \"gt\"
              },
              \"operator\": {
                \"type\": \"and\"
              },
              \"query\": {
                \"params\": [\"A\"]
              },
              \"reducer\": {
                \"params\": [],
                \"type\": \"last\"
              },
              "type": "query"
            }
          ],
          \"datasource\": {
            \"type\": \"__expr__\",
            \"uid\": \"__expr__\"
          },
          \"refId\": \"C\"
        }
      }
    ],
    \"folderUID\": \"${FOLDER_UID}\",
    \"noDataState\": \"NoData\",
    \"execErrState\": \"Error\",
    \"for\": \"10s\",
    \"isPaused\": false,
    \"notification_settings\": {
      \"receiver\": \"Email Notifications\"
    }
  }"

echo ""
echo "Creating Alert Rule: High Humidity (>80%)..."
curl -s -u ${AUTH} -X POST ${GRAFANA_URL}/api/v1/provisioning/alert-rules \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"High Humidity Alert\",
    \"condition\": \"C\",
    \"data\": [
      {
        \"refId\": \"A\",
        \"relativeTimeRange\": {
          \"from\": 300,
          \"to\": 0
        },
        \"datasourceUid\": \"${REDIS_DS_UID}\",
        \"model\": {
          \"command\": \"hget\",
          "expression": "A",
          \"field\": \"value\",
          \"keyName\": \"sensors:dht22_humedad:latest\",
          \"type\": \"command\",
          \"refId\": \"A\"
        }
      },
      {
        \"refId\": \"C\",
        \"relativeTimeRange\": {
          \"from\": 300,
          \"to\": 0
        },
        \"datasourceUid\": \"__expr__\",
        \"model\": {
          \"type\": \"threshold\",
          \"conditions\": [
            {
              \"evaluator\": {
                \"params\": [80],
                \"type\": \"gt\"
              },
              \"operator\": {
                \"type\": \"and\"
              },
              \"query\": {
                \"params\": [\"A\"]
              },
              \"reducer\": {
                \"params\": [],
                \"type\": \"last\"
              },
              "type": "query"
            }
          ],
          \"datasource\": {
            \"type\": \"__expr__\",
            \"uid\": \"__expr__\"
          },
          \"refId\": \"C\"
        }
      }
    ],
    \"folderUID\": \"${FOLDER_UID}\",
    \"noDataState\": \"NoData\",
    \"execErrState\": \"Error\",
    \"for\": \"10s\",
    \"isPaused\": false,
    \"notification_settings\": {
      \"receiver\": \"Email Notifications\"
    }
  }"

echo ""
echo "Creating Alert Rule: Gas Alarm Triggered..."
curl -s -u ${AUTH} -X POST ${GRAFANA_URL}/api/v1/provisioning/alert-rules \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Gas Alarm Alert\",
    \"condition\": \"C\",
    \"data\": [
      {
        \"refId\": \"A\",
        \"relativeTimeRange\": {
          \"from\": 300,
          \"to\": 0
        },
        \"datasourceUid\": \"${REDIS_DS_UID}\",
        \"model\": {
          \"command\": \"hget\",
          "expression": "A",
          \"field\": \"value\",
          \"keyName\": \"sensors:mq_gas_alarma:latest\",
          \"type\": \"command\",
          \"refId\": \"A\"
        }
      },
      {
        \"refId\": \"C\",
        \"relativeTimeRange\": {
          \"from\": 300,
          \"to\": 0
        },
        \"datasourceUid\": \"__expr__\",
        \"model\": {
          \"type\": \"threshold\",
          \"conditions\": [
            {
              \"evaluator\": {
                \"params\": [0.5],
                \"type\": \"gt\"
              },
              \"operator\": {
                \"type\": \"and\"
              },
              \"query\": {
                \"params\": [\"A\"]
              },
              \"reducer\": {
                \"params\": [],
                \"type\": \"last\"
              },
              "type": "query"
            }
          ],
          \"datasource\": {
            \"type\": \"__expr__\",
            \"uid\": \"__expr__\"
          },
          \"refId\": \"C\"
        }
      }
    ],
    \"folderUID\": \"${FOLDER_UID}\",
    \"noDataState\": \"NoData\",
    \"execErrState\": \"Error\",
    \"for\": \"5s\",
    \"isPaused\": false,
    \"notification_settings\": {
      \"receiver\": \"Email Notifications\"
    }
  }"

echo ""
echo "Alert rules created successfully!"
echo "Notification channel: Email Notifications (demo@iot-conference.com)"
echo ""
echo "Alert Rules Summary:"
echo "   Temperature > 30C -> WARNING"
echo "   Humidity > 80% -> WARNING"
echo "   Gas Alarm = 1 -> CRITICAL"
