#!/bin/bash
Xvfb :99 -ac -screen 0 "$XVFB_RES" -nolisten tcp &
XVFB_PROC=$!
sleep 2
pwd
ls -lsa
echo $DISPLAY
python run_sim.py
kill $XVFB_PROC