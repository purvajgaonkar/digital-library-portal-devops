# Phase 4: Automated UI Testing, Continuous Quality Gates, and Defect Workflow
**Project Name:** CI/CD Pipeline for a Digital Library Search Portal  
**Domain:** DevOps QA Automation & Continuous Testing  
**Phase:** 4 — Deliverables 9 & 10  

---

## 1. Deliverable 9: Selenium Test Design & Local Execution

### 1.1 Test Plan: 5 Critical User Journeys

| Journey ID | Journey Title | Preconditions | Action Sequence | Assertions & Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **UJ-01** | **Dashboard Metrics & Health Verification** | Server is running and reachable on port 5000. | 1. Navigate to `/`.<br>2. Inspect DOM for health badge.<br>3. Inspect the 6 metric counter cards. | &bull; Health badge displays `Service: UP`.<br>&bull; Numeric metric cards (`Total`, `Available`, `Checked Out`, `Reserved`, `Categories`, `Authors`) display positive integer counts. |
| **UJ-02** | **Create Record (Add Book) Workflow** | Portal dashboard loaded; database active. | 1. Click `#btnOpenAddModal`.<br>2. Inject title, author, unique timestamped ISBN, topic.<br>3. Click `#modalSubmitBtn`. | &bull; Modal appears smoothly.<br>&bull; Success toast appears confirming creation.<br>&bull; New title dynamically renders inside `#booksTableBody`. |
| **UJ-03** | **Real-Time Keyword Search & Reset** | Catalog populated with sample records. | 1. Enter keyword `DevOps` into `#searchInput`.<br>2. Verify debounce filtering.<br>3. Enter non-existent keyword `NonExistentTermXYZ999`.<br>4. Click `Reset` button. | &bull; Matching books appear in table.<br>&bull; Empty state banner displays: `No matching books found`.<br>&bull; Reset button restores full catalog without page reload. |
| **UJ-04** | **Interactive Status Update Workflow** | Catalog item in `Available` status. | 1. Locate status dropdown for first book.<br>2. Select `Checked Out`.<br>3. Wait for PUT completion. | &bull; Toast notification confirms status change.<br>&bull; Badge styling dynamically updates to amber.<br>&bull; Database updates without full page refresh. |
| **UJ-05** | **Inspect Book Details Modal** | Catalog items displayed in table. | 1. Click `View` button on book row.<br>2. Inspect modal contents.<br>3. Click `Close` button. | &bull; `#viewModal` opens.<br>&bull; Title, Author, and ISBN match the clicked row.<br>&bull; Closing removes modal from screen. |

---

### 1.2 Selenium Script Architecture (`tests/test_ui.py`)

The Selenium test suite is located in [`tests/test_ui.py`](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/tests/test_ui.py).

#### Architectural Highlights:
1. **Headless Chrome Execution:** Configured via `selenium.webdriver.chrome.options.Options` with arguments `--headless=new`, `--no-sandbox`, and `--disable-gpu` for headless execution in CI environments.
2. **Dynamic Server Management:** Includes a session-scoped fixture `ensure_server_running` that starts a background Flask thread on port 5000 if not already running.
3. **Explicit Waits (`WebDriverWait`):** Eliminates arbitrary sleep timers by waiting for DOM element visibility and text changes.
4. **Automated Defect Screenshot Capture:** Every test journey wraps execution in a `try...except` block; upon any assertion failure or unhandled exception, a full-resolution PNG screenshot is captured to `reports/screenshots/<test_name>_<timestamp>.png`.

```python
def capture_screenshot(driver, test_name):
    """Save an evidence screenshot when a test case fails."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_{timestamp}.png")
    driver.save_screenshot(file_path)
    print(f"\n[Test Failure Screenshot Saved] -> {file_path}")
    return file_path
```

---

### 1.3 Local Execution Instructions

#### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

#### 2. Execute UI Test Suite Locally
```powershell
# Run the automated UI test suite with JUnit XML reporting and verbose output
pytest -v tests/test_ui.py --junitxml=reports/selenium-results.xml
```

#### 3. Run Both Unit and UI Tests
```powershell
pytest -v tests/ --junitxml=reports/test-results.xml
```

---

## 2. Deliverable 10: Continuous Testing in Jenkins & Defect Workflow

### 2.1 Continuous Testing Stage in `Jenkinsfile`

The updated [`Jenkinsfile`](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/Jenkinsfile) places the Selenium test suite as a blocking quality gate prior to packaging and server deployment:

```
[Checkout] ──> [Build & Deps] ──> [Unit Tests] ──> [Selenium E2E Tests] ──> [Package] ──> [Deploy]
                                                           │
                                                  (If Failed: HALT)
                                                           │
                                                           ▼
                                              [Archive Screenshots & Logs]
```

