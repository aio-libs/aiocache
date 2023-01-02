#!/bin/bash

pushd "$(dirname "$0")"

for f in `find . -name '*.py' -not -path "./frameworks/*"`; do
  echo "########## Running $f #########"
  # ResourceWarning in __del__ fails to exit 1, so we grep for warnings.
  # Did try using sys.unraisablehook, but it wasn't working.
  python -bb -We -X dev $f 2>&1 | tee /dev/stderr | ( ! fgrep -i 'warning' > /dev/null ) || exit 1
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    exit 1
  fi
  echo;echo;echo
done

popd
