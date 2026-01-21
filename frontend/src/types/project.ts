import { Version } from './version';

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

  createGuestProject: (name: string, templateId: string, templateInputs: Record<string, string>) => Project;
  setCurrentProject: (projectId: string) => void;
  updateProject: (projectId: string, updates: Partial<Project>) => void;
  convertToUserProject: (projectId: string) => Promise<Project>;
  deleteProject: (projectId: string) => void;
  getProject: (projectId: string) => Project | undefined;
  getCurrentProject: () => Project | null;
}
