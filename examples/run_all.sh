#!/bin/bash

pushd "$(dirname "$0")"

for f in *.py; do
  python $f || exit 1
done

popd
