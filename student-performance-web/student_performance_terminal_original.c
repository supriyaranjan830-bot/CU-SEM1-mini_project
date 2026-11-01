/*
 * ============================================================================
 *  SMART STUDENT PERFORMANCE & STUDY RECOMMENDATION SYSTEM
 *  Language: C (ANSI C99)
 *  
 *  Features:
 *    - Student data input (name, roll, semester, subjects, marks, attendance)
 *    - Grade calculation (A+, A, B, C, D, F) with SGPA/CGPA
 *    - Per-subject performance analysis (weak / average / strong)
 *    - Personalized study recommendations
 *    - Study hours optimization
 *    - Weekly timetable generation
 *    - Career path suggestions based on strong subjects
 *    - Risk alerts for failing subjects
 *    - Formatted report output (can redirect to file)
 *
 *  Compile & Run:
 *    gcc -o student_performance student_performance.c -lm
 *    ./student_performance
 * ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_SUBJECTS 15
#define MAX_NAME 100
#define MAX_DAYS 7
#define MAX_SLOTS 5

/* ===================== STRUCTURES ===================== */

typedef struct {
    char name[MAX_NAME];
    float marks_obtained;
    float max_marks;
    float percentage;
    int   category;   /* 0=weak(<60), 1=average(60-79), 2=strong(>=80) */
} Subject;

typedef struct {
    char   name[MAX_NAME];
    char   roll[30];
    int    semester;
    int    num_subjects;
    Subject subjects[MAX_SUBJECTS];
    float  attendance;
    float  study_hours;
    float  overall_percentage;
    char   grade[3];
    float  sgpa;
    int    weak_count;
    int    avg_count;
    int    strong_count;
    int    fail_count;
} Student;

/* ===================== FUNCTION PROTOTYPES ===================== */

void   input_student_data(Student *s);
void   calculate_performance(Student *s);
void   assign_grade(Student *s);
float  calculate_sgpa(float percentage);
void   categorize_subjects(Student *s);
void   display_report_header(Student *s);
void   display_subject_analysis(Student *s);
void   display_grade_card(Student *s);
void   display_recommendations(Student *s);
void   display_study_plan(Student *s);
void   display_timetable(Student *s);
void   display_career_paths(Student *s);
void   display_risk_alerts(Student *s);
void   display_motivation(Student *s);
void   print_separator(char ch, int len);
void   print_centered(const char *text, int width);
void   print_bar(float percentage, int width);

/* ===================== MAIN ===================== */

int main() {
    Student student;
    int choice;

    printf("\n");
    print_separator('=', 70);
    print_centered("SMART STUDENT PERFORMANCE & STUDY RECOMMENDATION SYSTEM", 70);
    print_centered("Powered by C Algorithm Engine", 70);
    print_separator('=', 70);
    printf("\n");

    do {
        printf("\n");
        print_separator('-', 50);
        printf("  MAIN MENU\n");
        print_separator('-', 50);
        printf("  1. Analyze Student Performance\n");
        printf("  2. Quick Demo (Pre-filled Data)\n");
        printf("  3. Exit\n");
        print_separator('-', 50);
        printf("  Enter your choice: ");
        scanf("%d", &choice);
        getchar(); /* consume newline */

        switch (choice) {
            case 1:
                input_student_data(&student);
                calculate_performance(&student);
                break;
            case 2: {
                /* Pre-filled demo data */
                strcpy(student.name, "Supriya Sharma");
                strcpy(student.roll, "22CS1045");
                student.semester = 5;
                student.num_subjects = 6;
                student.attendance = 78.0;
                student.study_hours = 4.5;

                const char *subj_names[] = {"Mathematics", "Physics", "Chemistry",
                                            "Computer Science", "English", "Data Structures"};
                float marks[] = {72, 85, 55, 92, 68, 88};
                float max_m[] = {100, 100, 100, 100, 100, 100};
                for (int i = 0; i < 6; i++) {
                    strcpy(student.subjects[i].name, subj_names[i]);
                    student.subjects[i].marks_obtained = marks[i];
                    student.subjects[i].max_marks = max_m[i];
                }
                printf("\n  [Demo] Loaded sample data for %s\n", student.name);
                calculate_performance(&student);
                break;
            }
            case 3:
                printf("\n  Thank you for using the system. Goodbye!\n\n");
                break;
            default:
                printf("\n  Invalid choice. Please try again.\n");
        }
    } while (choice != 3);

    return 0;
}

