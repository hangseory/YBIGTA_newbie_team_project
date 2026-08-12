import {
  GoogleGenerativeAI,
  FunctionDeclarationsTool,
  SchemaType,
} from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");

// ============================================================
// MCP Tool 정의 (Gemini에게 "이런 도구를 쓸 수 있어"라고 알려주는 스펙)
// 나중에 실제 MCP 서버가 준비되면 이 스펙은 그대로 두고
// 아래 callMCPTool() 함수 내부만 실제 fetch 호출로 바꾸면 됩니다.
// ============================================================
const tools: FunctionDeclarationsTool[] = [
  {
    functionDeclarations: [
      {
        name: "get_latest_reviews",
        description: "가장 최근에 작성된 카카오맵 리뷰 목록을 가져온다.",
        parameters: {
          type: SchemaType.OBJECT,
          properties: {
            limit: {
              type: SchemaType.NUMBER,
              description: "가져올 리뷰 개수 (기본 5, 최대 20)",
            },
          },
        },
      },
      {
        name: "search_reviews",
        description:
          "특정 키워드가 포함된 리뷰를 기간 필터와 함께 검색한다.",
        parameters: {
          type: SchemaType.OBJECT,
          properties: {
            keyword: {
              type: SchemaType.STRING,
              description: "검색할 키워드 (예: '친절', '맛있어요')",
            },
            start_date: {
              type: SchemaType.STRING,
              description: "검색 시작일 (YYYY-MM-DD), 없으면 전체 기간",
            },
            end_date: {
              type: SchemaType.STRING,
              description: "검색 종료일 (YYYY-MM-DD), 없으면 전체 기간",
            },
            limit: {
              type: SchemaType.NUMBER,
              description: "가져올 리뷰 개수 (기본 5, 최대 20)",
            },
          },
          required: ["keyword"],
        },
      },
      {
        name: "aggregate_ratings",
        description:
          "특정 기간의 평균 별점, 리뷰 개수 등 통계를 집계한다. '이번 주 평균 별점', '지난달 대비' 같은 질문에 사용.",
        parameters: {
          type: SchemaType.OBJECT,
          properties: {
            start_date: {
              type: SchemaType.STRING,
              description: "집계 시작일 (YYYY-MM-DD)",
            },
            end_date: {
              type: SchemaType.STRING,
              description: "집계 종료일 (YYYY-MM-DD)",
            },
          },
          required: ["start_date", "end_date"],
        },
      },
    ],
  },
];

// ============================================================
// MCP 서버 호출 함수
// MCP_SERVER_URL이 설정되어 있으면 실제 MCP 서버를 호출하고,
// 없으면 개발 중 테스트를 위한 mock 데이터를 반환한다.
// ============================================================
async function callMCPTool(toolName: string, args: any) {
  const MCP_URL = process.env.MCP_SERVER_URL;
  const MCP_TOKEN = process.env.MCP_AUTH_TOKEN;

  if (MCP_URL) {
    const res = await fetch(`${MCP_URL}/tools/${toolName}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${MCP_TOKEN}`,
      },
      body: JSON.stringify(args),
    });
    if (!res.ok) {
      throw new Error(`MCP 서버 오류: ${res.status}`);
    }
    return await res.json();
  }

  // ---------- MCP 서버 준비 전 임시 Mock 데이터 ----------
  if (toolName === "get_latest_reviews") {
    return {
      reviews: [
        {
          rating: 5,
          review_date: "2026-08-12",
          review: "친절하고 음식이 맛있어요! (mock 데이터)",
        },
        {
          rating: 4,
          review_date: "2026-08-11",
          review: "분위기 좋고 재방문 의사 있습니다. (mock 데이터)",
        },
      ],
    };
  }

  if (toolName === "search_reviews") {
    return {
      keyword: args.keyword,
      reviews: [
        {
          rating: 5,
          review_date: "2026-08-10",
          review: `"${args.keyword}" 관련 mock 리뷰입니다.`,
        },
      ],
    };
  }

  if (toolName === "aggregate_ratings") {
    return {
      start_date: args.start_date,
      end_date: args.end_date,
      average_rating: 4.3,
      review_count: 27,
      note: "mock 데이터입니다. 실제 MCP 서버 연결 전 임시 값.",
    };
  }

  return { error: "알 수 없는 tool" };
}

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();

    if (!message) {
      return NextResponse.json(
        { error: "message가 필요합니다." },
        { status: 400 }
      );
    }

    const model = genAI.getGenerativeModel({
      model: "gemini-flash-latest",
      tools,
    });

    const chat = model.startChat();
    let result = await chat.sendMessage(message);

    const calledTools: string[] = [];
    const MAX_TURNS = 5; // 무한루프 방지 안전장치
    let turns = 0;

    // Gemini가 함수 호출을 계속 요청하는 동안 반복 처리
    while (turns < MAX_TURNS) {
      const call = result.response.functionCalls()?.[0];

      if (!call) {
        break;
      }

      calledTools.push(call.name);
      const toolResult = await callMCPTool(call.name, call.args);

      result = await chat.sendMessage(
        JSON.stringify([
          {
            functionResponse: {
              name: call.name,
              response: toolResult,
            },
          },
        ])
      );

      turns++;
    }

    const finalText = result.response.text();

    return NextResponse.json({
      reply:
        finalText ||
        "죄송해요, 답변 생성에 실패했어요. 다시 질문해주세요.",
      debug_tools_called: calledTools,
    });
  } catch (error: any) {
    console.error("Chat API error:", error?.message);
    return NextResponse.json(
      { error: "서버 오류가 발생했습니다." },
      { status: 500 }
    );
  }
}