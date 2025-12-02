#!/bin/bash
# fetch_classes.sh

curl -X POST \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0" \
  -H "Accept: application/json, text/javascript, */*; q=0.01" \
  -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Origin: https://commtech.byu.edu" \
  -H "Referer: https://commtech.byu.edu/noauth/classSchedule/index.php" \
  -d "searchObject[yearterm]=20261&sessionId=GH0JQG8JLMJVED9MSNAQ" \
  -o classes_full.json \
  "https://commtech.byu.edu/noauth/classSchedule/ajax/getClasses.php"

echo "Downloaded to classes_full.json"
ls -lh classes_full.json