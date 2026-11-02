
"""
DRRCS - Selenium End-to-End Allocation Workflow

Workflow:
1. Coordinator login
2. Open resource allocation page
3. Select a pending relief request
4. Select a matching volunteer and inventory item
5. Allocate resources
6. Verify assignment creation
7. Login as volunteer
8. Verify assignment notification
9. Save screenshots as evidence
"""

import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

BASE_URL = "http://127.0.0.1:5000"

COORDINATOR_EMAIL = "coordinator@example.com"
VOLUNTEER_EMAIL = "volunteer@example.com"
PASSWORD = "password123"

EVIDENCE_DIR = Path("artifacts/selenium")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

WAIT_TIME = 20


# -------------------------------------------------
# SCREENSHOT HELPER
# -------------------------------------------------

def save_screenshot(driver, filename):
    path = EVIDENCE_DIR / filename
    driver.save_screenshot(str(path))
    print(f"Screenshot saved: {path}")


# -------------------------------------------------
# LOGIN FUNCTION
# -------------------------------------------------

def login(driver, wait, email, password):

    print(f"\nLogging in as {email}...")

    driver.get(f"{BASE_URL}/login")

    email_input = wait.until(
        EC.visibility_of_element_located(
            (By.ID, "emailInput")
        )
    )

    password_input = driver.find_element(
        By.ID, "passwordInput"
    )

    email_input.clear()
    email_input.send_keys(email)

    password_input.clear()
    password_input.send_keys(password)

    driver.find_element(
        By.CSS_SELECTOR,
        "#loginForm button[type='submit']"
    ).click()

    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a[href='/logout']")
        )
    )

    print(f"PASS: Logged in as {email}")


# -------------------------------------------------
# FIND MATCHING REQUEST AND INVENTORY
# -------------------------------------------------

def find_matching_resources(request_select, item_select):

    for request_option in request_select.options:

        request_value = request_option.get_attribute("value")

        if not request_value:
            continue

        request_text = request_option.text.strip()

        request_match = re.search(
            r"—\s*(.*?)\s*[×x]\s*(\d+)",
            request_text,
            re.IGNORECASE
        )

        if not request_match:
            continue

        category = request_match.group(1).strip().lower()
        quantity = int(request_match.group(2))

        for item_option in item_select.options:

            item_value = item_option.get_attribute("value")

            if not item_value:
                continue

            item_text = item_option.text.strip()

            item_match = re.search(
                r"—\s*(.*?),\s*stock\s*(\d+)",
                item_text,
                re.IGNORECASE
            )

            if not item_match:
                continue

            item_category = item_match.group(1).strip().lower()
            available_stock = int(item_match.group(2))

            if (
                category == item_category
                and available_stock >= quantity
            ):
                return (
                    request_option,
                    item_option,
                    category,
                    quantity
                )

    raise AssertionError(
        "No matching pending request and inventory item "
        "with sufficient stock were found."
    )


# -------------------------------------------------
# VERIFY ASSIGNMENT
# -------------------------------------------------

def verify_assignment(driver, wait, request_id, volunteer_name):

    def assignment_visible(browser):

        rows = browser.find_elements(
            By.CSS_SELECTOR, "table tr"
        )

        for row in rows:

            row_text = row.text

            contains_request = (
                re.search(
                    rf"\b{re.escape(str(request_id))}\b",
                    row_text
                )
                is not None
            )

            if (
                contains_request
                and volunteer_name.lower() in row_text.lower()
                and "assigned" in row_text.lower()
            ):
                return True

        return False

    wait.until(assignment_visible)

    print("PASS: Assignment appears in tracking table")


# -------------------------------------------------
# MAIN SELENIUM WORKFLOW
# -------------------------------------------------

