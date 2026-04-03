# branch name starts with "local/" are not allowed to push

#!/bin/sh

branch="$(git branch --show-current)"

if echo "$branch" | grep -q '^local/'; then
  echo "Error: Pushing branches starting with 'local/' is not allowed."
  exit 1
fi

exit 0