/* ===================== INPUT ===================== */

void input_student_data(Student *s) {
    printf("\n");
    print_separator('=', 50);
    printf("  STUDENT DATA ENTRY\n");
    print_separator('=', 50);

    printf("  Student Name     : ");
    fgets(s->name, MAX_NAME, stdin);
    s->name[strcspn(s->name, "\n")] = '\0';

    printf("  Roll Number      : ");
    fgets(s->roll, 30, stdin);
    s->roll[strcspn(s->roll, "\n")] = '\0';

    printf("  Semester (1-8)   : ");
    scanf("%d", &s->semester);

    printf("  Number of Subjects (max %d): ", MAX_SUBJECTS);
    scanf("%d", &s->num_subjects);
    if (s->num_subjects > MAX_SUBJECTS) s->num_subjects = MAX_SUBJECTS;
    if (s->num_subjects < 1) s->num_subjects = 1;
    getchar();

    for (int i = 0; i < s->num_subjects; i++) {
        printf("\n  --- Subject %d ---\n", i + 1);
        printf("    Subject Name    : ");
        fgets(s->subjects[i].name, MAX_NAME, stdin);
        s->subjects[i].name[strcspn(s->subjects[i].name, "\n")] = '\0';
        printf("    Marks Obtained  : ");
        scanf("%f", &s->subjects[i].marks_obtained);
        printf("    Maximum Marks   : ");
        scanf("%f", &s->subjects[i].max_marks);
        getchar();
    }

    printf("\n  Attendance %%     : ");
    scanf("%f", &s->attendance);
    printf("  Study Hours/Day  : ");
    scanf("%f", &s->study_hours);
    getchar();
}

/* ===================== CALCULATIONS ===================== */

void calculate_performance(Student *s) {
    float total_obtained = 0, total_max = 0;

    for (int i = 0; i < s->num_subjects; i++) {
        s->subjects[i].percentage =
            (s->subjects[i].marks_obtained / s->subjects[i].max_marks) * 100.0f;
        total_obtained += s->subjects[i].marks_obtained;
        total_max += s->subjects[i].max_marks;
    }

    s->overall_percentage = (total_obtained / total_max) * 100.0f;
    assign_grade(s);
    s->sgpa = calculate_sgpa(s->overall_percentage);
    categorize_subjects(s);

    /* Display full report */
    display_report_header(s);
    display_grade_card(s);
    display_subject_analysis(s);
    display_risk_alerts(s);
    display_recommendations(s);
    display_study_plan(s);
    display_timetable(s);
    display_career_paths(s);
    display_motivation(s);
}

void assign_grade(Student *s) {
    float p = s->overall_percentage;
    if      (p >= 90) strcpy(s->grade, "A+");
    else if (p >= 80) strcpy(s->grade, "A");
    else if (p >= 70) strcpy(s->grade, "B");
    else if (p >= 60) strcpy(s->grade, "C");
    else if (p >= 50) strcpy(s->grade, "D");
    else              strcpy(s->grade, "F");
}

float calculate_sgpa(float percentage) {
    if (percentage >= 90) return 9.0f + (percentage - 90) / 10.0f;
    if (percentage >= 80) return 8.0f + (percentage - 80) / 10.0f;
    if (percentage >= 70) return 7.0f + (percentage - 70) / 10.0f;
    if (percentage >= 60) return 6.0f + (percentage - 60) / 10.0f;
    if (percentage >= 50) return 5.0f + (percentage - 50) / 10.0f;
    if (percentage >= 40) return 4.0f + (percentage - 40) / 10.0f;
    return percentage / 10.0f;
}

void categorize_subjects(Student *s) {
    s->weak_count = s->avg_count = s->strong_count = s->fail_count = 0;
    for (int i = 0; i < s->num_subjects; i++) {
        float p = s->subjects[i].percentage;
        if (p < 40) {
            s->subjects[i].category = 0;
            s->weak_count++;
            s->fail_count++;
        } else if (p < 60) {
            s->subjects[i].category = 0;
            s->weak_count++;
        } else if (p < 80) {
            s->subjects[i].category = 1;
            s->avg_count++;
        } else {
            s->subjects[i].category = 2;
            s->strong_count++;
        }
    }
}