def main():

    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument(
        "--disable-features=PasswordLeakDetection,PasswordCheck"
    )

    # Disable password-manager prompts in this temporary
    # Selenium browser profile only.
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        }
    )

    driver = webdriver.Chrome(options=options)

    wait = WebDriverWait(driver, WAIT_TIME)

    try:

        # =========================================
        # TEST 1: COORDINATOR LOGIN
        # =========================================

        login(
            driver,
            wait,
            COORDINATOR_EMAIL,
            PASSWORD
        )

        save_screenshot(
            driver,
            "01_coordinator_login.png"
        )

        # =========================================
        # TEST 2: OPEN RESOURCE ALLOCATION
        # =========================================

        print("\nOpening resource allocation page...")

        driver.get(f"{BASE_URL}/assignments")

        allocation_form = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "form[action='/assignments']")
            )
        )

        request_select = Select(
            allocation_form.find_element(
                By.NAME, "request_id"
            )
        )

        volunteer_select = Select(
            allocation_form.find_element(
                By.NAME, "volunteer_id"
            )
        )

        item_select = Select(
            allocation_form.find_element(
                By.NAME, "item_id"
            )
        )

        print("PASS: Resource allocation page opened")

        # =========================================
        # TEST 3: SELECT MATCHING REQUEST AND STOCK
        # =========================================

        (
            request_option,
            item_option,
            category,
            quantity
        ) = find_matching_resources(
            request_select,
            item_select
        )

        request_id = request_option.get_attribute("value")

        request_select.select_by_value(request_id)

        item_select.select_by_value(
            item_option.get_attribute("value")
        )

        # =========================================
        # TEST 4: SELECT VOLUNTEER
        # =========================================

        bob = next(
            (
                option
                for option in volunteer_select.options
                if "Volunteer Bob" in option.text
            ),
            None
        )

        if bob is None:
            raise AssertionError(
                "Volunteer Bob is not available."
            )

        volunteer_select.select_by_value(
            bob.get_attribute("value")
        )

        volunteer_name = bob.text.split("—", 1)[-1].strip()

        print("\nSelected details:")
        print(f"Request ID: {request_id}")
        print(f"Category: {category}")
        print(f"Quantity: {quantity}")
        print(f"Volunteer: {volunteer_name}")
        print(f"Inventory: {item_option.text}")

        save_screenshot(
            driver,
            "02_before_allocation.png"
        )

        # =========================================
        # TEST 5: ALLOCATE RESOURCES
        # =========================================

        print("\nAllocating resources...")

        submit_button = allocation_form.find_element(
            By.TAG_NAME, "button"
        )

        submit_button.click()

        # Wait for either success or error flash message.
        try:

            result_alert = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".alert")
                )
            )

        except TimeoutException as error:

            print("\nNo application alert appeared.")

            print(
                "Page content:",
                driver.find_element(By.TAG_NAME, "body").text
            )

            save_screenshot(
                driver,
                "allocation_no_alert.png"
            )

            raise AssertionError(
                "Allocation produced no visible application message."
            ) from error

        message = result_alert.text.strip()
        alert_class = result_alert.get_attribute("class") or ""

        print("\nAllocation response:", message)

        save_screenshot(
            driver,
            "03_allocation_response.png"
        )

        if "alert-danger" in alert_class:

            raise AssertionError(
                f"Application rejected allocation: {message}"
            )

        assert (
            "Resource allocated and volunteer notified"
            in message
        ), f"Unexpected allocation response: {message}"

        print("PASS: Resources allocated successfully")

        # =========================================
        # TEST 6: VERIFY ASSIGNMENT TRACKING
        # =========================================

        verify_assignment(
            driver,
            wait,
            request_id,
            volunteer_name
        )

        save_screenshot(
            driver,
            "04_assignment_tracking.png"
        )

        # =========================================
        # TEST 7: LOGOUT COORDINATOR
        # =========================================

        print("\nLogging out Coordinator...")

        driver.get(f"{BASE_URL}/logout")

        # =========================================
        # TEST 8: VOLUNTEER LOGIN
        # =========================================

        login(
            driver,
            wait,
            VOLUNTEER_EMAIL,
            PASSWORD
        )

        save_screenshot(
            driver,
            "05_volunteer_login.png"
        )

        # =========================================
        # TEST 9: VERIFY NOTIFICATION
        # =========================================

        print("\nOpening volunteer notifications...")

        driver.get(f"{BASE_URL}/notifications")

        wait.until(
            EC.visibility_of_element_located(
                (By.TAG_NAME, "body")
            )
        )

        body_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text.lower()

        wait.until(
            lambda browser: "assigned request"
            in browser.find_element(
                By.TAG_NAME, "body"
            ).text.lower()
        )

        assert "assigned request" in body_text or (
            "assigned request" in driver.find_element(
                By.TAG_NAME, "body"
            ).text.lower()
        )

        print(
            "PASS: Volunteer can see the assignment notification"
        )

        save_screenshot(
            driver,
            "06_volunteer_notification.png"
        )

        # =========================================
        # FINAL RESULT
        # =========================================

        print("\n" + "=" * 50)
        print("ALL SELENIUM WORKFLOW CHECKS PASSED")
        print("=" * 50)

        print(f"\nEvidence location: {EVIDENCE_DIR.resolve()}")

    except Exception as error:

        print("\n" + "=" * 50)
        print("SELENIUM WORKFLOW FAILED")
        print("=" * 50)

        print("Error:", error)

        try:

            print("Current URL:", driver.current_url)

            print(
                "Current page:",
                driver.find_element(
                    By.TAG_NAME, "body"
                ).text[:3000]
            )

            save_screenshot(
                driver,
                "failure_screenshot.png"
            )

        except Exception:
            print("Could not capture failure details.")

        input(
            "\nBrowser is still open. "
            "Press Enter to close it after inspection..."
        )

        raise

    finally:

        driver.quit()


# -------------------------------------------------
# EXECUTION ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":
    main()
