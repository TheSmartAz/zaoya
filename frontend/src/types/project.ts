import { Version } from './version';
import type { Page, DraftResponse } from './page';
import type { DesignSystem, NavigationConfig } from './design';

/** Project types */
export type ProjectStatus = 'draft' | 'published';

/** Project model */
export interface Project {
  id: string;
  name: string;
  templateId: string;
  templateInputs: Record<string, string>;
  currentVersion: Version | null;
  isGuest: boolean;
  userId?: string;
  status: ProjectStatus;
  publicId?: string;
  publishedUrl?: string;
  notification_email?: string;
  notification_enabled?: boolean;
  createdAt: number;
  updatedAt: number;
  // Multi-page additions
  currentDraftId?: string;
  publishedSnapshotId?: string;
  slug?: string;
  pages?: Page[];
  design_system?: DesignSystem;
  navigation?: NavigationConfig;
}

/** Project creation input */
export interface CreateProjectInput {
  name: string;
  templateId: string;
  templateInputs: Record<string, string>;
}

/** Project store state */
export interface ProjectState {
  projects: Project[];
  currentProjectId: string | null;

  // Multi-page state
  currentDraft: DraftResponse | null;
  pages: Page[];

  createGuestProject: (name: string, templateId: string, templateInputs: Record<string, string>) => Project;
  setCurrentProject: (projectId: string) => void;
  updateProject: (projectId: string, updates: Partial<Project>) => void;
  convertToUserProject: (projectId: string) => Promise<Project>;
  deleteProject: (projectId: string) => void;
  getProject: (projectId: string) => Project | undefined;
  getCurrentProject: () => Project | null;

  // Multi-page actions
  loadDraft: (projectId: string) => Promise<DraftResponse>;
  updateDesignSystem: (projectId: string, designSystem: DesignSystem) => Promise<void>;
  updateNavigation: (projectId: string, navigation: NavigationConfig) => Promise<void>;
  addPage: (projectId: string, page: import('./page').PageCreate) => Promise<Page>;
  updatePage: (projectId: string, pageId: string, updates: Partial<import('./page').PageCreate>) => Promise<Page>;
  deletePage: (projectId: string, pageId: string) => Promise<void>;
  reorderPages: (projectId: string, pageIds: string[]) => Promise<void>;
}
