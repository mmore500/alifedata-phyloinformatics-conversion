#!/bin/bash

cd "$(dirname "$0")"

for python in \
    3.7 \
    3.8 \
    3.9 \
    3.10 \
    3.11 \
    3.12 \
; do
    "python${python}" -m piptools compile "requirements.in" -o "requirements-${python}.txt" &
done

wait

ln -sf requirements-3.9.txt requirements.txt

echo "fin"
