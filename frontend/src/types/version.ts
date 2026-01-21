/** Version change type */
export type ChangeType = 'initial' | 'refinement' | 'quick_action' | 'restore';

/** Version metadata */
export interface VersionMetadata {
  prompt: string;
  timestamp: number;
  changeType: ChangeType;
}

/** Code snapshot version */
export interface Version {
  id: string;
  projectId: string;
  number: number;
  html: string;
  js: string | null;
  metadata: VersionMetadata;
}

/** Version diff for comparisons */
export interface VersionDiff {
  additions: string[];
  removals: string[];
  summary: string;
}
