#!/bin/bash

output=`ps -eaf | grep tomcat | awk '{print $1}'`

for val in $output
do
  if [ $val == 'tomcat7' ]; then
    echo "Tomcat installed."
    exit 0
  fi
done

echo "Tomcat not installed."
exit 1
