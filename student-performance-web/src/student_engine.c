/*
 * Smart Student Performance & Study Recommendation System
 * Browser engine: C compiled to WebAssembly.
 * The calculations and recommendation rules are implemented in C.
 * UI and presentation are handled by the browser front end.
 */

#define MAX_SUBJECTS 15
#define MAX_NAME 100
#define MAX_ROLL 30
#define MAX_CAREER_TEXT 180
#define MAX_MOTIVATION 120

#if defined(__wasm32__)
#define EXPORT __attribute__((visibility("default")))
#else
#define EXPORT
#endif

typedef struct {
    char name[MAX_NAME];
    float marks_obtained;
    float max_marks;
    float percentage;
    int category; /* 0 = weak (<60), 1 = average (60-79), 2 = strong (>=80) */
} Subject;

static char student_name[MAX_NAME];
static char roll_number[MAX_ROLL];
static int semester_number;
static int subject_count;
static Subject subjects[MAX_SUBJECTS];
static float attendance_percentage;
static float current_study_hours;
static float overall_percentage;
static char overall_grade[3];
static float sgpa_value;
static float cgpa_estimate;
static int weak_count;
static int average_count;
static int strong_count;
static int fail_count;
static float recommended_hours;
static float total_plan_hours;
static int timetable_order[MAX_SUBJECTS];
static int timetable[5][7];
static char career_text[MAX_SUBJECTS][MAX_CAREER_TEXT];
static char motivation_text[MAX_MOTIVATION];
static int analyzed;

static void copy_text(char *destination, int capacity, const char *source) {
    int i = 0;
    if (capacity <= 0) return;
    if (!source) source = "";
    while (i < capacity - 1 && source[i] != '\0') {
        destination[i] = source[i];
        i++;
    }
    destination[i] = '\0';
}

static int lower_ascii(int c) {
    if (c >= 'A' && c <= 'Z') return c + ('a' - 'A');
    return c;
}

static int contains_text(const char *text, const char *needle) {
    int i, j;
    if (!text || !needle || !needle[0]) return 0;
    for (i = 0; text[i] != '\0'; i++) {
        for (j = 0; needle[j] != '\0'; j++) {
            if (text[i + j] == '\0' || lower_ascii((unsigned char)text[i + j]) != lower_ascii((unsigned char)needle[j])) break;
        }
        if (needle[j] == '\0') return 1;
    }
    return 0;
}

static void assign_grade(void) {
    float p = overall_percentage;
    if (p >= 90.0f) copy_text(overall_grade, 3, "A+");
    else if (p >= 80.0f) copy_text(overall_grade, 3, "A");
    else if (p >= 70.0f) copy_text(overall_grade, 3, "B");
    else if (p >= 60.0f) copy_text(overall_grade, 3, "C");
    else if (p >= 50.0f) copy_text(overall_grade, 3, "D");
    else copy_text(overall_grade, 3, "F");
}

static float calculate_sgpa(float percentage) {
    if (percentage >= 90.0f) return 9.0f + (percentage - 90.0f) / 10.0f;
    if (percentage >= 80.0f) return 8.0f + (percentage - 80.0f) / 10.0f;
    if (percentage >= 70.0f) return 7.0f + (percentage - 70.0f) / 10.0f;
    if (percentage >= 60.0f) return 6.0f + (percentage - 60.0f) / 10.0f;
    if (percentage >= 50.0f) return 5.0f + (percentage - 50.0f) / 10.0f;
    if (percentage >= 40.0f) return 4.0f + (percentage - 40.0f) / 10.0f;
    return percentage / 10.0f;
}

static void categorize_subjects(void) {
    int i;
    weak_count = average_count = strong_count = fail_count = 0;
    for (i = 0; i < subject_count; i++) {
        float p = subjects[i].percentage;
        if (p < 40.0f) {
            subjects[i].category = 0;
            weak_count++;
            fail_count++;
        } else if (p < 60.0f) {
            subjects[i].category = 0;
            weak_count++;
        } else if (p < 80.0f) {
            subjects[i].category = 1;
            average_count++;
        } else {
            subjects[i].category = 2;
            strong_count++;
        }
    }
}

