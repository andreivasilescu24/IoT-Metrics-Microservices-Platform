import influxdb_client.client
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json
import influxdb_client 
from influxdb_client.client.write_api import WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone
import logging

load_dotenv()

MQTT_PORT = int(os.getenv('MQTT_PORT'))
MQTT_HOST = os.getenv('MQTT_HOST')

DB_URL = os.getenv('DB_URL')
DB_TOKEN = os.getenv('DB_TOKEN')
DB_ORG = os.getenv('DB_ORG')
DB_BUCKET = os.getenv('DB_BUCKET')

DEBUG_DATA_FLOW = True if os.getenv('DEBUG_DATA_FLOW', 'false').lower() == 'true' else False

db_client = influxdb_client.InfluxDBClient(
        url=DB_URL,
        token=DB_TOKEN,
        org=DB_ORG
    )

write_api = db_client.write_api(write_options=SYNCHRONOUS)

def check_loggging():
    if DEBUG_DATA_FLOW:
        logging_lvl = logging.DEBUG
    else:
        logging_lvl = logging.CRITICAL

    logging.basicConfig(format='{asctime} - {levelname} - {message}', style='{', level=logging_lvl, datefmt='%Y-%m-%d %H:%M:%S')

def on_connect(client, userdata, flags, reason_code, properties):
    logging.info(f"Connected to MQTT broker with result code {reason_code}")

    client.subscribe("#")

def on_message(client, userdata, msg):
    try:
        message_payload = json.loads(msg.payload)
        logging.info(f'Received message by topic [{msg.topic}]')
    except json.decoder.JSONDecodeError:
        logging.exception('Payload is not in a correct JSON format')
        return
    
    split_topic = msg.topic.split('/')
    
    location = split_topic[0]
    station = split_topic[1]

    db_topic_format = '.'.join(split_topic)
    
    influx_line = {}
    timestamp = None
    utc_timestamp = None

    if 'timestamp' not in message_payload:
        utc_timestamp = datetime.now(timezone.utc)
        timestamp = int(utc_timestamp.timestamp() * 1e9)
    else:
        try:
            utc_timestamp = datetime.fromisoformat(message_payload['timestamp']).astimezone(timezone.utc)
        except ValueError:
            logging.info("Received invalid timestamp format")
            utc_timestamp = datetime.now(timezone.utc)

        timestamp = int(utc_timestamp.timestamp() * 1e9)

    logging.info(f'Data timestamp is: {utc_timestamp}')

    for key in message_payload:
        if type(message_payload[key]) == int or type(message_payload[key]) == float:
            influx_line[key] = message_payload[key]

    for field in influx_line:
        logging.info(f'{db_topic_format}.{field} {influx_line[field]}')
        new_point = influxdb_client.Point(f'{station}.{field}') \
                    .tag('location', location) \
                    .tag('station', station) \
                    .field("value", float(influx_line[field])) \
                    .time(time=timestamp, write_precision=WritePrecision.NS)
        
        write_api.write(bucket=DB_BUCKET, org=DB_ORG, record=new_point)
    

if __name__ == '__main__':
    check_loggging()

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message

    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as e:
        logging.critical(f'Could not connect to MQTT broker: {e}')

    mqttc.loop_forever()
