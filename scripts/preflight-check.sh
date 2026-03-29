#!/bin/bash
set -euo pipefail

echo "=== Pre-flight checks ==="
ERRORS=0

for def in containers/*.def; do
    echo "Checking $def..."
    grep -q "^Bootstrap:" "$def" || { echo "ERROR: $def missing Bootstrap line"; ERRORS=$((ERRORS+1)); }

    if grep -q "^%post" "$def"; then
        grep -A2 "^%post" "$def" | grep -q "set -e" || echo "WARN: $def %post missing 'set -e'"
    fi

    if grep -q "apt-get" "$def"; then
        grep -q "DEBIAN_FRONTEND=noninteractive" "$def" || {
            echo "ERROR: $def uses apt-get without DEBIAN_FRONTEND=noninteractive"
            ERRORS=$((ERRORS+1))
        }
    fi

done

for def in containers/*.def; do
    if grep -q "requirements" "$def"; then
        while read -r src dst; do
            case "$src" in
                containers/*requirements*.txt)
                    [ -f "$src" ] || { echo "ERROR: $def references $src but file not found"; ERRORS=$((ERRORS+1)); }
                    ;;
            esac
        done < <(awk '/^%files/{flag=1;next}/^%/{if(flag){exit}}flag{print $1" "$2}' "$def")
    fi
done

for def in containers/stage*.def; do
    stage=$(basename "$def" .def)
    test_file="tests/test-${stage}.sh"
    [ -f "$test_file" ] || echo "WARN: No test file for $stage (expected $test_file)"
done

if [ "$ERRORS" -gt 0 ]; then
    echo "=== FAILED: $ERRORS errors found ==="
    exit 1
fi

echo "=== All pre-flight checks passed ==="
