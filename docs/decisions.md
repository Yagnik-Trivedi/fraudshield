# Decision Log

### D1: Sparkov as the primary dataset (Oct 11)
It has card ids, timestamps and merchant geo, which are required for velocity and distance features
and for a realistic stream. IEEE-CIS has no clean entity/time structure for streaming; PaySim's balance
columns leak the label. IEEE-CIS is kept as an offline second benchmark.

### D2: Redpanda instead of Apache Kafka (Oct 11)
Kafka API compatible (client code transfers unchanged), a single container, no JVM/ZooKeeper, and light
on a laptop. Redpanda Console gives topic inspection for free.

### D3: LightGBM as the main model (Oct 11)
Strong on tabular data, fast to train and serve (sub-millisecond per row), handles categoricals, and
SHAP TreeExplainer gives exact, fast explanations.

### D4: Custom Redis feature store before Feast (Oct 11)
Writing the online/offline pair by hand is the learning goal and keeps the parity logic explainable.
Feast is in "Later".

### D5: PR-AUC as the primary metric (Oct 11)
With ~0.5% positives, ROC-AUC stays high even for weak models. PR-AUC and recall at fixed FPR reflect
analyst workload and missed fraud.

### D6: MLflow aliases for promotion (Oct 11)
Model registry aliases (`@champion`, `@challenger`) are the current MLflow mechanism (stages are
deprecated). The scoring API loads `models:/fraudshield@champion`.
