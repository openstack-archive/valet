CREATE KEYSPACE IF NOT EXISTS valet_test WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor': '3' } AND durable_writes = true;

CREATE TABLE IF NOT EXISTS valet_test.placements(id text PRIMARY KEY, name text, orchestration_id text, resource_id text, location text, reserved boolean, plan_id text);

CREATE TABLE IF NOT EXISTS valet_test.groups(id text PRIMARY KEY, name text, description text, type text, members text);

CREATE TABLE IF NOT EXISTS valet_test.placement_requests(stack_id text PRIMARY KEY, request text);

CREATE TABLE IF NOT EXISTS valet_test.placement_results(stack_id text PRIMARY KEY, placement text);

CREATE TABLE IF NOT EXISTS valet_test.oslo_messages ("timestamp" text PRIMARY KEY, args text, exchange text, method text);

CREATE TABLE IF NOT EXISTS valet_test.plans (id text PRIMARY KEY, name text, stack_id text);

CREATE TABLE IF NOT EXISTS valet_test.uuid_map (uuid text PRIMARY KEY,  h_uuid text,  s_uuid text);

CREATE TABLE IF NOT EXISTS valet_test.app (stack_id text PRIMARY KEY,  app text);

CREATE TABLE IF NOT EXISTS valet_test.resource_status (site_name text PRIMARY KEY,  resource text);

CREATE TABLE IF NOT EXISTS valet_test.resource_log_index (site_name text PRIMARY KEY, resource_log_index text);

CREATE TABLE IF NOT EXISTS valet_test.app_log_index ( site_name text PRIMARY KEY,  app_log_index text);
