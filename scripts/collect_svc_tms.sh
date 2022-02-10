#!/bin/bash
# Collect from Service 1
rm -rf svc_1_times.log
for pod in `kubectl get pods | grep svc-1 | awk '{print $1}'`; do echo $pod >> svc_1_times.log; kubectl logs $pod testapp-svc-1 | grep INFO | grep Success | awk '{print $7$9}' >> svc_1_times.log; done
# Collect from Service 2
rm -rf svc_2_times.log
for pod in `kubectl get pods | grep svc-2 | awk '{print $1}'`; do echo $pod >> svc_2_times.log; kubectl logs $pod testapp-svc-2 | grep INFO | grep "No URLs" | awk '{print $7$9}' >> svc_2_times.log; done
