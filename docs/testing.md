# Testing Guide

## 1. Core Principle

* Tests are mandatory
* No feature is complete without passing tests

---

## 2. Testing Tool

* pytest
* Run pytest inside Docker with `docker compose run --rm app`

---

## 3. Test Scope

* Unit tests for services
* Mock external dependencies

  * API
  * crawler
  * database

---

## 4. Development Cycle

```text
Design → Test → Implement → Verify → Refactor → Test Again
```

---

## 5. Rules

* Write tests before or alongside code
* Do NOT skip tests
* Do NOT delete failing tests
* Fix code, not tests
* After feature development or bug fixes, run the full Docker test command

### Required Verification Command

```powershell
docker compose run --rm app
```

This command runs `uv run pytest -p no:cacheprovider` in the container, using the same Python and dependencies as the Docker development environment.

---

## 6. Example Test Structure

```python
def test_fetch_notices():
    notices = fetch_notices()
    assert len(notices) > 0
```

---

## 7. Refactoring Rule

* Always run all tests after refactoring
* If any test fails → rollback and fix

---

## Commit After Verification

* Commit only after the required Docker test command passes
* Keep each commit focused on a small feature or fix

---

## 8. Goal

Ensure reliability and prevent regressions.
