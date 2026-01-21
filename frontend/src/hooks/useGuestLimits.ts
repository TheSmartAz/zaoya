import { useProjectStore } from '@/stores/projectStore';
import { useAuthStore } from '@/stores/authStore';

const GUEST_PROJECT_LIMIT = 3;

export function useGuestLimits() {
  const projects = useProjectStore((s) => s.projects);
  const user = useAuthStore((s) => s.user);

  const guestProjects = projects.filter((p) => p.isGuest);
  const canCreateMore = user || guestProjects.length < GUEST_PROJECT_LIMIT;
  const remainingSlots = GUEST_PROJECT_LIMIT - guestProjects.length;
  const isAtLimit = !user && guestProjects.length >= GUEST_PROJECT_LIMIT;

  return {
    canCreateMore,
    remainingSlots,
    isGuest: !user,
    guestProjectCount: guestProjects.length,
    isAtLimit,
    GUEST_PROJECT_LIMIT,
  };
}
