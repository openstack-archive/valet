#!/usr/bin/env bash

# drop keyspace
echo "drop valet keyspace"
/opt/app/apache-cassandra-2.1.1/bin/cqlsh  -e "DROP KEYSPACE valet_test;"

sleep 5

# populate tables
echo "populate valet tables"
# /opt/app/apache-cassandra-2.1.1/bin/cqlsh  -f ./populate.cql
pecan populate /var/www/valet/config.py

/opt/app/apache-cassandra-2.1.1/bin/cqlsh  -e "DESCRIBE KEYSPACE valet_test;"

echo "Done populating"
