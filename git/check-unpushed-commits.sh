#! /bin/bash

for d in */; do
  echo "== $d =="
  (cd "$d" && git status -sb)
done