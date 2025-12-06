const API_BASE = (import.meta.env.PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export type SlideLibraryMetadata = {
  slide_id: string;
  file_hash: string;
  description: string;
  preview?: string | null;
  source_presentation: string;
  slide_index: number;
  updated_at?: string;
  tags?: string[];
  element_count?: number;
};

type SlideIngestResponse = { count: number; slides: SlideLibraryMetadata[] };

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: unknown = text;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // fall back to raw text
  }

  if (!response.ok) {
    const message =
      typeof data === "string"
        ? data
        : (data as any)?.detail ?? (data as any)?.error ?? `Request failed (${response.status})`;
    throw new Error(message || "Request failed");
  }

  return data as T;
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, init);
  return parseResponse<T>(response);
}

export async function searchSlides(query: string): Promise<SlideLibraryMetadata[]> {
  return request<SlideLibraryMetadata[]>("/slides/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      limit: 20,
      retrieval_limit: 20,
      return_scores: false,
    }),
  });
}

export async function listSlides(params: { skip?: number; limit?: number } = {}): Promise<{
  count: number;
  items: SlideLibraryMetadata[];
}> {
  const searchParams = new URLSearchParams();
  if (params.skip) searchParams.set("skip", String(params.skip));
  if (params.limit) searchParams.set("limit", String(params.limit));

  return request(`/slides${searchParams.toString() ? `?${searchParams}` : ""}`, {
    method: "GET",
  });
}

export function slideDownloadUrl(slideId: string) {
  return `${API_BASE}/slides/${slideId}/download`;
}

export function slidePreviewUrl(slideId: string) {
  return `${API_BASE}/slides/${slideId}/preview`;
}

export async function ingestSlide(file: File): Promise<SlideIngestResponse> {
  const form = new FormData();
  form.append("file", file);

  return request<SlideIngestResponse>("/slides/ingest", {
    method: "POST",
    body: form,
  });
}

export async function composeSlides({
  userContext,
  userPrompt,
  numSlides,
  outputDir = "output",
}: {
  userContext: string;
  userPrompt?: string;
  numSlides?: number | null;
  outputDir?: string;
}): Promise<Record<string, string>> {
  return request<Record<string, string>>("/generation/compose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_context: userContext,
      user_prompt: userPrompt ?? userContext,
      num_slides: numSlides ?? null,
      output_dir: outputDir,
    }),
  });
}

export async function generateSlides({
  template,
  userInput,
  documents = "",
  outputDir = "output",
}: {
  template: File;
  userInput: string;
  documents?: string;
  outputDir?: string;
}): Promise<Record<string, string>> {
  const form = new FormData();
  form.append(
    "payload",
    JSON.stringify({
      user_input: userInput,
      documents,
      output_dir: outputDir,
    })
  );
  form.append("template", template);

  return request<Record<string, string>>("/generation/generate", {
    method: "POST",
    body: form,
  });
}

