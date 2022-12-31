#!/bin/bash

pushd "$(dirname "$0")"

for f in `find . -name '*.py' -not -path "./frameworks/*"`; do
  echo "########## Running $f #########"
  python -bb -We -X dev $f || exit 1
  echo;echo;echo
done

popd
