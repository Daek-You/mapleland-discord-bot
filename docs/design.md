# MapleLand Discord Bot 설계서 (MVP → 확장형)

---

## 1. 프로젝트 개요

### 목표

메이플랜드 관련 정보를 자동으로 수집하고, 디스코드에서 조회/알림/요약/질문 기능을 제공하는 봇 개발

### 핵심 기능

* 공지사항 조회
* 패치노트 요약
* 자동 업데이트 알림
* 자연어 질문 응답

---

## 2. 시스템 아키텍처

```
[User]
   ↓
[Discord]
   ↓
[Discord Bot (Python)]
   ↓
[Service Layer]
   ↓
[Crawler / AI / DB]
```

### 데이터 흐름

#### 명령어 요청

```
User → Discord → Bot → Service → DB/AI → Bot → Discord 응답
```

#### 자동 알림

```
Bot Scheduler → Crawler → DB 비교 → 새 공지 → Discord 전송
```

---

## 3. 기술 스택

### Backend

* Python 3.11+
* discord.py

### 데이터 수집

* httpx (HTTP 요청)
* BeautifulSoup (HTML 파싱)

### 데이터베이스

* PostgreSQL (확장 고려)
* SQLAlchemy (ORM)
* Alembic (마이그레이션)

### AI 기능

* OpenAI API (요약 및 질의응답)

### 배포

* Docker
* Docker Compose

### 기타

* python-dotenv (환경 변수 관리)

---

## 4. 프로젝트 구조

```
mapleland-discord-bot/
├─ app/
│  ├─ bot/
│  │  ├─ commands/
│  │  │  ├─ notice.py
│  │  │  ├─ summary.py
│  │  │  └─ ask.py
│  │  └─ client.py
│  │
│  ├─ crawler/
│  │  └─ mapleland.py
│  │
│  ├─ services/
│  │  ├─ notice_service.py
│  │  ├─ notification_service.py
│  │  └─ ai_service.py
│  │
│  ├─ db/
│  │  ├─ models.py
│  │  └─ session.py
│  │
│  └─ main.py
│
├─ migrations/
├─ Dockerfile
├─ alembic.ini
├─ pyproject.toml
└─ .env.example
```

---

## 5. 데이터베이스 설계

### 5.1 notices 테이블

```sql
CREATE TABLE notices (
  id SERIAL PRIMARY KEY,
  source TEXT,
  external_id TEXT,
  title TEXT,
  url TEXT UNIQUE,
  category TEXT,
  content TEXT,
  summary TEXT,
  published_at TIMESTAMP,
  crawled_at TIMESTAMP
);
```

### 5.2 guild_settings 테이블

```sql
CREATE TABLE guild_settings (
  guild_id BIGINT PRIMARY KEY,
  notify_channel_id BIGINT,
  notification_enabled BOOLEAN DEFAULT TRUE,
  language TEXT DEFAULT 'ko',
  timezone TEXT DEFAULT 'Asia/Seoul'
);
```

---

## 6. 주요 기능 설계

### 6.1 /공지

**설명**

* 최신 공지 5개 조회

**동작**

```
DB 조회 → 없으면 크롤링 → 결과 반환
```

---

### 6.2 /요약

**설명**

* 최신 공지 또는 패치노트 요약

**동작**

```
공지 조회 → summary 없으면 OpenAI 호출 → DB 저장 → 반환
```

---

### 6.3 /질문

**설명**

* 자연어 기반 질의응답

**동작**

```
질문 입력
→ DB에서 관련 공지 검색
→ 관련 문서만 AI에 전달
→ 답변 생성 (출처 포함)
```

---

### 6.4 자동 공지 알림

**설명**

* 10분마다 공지 확인 후 새 글 알림

**동작**

```
Scheduler 실행
→ 크롤링
→ DB 비교
→ 신규 공지 발견
→ Discord 채널 전송
→ DB 저장
```

---

## 7. 크롤러 설계

### 대상

* 메이플랜드 공지사항 페이지

### 처리 흐름

```
HTML 요청
→ 공지 리스트 파싱
→ 상세 페이지 요청
→ title / content / date 추출
```

### 중복 방지

```python
if url not in DB:
    save()
    notify()
```

---

## 8. AI 처리 전략

### 요약

* 긴 공지 → 3~5줄 요약

### 질문 응답

* DB 기반 응답 (근거 포함)

### 비용 최적화

* summary 캐싱
* 동일 요청 최소화

---

## 9. 배포 전략

### 개발 환경

```
로컬 PC + Docker Compose
```

### 운영 환경

* Oracle Cloud
* AWS
* Fly.io

### Docker 구성 예시

```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file: .env
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: mapleland
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
```

---

## 10. 환경 변수

```
DISCORD_TOKEN=your_token
OPENAI_API_KEY=your_key
DATABASE_URL=postgresql://user:password@db:5432/mapleland
```

---

## 11. 개발 로드맵

### v0.1 (MVP)

* /공지
* 자동 공지 알림
* DB 저장

### v0.2

* /요약
* OpenAI 연동

### v0.3

* /질문
* 검색 기능

### v1.0

* 다중 서버 지원
* 설정 관리

---

## 12. 주의사항

* 게임 자동화/매크로 기능 금지
* Discord rate limit 고려
* 크롤링 구조 변경 대응 필요
* API 비용 관리

---

## 13. 향후 확장

* 벡터 검색 (semantic search)
* 웹 대시보드
* 사용자 맞춤 알림
* 커뮤니티 데이터 연동

---

## 14. 실행 목표 (첫 구현)

```
메이플랜드 공지사항 페이지를 10분마다 확인해서
새 공지가 있으면 디스코드 채널에 전송하는 봇 구현
```

---

END
