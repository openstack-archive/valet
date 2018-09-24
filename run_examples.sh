# run specific tests:
# sudo tox -epy27 --  '(TestAffinity|TestDiversity)'

# isolate
# sudo tox -- --isolated

# run all tests until failure
# sudo tox -- --until-failure
 
# unparallel running (serial)
# sudo tox -epy27 -- '--concurrency=1'

# use  commands = ostestr --slowest '{posargs}' in file tox.ini
# https://docs.openstack.org/os-testr/latest/#running-tests
