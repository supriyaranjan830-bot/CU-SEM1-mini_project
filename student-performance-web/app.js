const $ = (selector) => document.querySelector(selector);
const subjectList = $('#subject-list');
const form = $('#student-form');
const engineStatusText = $('#engine-status-text');
const statusDot = document.querySelector('.status-dot');
const formError = $('#form-error');
const analyzeButton = $('#analyze-button');

const encoder = new TextEncoder();
let engine = null;
let wasmMemory = null;
let scratchBase = 0;
const MAX_SUBJECTS = 15;

function addSubjectRow(name = '', marks = '', maximum = '100') {
  if (subjectList.children.length >= MAX_SUBJECTS) return;
  const row = document.createElement('div');
  row.className = 'subject-row';
  row.innerHTML = `
    <input class="subject-name-input" type="text" maxlength="90" placeholder="e.g. Mathematics" aria-label="Subject name" required>
    <input class="subject-marks-input" type="number" min="0" step="0.1" placeholder="Marks" aria-label="Marks obtained" required>
    <input class="subject-max-input" type="number" min="0.1" step="0.1" placeholder="Out of" aria-label="Maximum marks" required>
    <button class="remove-subject" type="button" aria-label="Remove subject" title="Remove subject">×</button>`;
  row.querySelector('.subject-name-input').value = name;
  row.querySelector('.subject-marks-input').value = marks;
  row.querySelector('.subject-max-input').value = maximum;
  row.querySelector('.remove-subject').addEventListener('click', () => {
    if (subjectList.children.length > 1) {
      row.remove();
      updateSubjectCounter();
    }
  });
  subjectList.appendChild(row);
  updateSubjectCounter();
}

function updateSubjectCounter() {
  const count = subjectList.children.length;
  $('#subject-counter').textContent = `${count} / ${MAX_SUBJECTS} subjects`;
  $('#add-subject').disabled = count >= MAX_SUBJECTS;
  $('#add-subject').style.opacity = count >= MAX_SUBJECTS ? '.45' : '1';
}

function setSampleData() {
  $('#student-name').value = 'Supriya Sharma';
  $('#roll-number').value = '22CS1045';
  $('#semester').value = '5';
  $('#attendance').value = '78';
  $('#study-hours').value = '4.5';
  subjectList.innerHTML = '';
  [
    ['Mathematics', '72', '100'],
    ['Physics', '85', '100'],
    ['Chemistry', '55', '100'],
    ['Computer Science', '92', '100'],
    ['English', '68', '100'],
    ['Data Structures', '88', '100']
  ].forEach((subject) => addSubjectRow(...subject));
  formError.textContent = '';
}

function writeCString(value, slot = 0) {
  const bytes = encoder.encode(String(value));
  const capacity = 256;
  if (bytes.length >= capacity) throw new Error('A name is too long. Please shorten it and try again.');
  const pointer = scratchBase + slot * capacity;
  const memoryBytes = new Uint8Array(wasmMemory.buffer, pointer, capacity);
  memoryBytes.fill(0);
  memoryBytes.set(bytes, 0);
  return pointer;
}

function readCString(pointer) {
  if (!pointer) return '';
  const bytes = new Uint8Array(wasmMemory.buffer);
  let end = pointer;
  while (end < bytes.length && bytes[end] !== 0) end++;
  return new TextDecoder().decode(bytes.subarray(pointer, end));
}

async function loadEngine() {
  try {
    const response = await fetch('/student_engine.wasm');
    if (!response.ok) throw new Error(`Could not load the C engine (${response.status}).`);
    let result;
    try {
      result = await WebAssembly.instantiateStreaming(response.clone(), {});
    } catch {
      result = await WebAssembly.instantiate(await response.arrayBuffer(), {});
    }
    engine = result.instance.exports;
    wasmMemory = engine.memory;
    scratchBase = wasmMemory.buffer.byteLength - 8192;
    engineStatusText.textContent = 'C engine ready · WebAssembly';
    statusDot.classList.add('ready');
  } catch (error) {
    engineStatusText.textContent = 'Engine unavailable';
    statusDot.style.background = '#df7868';
    formError.textContent = `${error.message} Run ./build.sh to rebuild the engine, then refresh.`;
    analyzeButton.disabled = true;
  }
}

