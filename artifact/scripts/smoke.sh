#!/usr/bin/env bash
#
# smoke.sh -- a few minutes end to end, to confirm the pipeline works.
#
# Runs the cheapest binaries of the packaged subset through the full cascade on
# both backbones and scores them. The numbers it prints come from far too little
# data to compare against the paper; this only answers "does it run and produce
# reports". It exercises both backbones on purpose: they load different
# frameworks from different sources, and a claim 1 run that reaches SAFE only
# after an hour and a half of BinShot is an expensive place to discover that
# TensorFlow or the downloaded weights are not working.
#
set -euo pipefail

ART="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-${PINPOINT_PYTHON:-python3}}"
OUT="$ART/results/smoke"
WORK="$OUT/targets"

mapfile -t SMOKE < <("$PY" - "$ART" <<'PYEOF'
import json, os, sys
with open(os.path.join(sys.argv[1], 'data', 'ground_truth', 'subset.json')) as f:
    print('\n'.join(json.load(f)['smoke']))
PYEOF
)

echo "== smoke set: ${#SMOKE[@]} binaries"
rm -rf "$WORK"; mkdir -p "$WORK"
for b in "${SMOKE[@]}"; do
    [ -f "$ART/data/targets/$b.json" ] && ln -sf "$ART/data/targets/$b.json" "$WORK/$b.json"
done
ls -1 "$WORK" | sed 's/^/   /'

echo
echo "== BinShot: running the cascade"
[ -d "$OUT" ] && find "$OUT" -name '*.lock' -delete 2>/dev/null || true
"$PY" "$ART/pinpoint.py" --vuln_db regular fno_inline \
    --data_dir "$WORK" --output_dir "$OUT" --cuda "${CUDA:-0}" --overwrite 2>&1 \
    | grep -vE '^Run ' | tail -8

echo
echo "== scoring (numbers are not comparable to the paper at this size)"
"$PY" "$ART/evaluate.py" --results "$OUT" --label "smoke" | tail -18

echo
echo "== SAFE: running the cascade"
# run_safe.py selects targets by name rather than from a directory, so the
# symlink farm above is not reused here.
TF_CPP_MIN_LOG_LEVEL=2 "$PY" "$ART/safe/run_safe.py" --vuln_db regular fno_inline \
    --only "${SMOKE[@]}" --output_dir "$OUT/safe" --overwrite 2>&1 | tail -10

echo
echo "[+] smoke test finished -- both backbones run end to end"
