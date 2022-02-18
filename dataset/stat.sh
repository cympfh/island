#!/bin/bash

echo "# Works"
echo -n "LastUpdated ="
sqlite3 dataset/works.db <<< "SELECT MAX(dt) FROM works ;"
echo -n "Items = "
sqlite3 dataset/works.db <<< "SELECT COUNT(*) FROM works ;"

echo

echo "# Records"
echo -n "LastUpdated ="
sqlite3 dataset/records.db <<< "SELECT MAX(dt) FROM records ;"
echo -n "Items = "
sqlite3 dataset/records.db <<< "SELECT COUNT(*) FROM records ;"

echo

echo "# Reviews"
echo -n "LastUpdated ="
sqlite3 dataset/reviews.db <<< "SELECT MAX(dt) FROM reviews ;"
echo -n "Items = "
sqlite3 dataset/reviews.db <<< "SELECT COUNT(*) FROM reviews ;"

echo

echo "# Staffs"
echo -n "LastUpdated ="
sqlite3 dataset/staffs.db <<< "SELECT MAX(dt) FROM staffs ;"
echo -n "Items = "
sqlite3 dataset/staffs.db <<< "SELECT COUNT(*) FROM staffs ;"
