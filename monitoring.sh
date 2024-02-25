#!/usr/bin/bash
#
# Some basic monitoring functionality; Tested on Amazon Linux 2023.
#
TOKEN=`curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)

#Added Functionality Anna Ballot
#reference: https://www.tecmint.com/linux-uptime-command-examples/

UP_TIME=$(uptime -p)
UP_SECONDS="$(cat /proc/uptime | grep -o '^[0-9]\+')"
UP_MINS="$((${UP_SECONDS} / 60))"


echo "Instance ID: $INSTANCE_ID"
echo "Memory utilisation: $MEMORYUSAGE"
echo "No of processes: $PROCESSES"
if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi
echo "Uptime of server: $UP_TIME" 
echo "UP_SECONDS of server: $UP_SECONDS" 
echo "UP_MINS of server: $UP_MINS" 
