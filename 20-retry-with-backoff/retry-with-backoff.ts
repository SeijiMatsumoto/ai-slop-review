// AI-generated PR — review this code
// Description: Added retry wrapper with exponential backoff for API calls

interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  timeoutMs: number;
  onRetry?: (attempt: number, error: Error) => void;
}

interface RequestConfig {
  url: string;
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  headers?: Record<string, string>;
  body?: unknown;
}

interface ApiResponse<T = unknown> {
  status: number;
  data: T;
  headers: Record<string, string>;
}

const DEFAULT_OPTIONS: RetryOptions = {
  maxRetries: 3,
  baseDelayMs: 1000,
  timeoutMs: 10000,
};

function calculateDelay(attempt: number, baseDelayMs: number): number {
  return baseDelayMs * Math.pow(2, attempt);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function makeRequest<T>(
  config: RequestConfig,
  timeoutMs: number
): Promise<ApiResponse<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const fetchOptions: RequestInit = {
      method: config.method,
      headers: {
        "Content-Type": "application/json",
        ...config.headers,
      },
      signal: controller.signal,
    };

    if (config.body && ["POST", "PUT", "PATCH", "DELETE"].includes(config.method)) {
      fetchOptions.body = JSON.stringify(config.body);
    }

    const response = await fetch(config.url, fetchOptions);

    const responseHeaders: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });

    const data = (await response.json()) as T;

    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: Request failed`);
      (error as any).status = response.status;
      (error as any).response = data;
      throw error;
    }

    return {
      status: response.status,
      data,
      headers: responseHeaders,
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

async function fetchWithRetry<T>(
  config: RequestConfig,
  options: Partial<RetryOptions> = {}
): Promise<ApiResponse<T>> {
  const opts: RetryOptions = { ...DEFAULT_OPTIONS, ...options };
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      const response = await makeRequest<T>(config, opts.timeoutMs);
      return response;
    } catch (error) {
      lastError = error as Error;

      if (attempt < opts.maxRetries) {
        const delay = calculateDelay(attempt, opts.baseDelayMs);

        if (opts.onRetry) {
          opts.onRetry(attempt + 1, lastError);
        }

        console.warn(
          `Request to ${config.url} failed (attempt ${attempt + 1}/${opts.maxRetries + 1}). ` +
            `Retrying in ${delay}ms...`,
          { error: lastError.message }
        );

        await sleep(delay);
      }
    }
  }

  throw new Error(`Max retries (${opts.maxRetries}) exceeded for ${config.url}`);
}

// Convenience methods
async function get<T>(
  url: string,
  options?: Partial<RetryOptions>
): Promise<ApiResponse<T>> {
  return fetchWithRetry<T>({ url, method: "GET" }, options);
}

async function post<T>(
  url: string,
  body: unknown,
  options?: Partial<RetryOptions>
): Promise<ApiResponse<T>> {
  return fetchWithRetry<T>({ url, method: "POST", body }, options);
}

async function put<T>(
  url: string,
  body: unknown,
  options?: Partial<RetryOptions>
): Promise<ApiResponse<T>> {
  return fetchWithRetry<T>({ url, method: "PUT", body }, options);
}

async function del<T>(
  url: string,
  options?: Partial<RetryOptions>
): Promise<ApiResponse<T>> {
  return fetchWithRetry<T>({ url, method: "DELETE" }, options);
}

// Batch request utility
async function batchRequests<T>(
  configs: RequestConfig[],
  options?: Partial<RetryOptions>
): Promise<ApiResponse<T>[]> {
  const results = await Promise.all(
    configs.map((config) => fetchWithRetry<T>(config, options))
  );
  return results;
}

export {
  fetchWithRetry,
  makeRequest,
  get,
  post,
  put,
  del,
  batchRequests,
  RetryOptions,
  RequestConfig,
  ApiResponse,
};
