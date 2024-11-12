#!/bin/bash
Xvfb :99 -ac -screen 0 "$XVFB_RES" -nolisten tcp &
XVFB_PROC=$!
sleep 2
exec "$@"
kill $XVFB_PROC