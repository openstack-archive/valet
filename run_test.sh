
sudo tox -epy27 -- '--concurrency=1' $*

# EXAMPLE:
# ./run_test '(TestAffinity)'

# run specific tests:
# sudo tox -epy27 --  '(TestAffinity|TestDiversity)'