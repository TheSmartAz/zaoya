import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import { EditorState, Compartment } from '@codemirror/state'
import { EditorView, keymap } from '@codemirror/view'
import { basicSetup } from '@codemirror/basic-setup'
import { html as htmlLang } from '@codemirror/lang-html'
import { javascript } from '@codemirror/lang-javascript'
import { css } from '@codemirror/lang-css'
import {
  search,
  SearchQuery,
  setSearchQuery,
  findNext,
  findPrevious,
} from '@codemirror/search'

export interface CodeMirrorHandle {
  findNext: () => void
  findPrevious: () => void
  setSearchQuery: (query: string) => void
  scrollToLine: (line: number) => void
}

interface CodeMirrorViewerProps {
  value: string
  language?: string
  className?: string
}

const languageExtension = (language?: string) => {
  switch (language) {
    case 'html':
      return htmlLang()
    case 'javascript':
    case 'js':
      return javascript()
    case 'css':
      return css()
    default:
      return htmlLang()
  }
}

export const CodeMirrorViewer = forwardRef<CodeMirrorHandle, CodeMirrorViewerProps>(
  ({ value, language, className }, ref) => {
    const containerRef = useRef<HTMLDivElement | null>(null)
    const viewRef = useRef<EditorView | null>(null)
    const languageCompartment = useRef(new Compartment())

    useImperativeHandle(ref, () => ({
      findNext: () => {
        if (viewRef.current) {
          findNext(viewRef.current)
        }
      },
      findPrevious: () => {
        if (viewRef.current) {
          findPrevious(viewRef.current)
        }
      },
      setSearchQuery: (query: string) => {
        if (!viewRef.current) return
        const trimmed = query.trim()
        const searchQuery = new SearchQuery({
          search: trimmed,
          caseSensitive: false,
          regexp: false,
        })
        viewRef.current.dispatch({
          effects: setSearchQuery.of(searchQuery),
        })
      },
      scrollToLine: (line: number) => {
        if (!viewRef.current || !line) return
        const view = viewRef.current
        const lineInfo = view.state.doc.line(Math.min(Math.max(line, 1), view.state.doc.lines))
        view.dispatch({
          selection: { anchor: lineInfo.from },
          scrollIntoView: true,
        })
      },
    }))

    useEffect(() => {
      if (!containerRef.current) return

      const state = EditorState.create({
        doc: value,
        extensions: [
          basicSetup,
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
          EditorView.lineWrapping,
          EditorView.theme({
            '&': { height: '100%' },
            '.cm-scroller': { overflow: 'auto' },
          }),
          languageCompartment.current.of(languageExtension(language)),
          search({ top: false }),
          keymap.of([]),
        ],
      })

      const view = new EditorView({
        state,
        parent: containerRef.current,
      })

      viewRef.current = view

      return () => {
        view.destroy()
        viewRef.current = null
      }
    }, [])

    useEffect(() => {
      const view = viewRef.current
      if (!view) return
      const current = view.state.doc.toString()
      if (current !== value) {
        view.dispatch({
          changes: { from: 0, to: view.state.doc.length, insert: value },
        })
      }
    }, [value])

    useEffect(() => {
      const view = viewRef.current
      if (!view) return
      view.dispatch({
        effects: languageCompartment.current.reconfigure(languageExtension(language)),
      })
    }, [language])

    return <div ref={containerRef} className={className} />
  }
)

CodeMirrorViewer.displayName = 'CodeMirrorViewer'
