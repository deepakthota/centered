export type DailyAction = {
  id: string;
  local_date: string;
  decision: {
    action: { key: string; title: string; minutes: number } | null;
    reason: string;
    evidence_status: string;
    input_source: string;
  };
  feedback: { status: 'completed' | 'skipped'; helpful: boolean | null } | null;
};

export async function request<T>(base: string, token: string, path: string, body?: object, method = 'GET'): Promise<T> {
  const parsed = new URL(base);
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error('Enter an HTTP(S) development API address without credentials or query parameters.');
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`${base.replace(/\/$/, '')}${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!response.ok) {
      // Do not log request bodies, health inputs or credentials.
      if (response.status === 401) throw new Error('Check your development token.');
      if (response.status === 409) throw new Error('An action or feedback already exists. Refresh history to see it.');
      throw new Error(`Request failed (${response.status}). Check your inputs and API connection.`);
    }
    return await response.json() as T;
  } finally {
    clearTimeout(timer);
  }
}
