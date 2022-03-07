# Cloud Function triggered by PubSub Event
# When a temperature over 23ºC or under 17ºC is received, a IoT Core command will be throw.

# Import libraries
import random
from datetime import datetime
from google.cloud import bigquery
import base64, json, sys, os
import google.cloud.logging
import logging
import pandas as pd

# Read from PubSub
def calculate_time(event, context):
    client = google.cloud.logging.Client()
    client.setup_logging()

    # Read message from Pubsub (decode from Base64)
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')

    # Load json
    message = json.loads(pubsub_message)

    logging.info(message)
    logging.debug(message)

    if message['status'] == 'salida':
        print('MESSAge: ', message)
        TABLE_READ = "aparkapp-343018.parkingDataset.iotToBigQuery"
        TABLE_DESTINATION ="aparkapp-343018.parkingDataset.status"

        def parse_time(timestamp):
            return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')

        departure_time = parse_time(message['timeStamp'])

        # Construct a BigQuery client object.
        client = bigquery.Client()
        """ READ BIGQUERY STATUS"""
        q = f"""SELECT * FROM `{TABLE_READ}` WHERE parking_id = '{message['parking_id']}' AND status = 'llegada'"""
        df = (client.query(q).result().to_dataframe())

        """ GET LAST ARRIVAL """
        df['timeStamp'] = df['timeStamp'].apply(parse_time)
        df = df[df['timeStamp']<departure_time].sort_values(by=['timeStamp'])
        arrival_time = df['timeStamp'].iloc[-1]

        ellapsed_time = departure_time - arrival_time
        precio = random.uniform(1.5, 1.9)

        status = [{'parking_id': message['parking_id'],
                    'arrival_time': str(arrival_time),
                    'departure_time': str(departure_time),
                    'total_time': str(ellapsed_time),
                    'combustible':message['combustible'],
                    'marca':message['marca'],
                    'matricula':message['matricula'],
                    'precio':precio}]

        bq_client = bigquery.Client()

        table = bq_client.get_table(TABLE_DESTINATION)
        errors = bq_client.insert_rows_json(table, status)
        if errors == []:
            logging.info(" #~#~#~#~#~#~# SUCCESS #~#~#~#~#~#~#")
        else:
            logging.info(" #~#~#~#~#~#~# FALLO #~#~#~#~#~#~#")
