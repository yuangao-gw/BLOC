#!/usr/bin/env bash
fname=$1
while true; do for nm in $(kubectl get pods | grep svc-2  | awk '{print $1}'); do kubectl logs $nm micoproxy | grep accepted | wc -l | tr '\n' ','; done; echo; sleep 2; done | tee ./logs/$fname.log
