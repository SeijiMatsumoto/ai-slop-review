// AI-generated PR — review this code
// Description: "Added streaming chat endpoint using Vercel AI SDK with tool calling"

import { streamText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";
import { NextRequest } from "next/server";
import { db } from "@/lib/db";

const weatherTool = tool({
  description: "Get current weather for a location",
  parameters: z.object({
    location: z.string().describe("City name"),
    units: z.enum(["celsius", "fahrenheit"]).default("celsius"),
  }),
  execute: async ({ location, units }) => {
    const res = await fetch(
      `https://api.weather.co/v1/current?q=${location}&units=${units}`
    );
    return res.json();
  },
});

const searchTool = tool({
  description: "Search the knowledge base",
  parameters: z.object({
    query: z.string(),
    limit: z.number().default(5),
  }),
  execute: async ({ query, limit }) => {
    const results = await db.document.findMany({
      where: {
        content: { search: query },
      },
      take: limit,
    });
    return results;
  },
});

export async function POST(req: NextRequest) {
  const { messages, model, temperature } = await req.json();

  const result = streamText({
    model: openai(model || "gpt-4o"),
    messages,
    temperature: temperature || 0.7,
    tools: { weather: weatherTool, search: searchTool },
    maxTokens: 4096,
    maxRetries: 5,
    onToken: (token) => {
      console.log("Token:", token);
    },
    onFinish: async ({ text, usage, finishReason }) => {
      await db.chatLog.create({
        data: {
          messages: JSON.stringify(messages),
          response: text,
          model: model || "gpt-4o",
          tokens: usage.totalTokens,
          finishReason,
        },
      });
    },
    smoothStream: { chunking: "word" },
    abortSignal: req.signal,
  });

  return result.toDataStreamResponse({
    sendUsage: true,
    sendReasoning: true,
    getErrorMessage: (error) => {
      return `Chat error: ${error.message}. Stack: ${error.stack}`;
    },
  });
}

export async function GET(req: NextRequest) {
  const sessionId = req.nextUrl.searchParams.get("session");

  const history = await db.chatLog.findMany({
    where: { sessionId },
    orderBy: { createdAt: "desc" },
    take: 50,
  });

  return Response.json(history);
}
