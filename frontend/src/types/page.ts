/** Page types for multi-page projects. */

export interface Page {
  id: string;
  slug: string;
  title: string;
  html: string;
  js?: string;
  metadata: Record<string, unknown>;
  is_home: boolean;
  display_order: number;
  created_at: string;
}

export interface PageCreate {
  slug: string;
  title: string;
  html: string;
  js?: string;
  metadata?: Record<string, unknown>;
  is_home?: boolean;
}

export interface PageUpdate {
  slug?: string;
  title?: string;
  html?: string;
  js?: string;
  metadata?: Record<string, unknown>;
  display_order?: number;
}
