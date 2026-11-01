# StudentIQ — C-powered student performance website

This project converts the terminal-based **Smart Student Performance & Study Recommendation System** into a responsive website. The grading, SGPA, subject categorization, study-time recommendations, career mapping, and timetable rotation remain in **C**. The C engine is compiled to WebAssembly and runs locally in the visitor's browser.

## Project structure

```text
student-performance-web/
├── index.html                       # Website
├── styles.css                       # Responsive dashboard styling
├── app.js                           # Form, browser UI, and WebAssembly bridge
├── student_engine.wasm              # Compiled C engine (already included)
├── src/
│   └── student_engine.c             # C calculation engine source
├── student_performance_terminal_original.c  # Original terminal program
├── build.sh                         # Rebuild WebAssembly with Clang
└── vercel.json                      # Static hosting and WebAssembly MIME type
```

## Run it locally

A browser should load the files through a local web server (not by opening `index.html` directly), because WebAssembly is fetched over HTTP.

```bash
cd student-performance-web
python3 -m http.server 8000
```

Open **http://localhost:8000**.

You can also use any static development server. No npm packages or application server are required.

## Rebuild the C engine

The compiled `student_engine.wasm` is included, so rebuilding is optional unless you change `src/student_engine.c`.

The build script needs a Clang installation with the `wasm32` target enabled:

```bash
./build.sh
```

On macOS, install LLVM if your system `clang` does not support the WebAssembly target:

```bash
brew install llvm
CLANG="$(brew --prefix llvm)/bin/clang" ./build.sh
```

The build is intentionally freestanding: the C engine does not require a C runtime or external libraries. The browser JavaScript only gathers form values, calls the exported C functions, and displays the result.

## Deploy to Vercel

### Option A — quickest: Vercel Drop

1. Make sure `student_engine.wasm` exists in the project root (it is included in this folder).
2. Open **https://vercel.com/drop** and sign in.
3. Drag the entire `student-performance-web` folder (or a ZIP of it) into the page.
4. Choose a project name and deploy.
5. Open the generated `*.vercel.app` URL.

Vercel Drop supports static folders and deploys them without a build step. The included `vercel.json` sets the WebAssembly content type explicitly.

### Option B — GitHub + automatic deployments

1. Create a new GitHub repository.
2. Upload the contents of this folder to the repository's root (so `index.html` is at the root).
3. In Vercel, choose **Add New → Project**, import that GitHub repository, and deploy.
4. Use these project settings if Vercel asks:
   - Framework Preset: **Other**
   - Build Command: **Leave empty**
   - Output Directory: **`.`** (project root)
   - Install Command: **Leave empty**
5. Future pushes to the connected GitHub branch will trigger new deployments.

### Option C — Vercel CLI

From the project directory:

```bash
npx vercel
npx vercel --prod
```

Follow the prompts to link the project and deploy it.

## Important notes about the original calculations

- The grade thresholds and SGPA conversion follow the original C program.
- The estimated CGPA remains `SGPA × 0.97`, exactly as in the original program. This is a project-specific estimate, **not** an official university conversion formula.
- Subject categories remain: weak below 60%, average from 60% to below 80%, strong at 80% or above. Failing subjects are below 40%.
- The 75% attendance threshold is the threshold used by the original program. Actual attendance and examination eligibility rules depend on the institution.
- Input validation was added for semester, attendance, subject count, maximum marks, and marks range to prevent invalid values and division by zero.
- Student data is processed in the browser. This version has no database, login, or server-side storage.