/* ===================== DISPLAY FUNCTIONS ===================== */

void display_report_header(Student *s) {
    printf("\n\n");
    print_separator('*', 70);
    print_centered("STUDENT PERFORMANCE ANALYSIS REPORT", 70);
    print_separator('*', 70);
    printf("\n");
    printf("  Student Name     : %s\n", s->name);
    printf("  Roll Number      : %s\n", s->roll);
    printf("  Semester         : %d\n", s->semester);
    printf("  Total Subjects   : %d\n", s->num_subjects);
    printf("  Attendance       : %.1f%%\n", s->attendance);
    printf("  Study Hours/Day  : %.1f hrs\n", s->study_hours);
    printf("\n");
}

void display_grade_card(Student *s) {
    print_separator('=', 70);
    print_centered("GRADE CARD", 70);
    print_separator('=', 70);
    printf("\n");
    printf("  Overall Percentage : %.2f%%\n", s->overall_percentage);
    printf("  Overall Grade      : %s\n", s->grade);
    printf("  SGPA (10-point)    : %.2f\n", s->sgpa);
    printf("  CGPA (estimated)   : %.2f\n", s->sgpa * 0.97f);
    printf("\n  Performance Bar    : ");
    print_bar(s->overall_percentage, 40);
    printf("\n\n");

    printf("  Subject Summary:\n");
    printf("    Strong (>=80%%)  : %d subjects\n", s->strong_count);
    printf("    Average (60-79%%): %d subjects\n", s->avg_count);
    printf("    Weak (<60%%)     : %d subjects\n", s->weak_count);
    if (s->fail_count > 0)
        printf("    FAILING (<40%%)  : %d subjects  *** ALERT ***\n", s->fail_count);
    printf("\n");
}

void display_subject_analysis(Student *s) {
    print_separator('=', 70);
    print_centered("SUBJECT-WISE ANALYSIS", 70);
    print_separator('=', 70);
    printf("\n");
    printf("  %-20s %8s %8s %8s  %-12s\n",
           "Subject", "Marks", "Max", "Pct(%)", "Status");
    print_separator('-', 70);

    for (int i = 0; i < s->num_subjects; i++) {
        const char *status;
        const char *indicator;
        if (s->subjects[i].category == 2) {
            status = "STRONG";
            indicator = "[****]";
        } else if (s->subjects[i].category == 1) {
            status = "AVERAGE";
            indicator = "[**  ]";
        } else {
            if (s->subjects[i].percentage < 40) {
                status = "FAILING!";
                indicator = "[!!!!]";
            } else {
                status = "WEAK";
                indicator = "[*   ]";
            }
        }

        printf("  %-20s %8.1f %8.1f %7.1f%%  %s %s\n",
               s->subjects[i].name,
               s->subjects[i].marks_obtained,
               s->subjects[i].max_marks,
               s->subjects[i].percentage,
               indicator, status);

        /* Mini bar chart */
        printf("  ");
        for (int j = 0; j < 22; j++) printf(" ");
        print_bar(s->subjects[i].percentage, 30);
        printf("\n");
    }
    printf("\n");
}

void display_risk_alerts(Student *s) {
    if (s->fail_count == 0 && s->attendance >= 75) return;

    print_separator('!', 70);
    print_centered("!! RISK ALERTS !!", 70);
    print_separator('!', 70);
    printf("\n");

    for (int i = 0; i < s->num_subjects; i++) {
        if (s->subjects[i].percentage < 40) {
            printf("  [CRITICAL] %s — %.1f%% — BELOW PASS MARK!\n",
                   s->subjects[i].name, s->subjects[i].percentage);
            printf("             You need %.0f more marks to pass.\n",
                   (40.0f * s->subjects[i].max_marks / 100.0f)
                       - s->subjects[i].marks_obtained);
        }
    }
    if (s->attendance < 75) {
        printf("  [WARNING]  Attendance is %.1f%% — below 75%% minimum!\n",
               s->attendance);
        printf("             Risk of debarment from examinations.\n");
    }
    if (s->fail_count >= 3) {
        printf("  [CRITICAL] %d subjects below passing. Academic probation risk!\n",
               s->fail_count);
    }
    printf("\n");
}

