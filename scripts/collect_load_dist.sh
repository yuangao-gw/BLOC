#!/usr/bin/env bash
while true; do for nm in $(kubectl get pods | grep svc-2  | awk '{print $1}'); do kubectl logs $nm micoproxy | grep incoming | wc -l | tr '\n' ','; done; echo; sleep 2; done | tee ./logs/dist.log
