const BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

export interface AskRequest {
  question: string;
  user_id: string;
}

export interface AskResponse {
  answer: string;
  approved: boolean;
  used_agents: string[];
  trace: unknown; // keep flexible unless you know exact backend shape
}

export async function askQuestion(req: AskRequest): Promise<AskResponse> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 60000);

  try {
    const response = await fetch(`${BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(req),
      signal: controller.signal,
    });

    const contentType = response.headers.get("content-type") || "";

    if (!response.ok) {
      let errorMessage = `Server error: ${response.status} ${response.statusText}`;

      if (contentType.includes("application/json")) {
        const errorData = await response.json().catch(() => null);
        if (errorData?.detail) {
          errorMessage = String(errorData.detail);
        } else if (errorData?.message) {
          errorMessage = String(errorData.message);
        }
      } else {
        const errorText = await response.text().catch(() => "");
        if (errorText) {
          errorMessage = errorText;
        }
      }

      throw new Error(errorMessage);
    }

    if (!contentType.includes("application/json")) {
      throw new Error("Invalid response from server: expected JSON.");
    }

    const data: AskResponse = await response.json();
    return data;
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out after 60 seconds.");
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error("Unknown error occurred while calling /ask.");
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE_URL}/health`, {
      method: "GET",
    });
    return response.ok;
  } catch {
    return false;
  }
}