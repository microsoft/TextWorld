#!/bin/bash
cd ../cheapglk && make -j16 && cd ../Git-Glulx && make -j16 && PYTHONPATH=. ./git-glulx ../Sherbrooke/textworld/games/test.ulx
