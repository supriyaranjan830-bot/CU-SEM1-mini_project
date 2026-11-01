#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CLANG_BIN="${CLANG:-clang}"
if ! command -v "$CLANG_BIN" >/dev/null 2>&1; then
  echo "clang was not found. Install LLVM/Clang and try again." >&2
  exit 1
fi

"$CLANG_BIN" --target=wasm32 -O2 -nostdlib -fno-builtin \
  -Wl,--no-entry \
  -Wl,--export-memory \
  -Wl,--export=sp_reset \
  -Wl,--export=sp_set_student \
  -Wl,--export=sp_add_subject \
  -Wl,--export=sp_analyze \
  -Wl,--export=sp_is_analyzed \
  -Wl,--export=sp_student_name_ptr \
  -Wl,--export=sp_roll_ptr \
  -Wl,--export=sp_grade_ptr \
  -Wl,--export=sp_motivation_ptr \
  -Wl,--export=sp_subject_name_ptr \
  -Wl,--export=sp_career_ptr \
  -Wl,--export=sp_semester \
  -Wl,--export=sp_subject_count \
  -Wl,--export=sp_weak_count \
  -Wl,--export=sp_average_count \
  -Wl,--export=sp_strong_count \
  -Wl,--export=sp_fail_count \
  -Wl,--export=sp_attendance_risk \
  -Wl,--export=sp_critical_fail_risk \
  -Wl,--export=sp_attendance \
  -Wl,--export=sp_current_study_hours \
  -Wl,--export=sp_overall_percentage \
  -Wl,--export=sp_sgpa \
  -Wl,--export=sp_cgpa_estimate \
  -Wl,--export=sp_recommended_hours \
  -Wl,--export=sp_total_plan_hours \
  -Wl,--export=sp_subject_marks \
  -Wl,--export=sp_subject_max \
  -Wl,--export=sp_subject_percentage \
  -Wl,--export=sp_subject_category \
  -Wl,--export=sp_subject_plan_hours \
  -Wl,--export=sp_subject_target_gap \
  -Wl,--export=sp_marks_needed_to_pass \
  -Wl,--export=sp_category_plan_hours \
  -Wl,--export=sp_timetable_subject \
  -Wl,--initial-memory=2097152 \
  -Wl,--max-memory=2097152 \
  -Wl,-z,stack-size=65536 \
  src/student_engine.c -o student_engine.wasm

echo "Built $ROOT/student_engine.wasm"
