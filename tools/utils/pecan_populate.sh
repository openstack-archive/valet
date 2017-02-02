PARSED_VAL=`grep keyspace /etc/valet/valet.conf |awk 'BEGIN{FS="="}{print $NF}'`
KEYSPACE_NAME="$PARSED_VAL"
sed -i -e "s/#VALET_KEYSPACE#/${KEYSPACE_NAME}/g" /opt/app/aic-valet-tools/populate.cql
cassandra_cnt=`/usr/bin/cqlsh -e "describe KEYSPACE ${KEYSPACE_NAME};"|grep -c CREATE`
if [ $cassandra_cnt -gt 15 ]; then
        exit 0
fi
/usr/bin/cqlsh -e "drop KEYSPACE ${KEYSPACE_NAME};"
sleep 5
/usr/bin/cqlsh -f /opt/app/aic-valet-tools/populate.cql
sleep 5
pecan populate /var/www/valet/config.py >> /var/log/valet/pecan_populate.out
sleep 5
exit 0
