import { useProjectStore } from '@/stores'
import type { ProductDocCardData } from '@/types/chat'

interface ProductDocCardProps {
  data: ProductDocCardData
}

export function ProductDocCard({ data }: ProductDocCardProps) {
  const loadProductDoc = useProjectStore((state) => state.loadProductDoc)

  const handleView = () => {
    if (data.project_id) {
      void loadProductDoc(data.project_id)
    }
    window.dispatchEvent(new CustomEvent('open-product-doc'))
  }

  return (
    <div className="max-w-md rounded-lg border bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-lg">📄</span>
        <span className="font-medium">ProductDoc ready</span>
      </div>
      <p className="text-sm text-muted-foreground">
        项目需求文档已生成，可以在预览面板查看并继续迭代。
      </p>
      <button
        onClick={handleView}
        className="mt-3 rounded-md border px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
      >
        查看 ProductDoc
      </button>
    </div>
  )
}
