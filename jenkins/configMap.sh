#!/bin/bash

kubectl create configmap airflow-dags --from-file=../project/airflow/dags/
kubectl create configmap airflow-files --from-file=../project/airflow/files/
kubectl create configmap streamlit-files --from-file=../project/weather-dashboard/files/
kubectl create configmap grafana-provisioning --from-file=../project/monitoring/provisioning/
kubectl create configmap prometheus-config --from-file=../project/monitoring/prometheus.yml
kubectl create configmap mariadb-initdb --from-file=../project/initdb/
