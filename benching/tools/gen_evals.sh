OUTPUT="$1"
NB_ITER=10

if [ "$#" -lt 1 ] ; then
    >&2 echo "Missing argument: output directory."
    exit 1
fi

if [ -z "$EH_ELFS" ]; then
    >&2 echo "Missing environment: EH_ELFS. Aborting."
    exit 1
fi

mkdir -p "$OUTPUT"

for flavour in 'eh_elf' 'vanilla' 'vanilla-nocache'; do
    >&2 echo "$flavour..."
    source "$(dirname "$0")/../../env/apply" "$flavour" release
    for iter in $(seq 1 $NB_ITER); do
        >&2 echo -e "\t$iter..."
        LD_LIBRARY_PATH="$EH_ELFS:$LD_LIBRARY_PATH" \
            perf report 2>&1 >/dev/null | tail -n 1 \
            | python "$(dirname $0)/to_report_fmt.py" \
            | sed 's/^.* & .* & \([0-9]*\) & .*$/\1/g'
    done > "$OUTPUT/${flavour}_times"
    deactivate
done
