# Development Guide

## 1. Git Branch Strategy

### Branch Types

* main: production-ready
* develop: integration branch
* feature/*: new features
* fix/*: bug fixes
* refactor/*: refactoring
* test/*: testing work

---

## 2. Workflow

1. Create branch from develop
2. Implement feature
3. Write tests
4. Run tests
5. Open Pull Request
6. Merge after review

---

## 3. Merge Strategy

* feature → develop: Rebase and merge
* develop → main: Merge commit

Alternative (simple mode):

* feature → main: Squash merge

---

## 4. Commit Convention

* feat: new feature
* fix: bug fix
* refactor: code improvement
* test: test code
* docs: documentation

Example:

```text
feat: add notice crawler
fix: prevent duplicate notifications
```

---

## 5. Code Style

* Follow PEP8
* Use type hints
* Avoid abbreviations
* Write self-explanatory code

---

## 6. Naming Convention

Good examples:

```python
get_latest_notices()
save_notice_to_db()
send_discord_notification()
```

Bad examples:

```python
fn1()
dataProc()
tmp()
```

---

## 7. SOLID Principles

* Single Responsibility
* Open/Closed
* Liskov Substitution
* Interface Segregation
* Dependency Inversion

---

## 8. Development Philosophy

* Small changes over big rewrites
* Stability over speed
* Code is maintained longer than written
