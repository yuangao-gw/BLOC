#!/bin/bash
read image=$1
sudo docker build -t ratnadeepb/testapp .
sudo docker push $image