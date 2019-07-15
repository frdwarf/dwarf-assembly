#!/bin/bash

if [ "$#" -lt 1 ] ; then
    >&2 echo "Missing argument: directory"
    exit 1
fi

BENCH_DIR="$(echo $1 | sed 's@/$@@g')"
ENV_APPLY="$(readlink -f "$(dirname $0)/../../env/apply")"

if ! [ -f "$ENV_APPLY" ] ; then
    >&2 echo "Cannot find helper scripts. Abort."
    exit 1
fi

function status_report {
    echo -e "\e[33;1m[$BENCH_DIR]\e[0m $1"
}