function validateAndReadForm() {
  const name = $('#student-name').value.trim();
  const roll = $('#roll-number').value.trim();
  const semester = Number($('#semester').value);
  const attendanceInput = $('#attendance').value.trim();
  const studyHoursInput = $('#study-hours').value.trim();
  const attendance = Number(attendanceInput);
  const studyHours = Number(studyHoursInput);
  const rows = [...subjectList.querySelectorAll('.subject-row')];

  if (!name || !roll) throw new Error('Enter the student name and roll number.');
  if (!Number.isInteger(semester) || semester < 1 || semester > 8) throw new Error('Select a semester between 1 and 8.');
  if (attendanceInput === '' || !Number.isFinite(attendance) || attendance < 0 || attendance > 100) throw new Error('Attendance must be between 0 and 100%.');
  if (studyHoursInput === '' || !Number.isFinite(studyHours) || studyHours < 0 || studyHours > 24) throw new Error('Study hours must be between 0 and 24.')
  if (rows.length < 1 || rows.length > MAX_SUBJECTS) throw new Error(`Add between 1 and ${MAX_SUBJECTS} subjects.`);

  const subjects = rows.map((row, index) => {
    const subjectName = row.querySelector('.subject-name-input').value.trim();
    const marksInput = row.querySelector('.subject-marks-input').value.trim();
    const maximumInput = row.querySelector('.subject-max-input').value.trim();
    const marks = Number(marksInput);
    const maximum = Number(maximumInput);
    if (!subjectName) throw new Error(`Enter a name for subject ${index + 1}.`);
    if (marksInput === '' || maximumInput === '' || !Number.isFinite(marks) || !Number.isFinite(maximum) || maximum <= 0 || marks < 0 || marks > maximum) {
      throw new Error(`Check the marks for ${subjectName}: marks must be from 0 up to a positive maximum.`);
    }
    return { name: subjectName, marks, maximum };
  });
  return { name, roll, semester, attendance, studyHours, subjects };
}

function calculateWithC(data) {
  engine.sp_reset();
  const namePointer = writeCString(data.name, 0);
  const rollPointer = writeCString(data.roll, 1);
  const accepted = engine.sp_set_student(namePointer, rollPointer, data.semester, data.attendance, data.studyHours);
  if (!accepted) throw new Error('The C engine rejected the student details. Check the values and try again.');
  for (const subject of data.subjects) {
    const subjectPointer = writeCString(subject.name, 2);
    const result = engine.sp_add_subject(subjectPointer, subject.marks, subject.maximum);
    if (result < 0) throw new Error(`The C engine could not add ${subject.name}. Check its marks.`);
  }
  const result = engine.sp_analyze();
  if (result !== 1 || !engine.sp_is_analyzed()) throw new Error('The C engine could not calculate this report. Please check the subject marks.');
}

const categoryInfo = (category) => {
  if (category === 2) return { label: 'STRONG', className: 'strong', color: '#3ca88f' };
  if (category === 1) return { label: 'AVERAGE', className: 'average', color: '#e2b45d' };
  return { label: 'WEAK', className: 'weak', color: '#e88772' };
};

function renderSubjectResults() {
  const count = engine.sp_subject_count();
  const items = [];
  for (let i = 0; i < count; i++) {
    const name = readCString(engine.sp_subject_name_ptr(i));
    const marks = engine.sp_subject_marks(i);
    const maximum = engine.sp_subject_max(i);
    const percentage = engine.sp_subject_percentage(i);
    const category = categoryInfo(engine.sp_subject_category(i));
    items.push({ name, marks, maximum, percentage, category });
  }
  $('#subject-total').textContent = `${count} subject${count === 1 ? '' : 's'}`;
  $('#strong-count').textContent = engine.sp_strong_count();
  $('#average-count').textContent = engine.sp_average_count();
  $('#weak-count').textContent = engine.sp_weak_count();
  $('#subject-results').innerHTML = items.map((item) => `
    <div class="subject-result">
      <div class="subject-line"><strong>${escapeHtml(item.name)}</strong><span>${item.percentage.toFixed(1)}%</span></div>
      <div class="subject-progress"><span style="width:${Math.max(0, Math.min(100, item.percentage))}%;background:${item.category.color}"></span></div>
      <div class="subject-meta"><span>${formatNumber(item.marks)} / ${formatNumber(item.maximum)} marks</span><span class="subject-status status-${item.category.className}">${item.category.label}${item.percentage < 40 ? ' · FAILING' : ''}</span></div>
    </div>`).join('');
  return items;
}