#### Pipeline Stage Definition:
```groovy
stage('Continuous Testing (Selenium E2E)') {
    when {
        expression { return params.RUN_UI_TESTS == true }
    }
    steps {
        echo "=========================================================="
        echo "Stage 4: Automated End-to-End Headless Selenium Testing"
        echo "=========================================================="
        sh '''
            . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate
            mkdir -p reports/screenshots

            export BASE_URL="http://127.0.0.1:${PORT}"
            
            # Non-zero exit code halts pipeline before Package & Deploy!
            pytest -v tests/test_ui.py --junitxml=reports/selenium-results.xml
        '''
    }
    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/selenium-results.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/screenshots/*.png'
        }
        failure {
            echo "⚠️ Continuous Testing FAILED! Failure screenshots and logs preserved in build artifacts."
            echo "Halting pipeline: deployment stage skipped due to test regression."
        }
    }
}
```

---

### 2.2 Step-by-Step Defect Workflow

#### Step 1: Deliberately Introduce a UI Defect
To simulate a real-world frontend regression, alter the "Add Book" button ID in [`templates/index.html`](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/templates/index.html#L55):

```html
<!-- INTENTIONAL DEFECT: Changed button ID from 'btnOpenAddModal' to 'btnOpenAddModal-broken' -->
<button onclick="openAddModal()" id="btnOpenAddModal-broken" class="px-4 py-2 rounded-xl bg-sky-500 ...">
    Add Book
</button>
```

#### Step 2: Commit Defect and Trigger CI Pipeline
```powershell
git checkout -b bugfix/simulate-ui-defect
git commit -am "test(defect): intentionally break Add Book button ID to test CI quality gate"
git push origin bugfix/simulate-ui-defect
```

#### Step 3: Pipeline Failure & Quality Gate Blocking
Jenkins triggers build `#3`. During Stage 4 (`Continuous Testing`), Selenium attempts to locate `#btnOpenAddModal`:

```text
=================================== FAILURES ===================================
________________________ test_uj2_create_book_workflow _________________________

driver = <selenium.webdriver.chrome.webdriver.WebDriver (session="481a9f...")>

    def test_uj2_create_book_workflow(driver):
        ...
>       add_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnOpenAddModal")))
E       selenium.common.exceptions.TimeoutException: Message: 
E       Stacktrace:
E       Backtrace:
E       ...

[Test Failure Screenshot Saved] -> reports/screenshots/test_uj2_create_book_workflow_20261001_121500.png

- Generated junitxml file: reports/selenium-results.xml -
=========================== 1 failed, 4 passed in 12.4s ===========================
[Pipeline] echo
⚠️ Continuous Testing FAILED! Failure screenshots and logs preserved in build artifacts.
Halting pipeline: deployment stage skipped due to test regression.
[Pipeline] }
[Pipeline] // stage
[Pipeline] stage (Package) skipped
[Pipeline] stage (Deploy) skipped
Finished: FAILURE
```

#### Pipeline Stage View:
```
+-------------------------------------------------------------------------------------------------------------------------+
| Pipeline Stage View: Digital-Library-Pipeline #3                                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
|  Checkout   |  Build/Dependencies  |  Unit Testing  |  Continuous Testing (Selenium)  |   Package   |      Deploy     |
|   (2 sec)   |       (15 sec)       |    (3 sec)     |            (14 sec)             |  (SKIPPED)  |    (SKIPPED)    |
|   SUCCESS   |        SUCCESS       |    SUCCESS     |             FAILED              |   SKIPPED   |     SKIPPED     |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

#### Step 4: Correct the Defect & Commit the Fix
Restore the element ID in [`templates/index.html`](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/templates/index.html):

```html
<!-- RESOLUTION: Corrected button ID back to 'btnOpenAddModal' -->
<button onclick="openAddModal()" id="btnOpenAddModal" class="px-4 py-2 rounded-xl bg-sky-500 ...">
    Add Book
</button>
```

Commit and push the fix:
```powershell
git commit -am "fix(ui): restore correct btnOpenAddModal element ID"
git checkout main
git merge bugfix/simulate-ui-defect
git push origin main
```

#### Step 5: Successful Pipeline Rerun
Jenkins detects the commit on `main` and triggers build `#4`. All stages execute cleanly to completion:

```text
tests/test_ui.py::test_uj1_dashboard_and_health_visibility PASSED       [ 20%]
tests/test_ui.py::test_uj2_create_book_workflow PASSED                   [ 40%]
tests/test_ui.py::test_uj3_search_and_filter_workflow PASSED             [ 60%]
tests/test_ui.py::test_uj4_status_update_workflow PASSED                 [ 80%]
tests/test_ui.py::test_uj5_view_book_details_modal PASSED               [100%]

============================== 5 passed in 8.12s ===============================
[Pipeline] { (Package) } ... SUCCESS
[Pipeline] { (Deploy) }  ... SUCCESS
==========================================================
🎉 DEPLOYMENT SUCCESSFUL!
Target Environment : staging
Service URL        : http://localhost:5000
==========================================================
Finished: SUCCESS
```
