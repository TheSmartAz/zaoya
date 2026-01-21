/** Design system types for multi-page projects. */

export interface DesignSystem {
  colors: Record<string, string>;
  typography: Record<string, string>;
  spacing: Record<string, string>;
  components?: Record<string, unknown>;
}

export interface NavigationConfig {
  header: {
    enabled?: boolean;
    logo?: string;
    title?: string;
    links?: Array<{ title: string; slug: string }>;
  };
  footer: {
    enabled?: boolean;
    text?: string;
    links?: Array<{ title: string; url: string }>;
  };
}

export interface DraftResponse {
  id: string;
  project_id: string;
  version_number: number;
  summary?: string;
  design_system: DesignSystem;
  navigation: NavigationConfig;
  created_at: string;
}

export interface SnapshotResponse {
  id: string;
  project_id: string;
  version_number: number;
  summary?: string;
  design_system: DesignSystem;
  navigation: NavigationConfig;
  is_draft: boolean;
  created_at: string;
}
