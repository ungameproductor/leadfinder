export type Category = {
  id: string;
  label: string;
  search_query: string;
  google_type: string | null;
};

export type AppConfig = {
  location: {
    city: string;
    country: string;
    postal_code: string | null;
    latitude: number | null;
    longitude: number | null;
    radius_km: number;
  };
  provider: string;
  has_google_key: boolean;
  categories: Category[];
  max_results_per_query: number;
};

export type Lead = {
  id: string;
  source_provider: string;
  source_external_id: string | null;
  name: string;
  category: string | null;
  address: string | null;
  city: string | null;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  phone: string | null;
  website: string | null;
  public_email: string | null;
  email_source_url: string | null;
  website_status: string;
  website_quality_score: number | null;
  website_quality_evidence: string[];
  email_status: string;
  lead_score: number;
  priority: string;
  suggested_service: string | null;
  notes: string | null;
  scoring_evidence: string[];
  match_confidence: number;
  phase_status: string;
  first_seen_at: string | null;
  last_checked_at: string | null;
  manual_status: string;
  contact_status: string;
  quality_data_insufficient: boolean;
  is_new?: boolean | null;
};

export type LeadFacets = {
  cities: string[];
  categories: string[];
  runs: {
    id: string;
    city: string | null;
    status: string;
    started_at: string | null;
    results_count: number;
    new_count: number;
  }[];
};

export type Stats = {
  total: number;
  priority_a: number;
  priority_b: number;
  priority_c: number;
  no_website: number;
  problematic_sites: number;
  emails_found: number;
  confirmed: number;
  discarded: number;
  do_not_contact: number;
};

export type SearchRun = {
  id: string;
  status: string;
  results_count: number;
  processed_count: number;
  errors: string[];
  api_usage: Record<string, unknown>;
  message: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  config: () => request<AppConfig>("/api/config/categories"),
  stats: () => request<Stats>("/api/stats"),
  facets: () => request<LeadFacets>("/api/leads/facets"),
  leads: (params: Record<string, string | undefined>) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v) q.set(k, v);
    });
    return request<{ total: number; items: Lead[] }>(`/api/leads?${q.toString()}`);
  },
  lead: (id: string) => request<Lead>(`/api/leads/${id}`),
  patchLead: (id: string, body: Record<string, string>) =>
    request<Lead>(`/api/leads/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  verifyLead: (id: string) => request<SearchRun>(`/api/leads/${id}/verify`, { method: "POST" }),
  startSearch: (body: Record<string, unknown>) =>
    request<SearchRun>("/api/search", { method: "POST", body: JSON.stringify(body) }),
  getSearch: (id: string) => request<SearchRun>(`/api/search/${id}`),
  exportCsvUrl: (params: Record<string, string | undefined>) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v) q.set(k, v);
    });
    return `/api/export/csv?${q.toString()}`;
  },
};
