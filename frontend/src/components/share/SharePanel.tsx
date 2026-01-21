import { useState } from 'react';
import { Copy, Twitter, Mail, Link } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

interface SharePanelProps {
  url: string;
  title?: string;
}

export function SharePanel({ url, title = 'Check out my page!' }: SharePanelProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareOptions = [
    {
      name: 'Copy link',
      icon: Link,
      action: copyToClipboard,
      color: 'text-gray-600',
    },
    {
      name: 'Twitter',
      icon: Twitter,
      action: () => window.open(
        `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`,
        '_blank'
      ),
      color: 'text-blue-400',
    },
    {
      name: 'Email',
      icon: Mail,
      action: () => window.open(
        `mailto:?subject=Check out this page&body=${encodeURIComponent(url)}`,
        '_blank'
      ),
      color: 'text-gray-600',
    },
  ];

  return (
    <div className="space-y-4">
      {/* URL Input with Copy */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={url}
          readOnly
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
        />
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          {copied ? <Copy size={16} /> : <Link size={16} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      {/* Share Options */}
      <div className="flex gap-3">
        {shareOptions.map((option) => (
          <button
            key={option.name}
            onClick={option.action}
            className="flex flex-col items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 flex-1 transition-colors"
          >
            <option.icon size={24} className={option.color} />
            <span className="text-xs font-medium text-gray-700">{option.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

interface QRCodeDisplayProps {
  url: string;
  size?: number;
}

export function QRCodeDisplay({ url, size = 200 }: QRCodeDisplayProps) {
  return (
    <div className="flex flex-col items-center p-6 bg-white rounded-lg">
      <QRCodeSVG value={url} size={size} level="M" marginSize={2} />
      <p className="mt-4 text-sm text-gray-500">Scan to open on mobile</p>
    </div>
  );
}
