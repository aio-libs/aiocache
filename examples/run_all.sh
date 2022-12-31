#!/bin/bash

pushd "$(dirname "$0")"

for f in *.py; do
  echo "########## Running $f #########"
  python -bb -We -X dev -c "import asyncio, os, sys, ${f%.*}; sys.unraisablehook = lambda _: os._exit(1); asyncio.run(${f%.*}.main()); del ${f%.*}" || exit 1
done

popd
