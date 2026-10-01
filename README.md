# Digital Library Search Portal (CI/CD DevOps Mini-Project)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Framework: Flask](https://img.shields.io/badge/framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![Database: SQLite](https://img.shields.io/badge/database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Tailwind CSS](https://img.shields.io/badge/styling-Tailwind_CSS-38bdf8.svg)](https://tailwindcss.com/)
[![Release Baseline](https://img.shields.io/badge/release-v1.0--MVP-emerald.svg)](#)

A resilient, lightweight web portal designed for academic institutions to manage, catalog, and query digital library resources in real-time, backed by an end-to-end automated **CI/CD DevOps Pipeline** (Git, Jenkins, Docker, Selenium, and Ansible).

---

## 📁 Repository Directory Structure

```text
.
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md             # Defect reporting template
│       └── feature_request.md        # Agile user story & feature template
├── docs/
│   ├── 01_Problem_and_Scope.md       # Problem definition, stakeholders & 15-task scope
│   ├── 02_Agile_Plan_and_Workflow.md # User stories, Scrum plan & Mermaid DevOps diagram
│   └── 03_Architecture_and_Requirements.md # SRS, architecture diagrams & REST API contract
├── templates/
│   └── index.html                    # Tailwind CSS responsive dashboard and catalog view
├── app.py                            # Flask application core, SQLite schema & REST endpoints
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore patterns for Python/Flask/SQLite
└── README.md                         # Project documentation
```

---

## 🌿 Git Branching Strategy & Conventions

To maintain production stability and seamless continuous integration, all contributors adhere to the following branch policy:

| Branch Type | Naming Convention | Description | Merging Rule |
| :--- | :--- | :--- | :--- |
| **Main / Production** | `main` | Production-ready baseline; strictly deployable code. | Direct push prohibited; PR with review only. |
| **Development** | `develop` | Integration branch for staging builds. | Target for feature branch PRs. |
| **Feature Branches** | `feature/<short-desc>` | Dedicated branches for isolated user stories. | PR into `develop` or `main`. |
| **Bugfix Branches** | `bugfix/<issue-id-desc>` | Fixes for issues identified during QA / testing. | PR into `develop`. |
| **Hotfix Branches** | `hotfix/<critical-desc>`| Emergency fixes for production defects. | Merged to `main` and `develop`. |

### Commit Message Standard (Conventional Commits)
All commit messages must follow the format: `<type>(<scope>): <short description>`
- `feat`: A new feature or user story implementation
- `fix`: A bug fix or defect resolution
- `docs`: Documentation updates
- `test`: Adding or modifying automated test suites
- `refactor`: Code refactoring without behavioral alterations
- `chore`: Build processes, tooling, or repository maintenance

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ installed
- Git CLI installed

### 2. Installation
```powershell
# Clone the repository (or navigate to project directory)
cd MiniProject

# Create and activate virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\activate   # On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```powershell
python app.py
```
Visit **`http://localhost:5000`** in your browser. The SQLite database `library.db` will be automatically initialized and seeded with baseline digital library records.
