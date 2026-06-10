#!/usr/bin/env bash
set -e
HOST="http://149.28.144.51"
LOCUST=".venv/Scripts/locust"

echo "=== Stage 2: 3 users ==="
$LOCUST -f test/locustfile.py --host $HOST --headless -u 3 -r 1 --run-time 3m --csv test/load_s2 --html test/load_s2.html

echo "=== Stage 3: 6 users ==="
$LOCUST -f test/locustfile.py --host $HOST --headless -u 6 -r 1 --run-time 3m --csv test/load_s3 --html test/load_s3.html

echo "=== Stage 4: 9 users ==="
$LOCUST -f test/locustfile.py --host $HOST --headless -u 9 -r 1 --run-time 3m --csv test/load_s4 --html test/load_s4.html

echo "=== All stages complete ==="
