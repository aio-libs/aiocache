#!/bin/bash

pushd "$(dirname "$0")"

for f in *.py; do
  echo "########## Running $f #########"
  # ResourceWarning fails to exit 1, so we grep for warnings.
  python -bb -We -X dev -c "import asyncio, os, sys, ${f%.*}; sys.unraisablehook = lambda: os._exit(1); asyncio.run(${f%.*}.main())" || exit 1
  echo;echo;echo
done

popd
