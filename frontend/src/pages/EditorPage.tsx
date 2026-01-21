import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, History as HistoryIcon } from 'lucide-react';
import { useChatStream } from '@/hooks/useChatStream';
import { usePreviewMessages } from '@/hooks/usePreviewMessages';
import { useVersionStore } from '@/stores/versionStore';
import { useChatStore } from '@/stores/chatStore';
import { useProjectStore } from '@/stores/projectStore';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { PreviewPanel } from '@/components/preview/PreviewPanel';
import { PhoneFrame } from '@/components/preview/PhoneFrame';
import { VersionHistoryPanel } from '@/components/version/VersionHistoryPanel';
import { PublishButton } from '@/components/editor/PublishButton';
import { Template } from '@/types/template';
import { templates } from '@/data/templates';
import { extractCode } from '@/utils/codeExtractor';
import { processGeneration } from '@/utils/renderPipeline';

export function EditorPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  usePreviewMessages();
  const { messages, sendMessage } = useChatStream();
  const interviewAnswers = useChatStore((s) => s.interviewAnswers);
  const project = useProjectStore((s) => (projectId ? s.getProject(projectId) : null));
  const setCurrentProject = useProjectStore((s) => s.setCurrentProject);
  const setProjectId = useVersionStore((s) => s.setProjectId);
  const loadVersions = useVersionStore((s) => s.loadVersions);
  const createVersion = useVersionStore((s) => s.createVersion);
  const versions = useVersionStore((s) => s.versions);
  const currentVersionId = useVersionStore((s) => s.currentVersionId);

  const [template, setTemplate] = useState<Template | null>(null);
  const [templateInputs, setTemplateInputs] = useState<Record<string, string>>({});
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [lastProcessedMessageId, setLastProcessedMessageId] = useState<string | null>(null);
  const [lastValidationErrorId, setLastValidationErrorId] = useState<string | null>(null);

  const hasGenerated = versions.length > 0;
  const currentVersion = useMemo(
    () => versions.find((version) => version.id === currentVersionId) || null,
    [versions, currentVersionId]
  );

  const buildFallbackContext = () => ({
    template: template ? {
      id: template.id,
      name: template.name,
      systemPromptAddition: template.systemPromptAddition,
    } : null,
    templateInputs,
    interviewAnswers,
  });

  // Initialize project
  useEffect(() => {
    if (!projectId) {
      navigate('/create');
      return;
    }

    setCurrentProject(projectId);
    setProjectId(projectId);
    loadVersions(projectId);

    if (project) {
      const found = templates.find((t: Template) => t.id === project.templateId);
      if (found) {
        setTemplate(found);
        setTemplateInputs(project.templateInputs || {});
      }
    }
  }, [projectId, project, setCurrentProject, setProjectId, loadVersions, navigate]);

  // Extract code when messages change
  useEffect(() => {
    if (!projectId) {
      return;
    }

    const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant');
    if (!lastAssistantMsg || !lastAssistantMsg.content) {
      return;
    }

    if (lastAssistantMsg.id === lastProcessedMessageId) {
      return;
    }

    if (lastAssistantMsg && lastAssistantMsg.content) {
      const extracted = extractCode(lastAssistantMsg.content);
      if (extracted.html) {
        setLastProcessedMessageId(lastAssistantMsg.id);

        // Process through validation pipeline
        processGeneration(extracted.html, extracted.js).then((result) => {
          if (result.type === 'success') {
            const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
            const changeType = hasGenerated
              ? (lastUserMsg?.meta?.isQuickAction ? 'quick_action' : 'refinement')
              : 'initial';

            createVersion({
              projectId,
              html: result.html,
              js: result.js,
              metadata: {
                prompt: lastUserMsg?.content.slice(0, 120) || 'Generated page',
                timestamp: Date.now(),
                changeType,
              },
            }).catch((error) => {
              const reason = error instanceof Error ? error.message : 'Validation failed';
              sendMessage(
                `The previous HTML/JS failed server validation (${reason}). Please regenerate the page without using blocked patterns or unsafe code.`,
                buildFallbackContext()
              );
            });
          } else if (lastAssistantMsg.id !== lastValidationErrorId) {
            setLastValidationErrorId(lastAssistantMsg.id);
            sendMessage(
              `The generated JavaScript failed validation: ${result.errors.join(', ')}. ` +
              'Please regenerate the page without unsafe or blocked patterns, and omit JS if not needed.',
              buildFallbackContext()
            );
          }
        });
      }
    }
  }, [
    messages,
    projectId,
    createVersion,
    hasGenerated,
    lastProcessedMessageId,
    lastValidationErrorId,
    sendMessage,
    template,
    templateInputs,
    interviewAnswers,
  ]);

  const handleBack = () => {
    navigate('/create');
  };

  return (
    <div className="flex h-screen">
      {/* Left panel - Chat or Version History */}
      <div className={`flex transition-all duration-300 ${showVersionHistory ? 'w-2/3' : 'w-1/2'} min-w-[400px] border-r border-gray-200`}>
        {showVersionHistory ? (
          <VersionHistoryPanel />
        ) : (
          <ChatPanel
            template={template}
            templateInputs={templateInputs}
            hasGenerated={hasGenerated}
          />
        )}
      </div>

      {/* Right panel - Preview */}
      <div className="flex-1 flex items-center justify-center bg-gray-100">
        <div className="relative">
          {/* Header actions */}
          <div className="absolute -top-12 left-0 right-0 flex items-center justify-between">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              <ArrowLeft size={20} />
              <span>Back</span>
            </button>

            <div className="flex items-center gap-3">
              {projectId && <PublishButton projectId={projectId} />}
              <button
                onClick={() => setShowVersionHistory(!showVersionHistory)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
                  showVersionHistory
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <HistoryIcon size={18} />
                <span>History</span>
              </button>
            </div>
          </div>

          <PhoneFrame>
            <PreviewPanel
              html={currentVersion?.html || ''}
              js={currentVersion?.js || null}
            />
          </PhoneFrame>
        </div>
      </div>
    </div>
  );
}
