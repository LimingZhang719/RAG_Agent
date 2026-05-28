export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}
