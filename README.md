# MLFLow and scikit-multiflow, a good match

1. Generate abrupt drifts,
2. Send them into a kafka topic
3. We listen to this kafka topic on another entry_point
4. We detect drifts and log them into MLFlow

## Install & Setup (OSX)
For OSX users:
```bash
brew install librdkafka
brew cask install homebrew/cask-versions/adoptopenjdk8
brew install kafka
```

### Creating topics with kafka
```bash
kafka-topics --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic drift_detection
```

### Start zookeeper and kafka
```bash
brew services start zookeeper  # TODO zookeeper should only be required by confluent-kafka, REMOVE ME ?
brew services start kafka
```

### small issues, big impact
You need to add conda-forge to install packages like scikit-multiflow directly from conda
```bash
conda config --add topics conda-forge
```

## RUN
First make the producer send data though kafka
Here we generate 100 concept drift, pushing 10 rows into kafka every 0.5 seconds
```bash
mlflow run https://github.com/Quantmetry/mlflow.git/examples/abrupt_drift_detection -e producer -P n_drifts=100 -P interval=0.5 -P batch_size=10 -P n_classes=3
```

Then we have the detector listening on the right kafka topic, crashing logs whenever a drift is detected
```bash
mlflow run https://github.com/Quantmetry/MLflow_example.git -e detect_drifts -P delta=0.001
```

Finally visualize all this in the MLFLow UI
```bash
mlfow ui
```

### Deleting topics with kafka, (to rerun failed experiments)
```bash
kafka-server-start /usr/local/etc/kafka/server.properties  --override delete.topic.enable=true
kafka-topics --zookeeper 127.0.0.1:2181 --delete --topic drift_detection
```

## Further readings
* [Putting ML in productions using Kafka](https://towardsdatascience.com/putting-ml-in-production-i-using-apache-kafka-in-python-ce06b3a395c8)
* [Adaptive Windowing](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.144.2279&rep=rep1&type=pdf)
