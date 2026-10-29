# 🎓 Student Performance System — Native C Implementation

## Compile & Run

```bash
# Compile
gcc -o student_performance student_performance.c -lm -std=c99

# Run (Interactive mode)
./student_performance

# Quick demo (auto-filled data)
echo "2" | ./student_performance

# Save report to file
echo "2" | ./student_performance > report.txt
```

## Features (Pure C)
- Menu-driven console interface
- Student data input: name, roll, semester, subjects, marks, attendance
- Grade calculation: A+, A, B, C, D, F
- SGPA/CGPA computation (10-point scale)
- Per-subject ASCII bar charts & analysis
- Personalized recommendations engine
- Weekly study timetable generation
- Career path suggestions (keyword matching)
- Risk alerts for failing/low attendance
- Motivational messages
