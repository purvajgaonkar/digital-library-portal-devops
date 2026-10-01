# Phase 1: Problem Definition, Stakeholders, Constraints, and MVP Scope
**Project Name:** CI/CD Pipeline for a Digital Library Search Portal  
**Domain:** DevOps Engineering & Academic Information Systems  
**Phase:** 1 — Planning, Scope, and Architecture  

---

## 1. Problem Definition

### 1.1 Background & Real-Time Academic Need
Modern academic institutions and research organizations manage vast inventories of physical, digitized, and born-digital resources (research papers, textbooks, periodicals, thesis publications, and multimedia archives). Traditional library management systems often suffer from:
1. **Monolithic, tightly coupled architectures** that make maintenance difficult and lead to frequent downtimes during updates.
2. **Slow, unindexed query latency**, frustrating students and faculty during peak academic hours (e.g., exams, assignment deadlines, research submissions).
3. **Manual, error-prone deployment practices** where code changes are uploaded directly to servers, lacking automated testing, vulnerability scanning, and regression safeguards.
4. **Lack of operational visibility**, making it difficult to trace availability, checkouts, and system health in real time.

### 1.2 The DevOps Solution
The **Digital Library Search Portal** addresses these pain points by pairing a lightweight, resilient web portal with an end-to-end automated **CI/CD Pipeline**. By leveraging modern DevOps paradigms (infrastructure-as-code, containerization, automated multi-stage testing, and configuration management), the library portal ensures:
- **Zero-friction delivery** of new search features and catalog updates.
- **Continuous reliability and automated quality gates** prior to any deployment.
- **Rapid search and tracking** of catalog items with status visibility (Available, Checked Out, Reserved).

---

## 2. Stakeholders & Roles

| Stakeholder Role | Representative Users | Key Interests & Responsibilities |
| :--- | :--- | :--- |
| **End Users / Patrons** | Students, Researchers, Faculty Members | Fast search by title/author/ISBN, real-time availability status, intuitive and accessible web interface. |
| **Portal Administrators** | Librarians, Catalog Managers | Catalog administration (CRUD operations), managing checkouts/returns, viewing library metrics via the summary dashboard. |
| **DevOps Engineers** | Lab DevOps Team, Release Engineers | Design and maintenance of CI/CD pipelines (Jenkins, Git, Docker, Ansible), environment automation, monitoring, and rollback strategies. |
| **Software Developers** | Python/Flask Developers, UI Engineers | Developing core portal features, writing unit/integration test suites, maintaining clean APIs and database migrations. |
| **Quality Assurance (QA)** | Test Automation Engineers | Writing and executing Selenium end-to-end UI tests, functional validation, regression prevention in the staging environment. |

---

## 3. Constraints & Measurable Success Criteria

### 3.1 Technical & Operational Constraints
- **Application Stack:** Python 3.10+ with Flask microframework and embedded SQLite database for rapid local provisioning.
- **Frontend Standard:** Semantic HTML5 styled with Tailwind CSS for high usability and responsiveness.
- **Containerization:** Docker container runtime for consistent environments between dev, test, and production.
- **CI Automation:** Jenkins pipeline driven by a declarative `Jenkinsfile` triggered on Git events.
- **Testing Guardrails:** Mandatory unit tests (pytest) and UI automation tests (headless Selenium) before staging promotions.
- **Configuration Management:** Ansible playbooks for automated provisioning and deployment.
- **Resource Constraints:** Designed to operate efficiently within lab resource limits (single VM / containerized node, minimal memory footprint).

### 3.2 Measurable Success Criteria (KPIs)

| Metric | Target Goal | Verification Method |
| :--- | :--- | :--- |
| **CI Pipeline Duration** | $< 4\text{ minutes}$ from commit to container image build | Jenkins build duration logs |
| **Automated Test Coverage** | $\ge 80\%$ line coverage for backend route handlers & models | Pytest-cov reports in CI |
| **UI Automated Test Pass Rate** | $100\%$ pass rate on core search and checkout flows | Selenium test runner stage |
| **Deployment Automation** | Zero manual terminal commands required for deployment | Ansible playbook execution via Jenkins CD |
| **Query Latency** | $< 250\text{ ms}$ for catalog keyword search over sample dataset | HTTP latency benchmarking |
| **Mean Time to Recover (MTTR)**| $< 2\text{ minutes}$ via automated container rollback | Staging rollback simulation |

