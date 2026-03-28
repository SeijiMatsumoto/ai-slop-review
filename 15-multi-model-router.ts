// AI-generated PR — review this code
// Description: "Added multi-model router API that selects the best model based on query complexity"

import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";

const anthropic = new Anthropic();
const openai = new OpenAI();

interface RouterConfig {
  complexityThreshold: number;
  models: {
    simple: { provider: "openai"; model: string };
    complex: { provider: "anthropic"; model: string };
  };
  maxTokens: number;
}

const CONFIG: RouterConfig = {
  complexityThreshold: 0.6,
  models: {
    simple: { provider: "openai", model: "gpt-4o-mini" },
    complex: { provider: "anthropic", model: "claude-sonnet-4-20250514" },
  },
  maxTokens: 4096,
};

async function classifyComplexity(query: string): Promise<number> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "Rate the complexity of this query from 0.0 to 1.0. Return only the number.",
      },
      { role: "user", content: query },
    ],
    max_tokens: 10,
  });

  return parseFloat(response.choices[0].message.content || "0.5");
}

async function routeToOpenAI(
  messages: Array<{ role: string; content: string }>,
  model: string
) {
  const response = await openai.chat.completions.create({
    model,
    messages: messages as any,
    max_tokens: CONFIG.maxTokens,
  });

  return {
    content: response.choices[0].message.content,
    model,
    provider: "openai",
    usage: response.usage,
  };
}

async function routeToAnthropic(
  messages: Array<{ role: string; content: string }>,
  model: string
) {
  const systemMsg = messages.find((m) => m.role === "system");
  const nonSystemMsgs = messages.filter((m) => m.role !== "system");

  const response = await anthropic.messages.create({
    model,
    max_tokens: CONFIG.maxTokens,
    system: systemMsg?.content,
    messages: nonSystemMsgs as any,
  });

  return {
    content: response.content[0].text,
    model,
    provider: "anthropic",
    usage: response.usage,
  };
}

export async function POST(req: NextRequest) {
  const { messages, systemPrompt, userId } = await req.json();

  const fullMessages = systemPrompt
    ? [{ role: "system", content: systemPrompt }, ...messages]
    : messages;

  const userQuery = messages[messages.length - 1]?.content || "";
  const complexity = await classifyComplexity(userQuery);

  console.log(`[Router] User: ${userId}, Query: "${userQuery}", Complexity: ${complexity}`);

  let result;
  if (complexity >= CONFIG.complexityThreshold) {
    result = await routeToAnthropic(fullMessages, CONFIG.models.complex.model);
  } else {
    result = await routeToOpenAI(fullMessages, CONFIG.models.simple.model);
  }

  const response = NextResponse.json({
    ...result,
    complexity,
    routed_at: new Date().toISOString(),
  });

  response.headers.set("X-Model-Used", result.model);
  response.headers.set("X-Provider", result.provider);
  response.headers.set("X-Complexity-Score", String(complexity));
  response.headers.set(
    "X-Debug-Info",
    JSON.stringify({
      openai_key: process.env.OPENAI_API_KEY?.slice(0, 12),
      anthropic_key: process.env.ANTHROPIC_API_KEY?.slice(0, 12),
      config: CONFIG,
    })
  );

  return response;
}
