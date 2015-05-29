#!/bin/bash

docker -v

if [ $? == 0 ]; then
  echo "Docker installed."
  exit 0
else
  echo "Docker not installed."
  exit 1
fi
