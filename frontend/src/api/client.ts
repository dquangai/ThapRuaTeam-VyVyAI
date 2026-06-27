import type {
  FastCheckResponse,
  InvestigationRequest,
  InvestigationResponse,
} from "../types";

const DEFAULT_TIMEOUT_MS = 20_000;

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export interface ApiClientOptions {
  baseUrl?: string;
  timeoutMs?: number;
}

export class VyvyApiClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = trimTrailingSlash(
      options.baseUrl ?? import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
    );
    this.timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  }

  fastCheck(request: InvestigationRequest): Promise<FastCheckResponse> {
    return this.post<FastCheckResponse>("/api/v1/fast-check", request);
  }

  investigate(request: InvestigationRequest): Promise<InvestigationResponse> {
    return this.post<InvestigationResponse>("/api/v1/investigate", request);
  }

  private async post<ResponseT>(path: string, body: InvestigationRequest): Promise<ResponseT> {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      const payload: unknown = await readJsonSafely(response);
      if (!response.ok) {
        throw new ApiClientError(errorMessageFromPayload(payload), response.status);
      }
      return payload as ResponseT;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiClientError("Yêu cầu quá thời gian chờ. Vui lòng thử lại.", 408);
      }
      throw new ApiClientError(
        "Không thể kết nối backend. Kiểm tra server hoặc cấu hình VITE_API_BASE_URL.",
      );
    } finally {
      window.clearTimeout(timeoutId);
    }
  }
}

export const vyvyApiClient = new VyvyApiClient();

async function readJsonSafely(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function errorMessageFromPayload(payload: unknown): string {
  if (isRecord(payload)) {
    const error = payload.error;
    if (isRecord(error) && typeof error.message === "string") {
      return error.message;
    }
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return "Dữ liệu đầu vào chưa hợp lệ. Vui lòng kiểm tra độ dài và định dạng.";
    }
  }
  return "Backend trả về lỗi nhưng không có thông báo hợp lệ.";
}

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
