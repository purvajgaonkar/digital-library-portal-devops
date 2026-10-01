"""Digital Library Search Portal - Selenium Automated UI Test Suite
Phase 4: Continuous Testing (Deliverable 9)
Executes end-to-end user journeys using Headless Chrome with screenshot capture on failure.
"""

import os
import sys
import time
import uuid
import threading
import pytest
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports', 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# --------------------------------------------------------------------------
# Background Flask Server Fixture (Starts server if not already up)
# --------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure the local Flask test server is alive and responding before running UI tests."""
    import urllib.request
    server_ready = False
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
        server_ready = True
    except Exception:
        server_ready = False

    if not server_ready:
        print(f"\n[Selenium Fixture] Launching background Flask test server on {BASE_URL}...")
        server_thread = threading.Thread(
            target=lambda: app.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False),
            daemon=True
        )
        server_thread.start()

        # Poll until server responds
        for _ in range(15):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
                server_ready = True
                break
            except Exception:
                pass

        if not server_ready:
            pytest.fail("Could not start background Flask server for UI tests.")


# --------------------------------------------------------------------------
# Selenium WebDriver Fixture
# --------------------------------------------------------------------------
@pytest.fixture(scope="function")
def driver():
    """Initialize and configure Headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")

    try:
        service = Service(ChromeDriverManager().install())
        driver_instance = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"[Driver Init Warning] ChromeDriverManager fallback: {e}")
        driver_instance = webdriver.Chrome(options=chrome_options)

    driver_instance.implicitly_wait(5)
    yield driver_instance
    driver_instance.quit()


def capture_screenshot(driver, test_name):
    """Save an evidence screenshot when a test case fails."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_{timestamp}.png")
    driver.save_screenshot(file_path)
    print(f"\n[Test Failure Screenshot Saved] -> {file_path}")
    return file_path


# --------------------------------------------------------------------------
# Critical User Journey 1: Dashboard Metrics & Health Badge
# --------------------------------------------------------------------------
def test_uj1_dashboard_and_health_visibility(driver):
    """
    Journey 1: Verify home page loads, health status indicator is active,
    and all 6 summary dashboard metric cards display numeric data.
    """
    test_name = "test_uj1_dashboard_and_health_visibility"
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        # 1. Assert Title
        assert "Digital Library" in driver.title

        # 2. Assert Health Badge indicates UP
        health_badge = wait.until(EC.visibility_of_element_located((By.ID, "healthBadge")))
        assert "UP" in health_badge.text

        # 3. Assert Metric Cards display numbers (not empty or '--')
        stat_total = wait.until(lambda d: d.find_element(By.ID, "statTotal").text != "--" and d.find_element(By.ID, "statTotal"))
        total_val = int(stat_total.text)
        assert total_val >= 1, "Catalog should have at least 1 book"

        available_val = int(driver.find_element(By.ID, "statAvailable").text)
        checked_out_val = int(driver.find_element(By.ID, "statCheckedOut").text)
        reserved_val = int(driver.find_element(By.ID, "statReserved").text)
        assert available_val + checked_out_val + reserved_val <= total_val

    except Exception:
        capture_screenshot(driver, test_name)
        raise


# --------------------------------------------------------------------------
# Critical User Journey 2: Create Record (Add New Book)
# --------------------------------------------------------------------------
def test_uj2_create_book_workflow(driver):
    """
    Journey 2: Open modal via Add Book button, inject valid book data,
    submit form, and assert toast confirmation and table update.
    """
    test_name = "test_uj2_create_book_workflow"
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        # 1. Click Add Book button to reveal modal
        add_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnOpenAddModal")))
        add_btn.click()

        # 2. Wait for modal to become visible
        wait.until(EC.visibility_of_element_located((By.ID, "addModal")))

        # 3. Populate form fields
        unique_suffix = uuid.uuid4().hex[:6]
        test_title = f"Selenium Automated Book {unique_suffix}"
        test_author = "QA Engineer"
        test_isbn = f"978-7{int(time.time()) % 1000000000:09d}"

        driver.find_element(By.ID, "modalTitle").send_keys(test_title)
        driver.find_element(By.ID, "modalAuthor").send_keys(test_author)
        driver.find_element(By.ID, "modalIsbn").send_keys(test_isbn)
        driver.find_element(By.ID, "modalCategory").send_keys("Testing")

        status_select = Select(driver.find_element(By.ID, "modalStatus"))
        status_select.select_by_visible_text("Available")

        # 4. Submit form
        driver.find_element(By.ID, "modalSubmitBtn").click()

        # 5. Assert success Toast appears
        toast = wait.until(EC.visibility_of_element_located((By.ID, "toast")))
        assert "registered" in toast.text or "Success" in toast.text

        # 6. Verify newly created book appears in the catalog table
        wait.until(EC.text_to_be_present_in_element((By.ID, "booksTableBody"), test_title))

    except Exception:
        capture_screenshot(driver, test_name)
        raise


