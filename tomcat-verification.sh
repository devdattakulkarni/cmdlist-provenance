#!/bin/bash

output=`ls /var/lib/tomcat*/webapps`

for val in $output
do
  if [ $val == 'ROOT' ]; then
    echo "Tomcat installed."
    exit 0
  fi
done

echo "Tomcat not installed."
exit 1
