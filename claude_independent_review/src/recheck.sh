#!/usr/bin/env bash
# recheck.sh -- re-run the independent cross-check and compare it with the recorded outputs in out/.
#
# Run from claude_independent_review/ after compiling census, completeness, g_sources and build into it
# (see docs/reproducing.md).  New outputs go to the scratch folder .recheck-tmp/ (removed at the end);
# out/ is only read.
#   - each program must exit 0 and print the same output as its recorded log (timing lines ignored);
#   - the rebuilt plan must be byte-identical to out/my_plan_v1.txt;
#   - invalid input must be rejected with a non-zero exit code (negative tests).
# Exit code: 0 if every check passes, 1 otherwise.
set -u
TMP=.recheck-tmp            # relative, so that program output contains no machine-specific paths
rm -rf "$TMP" && mkdir "$TMP" || exit 1
trap 'rm -rf "$TMP"' EXIT
fail=0
norm() { grep -v '^elapsed\|^RESULT:' "$1" | sed -E 's/ *\[[0-9.]+ s\]//'; }

check() {  # recorded-log program args...
  local rec=$1; shift
  "$@" > "$TMP/run.out" 2>&1
  local code=$?
  printf '== %s\n   exit code: %s' "$*" "$code"
  grep -h '^RESULT' "$TMP/run.out" | sed 's/^/ ; /' | tr -d '\n'
  echo
  [ "$code" -eq 0 ] || fail=1
  if diff <(norm "out/$rec") <(norm "$TMP/run.out" | sed -e "s#$TMP/classes\.txt#out/classes_census.txt#" -e "s#$TMP/plan\.txt#out/my_plan_v1.txt#") > /dev/null; then
    echo "   output: identical to out/$rec apart from timing"
  else
    echo "   output: DIFFERS from out/$rec"; fail=1
  fi
}

expect() {  # expected-exit-code description program args...
  local want=$1 what=$2; shift 2
  "$@" > "$TMP/neg.out" 2>&1
  local code=$?
  echo "== $what -> exit code $code (expected $want): $(grep -h 'invalid\|VERDICT\|^\[plan\] classes\|TENPAI HANDS\|^RESULT' "$TMP/neg.out" | tr '\n' ' ')"
  [ "$code" -eq "$want" ] || fail=1
}

echo "# Cross-check re-run: programs against the recorded outputs in out/"
check census_with_their_plan.log ./census.exe out/their_plan_k4_FINAL.txt -usage -classes "$TMP/classes.txt"
if diff <(sort "$TMP/classes.txt") <(sort out/classes_census.txt) > /dev/null; then
  echo "   class list: same lines as out/classes_census.txt (line order follows hash slots)"
else echo "   class list: DIFFERS from out/classes_census.txt"; fail=1; fi
check census_with_my_plan_v1.log ./census.exe out/my_plan_v1.txt -usage
check census_naive_recheck.log ./census.exe out/my_plan_v1.txt -naive
check completeness.log ./completeness.exe
check g_sources.log ./g_sources.exe
check build_v1.log ./build.exe out/classes_census.txt "$TMP/plan.txt"
if cmp -s "$TMP/plan.txt" out/my_plan_v1.txt; then echo "   rebuilt plan: byte-identical to out/my_plan_v1.txt"
else echo "   rebuilt plan: DIFFERS from out/my_plan_v1.txt"; fail=1; fi

echo
echo "# Negative tests"
for t in 0 65 abc; do expect 2 "census.exe -threads $t" ./census.exe out/their_plan_k4_FINAL.txt -threads "$t"; done
sed '1d' out/their_plan_k4_FINAL.txt > "$TMP/missing_class.txt"
expect 1 "census.exe <plan without its first class>" ./census.exe "$TMP/missing_class.txt"
awk 'NR == 6 { $4 = 34 } { print }' out/their_plan_k4_FINAL.txt > "$TMP/bad_tile.txt"
expect 1 "census.exe <plan with tile index 34>" ./census.exe "$TMP/bad_tile.txt"
expect 0 "census.exe -threads 1" ./census.exe out/their_plan_k4_FINAL.txt -threads 1

echo
echo "RECHECK: $([ "$fail" -eq 0 ] && echo OK || echo FAILED)"
exit "$fail"