void display_recommendations(Student *s) {
    print_separator('=', 70);
    print_centered("PERSONALIZED STUDY RECOMMENDATIONS", 70);
    print_separator('=', 70);
    printf("\n");

    /* --- Weak Subject Recommendations --- */
    if (s->weak_count > 0) {
        printf("  [A] WEAK SUBJECT STRATEGY (Priority: HIGH)\n");
        print_separator('-', 50);
        printf("      Allocate 60%% of study time to these subjects:\n\n");
        for (int i = 0; i < s->num_subjects; i++) {
            if (s->subjects[i].category == 0) {
                float gap = 70.0f - s->subjects[i].percentage;
                printf("      * %s (%.1f%%) — Target: 70%%\n",
                       s->subjects[i].name, s->subjects[i].percentage);
                printf("        - Need to improve by %.1f%% points\n", gap);
                printf("        - Practice previous year questions daily\n");
                printf("        - Use spaced repetition (revise every 2-3 days)\n");
                if (s->subjects[i].percentage < 40)
                    printf("        - ** Consider joining coaching/tuition **\n");
                printf("\n");
            }
        }
    }

    /* --- Strong Subject Leverage --- */
    if (s->strong_count > 0) {
        printf("  [B] STRONG SUBJECT LEVERAGE\n");
        print_separator('-', 50);
        printf("      Maintain excellence in:\n\n");
        for (int i = 0; i < s->num_subjects; i++) {
            if (s->subjects[i].category == 2) {
                printf("      * %s (%.1f%%)\n",
                       s->subjects[i].name, s->subjects[i].percentage);
                printf("        - Participate in competitions/olympiads\n");
                printf("        - Help peers (teaching deepens understanding)\n");
                printf("        - Explore advanced topics & projects\n\n");
            }
        }
    }

    /* --- Average Subject Quick Wins --- */
    if (s->avg_count > 0) {
        printf("  [C] AVERAGE SUBJECTS — QUICK WINS\n");
        print_separator('-', 50);
        printf("      Small effort can push these to 80%%+:\n\n");
        for (int i = 0; i < s->num_subjects; i++) {
            if (s->subjects[i].category == 1) {
                printf("      * %s (%.1f%%) — Just %.1f%% away from 'Strong'\n",
                       s->subjects[i].name, s->subjects[i].percentage,
                       80.0f - s->subjects[i].percentage);
                printf("        - Focus on high-weightage chapters\n");
                printf("        - Solve 10 extra problems per week\n\n");
            }
        }
    }

    /* --- Study Hours Recommendation --- */
    printf("  [D] STUDY HOURS OPTIMIZATION\n");
    print_separator('-', 50);
    float recommended_hours;
    if (s->weak_count >= 3)      recommended_hours = 8.0f;
    else if (s->weak_count >= 1) recommended_hours = 6.0f;
    else if (s->avg_count >= 3)  recommended_hours = 5.0f;
    else                         recommended_hours = 4.0f;

    if (s->attendance < 75) recommended_hours += 1.0f;

    printf("      Current   : %.1f hrs/day\n", s->study_hours);
    printf("      Recommended: %.1f hrs/day\n", recommended_hours);
    if (s->study_hours < recommended_hours)
        printf("      ** Increase study time by %.1f hrs **\n",
               recommended_hours - s->study_hours);
    else
        printf("      Your study hours are adequate. Focus on quality!\n");

    printf("\n      Study Tips:\n");
    printf("        - Use Pomodoro Technique (25 min study + 5 min break)\n");
    printf("        - Study difficult subjects during morning hours (8-11 AM)\n");
    printf("        - Review notes within 24 hours of class\n");
    printf("        - Active recall > passive reading\n");

    /* --- Attendance Advisory --- */
    printf("\n  [E] ATTENDANCE ADVISORY\n");
    print_separator('-', 50);
    if (s->attendance >= 90)
        printf("      Excellent attendance (%.1f%%)! Keep it up.\n", s->attendance);
    else if (s->attendance >= 75)
        printf("      Satisfactory attendance (%.1f%%). Try to reach 85%%+.\n",
               s->attendance);
    else {
        printf("      CRITICAL: Attendance is %.1f%% (below 75%% minimum)!\n",
               s->attendance);
        printf("      - Attend all remaining classes without exception\n");
        printf("      - Meet your faculty advisor immediately\n");
        printf("      - Risk: Exam debarment / year-back\n");
    }
    printf("\n");
}

