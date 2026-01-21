import { ReactNode } from 'react'

interface PhoneFrameProps {
  children: ReactNode
}

export function PhoneFrame({ children }: PhoneFrameProps) {
  return (
    <div className="relative flex items-center justify-center p-8">
      <div className="relative">
        {/* iPhone-style frame */}
        <div className="w-[375px] h-[812px] bg-black rounded-[40px] shadow-2xl p-3">
          {/* Notch */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-black rounded-b-2xl z-10" />
          {/* Screen area */}
          <div className="w-full h-full bg-white rounded-[32px] overflow-hidden">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
