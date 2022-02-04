#!/usr/bin/env bash
PORT=`kubectl get svc testapp-svc-2 -o go-template='{{range.spec.ports}}{{if .nodePort}}{{.nodePort}}{{"\n"}}{{end}}{{end}}'`
while true; do curl localhost:$PORT/statistics; sleep 2; done | tee ../logs/load.log