static void assign_career_paths(void) {
    int i;
    for (i = 0; i < subject_count; i++) {
        const char *name = subjects[i].name;
        if (contains_text(name, "math"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Data Scientist, Actuary, Quant Analyst, Statistician");
        else if (contains_text(name, "computer") || contains_text(name, "programming") || contains_text(name, "data struct"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Software Engineer, ML Engineer, Systems Architect");
        else if (contains_text(name, "physics"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Research Scientist, Aerospace Engineer, Physicist");
        else if (contains_text(name, "chemistry"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Pharmaceutical Scientist, Chemical Engineer, Biochemist");
        else if (contains_text(name, "english") || contains_text(name, "communication"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Content Strategist, Technical Writer, Journalist");
        else if (contains_text(name, "biology"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Biotech Researcher, Medical Professional, Geneticist");
        else if (contains_text(name, "economics") || contains_text(name, "commerce"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "Economist, Financial Analyst, Management Consultant");
        else if (contains_text(name, "electronics") || contains_text(name, "electrical"))
            copy_text(career_text[i], MAX_CAREER_TEXT, "VLSI Designer, Embedded Systems Engineer, IoT Developer");
        else
            copy_text(career_text[i], MAX_CAREER_TEXT, "Researcher, Subject Matter Expert, Educator");
    }
}

static void assign_motivation(void) {
    if (overall_percentage >= 90.0f)
        copy_text(motivation_text, MAX_MOTIVATION, "Excellence is not a destination but a continuous journey.");
    else if (overall_percentage >= 80.0f)
        copy_text(motivation_text, MAX_MOTIVATION, "You're doing great! Push a little more for the top.");
    else if (overall_percentage >= 70.0f)
        copy_text(motivation_text, MAX_MOTIVATION, "Good work! Consistency will take you to the next level.");
    else if (overall_percentage >= 60.0f)
        copy_text(motivation_text, MAX_MOTIVATION, "Every expert was once a beginner. Keep going!");
    else if (overall_percentage >= 50.0f)
        copy_text(motivation_text, MAX_MOTIVATION, "Difficult roads lead to beautiful destinations. Don't give up!");
    else
        copy_text(motivation_text, MAX_MOTIVATION, "Fall seven times, stand up eight. Your comeback starts NOW!");
}

static void build_timetable(void) {
    int i, count = 0, slot, day, subject_index = 0;
    for (i = 0; i < subject_count; i++) if (subjects[i].category == 0) timetable_order[count++] = i;
    for (i = 0; i < subject_count; i++) if (subjects[i].category == 1) timetable_order[count++] = i;
    for (i = 0; i < subject_count; i++) if (subjects[i].category == 2) timetable_order[count++] = i;
    for (slot = 0; slot < 5; slot++) {
        for (day = 0; day < 7; day++) {
            if (day == 6 && slot >= 3) timetable[slot][day] = -1;
            else {
                timetable[slot][day] = timetable_order[subject_index % subject_count];
                subject_index++;
            }
        }
    }
}

EXPORT void sp_reset(void) {
    int i;
    student_name[0] = '\0';
    roll_number[0] = '\0';
    semester_number = 1;
    subject_count = 0;
    attendance_percentage = 0.0f;
    current_study_hours = 0.0f;
    overall_percentage = 0.0f;
    overall_grade[0] = '\0';
    sgpa_value = cgpa_estimate = 0.0f;
    weak_count = average_count = strong_count = fail_count = 0;
    recommended_hours = total_plan_hours = 0.0f;
    motivation_text[0] = '\0';
    analyzed = 0;
    for (i = 0; i < MAX_SUBJECTS; i++) {
        subjects[i].name[0] = '\0';
        subjects[i].marks_obtained = 0.0f;
        subjects[i].max_marks = 0.0f;
        subjects[i].percentage = 0.0f;
        subjects[i].category = 0;
        career_text[i][0] = '\0';
    }
}

/* Pointers are offsets into WebAssembly linear memory. */
EXPORT int sp_set_student(int name_pointer, int roll_pointer, int semester, float attendance, float study_hours) {
    const char *name = (const char *)(unsigned long)name_pointer;
    const char *roll = (const char *)(unsigned long)roll_pointer;
    if (!name || !roll || semester < 1 || semester > 8 || attendance < 0.0f || attendance > 100.0f || study_hours < 0.0f || study_hours > 24.0f) return 0;
    sp_reset();
    copy_text(student_name, MAX_NAME, name);
    copy_text(roll_number, MAX_ROLL, roll);
    semester_number = semester;
    attendance_percentage = attendance;
    current_study_hours = study_hours;
    return 1;
}

EXPORT int sp_add_subject(int name_pointer, float marks, float maximum) {
    const char *name = (const char *)(unsigned long)name_pointer;
    if (!name || subject_count >= MAX_SUBJECTS || maximum <= 0.0f || marks < 0.0f || marks > maximum) return -1;
    copy_text(subjects[subject_count].name, MAX_NAME, name);
    subjects[subject_count].marks_obtained = marks;
    subjects[subject_count].max_marks = maximum;
    subject_count++;
    analyzed = 0;
    return subject_count;
}

EXPORT int sp_analyze(void) {
    int i;
    float total_obtained = 0.0f, total_maximum = 0.0f;
    if (subject_count < 1) return -1;
    for (i = 0; i < subject_count; i++) {
        if (subjects[i].max_marks <= 0.0f) return -2;
        subjects[i].percentage = (subjects[i].marks_obtained / subjects[i].max_marks) * 100.0f;
        total_obtained += subjects[i].marks_obtained;
        total_maximum += subjects[i].max_marks;
    }
    if (total_maximum <= 0.0f) return -2;
    overall_percentage = (total_obtained / total_maximum) * 100.0f;
    assign_grade();
    sgpa_value = calculate_sgpa(overall_percentage);
    cgpa_estimate = sgpa_value * 0.97f;
    categorize_subjects();

    if (weak_count >= 3) recommended_hours = 8.0f;
    else if (weak_count >= 1) recommended_hours = 6.0f;
    else if (average_count >= 3) recommended_hours = 5.0f;
    else recommended_hours = 4.0f;
    if (attendance_percentage < 75.0f) recommended_hours += 1.0f;

    total_plan_hours = (weak_count >= 2) ? 8.0f : 6.0f;
    assign_career_paths();
    assign_motivation();
    build_timetable();
    analyzed = 1;
    return 1;
}

EXPORT int sp_is_analyzed(void) { return analyzed; }
EXPORT int sp_student_name_ptr(void) { return (int)(unsigned long)student_name; }
EXPORT int sp_roll_ptr(void) { return (int)(unsigned long)roll_number; }
EXPORT int sp_grade_ptr(void) { return (int)(unsigned long)overall_grade; }
EXPORT int sp_motivation_ptr(void) { return (int)(unsigned long)motivation_text; }
EXPORT int sp_subject_name_ptr(int index) { return (index >= 0 && index < subject_count) ? (int)(unsigned long)subjects[index].name : 0; }
EXPORT int sp_career_ptr(int index) { return (index >= 0 && index < subject_count) ? (int)(unsigned long)career_text[index] : 0; }
EXPORT int sp_semester(void) { return semester_number; }
EXPORT int sp_subject_count(void) { return subject_count; }
EXPORT int sp_weak_count(void) { return weak_count; }
EXPORT int sp_average_count(void) { return average_count; }
EXPORT int sp_strong_count(void) { return strong_count; }
EXPORT int sp_fail_count(void) { return fail_count; }
EXPORT int sp_attendance_risk(void) { return attendance_percentage < 75.0f; }
EXPORT int sp_critical_fail_risk(void) { return fail_count >= 3; }
EXPORT float sp_attendance(void) { return attendance_percentage; }
EXPORT float sp_current_study_hours(void) { return current_study_hours; }
EXPORT float sp_overall_percentage(void) { return overall_percentage; }
EXPORT float sp_sgpa(void) { return sgpa_value; }
EXPORT float sp_cgpa_estimate(void) { return cgpa_estimate; }
EXPORT float sp_recommended_hours(void) { return recommended_hours; }
EXPORT float sp_total_plan_hours(void) { return total_plan_hours; }
EXPORT float sp_subject_marks(int index) { return (index >= 0 && index < subject_count) ? subjects[index].marks_obtained : 0.0f; }
EXPORT float sp_subject_max(int index) { return (index >= 0 && index < subject_count) ? subjects[index].max_marks : 0.0f; }
EXPORT float sp_subject_percentage(int index) { return (index >= 0 && index < subject_count) ? subjects[index].percentage : 0.0f; }
EXPORT int sp_subject_category(int index) { return (index >= 0 && index < subject_count) ? subjects[index].category : -1; }
EXPORT float sp_subject_plan_hours(int index) {
    int category, count;
    float share;
    if (!analyzed || index < 0 || index >= subject_count) return 0.0f;
    category = subjects[index].category;
    if (category == 0) { count = weak_count; share = 0.60f; }
    else if (category == 1) { count = average_count; share = 0.25f; }
    else { count = strong_count; share = 0.15f; }
    if (count <= 0) return 0.0f;
    return (total_plan_hours * share) / (float)count;
}
EXPORT float sp_subject_target_gap(int index) {
    if (index < 0 || index >= subject_count) return 0.0f;
    if (subjects[index].category == 0) return 70.0f - subjects[index].percentage;
    if (subjects[index].category == 1) return 80.0f - subjects[index].percentage;
    return 0.0f;
}
EXPORT float sp_marks_needed_to_pass(int index) {
    if (index < 0 || index >= subject_count) return 0.0f;
    if (subjects[index].percentage >= 40.0f) return 0.0f;
    return (40.0f * subjects[index].max_marks / 100.0f) - subjects[index].marks_obtained;
}
EXPORT float sp_category_plan_hours(int category) {
    float share;
    int count;
    if (category == 0) { share = 0.60f; count = weak_count; }
    else if (category == 1) { share = 0.25f; count = average_count; }
    else if (category == 2) { share = 0.15f; count = strong_count; }
    else return 0.0f;
    return count > 0 ? total_plan_hours * share : 0.0f;
}
EXPORT int sp_timetable_subject(int slot, int day) {
    if (!analyzed || slot < 0 || slot >= 5 || day < 0 || day >= 7) return -1;
    return timetable[slot][day];
}
