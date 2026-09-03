#!/bin/bash

# read target field, sort and calc 95% percentile
awk -F '[=,]' '{ print $4 }' ./demo.log | sort -n | awk ' { all[NR]=$0 } END { print all[int(NR*0.95 - 0.5)]} '