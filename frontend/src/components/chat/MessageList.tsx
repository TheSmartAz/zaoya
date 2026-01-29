import { useEffect, useMemo, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { useBuildStore, useProjectStore, useVersionStore } from '@/stores'
import { QuickActionChip } from '@/components/composed'
import type {
  ChatMessage,
  BuildPlanCardData,
  LiveTaskMessage,
  InterviewCardData,
  PageCardData,
  ValidationCardData,
  ProductDocCardData,
  VersionCardData,
} from '@/types/chat'
import { TaskItem, AgentThinkingItem } from './TaskItem'
import { BuildPlanCard } from './cards/BuildPlanCard'
import { InterviewCard } from './cards/InterviewCard'
import { PageCard } from './cards/PageCard'
import { ValidationCard } from './cards/ValidationCard'
import { ProductDocCard } from './cards/ProductDocCard'
import { VersionSummaryCard } from './cards/VersionSummaryCard'

interface MessageListProps {
  messages: ChatMessage[]
  className?: string
}

export function MessageList({ messages, className }: MessageListProps) {
  const liveTasks = useBuildStore((state) => state.liveTasks)
  const approveBuildPlan = useBuildStore((state) => state.approveBuildPlan)
  const dismissBuildPlan = useBuildStore((state) => state.dismissBuildPlan)
  const retryBuildPage = useBuildStore((state) => state.retryBuildPage)
  const streamStatus = useBuildStore((state) => state.streamStatus)
  const streamError = useBuildStore((state) => state.streamError)
  const getVersionDetail = useVersionStore((state) => state.getVersionDetail)
  const pinVersion = useVersionStore((state) => state.pinVersion)
  const setActiveVersion = useVersionStore((state) => state.setActiveVersion)
  const createBranch = useVersionStore((state) => state.createBranch)
  const loadBranches = useVersionStore((state) => state.loadBranches)
  const loadVersions = useVersionStore((state) => state.loadVersions)
  const activeBranchId = useVersionStore((state) => state.activeBranchId)
  const {
    project,
    pages,
    currentPageId,
    productDoc,
    loadPages,
    setCurrentPage,
  } = useProjectStore((state) => ({
    project: state.project,
    pages: state.pages,
    currentPageId: state.currentPageId,
    productDoc: state.productDoc,
    loadPages: state.loadPages,
    setCurrentPage: state.setCurrentPage,
  }))
  const allItems = useMemo(
    () =>
      [...messages, ...liveTasks].sort(
        (a, b) => (a.timestamp || 0) - (b.timestamp || 0)
      ),
    [messages, liveTasks]
  )
  const bottomRef = useRef<HTMLDivElement>(null)
  const defaultPageId =
    currentPageId || pages.find((page) => page.is_home)?.id || pages[0]?.id

  const openPreview = (pageId?: string) => {
    window.dispatchEvent(
      new CustomEvent('open-preview', {
        detail: { pageId },
      })
    )
  }

  const openOverview = () => {
    window.dispatchEvent(new CustomEvent('open-overview'))
  }

  const openProductDoc = () => {
    window.dispatchEvent(new CustomEvent('open-product-doc'))
  }

  const handleViewPreview = (page: PageCardData) => {
    if (!page?.id) {
      openPreview()
      return
    }

    if (!pages.find((item) => item.id === page.id) && project?.id) {
      void loadPages(project.id, { preserveSelection: true }).then(() => {
        setCurrentPage(page.id)
      })
    } else {
      setCurrentPage(page.id)
    }

    openPreview(page.id)
  }

  const handleVersionPreview = async (data: VersionCardData) => {
    if (!project?.id) return
    const detail = await getVersionDetail(project.id, data.id)
    if (!detail || !detail.pages.length) return
    const page = detail.pages.find((item) => item.is_home) || detail.pages[0]
    const html = (page.content?.html as string | undefined) || ''
    const js = (page.content?.js as string | undefined) || ''
    setActiveVersion(data.id)
    window.dispatchEvent(
      new CustomEvent('open-version-preview', {
        detail: {
          versionId: data.id,
          pageId: page.id,
          pageName: page.name,
          pagePath: page.path,
          html,
          js,
        },
      })
    )
  }

  const handleVersionCode = (data: VersionCardData) => {
    setActiveVersion(data.id)
    window.dispatchEvent(new CustomEvent('open-code-view'))
  }

  const handleVersionPin = (data: VersionCardData) => {
    if (!project?.id) return
    void pinVersion(project.id, data.id, !data.is_pinned)
  }

  const handleVersionBranch = async (data: VersionCardData) => {
    if (!project?.id) return
    const name = window.prompt('Branch name')
    if (!name) return
    const branch = await createBranch(project.id, data.id, {
      name,
      label: name,
      set_active: true,
    })
    await loadBranches(project.id)
    await loadVersions(project.id, branch?.id || activeBranchId)
    await loadPages(project.id, { preserveSelection: false })
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [allItems.length])

  return (
    <ScrollArea className={cn('flex-1 px-4', className)}>
      <div className="py-4 space-y-4">
        {allItems.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <p className="text-lg font-medium">What do you want to create?</p>
            <p className="text-sm mt-1">
              Describe your page and I&apos;ll build it for you.
            </p>
          </div>
        ) : (
          allItems.map((item) => {
            if ('role' in item) {
              const message = item as ChatMessage
              return (
                <div
                  key={message.id}
                  className={cn(
                    'animate-slide-up',
                    message.role === 'user' ? 'flex justify-end' : ''
                  )}
                >
                  <div
                    className={cn(
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[85%]'
                        : 'text-foreground'
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              )
            }

            const task = item as LiveTaskMessage

            if (task.card) {
              switch (task.card.type) {
                case 'page':
                  return (
                    <PageCard
                      key={task.id}
                      page={task.card.data as PageCardData}
                      onViewPreview={() =>
                        handleViewPreview(task.card?.data as PageCardData)
                      }
                    />
                  )
                case 'validation':
                  return (
                    <ValidationCard
                      key={task.id}
                      {...(task.card.data as ValidationCardData)}
                      onRetry={
                        (task.card.data as ValidationCardData).page_id
                          ? () =>
                              retryBuildPage(
                                `page-${(task.card.data as ValidationCardData).page_id}`
                              )
                          : undefined
                      }
                    />
                  )
                case 'build_plan':
                  return (
                    <BuildPlanCard
                      key={task.id}
                      plan={task.card.data as BuildPlanCardData}
                      onApprove={
                        (task.card.data as BuildPlanCardData).approval_required
                          ? (pages) => approveBuildPlan(pages)
                          : undefined
                      }
                      onCancel={
                        (task.card.data as BuildPlanCardData).approval_required
                          ? () => dismissBuildPlan(task.id)
                          : undefined
                      }
                    />
                  )
                case 'interview':
                  return (
                    <InterviewCard
                      key={task.id}
                      interview={task.card.data as InterviewCardData}
                    />
                  )
                case 'product_doc_ready':
                  return (
                    <ProductDocCard
                      key={task.id}
                      data={task.card.data as ProductDocCardData}
                    />
                  )
                case 'version':
                  return (
                    <VersionSummaryCard
                      key={task.id}
                      data={task.card.data as VersionCardData}
                      onViewPreview={() =>
                        handleVersionPreview(task.card?.data as VersionCardData)
                      }
                      onViewCode={() =>
                        handleVersionCode(task.card?.data as VersionCardData)
                      }
                      onTogglePin={() =>
                        handleVersionPin(task.card?.data as VersionCardData)
                      }
                      onCreateBranch={() =>
                        handleVersionBranch(task.card?.data as VersionCardData)
                      }
                    />
                  )
                default:
                  return null
              }
            }

            if (task.type === 'agent_thinking') {
              return <AgentThinkingItem key={task.id} message={task.title} />
            }

            if (task.type === 'build_complete') {
              return (
                <div key={task.id} className="space-y-2">
                  <TaskItem title={task.title} status={task.status} />
                  <div className="flex flex-wrap gap-2 pl-6">
                    <QuickActionChip
                      label="View preview"
                      onClick={() => openPreview(defaultPageId)}
                    />
                    <QuickActionChip label="Page overview" onClick={openOverview} />
                    {productDoc && (
                      <QuickActionChip label="ProductDoc" onClick={openProductDoc} />
                    )}
                  </div>
                </div>
              )
            }

            return (
              <TaskItem
                key={task.id}
                title={task.title}
                status={task.status}
                onRetry={
                  task.status === 'failed' && task.id.startsWith('page-')
                    ? () => retryBuildPage(task.id)
                    : undefined
                }
              />
            )
          })
        )}
        {streamStatus === 'reconnecting' && (
          <div className="text-xs text-muted-foreground flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-yellow-400" />
            <span>{streamError || 'Reconnecting...'}</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}

export type { ChatMessage }