---

## 4. Frozen 15-Task MVP Scope (Full DevOps Lifecycle)

The project scope is strictly frozen across 15 sequentially interdependent tasks spanning the entire software delivery and operations lifecycle:

```
[PLAN & CODE] ──> [BUILD & TEST] ──> [CONTAINERIZE] ──> [AUTOMATE CD] ──> [OPERATE & MONITOR]
  (Tasks 1-3)       (Tasks 4-5)        (Tasks 6-8)         (Tasks 9-12)        (Tasks 13-15)
```

### Phase A: Planning, Application Core & Version Control
1. **Task 01: Requirement Specification & Scope Baseline**  
   Define problem statement, stakeholder matrix, constraints, and freeze the 15-task scope.
2. **Task 02: Agile Sprint Planning & Kanban Backlog Formulation**  
   Author user stories with acceptance criteria, sprint roadmap, and Definition of Done (DoD).
3. **Task 03: Architecture Design & Application Baseline Implementation**  
   Implement Flask backend, SQLite data model, RESTful APIs, and Tailwind CSS responsive dashboard.
4. **Task 04: Git Repository Architecture & Branching Strategy Setup**  
   Establish Git repository with standard branch protections (`main`, `develop`, `feature/*`), `.gitignore`, and commit conventions.

### Phase B: Quality Assurance & Containerization
5. **Task 05: Automated Unit & Integration Testing Suite**  
   Implement test cases using `pytest` covering database operations, API endpoints, and input validation.
6. **Task 06: Containerization with Docker & Multi-Stage Optimization**  
   Author `Dockerfile` and `.dockerignore` for the Flask application, verifying lightweight container build and isolation.
7. **Task 07: Container Orchestration & Local Environment Parity**  
   Create `docker-compose.yml` to orchestrate web service, volume mounting for persistent SQLite data, and health-check directives.

### Phase C: Continuous Integration (Jenkins CI)
8. **Task 08: Jenkins CI Server & Build Agent Provisioning**  
   Set up Jenkins instance with required plugins (Git, Docker Pipeline, Pipeline Stage View, HTML Publisher).
9. **Task 09: Declarative Jenkinsfile Pipeline Construction**  
   Script multi-stage declarative pipeline: *Checkout* $\rightarrow$ *Lint/Static Analysis* $\rightarrow$ *Unit Tests* $\rightarrow$ *Docker Image Build*.
10. **Task 10: Automated End-to-End Testing with Headless Selenium**  
    Integrate Selenium test suite into the CI pipeline to validate user interactions (search bar query, book submission, status toggle).
11. **Task 11: Image Packaging & Docker Registry Publishing**  
    Automate tagged Docker image push (`library-search-portal:latest` and build ID) to Docker Hub upon pipeline test success.

### Phase D: Continuous Deployment (CD) & Configuration Management
12. **Task 12: Ansible Playbook Authoring for Environment Configuration**  
    Develop Ansible inventory and playbooks to automate target server prerequisites (Docker engine, network bridge, directory structures).
13. **Task 13: Automated Deployment & Continuous Delivery Integration**  
    Link Jenkins CD stage to trigger Ansible deployment playbook for pull-and-run container deployment with zero-downtime container replacement.

### Phase E: Operations, Monitoring & Post-Mortem
14. **Task 14: Smoke Testing, Health Checks & Rollback Automation**  
    Implement automated post-deployment verification HTTP checks with instant rollback to previous container tag if health checks fail.
15. **Task 15: Telemetry, Logging Aggregation & Project Review**  
    Configure structured container logging, document pipeline execution metrics, and compile final DevOps lab report.