void display_study_plan(Student *s) {
    print_separator('=', 70);
    print_centered("RECOMMENDED DAILY STUDY PLAN", 70);
    print_separator('=', 70);
    printf("\n");

    float total_hours = 6.0f;
    if (s->weak_count >= 2) total_hours = 8.0f;
    float weak_share = 0.60f, avg_share = 0.25f, strong_share = 0.15f;

    if (s->weak_count > 0) {
        float hrs = total_hours * weak_share / (s->weak_count > 0 ? s->weak_count : 1);
        printf("  WEAK SUBJECTS (60%% time = %.1f hrs total):\n", total_hours * weak_share);
        for (int i = 0; i < s->num_subjects; i++)
            if (s->subjects[i].category == 0)
                printf("    %-20s : %.1f hrs/day\n", s->subjects[i].name, hrs);
    }
    if (s->avg_count > 0) {
        float hrs = total_hours * avg_share / (s->avg_count > 0 ? s->avg_count : 1);
        printf("  AVERAGE SUBJECTS (25%% time = %.1f hrs total):\n", total_hours * avg_share);
        for (int i = 0; i < s->num_subjects; i++)
            if (s->subjects[i].category == 1)
                printf("    %-20s : %.1f hrs/day\n", s->subjects[i].name, hrs);
    }
    if (s->strong_count > 0) {
        float hrs = total_hours * strong_share / (s->strong_count > 0 ? s->strong_count : 1);
        printf("  STRONG SUBJECTS (15%% time = %.1f hrs total):\n", total_hours * strong_share);
        for (int i = 0; i < s->num_subjects; i++)
            if (s->subjects[i].category == 2)
                printf("    %-20s : %.1f hrs/day\n", s->subjects[i].name, hrs);
    }
    printf("\n");
}

void display_timetable(Student *s) {
    print_separator('=', 70);
    print_centered("WEEKLY STUDY TIMETABLE", 70);
    print_separator('=', 70);
    printf("\n");

    const char *days[] = {"Monday", "Tuesday", "Wednesday", "Thursday",
                          "Friday", "Saturday", "Sunday"};
    const char *slots[] = {"6:00-7:30 AM ", "4:00-5:30 PM ",
                           "5:30-7:00 PM ", "7:30-9:00 PM ", "9:00-10:00 PM"};

    /* Build a rotation of subjects, prioritizing weak ones */
    int order[MAX_SUBJECTS], oidx = 0;
    for (int i = 0; i < s->num_subjects; i++)
        if (s->subjects[i].category == 0) order[oidx++] = i;
    for (int i = 0; i < s->num_subjects; i++)
        if (s->subjects[i].category == 1) order[oidx++] = i;
    for (int i = 0; i < s->num_subjects; i++)
        if (s->subjects[i].category == 2) order[oidx++] = i;

    printf("  %-12s", "Time Slot");
    for (int d = 0; d < 7; d++)
        printf(" %-10s", days[d]);
    printf("\n");
    print_separator('-', 70);

    int subj_idx = 0;
    for (int sl = 0; sl < MAX_SLOTS; sl++) {
        printf("  %s", slots[sl]);
        for (int d = 0; d < 7; d++) {
            if (d == 6 && sl >= 3) {
                printf(" %-10s", "REST");
            } else {
                /* Truncate subject name to 10 chars */
                char short_name[11];
                strncpy(short_name, s->subjects[order[subj_idx % oidx]].name, 10);
                short_name[10] = '\0';
                printf(" %-10s", short_name);
                subj_idx++;
            }
        }
        printf("\n");
    }
    printf("\n  Note: Weak subjects appear more frequently in the timetable.\n\n");
}

