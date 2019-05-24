
"""
This module produces abrupt concept drifts by
instantiating a generator and switching
from a centroid to another, abruptly

Eventualy one could try to produce more complex
drifts (gradual, sequential, etc...)
But this is just to show intercations with MLFLow
"""

import click
import time
import pickle
import datetime as dt
import signal

import numpy as np
from skmultiflow.data.random_rbf_generator import RandomRBFGenerator
from kafka import KafkaProducer


import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
import mlflow

CENTROID_LOW, CENTROID_HIGH = 0, 10  # TODO : should be variables

@click.command('', help=__doc__)
@click.option('--n-drifts', '-n', help='number of drifts to produce', default=100, type=int)
@click.option('--interval', '-i', help='time lapse bewteen two drifts, in seconds', default=0.5, type=float)
@click.option('--batch-size', '-b', help='number of samples to produce in a single interval', default=10, type=int)
@click.option('--n-classes', '-c', help='number of classes, or entries', default=1, type=int)
@click.option('--kafka-topic', '-t', help='kafka topic to produce on', default='drift_detection', type=str)
@click.option('--kafka-server', '-s', help='kafka server', default='localhost:9092', type=str)
def produce_abrupt_drifts(n_drifts, interval, batch_size, n_classes, kafka_topic, kafka_server):
    producer = KafkaProducer(
        bootstrap_servers=[kafka_server],
        value_serializer=pickle.dumps,
    )
    rbf_generator = RandomRBFGenerator(n_classes=n_classes, n_features=1, n_centroids=n_classes)
    rbf_generator.prepare_for_use()
    #logger.info(f"starting producer with {n_drifts} drifts seperated by {interval} seconds")

    old_time, curr_time = dt.datetime.now(), None

    mlflow.log_param('n_drifts', n_drifts)
    mlflow.log_param('interval', interval)
    mlflow.log_param('batch_size', batch_size)
    mlflow.log_param('n_classes', n_classes)

    def sigint_handler(signum, frame):
        import sys
        producer.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)  # safe exit in case of a ctrl-c

    drift_ctr = 0
    while drift_ctr < n_drifts:
        curr_time = dt.datetime.now()
        if (curr_time.second - old_time.second) > interval:
            metrics = dict()
            for idx, centroid in enumerate(rbf_generator.centroids):
                centroid.centre = list(np.random.randint(CENTROID_LOW, CENTROID_HIGH, size=(1, )))
                metrics[f"centroid {idx}"] = centroid.centre[0]
            mlflow.log_metrics(metrics)
            drift_ctr += 1

        curr_time = old_time

        sample = rbf_generator.next_sample(batch_size)[0]  # just take entries, not targets
        time.sleep(1.0)
        producer.send(kafka_topic, sample)

    producer.flush()


if __name__ == '__main__':
    produce_abrupt_drifts()