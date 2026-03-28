
ts() {
  local fmt="%Y-%m-%d %H:%M:%S"
  local help="Usage: ts [time]

Convert between epoch and time.

Input:
  epoch seconds (10 digits)
  epoch milliseconds (13 digits)
  \"yyyy-MM-dd HH:mm:ss\"
  \"yyyy-MM-dd\"

Output:
  UTC time
  Local time
  epoch seconds
  epoch milliseconds

Examples:
  ts
  ts 1710800000
  ts 1710800000123
  ts \"2026-03-19 12:30:00\"
  ts \"2026-03-19\"
"

  [[ "$1" == "-h" ]] && { echo "$help"; return; }

  format_output() {
    local sec="$1"
    local ms="$2"

    local utc=$(date -u -r "$sec" +"$fmt")
    local localt=$(date -r "$sec" +"$fmt")

    printf "UTC   : %s.%03d\n" "$utc" "$ms"
    printf "Local : %s.%03d\n" "$localt" "$ms"
    printf "epoch_sec : %s\n" "$sec"
    printf "epoch_ms  : %s%03d\n" "$sec" "$ms"
  }

  # no argument → current time
  if [[ -z "$1" ]]; then
    local sec=$(date +%s)
    local ms=$(($(date +%s%N 2>/dev/null | cut -c11-13)))
    [[ -z "$ms" ]] && ms=000
    format_output "$sec" "$ms"
    return
  fi

  local in="$1"

  # epoch milliseconds
  if [[ "$in" =~ ^[0-9]{13}$ ]]; then
    local sec=${in:0:10}
    local ms=${in:10:3}
    format_output "$sec" "$ms"
    return
  fi

  # epoch seconds
  if [[ "$in" =~ ^[0-9]{10}$ ]]; then
    format_output "$in" "000"
    return
  fi

  # yyyy-MM-dd HH:mm:ss
  if [[ "$in" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
    local sec=$(date -u -j -f "%Y-%m-%d %H:%M:%S" "$in" +%s)
    format_output "$sec" "000"
    return
  fi

  # yyyy-MM-dd
  if [[ "$in" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    local sec=$(date -u -j -f "%Y-%m-%d" "$in" +%s)
    format_output "$sec" "000"
    return
  fi

  echo "Invalid input. Run: ts -h"
}