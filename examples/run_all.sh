#!/bin/bash

pushd "$(dirname "$0")"

for f in `find . -name '*.py'`; do
  echo "########## Running $f #########"
  python $f || exit 1
  echo;echo;echo
done

popd
