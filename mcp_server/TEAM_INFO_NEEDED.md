# 팀원에게 받아야 하는 값

MCP 서버를 실제 AWS/RDS에 붙일 때 필요한 값만 정리한 문서입니다.

## AWS / RDS 담당자에게 받을 것

아래 5개는 MCP 서버의 `.env`에 들어갑니다.

```env
MYSQL_HOST=<RDS endpoint>
MYSQL_PORT=3306
MYSQL_DB=reviewdb
MCP_DB_USER=mcp_user
MCP_DB_PASSWORD=<mcp_user 비밀번호>
```

추가로 확인할 것:

- RDS가 **Private Subnet**에 있는지
- RDS `Publicly accessible = No`인지
- RDS Security Group의 3306 inbound source가 `0.0.0.0/0`이 아니라 **MCP EC2의 Security Group(mcp-sg)** 인지
- MCP를 올릴 EC2의 Public DNS / 도메인 / Public IP가 무엇인지
  - 이 값은 `MCP_ALLOWED_HOSTS`와 Nginx `server_name` 설정에 필요

> RDS가 Private Subnet이면 보통 로컬 PC에서 RDS로 직접 접속할 수 없습니다. 최종 연결 테스트는 같은 VPC의 MCP EC2에서 하는 것이 가장 간단합니다.

## Web / Next.js 담당자와 맞출 것

`MCP_AUTH_TOKEN`은 외부 서비스에서 발급받는 API Key가 아닙니다.
우리 팀이 긴 랜덤 문자열을 하나 만들어 MCP와 Vercel 양쪽에 똑같이 넣으면 됩니다.

MCP 서버 쪽:

```env
MCP_AUTH_TOKEN=<같은 랜덤 토큰>
```

Web/Vercel 쪽:

```env
MCP_SERVER_URL=https://<MCP 주소>
MCP_AUTH_TOKEN=<같은 랜덤 토큰>
```

- `GEMINI_API_KEY`는 **Web 담당자가 Gemini 호출용으로 관리하는 값**이며 MCP 서버에는 필요 없습니다.
- 현재 collector는 카카오맵 페이지를 Selenium으로 크롤링하므로 **Kakao API Key는 필요하지 않습니다.**

## MCP 담당자가 팀원에게 주게 되는 값

배포가 끝나면 오히려 MCP 담당자가 Web 담당자에게 아래를 알려줘야 합니다.

```text
MCP 표준 endpoint: https://<MCP 주소>/mcp
MCP_AUTH_TOKEN: 팀에서 정한 동일 토큰
```

현재 팀의 `web/app/api/chat/route.ts`는 `/tools/<tool_name>` 호환 HTTP endpoint를 호출하도록 작성돼 있어 이 서버가 그대로 응답합니다.
다만 과제에서 **Agent가 실제 MCP Tool을 사용한다는 점을 엄격하게 확인한다면**, 최종 제출 전 Web 담당자가 공식 MCP TypeScript Client를 사용해 `/mcp`에 연결하고 `listTools` / `callTool`을 호출하도록 바꾸는 것을 권장합니다.