function renderHeader(data) {
  const overall = engine.sp_overall_percentage();
  const grade = readCString(engine.sp_grade_ptr());
  const sgpa = engine.sp_sgpa();
  const recommended = engine.sp_recommended_hours();
  $('#student-avatar').textContent = [...data.name.trim()][0].toUpperCase();
  $('#report-name').textContent = data.name;
  $('#report-meta').textContent = `${data.roll} · Semester ${data.semester}`;
  $('#report-attendance').textContent = `${engine.sp_attendance().toFixed(1)}%`;
  $('#report-study').innerHTML = `${engine.sp_current_study_hours().toFixed(1)} <small>hrs</small>`;
  $('#report-subtitle').textContent = `Analysis for ${data.name} · ${data.subjects.length} subjects reviewed`;
  $('#metric-percentage').textContent = overall.toFixed(2);
  $('#metric-grade').textContent = grade;
  $('#metric-grade-label').textContent = `Grade ${grade}`;
  $('#metric-sgpa').textContent = sgpa.toFixed(2);
  document.querySelector('#metric-sgpa').closest('.metric-card').querySelector('.metric-caption').textContent = `Estimated CGPA: ${engine.sp_cgpa_estimate().toFixed(2)} / 10`; 
  $('#metric-hours').textContent = recommended.toFixed(1);
  $('#metric-hours-note').textContent = recommended > engine.sp_current_study_hours()
    ? `Increase by ${(recommended - engine.sp_current_study_hours()).toFixed(1)} hrs/day`
    : 'Your current time meets this target';
  $('#overall-progress').style.width = `${Math.min(100, Math.max(0, overall))}%`;
}

function renderRisks() {
  const riskBox = $('#risk-alerts');
  const alerts = [];
  const failCount = engine.sp_fail_count();
  if (failCount > 0) {
    const failed = [];
    for (let i = 0; i < engine.sp_subject_count(); i++) {
      if (engine.sp_subject_percentage(i) < 40) {
        failed.push({ name: readCString(engine.sp_subject_name_ptr(i)), needed: engine.sp_marks_needed_to_pass(i) });
      }
    }
    alerts.push(`<div class="risk-alert"><span class="risk-symbol">!</span><div><strong>${failCount} subject${failCount === 1 ? '' : 's'} below the 40% pass threshold</strong><p>${failed.map((item) => `${escapeHtml(item.name)}: ${formatNumber(item.needed)} more marks to reach 40%`).join(' · ')}${engine.sp_critical_fail_risk() ? ' · Multiple failing subjects need urgent attention.' : ''}</p></div></div>`);
  }
  if (engine.sp_attendance_risk()) {
    alerts.push(`<div class="risk-alert warning"><span class="risk-symbol">◷</span><div><strong>Attendance is below the 75% threshold used by this program</strong><p>Current attendance: ${engine.sp_attendance().toFixed(1)}%. The original program flags this as a potential examination eligibility risk; check your institution's actual rules.</p></div></div>`);
  }
  riskBox.innerHTML = alerts.join('');
  riskBox.hidden = alerts.length === 0;
}

function renderRecommendations(subjects) {
  const weak = subjects.filter((item) => item.category.className === 'weak');
  const average = subjects.filter((item) => item.category.className === 'average');
  const strong = subjects.filter((item) => item.category.className === 'strong');
  const recommendations = [];
  if (weak.length) {
    const failedCount = subjects.filter((item) => item.percentage < 40).length;
    recommendations.push({ icon: '!', tone: 'warning', title: 'Prioritize your weak subjects', text: `${weak.map((item) => item.name).join(', ')} need attention. The C engine allocates 60% of your study plan to this group. Aim for 70%, practice previous-year questions, and revise every 2–3 days.${failedCount ? ' Arrange extra support for subjects below 40%.' : ''}` });
  }
  if (average.length) {
    recommendations.push({ icon: '↗', tone: 'amber', title: 'Turn average results into strong ones', text: `${average.map((item) => item.name).join(', ')} are within reach of 80%. Focus on high-weightage chapters and solve extra practice problems each week.` });
  }
  if (strong.length) {
    recommendations.push({ icon: '✓', tone: '', title: 'Build on your strengths', text: `${strong.map((item) => item.name).join(', ')} are your strongest areas. Explore advanced topics, practical projects, and opportunities to teach or mentor others.` });
  }
  if (engine.sp_attendance_risk()) {
    recommendations.push({ icon: '◷', tone: 'warning', title: 'Improve attendance', text: 'The program uses 75% as its advisory threshold. Attend upcoming classes and speak with your faculty advisor about your institution’s attendance policy.' });
  } else {
    recommendations.push({ icon: '✦', tone: '', title: 'Keep a sustainable routine', text: `The suggested target is ${engine.sp_recommended_hours().toFixed(1)} hours a day. Use focused 25-minute sessions, take breaks, and review class notes within 24 hours.` });
  }
  $('#recommendation-list').innerHTML = recommendations.map((item) => `<div class="recommendation"><span class="rec-bullet ${item.tone}">${item.icon}</span><div><strong>${item.title}</strong><p>${item.text}</p></div></div>`).join('');
}

