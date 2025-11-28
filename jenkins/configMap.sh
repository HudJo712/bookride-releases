#!/bin/bash

kubectl create configmap grafana-provisioning --from-file=../project/monitoring/provisioning/
kubectl create configmap prometheus-config --from-file=../project/monitoring/prometheus.yml