void display_career_paths(Student *s) {
    print_separator('=', 70);
    print_centered("CAREER PATH SUGGESTIONS", 70);
    print_separator('=', 70);
    printf("\n  Based on your strong subjects:\n\n");

    int found = 0;
    for (int i = 0; i < s->num_subjects; i++) {
        if (s->subjects[i].category == 2) {
            found = 1;
            printf("  [*] %s (%.1f%%)\n", s->subjects[i].name,
                   s->subjects[i].percentage);

            char lower_name[MAX_NAME];
            strcpy(lower_name, s->subjects[i].name);
            for (int j = 0; lower_name[j]; j++)
                if (lower_name[j] >= 'A' && lower_name[j] <= 'Z')
                    lower_name[j] += 32;

            if (strstr(lower_name, "math"))
                printf("      -> Data Scientist, Actuary, Quant Analyst, Statistician\n");
            else if (strstr(lower_name, "computer") || strstr(lower_name, "programming")
                     || strstr(lower_name, "data struct"))
                printf("      -> Software Engineer, ML Engineer, Systems Architect\n");
            else if (strstr(lower_name, "physics"))
                printf("      -> Research Scientist, Aerospace Engineer, Physicist\n");
            else if (strstr(lower_name, "chemistry"))
                printf("      -> Pharmaceutical Scientist, Chemical Engineer, Biochemist\n");
            else if (strstr(lower_name, "english") || strstr(lower_name, "communication"))
                printf("      -> Content Strategist, Technical Writer, Journalist\n");
            else if (strstr(lower_name, "biology"))
                printf("      -> Biotech Researcher, Medical Professional, Geneticist\n");
            else if (strstr(lower_name, "economics") || strstr(lower_name, "commerce"))
                printf("      -> Economist, Financial Analyst, Management Consultant\n");
            else if (strstr(lower_name, "electronics") || strstr(lower_name, "electrical"))
                printf("      -> VLSI Designer, Embedded Systems Engineer, IoT Developer\n");
            else
                printf("      -> Researcher, Subject Matter Expert, Educator\n");
            printf("\n");
        }
    }
    if (!found) {
        printf("  No subjects in the 'Strong' category yet.\n");
        printf("  Focus on improving your best subjects to 80%%+ to unlock career insights.\n\n");
    }
}

void display_motivation(Student *s) {
    print_separator('=', 70);
    printf("\n");
    if (s->overall_percentage >= 90)
        print_centered("\"Excellence is not a destination but a continuous journey.\"", 70);
    else if (s->overall_percentage >= 80)
        print_centered("\"You're doing great! Push a little more for the top.\"", 70);
    else if (s->overall_percentage >= 70)
        print_centered("\"Good work! Consistency will take you to the next level.\"", 70);
    else if (s->overall_percentage >= 60)
        print_centered("\"Every expert was once a beginner. Keep going!\"", 70);
    else if (s->overall_percentage >= 50)
        print_centered("\"Difficult roads lead to beautiful destinations. Don't give up!\"", 70);
    else
        print_centered("\"Fall seven times, stand up eight. Your comeback starts NOW!\"", 70);

    printf("\n");
    print_separator('=', 70);
    print_centered("END OF REPORT", 70);
    print_separator('=', 70);
    printf("\n");
}

/* ===================== UTILITY FUNCTIONS ===================== */

void print_separator(char ch, int len) {
    printf("  ");
    for (int i = 0; i < len; i++) putchar(ch);
    printf("\n");
}

void print_centered(const char *text, int width) {
    int len = (int)strlen(text);
    int pad = (width - len) / 2;
    if (pad < 0) pad = 0;
    printf("  ");
    for (int i = 0; i < pad; i++) putchar(' ');
    printf("%s\n", text);
}

void print_bar(float percentage, int width) {
    int filled = (int)(percentage / 100.0f * width);
    if (filled > width) filled = width;
    if (filled < 0) filled = 0;

    printf("[");
    for (int i = 0; i < width; i++) {
        if (i < filled) {
            if (percentage >= 80)      putchar('#');
            else if (percentage >= 60) putchar('=');
            else if (percentage >= 40) putchar('-');
            else                       putchar('!');
        } else {
            putchar(' ');
        }
    }
    printf("] %.1f%%", percentage);
}
