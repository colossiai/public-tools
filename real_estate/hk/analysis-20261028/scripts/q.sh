#!/bin/sh
curl -s -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36' -H 'Content-Type: application/json' -H 'Platform: Web' -H 'Referer: https://hk.centanet.com/findproperty/list/transaction' --max-time 30 -X POST 'https://hk.centanet.com/findproperty/api/Transaction/Search' -d "$1"
