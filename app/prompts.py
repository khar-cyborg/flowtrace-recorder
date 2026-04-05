# Curated prompt library for QA / Automation Engineers
# Each entry: (title, description, prompt_text)

PROMPT_CATEGORIES = {

    "Screenshots": [
        (
            "Full Page Screenshot on Every Step",
            "Generate a Playwright script that takes a full-page screenshot after every action.",
            """Write a Playwright (Python) test script for the following flow:
[PASTE YOUR FLOW / URL HERE]

Requirements:
- Take a FULL PAGE screenshot after every major action (click, fill, navigation).
- Save screenshots to a folder called "screenshots/" with descriptive filenames like "step_01_login_page.png", "step_02_fill_username.png", etc.
- Use page.screenshot(full_page=True, path=...) for each capture.
- Add a short comment above each screenshot call explaining what was just done.
- Use explicit waits (expect / wait_for_selector) before capturing so the page is fully loaded."""
        ),
        (
            "Element-Level Screenshot",
            "Capture a screenshot of a specific element instead of the full page.",
            """Write a Playwright (Python) script that:
1. Navigates to: [PASTE URL]
2. Locates the element: [DESCRIBE ELEMENT OR PASTE SELECTOR]
3. Takes a screenshot of ONLY that element using element.screenshot(path="element.png")
4. Also takes a full-page screenshot for context.

Use explicit waits to ensure the element is visible before capturing.
Add error handling in case the element is not found."""
        ),
        (
            "Visual Comparison / Baseline Screenshots",
            "Create baseline screenshots and compare them across test runs.",
            """Write a Playwright (Python) test that implements visual regression testing:

1. Navigate to: [PASTE URL]
2. Take a full-page screenshot and save it as "baseline.png" if it doesn't exist yet.
3. If "baseline.png" already exists, take a new screenshot as "current.png".
4. Compare the two images pixel-by-pixel using Pillow (PIL).
5. Highlight differences in red and save the diff as "diff.png".
6. Print a similarity percentage and fail the test if it drops below 95%.

Include all necessary imports (playwright, PIL, os)."""
        ),
    ],

    "Video Recording": [
        (
            "Record Full Test Execution as Video",
            "Capture a video of the entire test session for evidence.",
            """Write a Playwright (Python) test script that RECORDS A VIDEO of the entire browser session.

Requirements:
- Use browser.new_context(record_video_dir="videos/", record_video_size={"width": 1280, "height": 720})
- Navigate to: [PASTE URL]
- Perform these actions: [DESCRIBE YOUR TEST STEPS]
- After the test, close the context so the video is saved.
- Print the path to the saved video file using page.video.path().
- Make sure the video directory exists before starting."""
        ),
        (
            "Video + Screenshots Combined Evidence",
            "Record video AND take screenshots at key checkpoints.",
            """Write a Playwright (Python) test that captures BOTH video and screenshots:

1. Create a browser context with video recording enabled (record_video_dir="evidence/videos/").
2. Navigate to: [PASTE URL]
3. At each key checkpoint in the flow, take a full-page screenshot saved to "evidence/screenshots/".
4. Perform these test steps: [DESCRIBE STEPS]
5. After completion, close context to finalize the video.
6. Print summary: video path + list of all screenshot paths.

This gives both continuous video evidence and high-resolution checkpoint images."""
        ),
    ],

    "Trace Viewer": [
        (
            "Generate Trace File for Debugging",
            "Record a full trace with snapshots, network, and console logs.",
            """Write a Playwright (Python) test that generates a TRACE FILE for debugging:

Requirements:
- Start tracing with: context.tracing.start(screenshots=True, snapshots=True, sources=True)
- Navigate to: [PASTE URL]
- Perform these steps: [DESCRIBE YOUR FLOW]
- Stop tracing and save: context.tracing.stop(path="trace.zip")
- Print instructions: "Open trace with: playwright show-trace trace.zip"

The trace file will contain:
- DOM snapshots at each action
- Network requests and responses
- Console logs
- Screenshots at each step
- Source code mapping"""
        ),
        (
            "Trace on Failure Only",
            "Only save traces when a test fails to save disk space.",
            """Write a Playwright (Python) test with CONDITIONAL TRACING (trace only on failure):

1. Start tracing at the beginning of the test.
2. Navigate to: [PASTE URL]
3. Perform test steps: [DESCRIBE STEPS]
4. Add assertions to verify expected outcomes.
5. In a try/except block:
   - If test PASSES: discard the trace (context.tracing.stop())
   - If test FAILS: save the trace (context.tracing.stop(path="failure_trace.zip"))
     and print the path for debugging.

This saves disk space by only keeping traces for failed tests."""
        ),
    ],

    "Code from Codegen": [
        (
            "Clean Up Codegen Output",
            "Take raw codegen output and convert it into a structured, reusable test.",
            """I have the following Playwright Codegen output:

```
[PASTE YOUR CODEGEN OUTPUT HERE]
```

Please refactor this into a clean, production-ready Playwright (Python) test:
1. Wrap it in a proper test function using pytest.
2. Add explicit waits (expect) instead of relying on auto-waiting.
3. Replace hardcoded selectors with more resilient ones (data-testid, role, text).
4. Add meaningful assertions after key actions.
5. Add docstrings and comments explaining each step.
6. Extract any repeated logic into helper functions.
7. Add proper error handling with descriptive messages."""
        ),
        (
            "Convert Codegen to Page Object Model",
            "Transform codegen output into a POM architecture.",
            """I have this Playwright Codegen output:

```
[PASTE YOUR CODEGEN OUTPUT HERE]
```

Convert this into a Page Object Model (POM) structure:
1. Create a Page class (e.g., LoginPage, DashboardPage) with:
   - Locators as class properties
   - Action methods (login, fill_form, submit, etc.)
   - Assertion methods (verify_title, verify_element_visible, etc.)
2. Create a test file that imports and uses the Page class.
3. Use Python type hints and docstrings.
4. Follow the Arrange-Act-Assert pattern in the test.

Output both files: the page class and the test file."""
        ),
        (
            "Convert Codegen to Data-Driven Test",
            "Turn a single codegen flow into a parameterized test with multiple data sets.",
            """I have this Playwright Codegen output for a single flow:

```
[PASTE YOUR CODEGEN OUTPUT HERE]
```

Convert this into a DATA-DRIVEN test:
1. Extract all input values (form fields, search terms, etc.) into test data.
2. Use @pytest.mark.parametrize to run the same flow with multiple data sets.
3. Create at least 3 sample data sets including edge cases (empty values, special characters, very long strings).
4. Add assertions that validate the outcome based on the input data.
5. Generate a clear test report name for each parametrized case."""
        ),
    ],

    "API & Network": [
        (
            "Intercept and Validate API Responses",
            "Monitor network requests and assert on API response data.",
            """Write a Playwright (Python) test that intercepts and validates API calls:

1. Navigate to: [PASTE URL]
2. Set up a route handler to intercept requests matching: [PASTE API PATTERN, e.g., "**/api/users"]
3. Capture the response status code, headers, and JSON body.
4. Perform the UI action that triggers the API call: [DESCRIBE ACTION]
5. Assert that:
   - Response status is 200
   - Response body contains expected fields
   - Response time is under 2 seconds
6. Print a summary of the captured request/response."""
        ),
        (
            "Mock API Response for Testing",
            "Replace real API responses with mock data.",
            """Write a Playwright (Python) test that MOCKS an API response:

1. Before navigating, set up a route to intercept: [PASTE API ENDPOINT]
2. Return a mock JSON response with controlled test data:
   ```json
   [PASTE YOUR MOCK DATA OR DESCRIBE IT]
   ```
3. Navigate to: [PASTE URL]
4. Verify the UI renders the mock data correctly.
5. Test with different mock scenarios:
   - Normal data
   - Empty response
   - Error response (500)

Use page.route() with route.fulfill() for mocking."""
        ),
    ],

    "Authentication & Session": [
        (
            "Reusable Login with Saved Session",
            "Login once, save cookies/storage, and reuse across tests.",
            """Write a Playwright (Python) setup that handles authentication efficiently:

1. Create a script that:
   a. Logs into: [PASTE LOGIN URL]
   b. Fills credentials: [DESCRIBE FIELDS]
   c. Saves the authenticated state using context.storage_state(path="auth_state.json")

2. Create a test that:
   a. Loads the saved state: browser.new_context(storage_state="auth_state.json")
   b. Navigates directly to a protected page (skipping login)
   c. Verifies the user is authenticated

This avoids logging in before every test, saving significant time."""
        ),
    ],

    "CI/CD & Reporting": [
        (
            "GitHub Actions Pipeline with Artifacts",
            "Generate a CI config that runs tests and uploads evidence.",
            """Generate a GitHub Actions workflow YAML file that:

1. Runs Playwright tests on every push and pull request.
2. Uses the official Playwright Docker image or installs browsers.
3. Runs tests with: pytest --html=report.html --self-contained-html
4. On failure, captures:
   - Screenshots (from screenshots/ folder)
   - Videos (from videos/ folder)
   - Traces (from traces/ folder)
   - HTML test report
5. Uploads all evidence as GitHub Actions artifacts.
6. Supports running tests in parallel across 3 shards.

Include proper caching for pip dependencies and Playwright browsers."""
        ),
        (
            "HTML Test Report with Embedded Evidence",
            "Generate a rich HTML report with screenshots and results.",
            """Write a Playwright (Python) test setup using pytest that generates a RICH HTML REPORT:

1. Use pytest-html plugin for report generation.
2. In conftest.py, add a pytest hook that:
   - Takes a screenshot on test failure
   - Embeds the screenshot directly into the HTML report (base64)
   - Logs the test duration
   - Captures console errors from the browser
3. Configure pytest to output the report as "test_report.html".
4. Include test metadata: browser, viewport size, base URL, timestamp.

The report should be a single self-contained HTML file that can be shared."""
        ),
    ],

    "Accessibility & Performance": [
        (
            "Accessibility Audit with Playwright",
            "Run an accessibility check on a page and generate a report.",
            """Write a Playwright (Python) script that performs an ACCESSIBILITY AUDIT:

1. Navigate to: [PASTE URL]
2. Inject and run the axe-core accessibility engine using page.evaluate().
3. Capture all violations grouped by severity (critical, serious, moderate, minor).
4. For each violation, capture:
   - Description and impact level
   - Affected elements (selectors)
   - A screenshot highlighting the element
5. Generate a summary report as a JSON file and print a human-readable summary.
6. Fail the test if any critical or serious violations are found.

Include the axe-core CDN injection script."""
        ),
        (
            "Page Performance Metrics",
            "Measure load time, LCP, FCP, and other Web Vitals.",
            """Write a Playwright (Python) script that measures PERFORMANCE METRICS:

1. Navigate to: [PASTE URL]
2. Capture these metrics using the Performance API (page.evaluate):
   - Page Load Time (loadEventEnd - navigationStart)
   - First Contentful Paint (FCP)
   - Largest Contentful Paint (LCP)
   - Time to Interactive (TTI)
   - Total Blocking Time (TBT)
   - DOM Content Loaded time
3. Also capture:
   - Number of network requests
   - Total transfer size
4. Print a formatted report with pass/fail thresholds:
   - LCP < 2.5s = Good, < 4s = Needs Improvement, > 4s = Poor
   - FCP < 1.8s = Good
5. Save the report as performance_report.json."""
        ),
    ],
}
