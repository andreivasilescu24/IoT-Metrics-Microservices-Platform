# IoT Metrics Microservices Platform

## Deploy

Before running the platform, you must create a `.env` file in the root directory to define the necessary environment variables:

- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_ORG`: InfluxDB organization
- `DB_BUCKET`: InfluxDB initial bucket
- `DB_TOKEN`: Database security token
- `GF_ADMIN_USER`: Grafana login username
- `GF_ADMIN_PASSWORD`: Grafana login password

The `adapter` service has a evironment variable named `DEBUG_DATA_FLOW`, defined inside the `stack.yml` file, which can be set to `true` in order to log the actions inside the console, or `false` otherwise

Run the script `run.sh` in order to build the Docker image for the adapter and then deploy the micoreservices using Docker Swarm stack named `station_metrics`.

This will start the following microservices:

- `mosquitto-broker` – MQTT broker for message communication, running on port 1883
- `adapter` – Connects to the MQTT broker and stores metrics in InfluxDB
- `influxdb` – Time-series database for storing IoT metrics (internal network only)
- `grafana` – Visualization and monitoring tool, accessible at `http://localhost:80`

### Adapter

The `adapter.py` file implements an adapter that connects to the MQTT broker, which is represented by a container running the `eclipse-mosquitto` image.

Upon connecting to the broker, the adapter subscribes to all topics by subscribing to the special topic `#`. Additionally, the
adapter checks the value (`true/false`) of the `DEBUG_DATA_FLOW` environment variable (defined in `stack.yml`), which determines
whether the adapter will enable logging.

The adapter connects to the InfluxDB database using the credentials specified in the `.env` file, which must be defined before execution.

When a message is received on any topic, the adapter verifies whether the payload follows a proper JSON format. If valid, it
parses the topic by splitting the string using `/` to extract `location` and `station`. If the payload contains a `timestamp`
field in the correct format, it will use that timestamp for inserting data into the database (converted to UTC timestamp)
Otherwise, it considers the current UTC time at the moment of message reception as the database timestamp. After this
validation, the adapter filters out only key-value pairs from the payload where the value is of type `int` or `float`.

Following the selection process, the adapter inserts the data into the database, where `_measurement` is represented as a string
in the format `STATION.METRIC`, allowing easier data grouping in Grafana dashboards by maintaining a consistent format. The
`_field` contains the metric value, and two tags are added: one for location (`location`) and another for station (`station`),
along with the timestamp.

### MQTT Broker

The broker is configured in the `mosquitto.conf` file.  
Accessible on port `1883` from `localhost`.

### InfluxDB

InfluxDB does not expose any ports to `localhost`; it is accessible only within the Docker network on port `8086`.

### Grafana

Accessible on port `80` from `localhost`.  
The `grafana` folder contains dashboard configurations in JSON format.

To connect Grafana to InfluxDB, the credentials specified in the environment variables from the `stack.yml` file should be
used.

For the URL, either the InfluxDB service name or the private IP within the Docker network where Grafana and the database reside
should be used.

The `grafana` directory has two JSON files which can be imported inside Grafana to display the created Dashboards.