function renderStudyPlan(subjects) {
  const groups = [
    { category: 0, title: 'Weak', color: '#e88772' },
    { category: 1, title: 'Average', color: '#e2b45d' },
    { category: 2, title: 'Strong', color: '#3ca88f' }
  ];
  const total = engine.sp_total_plan_hours();
  $('#plan-total').textContent = `${total.toFixed(1)} hrs total`;
  $('#study-plan').innerHTML = groups.map((group) => {
    const hours = engine.sp_category_plan_hours(group.category);
    const count = subjects.filter((item) => item.category.className === ['weak', 'average', 'strong'][group.category]).length;
    if (!count) return '';
    return `<div><div class="plan-row"><span class="plan-label">${group.title}</span><div class="plan-track"><span style="width:${(hours / total) * 100}%;background:${group.color}"></span></div><span class="plan-hours">${hours.toFixed(1)}h</span></div><div class="plan-foot">${(hours / count).toFixed(1)} hrs per subject · ${count} subject${count === 1 ? '' : 's'}</div></div>`;
  }).join('');
}

function renderCareers(subjects) {
  const cards = [];
  for (let i = 0; i < subjects.length; i++) {
    if (engine.sp_subject_category(i) !== 2) continue;
    const career = readCString(engine.sp_career_ptr(i));
    cards.push(`<div class="career-item"><strong>${escapeHtml(subjects[i].name)} · ${subjects[i].percentage.toFixed(1)}%</strong><span>${escapeHtml(career)}</span></div>`);
  }
  $('#career-list').innerHTML = cards.length ? cards.join('') : '<div class="career-item"><strong>Your next opportunity</strong><span>No subject is in the strong (80%+) category yet. Strengthen your best-performing subject to unlock subject-linked career suggestions.</span></div>';
}

function renderTimetable() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const slots = ['6:00–7:30 AM', '4:00–5:30 PM', '5:30–7:00 PM', '7:30–9:00 PM', '9:00–10:00 PM'];
  $('#timetable-head').innerHTML = `<tr><th>TIME SLOT</th>${days.map((day) => `<th>${day}</th>`).join('')}</tr>`;
  const rows = slots.map((slot, slotIndex) => {
    const cells = days.map((day, dayIndex) => {
      const subjectIndex = engine.sp_timetable_subject(slotIndex, dayIndex);
      if (subjectIndex < 0) return '<td class="is-rest">REST</td>';
      const category = engine.sp_subject_category(subjectIndex);
      const className = category === 0 ? 'is-weak' : category === 1 ? 'is-average' : 'is-strong';
      const name = readCString(engine.sp_subject_name_ptr(subjectIndex));
      return `<td class="${className}" title="${escapeHtml(name)}">${escapeHtml(shorten(name, 12))}</td>`;
    }).join('');
    return `<tr><td>${slot}</td>${cells}</tr>`;
  });
  $('#timetable-body').innerHTML = rows.join('');
}

function renderReport(data) {
  renderHeader(data);
  renderRisks();
  const subjects = renderSubjectResults();
  renderRecommendations(subjects);
  renderStudyPlan(subjects);
  renderCareers(subjects);
  renderTimetable();
  $('#motivation-text').textContent = readCString(engine.sp_motivation_ptr());
  $('#results').hidden = false;
  $('#results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatNumber(number) {
  return Number.isInteger(number) ? String(number) : Number(number).toFixed(1);
}
function shorten(text, maxLength) { return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text; }
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
}

$('#add-subject').addEventListener('click', () => addSubjectRow());
$('#load-demo').addEventListener('click', () => {
  setSampleData();
  $('#results').hidden = true;
  $('#student-name').focus();
});
form.addEventListener('submit', (event) => {
  event.preventDefault();
  formError.textContent = '';
  if (!engine) {
    formError.textContent = 'The C engine is not ready. Refresh the page or rebuild student_engine.wasm.';
    return;
  }
  try {
    const data = validateAndReadForm();
    analyzeButton.disabled = true;
    analyzeButton.querySelector('span:first-child').textContent = 'Analyzing…';
    calculateWithC(data);
    renderReport(data);
  } catch (error) {
    formError.textContent = error.message;
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.querySelector('span:first-child').textContent = 'Analyze my performance';
  }
});
$('#print-report').addEventListener('click', () => window.print());
$('#back-to-form').addEventListener('click', () => {
  $('#student-name').focus({ preventScroll: true });
  window.scrollTo({ top: $('#student-form').getBoundingClientRect().top + window.scrollY - 25, behavior: 'smooth' });
});

setSampleData();
loadEngine();
