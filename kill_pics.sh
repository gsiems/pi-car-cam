#!/bin/bash

for pid in `ps -ef | grep \[t]ake_pics | awk '{print $2}'` ; do
    kill -9 $pid
done
