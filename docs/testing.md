# Testing Guide

## 1. Core Principle

* Tests are mandatory
* No feature is complete without passing tests

---

## 2. Testing Tool

* pytest

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

## 8. Goal

Ensure reliability and prevent regressions.
