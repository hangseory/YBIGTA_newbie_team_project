# YBIGTA Review MCP Server

과제 명세의 `Tool → Service → Repository → DB` 구조에 맞춘 카카오맵 리뷰 조회용 MCP 서버입니다.

## 구조

```text
mcp_server/
├── tools/
│   ├── search.py
│   ├── aggregation.py
│   └── latest.py
├── services/
│   └── review_service.py
├── repositories/
│   └── review_repository.py
├── server.py
├── Dockerfile
└── requirements.txt
```

## Tool 3개

- `get_latest_reviews(limit=5)` : 최신 리뷰 조회, 최대 20행
- `search_reviews(keyword, start_date, end_date, limit=5)` : 키워드 + 기간 검색, 최대 20행
- `aggregate_ratings(start_date, end_date)` : 평균 별점/리뷰 수/최소·최대/별점 분포 집계

Raw SQL Tool은 없고 모든 SQL은 Repository에서 parameterized query로 실행합니다. MCP DB 계정은 `mcp_user`(SELECT only)를 사용합니다.

## 1. 로컬 실행

```bash
cd mcp_server
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```

`.env`에 RDS 접속정보와 `MCP_AUTH_TOKEN`을 넣고:

```bash
python server.py
```

- 표준 MCP endpoint: `http://localhost:8000/mcp`
- health: `http://localhost:8000/health`

## 2. MCP Inspector

Inspector에서 transport를 **Streamable HTTP**로 선택하고 URL을 아래처럼 사용합니다.

```text
http://localhost:8000/mcp
```

Authorization header에는:

```text
Bearer <MCP_AUTH_TOKEN>
```

을 넣습니다. Tool 목록과 실제 Tool 호출을 캡처하면 `aws/mcp_tools.png`, `aws/mcp_call.png` 증빙으로 사용할 수 있습니다.

## 3. 기존 Next.js 코드와 연결

현재 팀의 `web/app/api/chat/route.ts`는 다음 endpoint를 POST로 호출하도록 되어 있으므로 그대로 연결됩니다.

```text
/tools/get_latest_reviews
/tools/search_reviews
/tools/aggregate_ratings
```

`web/.env`:

```env
MCP_SERVER_URL=http://<EC2 또는 Nginx 주소>
MCP_AUTH_TOKEN=<동일한 토큰>
```

> `/mcp`가 실제 표준 MCP endpoint이고, `/tools/*`는 현재 팀의 Next.js 코드와 바로 붙이기 위한 호환 endpoint입니다.

## 4. Docker

```bash
docker build -t ybigta-mcp .
docker run -d \
  --name ybigta-mcp \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  ybigta-mcp
```

`127.0.0.1:8000:8000`으로 바인딩하면 8000번이 인터넷 전체에 직접 공개되지 않습니다. 외부 요청은 Nginx 80/443을 거쳐 전달하세요.

## 5. EC2/Nginx 배포 시

`.env`의 `MCP_ALLOWED_HOSTS`에 Nginx가 전달하는 Host를 넣어야 합니다.

예:

```env
MCP_ALLOWED_HOSTS=mcp.example.com,mcp.example.com:*,localhost,localhost:8000
```

EC2 Public IP를 Host로 쓴다면 해당 IP와 `IP:*`도 추가합니다.

## 보안 체크

- RDS: Private Subnet / Publicly accessible = No
- RDS SG: `3306 <- mcp-sg`만 허용
- MCP DB 사용자: `mcp_user`, SELECT only
- MCP: Bearer token 필수
- Raw SQL Tool 없음
- 조회 최대 20행
- 날짜/keyword/limit validation
- DB 연결/조회 timeout 적용
- Docker 8000 포트는 localhost에만 bind하고 Nginx를 통해 외부 접근

## 팀 통합 전에 확인

필요한 RDS/EC2 값과 Web 담당자와 공유해야 하는 값은 `TEAM_INFO_NEEDED.md`를 먼저 확인하세요.

현재 팀의 Next.js `route.ts`는 `/tools/*` 호환 endpoint를 호출하므로 바로 연결할 수 있습니다. 다만 과제의 "Agent → MCP Tool"을 가장 명확하게 증빙하려면 최종적으로 Next.js 서버에서 공식 MCP Client로 `/mcp`를 호출하는 방식이 가장 안전합니다.