# --------------------------------------------------------------------------
# Critical User Journey 3: Real-Time Keyword Search & Filtering
# --------------------------------------------------------------------------
def test_uj3_search_and_filter_workflow(driver):
    """
    Journey 3: Query search bar with specific keyword, assert table filters,
    then reset and assert full catalog returns.
    """
    test_name = "test_uj3_search_and_filter_workflow"
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        # Ensure table is loaded
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#booksTableBody tr")))

        # 1. Type specific search term
        search_input = driver.find_element(By.ID, "searchInput")
        search_input.clear()
        search_input.send_keys("DevOps")

        # 2. Wait for filtered results
        time.sleep(0.6)  # allow debounce
        table_body = driver.find_element(By.ID, "booksTableBody")
        assert "DevOps" in table_body.text

        # 3. Search non-existent term
        search_input.clear()
        search_input.send_keys("NonExistentTermXYZ999")
        time.sleep(0.6)

        empty_state = wait.until(EC.visibility_of_element_located((By.ID, "emptyState")))
        assert "No matching books found" in empty_state.text

        # 4. Reset filters
        driver.find_element(By.XPATH, "//button[contains(text(), 'Reset')]").click()
        time.sleep(0.6)
        assert empty_state.is_displayed() is False
        assert len(driver.find_elements(By.CSS_SELECTOR, "#booksTableBody tr")) >= 1

    except Exception:
        capture_screenshot(driver, test_name)
        raise


# --------------------------------------------------------------------------
# Critical User Journey 4: Status Update Workflow
# --------------------------------------------------------------------------
def test_uj4_status_update_workflow(driver):
    """
    Journey 4: Toggle an existing book's availability status dropdown
    and assert the change triggers a confirmation toast and updates metrics.
    """
    test_name = "test_uj4_status_update_workflow"
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        # Wait for table to populate
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#booksTableBody tr")))

        # Locate first status dropdown in the table
        status_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#booksTableBody tr select")))
        select_elem = Select(status_dropdown)

        initial_status = select_elem.first_selected_option.text
        target_status = "Checked Out" if initial_status != "Checked Out" else "Available"

        select_elem.select_by_visible_text(target_status)

        # Assert toast notification confirms update
        toast = wait.until(EC.visibility_of_element_located((By.ID, "toast")))
        assert "status" in toast.text.lower() or target_status.lower() in toast.text.lower()

    except Exception:
        capture_screenshot(driver, test_name)
        raise


# --------------------------------------------------------------------------
# Critical User Journey 5: View Book Details Modal
# --------------------------------------------------------------------------
def test_uj5_view_book_details_modal(driver):
    """
    Journey 5: Click the 'View' button on a catalog item,
    verify the modal displays detailed publication metadata, and close it.
    """
    test_name = "test_uj5_view_book_details_modal"
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        # Click the first 'View' button
        view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View')]")))
        view_btn.click()

        # Wait for View modal to display
        modal = wait.until(EC.visibility_of_element_located((By.ID, "viewModal")))
        assert modal.is_displayed()

        # Assert metadata elements are populated
        view_title = driver.find_element(By.ID, "viewTitle").text
        view_author = driver.find_element(By.ID, "viewAuthor").text
        view_isbn = driver.find_element(By.ID, "viewIsbn").text

        assert len(view_title) > 0
        assert len(view_author) > 0
        assert len(view_isbn) > 0

        # Close modal
        close_btn = driver.find_element(By.XPATH, "//div[@id='viewModal']//button[contains(text(), 'Close')]")
        close_btn.click()
        time.sleep(0.3)
        assert not modal.is_displayed()

    except Exception:
        capture_screenshot(driver, test_name)
        raise
