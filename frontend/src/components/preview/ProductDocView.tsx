import type { ProductDoc } from '@/types/productDoc'
import { cn } from '@/lib/utils'

interface ProductDocViewProps {
  doc: ProductDoc
  className?: string
}

export function ProductDocView({ doc, className }: ProductDocViewProps) {
  return (
    <div className={cn('h-full overflow-auto bg-muted/40 p-6', className)}>
      <div className="mx-auto w-full max-w-2xl rounded-lg bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-gray-900">项目需求文档</h1>
        <p className="mt-1 text-xs text-gray-500">
          最后更新: {new Date(doc.updated_at).toLocaleString('zh-CN')}
        </p>

        <Section title="概述">
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{doc.overview}</p>
        </Section>

        {doc.target_users && doc.target_users.length > 0 && (
          <Section title="目标用户">
            <ul className="list-disc list-inside text-sm text-gray-700">
              {doc.target_users.map((user, index) => (
                <li key={`${user}-${index}`}>{user}</li>
              ))}
            </ul>
          </Section>
        )}

        <Section title="内容结构">
          <div className="space-y-3">
            {(doc.content_structure?.sections || []).map((section, index) => (
              <div key={`${section.name}-${index}`} className="border-l-2 border-blue-200 pl-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {section.name}
                  </span>
                  <PriorityBadge priority={section.priority} />
                </div>
                <p className="text-xs text-gray-600">{section.description}</p>
                {section.content_hints && section.content_hints.length > 0 && (
                  <div className="mt-1 text-xs text-gray-500">
                    提示: {section.content_hints.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>

        {doc.design_requirements && (
          <Section title="设计要求">
            <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              {doc.design_requirements.style && (
                <InfoItem label="风格" value={doc.design_requirements.style} />
              )}
              {doc.design_requirements.typography && (
                <InfoItem label="字体" value={doc.design_requirements.typography} />
              )}
              {doc.design_requirements.mood && (
                <InfoItem label="氛围" value={doc.design_requirements.mood} />
              )}
              {doc.design_requirements.colors && doc.design_requirements.colors.length > 0 && (
                <div className="sm:col-span-2">
                  <span className="text-xs text-gray-500">配色:</span>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {doc.design_requirements.colors.map((color, index) => (
                      <span
                        key={`${color}-${index}`}
                        className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                      >
                        {color}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        <Section title="页面规划">
          <div className="space-y-2">
            {(doc.page_plan?.pages || []).map((page) => (
              <div
                key={page.id}
                className={cn(
                  'flex items-start gap-3 rounded-md border px-3 py-2',
                  page.is_main && 'border-blue-200 bg-blue-50'
                )}
              >
                <code className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                  {page.path}
                </code>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">
                    {page.name}
                    {page.is_main && (
                      <span className="ml-2 text-xs text-blue-600">(首页)</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600">{page.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {doc.technical_constraints && doc.technical_constraints.length > 0 && (
          <Section title="技术约束">
            <ul className="list-disc list-inside text-sm text-gray-700">
              {doc.technical_constraints.map((constraint, index) => (
                <li key={`${constraint}-${index}`}>{constraint}</li>
              ))}
            </ul>
          </Section>
        )}

        <div className="mt-8 rounded-md bg-gray-50 px-3 py-2 text-center text-xs text-gray-500">
          在聊天中说 "修改概述为..." 或 "添加新页面..." 来更新此文档
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-6">
      <h2 className="mb-2 text-base font-semibold text-gray-800">{title}</h2>
      {children}
    </section>
  )
}

function PriorityBadge({ priority }: { priority: 'high' | 'medium' | 'low' }) {
  const colors = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-green-100 text-green-700',
  }

  const labels = {
    high: '高',
    medium: '中',
    low: '低',
  }

  return (
    <span className={cn('rounded px-1.5 py-0.5 text-[10px]', colors[priority])}>
      {labels[priority]}
    </span>
  )
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-sm">
      <span className="text-xs text-gray-500">{label}:</span>{' '}
      <span className="font-medium text-gray-800">{value}</span>
    </div>
  )
}
