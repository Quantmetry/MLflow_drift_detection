"""
This module implements the follownig workflow:
1. connect to a kafka topic and consume data from it
2. instantiate a drift detector (ADWIN)
3. add elements to ADWIN
4. if a change is detected, send information into mlflow to get fancy tracking/viz
"""
import click
import time
import pickle

import numpy as np
from skmultiflow.drift_detection.adwin import ADWIN
from kafka import KafkaConsumer

# use basic logging, logs from the producer should not be present in the producer, only in the consumer
import mlflow
import mlflow.sklearn

DELTA_EXPLAIN = 'delta value for the ADWIN detector, the greater this value is, the more nervous the detector will be'

@click.command('', help=__doc__)
@click.option('--delta', '-d', help=DELTA_EXPLAIN, default=0.01)
@click.option('--kafka-topic', '-t', help='kafka topic to produce on', default='drift_detection', type=str)
@click.option('--kafka-server', '-s', help='kafka server', default='localhost:9092', type=str)
def detect_drifts(delta, kafka_topic, kafka_server):
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=[kafka_server],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        value_deserializer=pickle.loads
    )

    adwin = ADWIN(delta=delta)
    mlflow.log_param("delta", delta)

    for message in consumer:
        array = message.value
        for row in array:  # TODO : parallel version, apply on columns instead
            for feature_num, e in enumerate(row):  # for the moment skmultiflow detectors take scalars as input, hopefully they will take
                start = time.time()
                adwin.add_element(e)
                change = adwin.detected_change()
                run_time = time.time() - start
                if change:
                    mlflow.log_metric(f"drift on feature {feature_num}", run_time)
                    adwin.reset()

    mlflow.sklearn.log_model(adwin)



if __name__ == '__main__':
    detect_drifts()
