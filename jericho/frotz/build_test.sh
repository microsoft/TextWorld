#!/bin/bash

gcc -g -o test test.c -I src/interface/ -Wl,-rpath=src -Lsrc -lfrotz