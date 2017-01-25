#!/usr/bin/env bash

if [ -z $VALET_KEYSPACE ]; then
   echo "ERR: VALET_KEYSPACE is not defined."
   exit
else
   sed -i.bak "s/#VALET_KEYSPACE#/${VALET_KEYSPACE}/g" ./populate.cql
fi

if [ -z $CASSANDRA_BIN ]; then
   echo "ERR: CASSANDRA_BIN is not defined."
   exit
fi

# drop keyspace
echo "Drop Valet keyspace - ${VALET_KEYSPACE}"
${CASSANDRA_BIN}cqlsh  -e "DROP KEYSPACE ${VALET_KEYSPACE};"

sleep 5

# populate tables
echo "Populate Valet Api tables"
pecan populate /var/www/valet/config.py

echo "Populate Valet Engine tables + Api indexes"
${CASSANDRA_BIN}cqlsh  -f ./populate.cql

${CASSANDRA_BIN}cqlsh  -e "DESCRIBE KEYSPACE ${VALET_KEYSPACE};"

echo "Done populating - ${VALET_KEYSPACE}"
