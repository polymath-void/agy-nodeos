#!/bin/bash
pkill -f daemon.py || true
rm -f daemon.log
python daemon.py --run-as-daemon
sleep 2

echo -e "\033[93m[1] Creating 50 dummy python files to stress the AST parser and Physics Engine...\033[0m"
mkdir -p mess_test
for i in {1..50}; do
  echo "def func_$i(): pass" > mess_test/file_$i.py
  if [ $i -gt 1 ]; then
    prev=$((i-1))
    echo -e "import file_$prev\nfile_$prev.func_$prev()" >> mess_test/file_$i.py
  fi
done

sleep 3
echo -e "\n\033[92m[2] Querying SQLite Database for ingested kinetic nodes:\033[0m"
sqlite3 agy_nodeos.db "SELECT count(*) FROM nodes WHERE filepath LIKE '%mess_test%';"

echo -e "\n\033[93m[3] Simulating high-frequency Swarm Agent drops into workflow.json to test debouncing...\033[0m"
for i in {1..10}; do
  echo "{\"type\": \"JSON_Task\", \"status\": \"pending\", \"action\": \"stress_test_$i\"}" > workflow.json
  sleep 0.1
done

sleep 3
echo -e "\n\033[93m[4] Deleting the 'mess_test' directory to trigger mass FileDeletedEvents...\033[0m"
rm -rf mess_test

sleep 4
echo -e "\n\033[92m[5] Querying SQLite Database to verify real-time purge:\033[0m"
sqlite3 agy_nodeos.db "SELECT count(*) FROM nodes WHERE filepath LIKE '%mess_test%';"

echo -e "\n\033[96m[6] Inspecting the final Daemon Log:\033[0m"
tail -n 25 daemon.log
