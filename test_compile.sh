#!/bin/bash

cd $GITPOD_REPO_ROOT

python3 -m unittest tests.test_generate

g++ -I/tmp/include -c /tmp/src/objects_world.cpp
