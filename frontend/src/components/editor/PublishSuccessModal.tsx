import { Copy, Check, X, Twitter, Mail } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { useState } from 'react';

interface PublishSuccessModalProps {
  url: string;
  onClose: () => void;
}

export function PublishSuccessModal({ url, onClose }: PublishSuccessModalProps) {
  const [copied, setCopied] = useState(false);
  const [showQR, setShowQR] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareOptions = [
    {
      name: 'Twitter',
      icon: Twitter,
      color: 'text-blue-400',
      onClick: () => window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent('Check out my page!')}`, '_blank'),
    },
    {
      name: 'Email',
      icon: Mail,
      color: 'text-gray-600',
      onClick: () => window.open(`mailto:?subject=Check out this page&body=${encodeURIComponent(url)}`, '_blank'),
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="text-green-600" size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Published!</h2>
              <p className="text-sm text-gray-500">Your page is now live</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        {!showQR ? (
          <div className="space-y-4">
            {/* URL Input */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={url}
                readOnly
                className="flex-1 px-3 py-2 bg-gray-100 border border-gray-200 rounded-lg text-sm"
              />
              <button
                onClick={copyToClipboard}
                className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>

            {/* Share Options */}
            <div className="flex gap-2">
              {shareOptions.map((option) => (
                <button
                  key={option.name}
                  onClick={option.onClick}
                  className="flex flex-col items-center gap-1 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 flex-1"
                >
                  <option.icon size={20} className={option.color} />
                  <span className="text-xs text-gray-600">{option.name}</span>
                </button>
              ))}
              <button
                onClick={() => setShowQR(true)}
                className="flex flex-col items-center gap-1 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 flex-1"
              >
                <div className="w-5 h-5 bg-gray-200 rounded" />
                <span className="text-xs text-gray-600">QR Code</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="w-full py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-col items-center p-6 bg-white rounded-lg">
              <QRCodeSVG value={url} size={200} level="M" />
              <p className="mt-4 text-sm text-gray-500">Scan to open on mobile</p>
            </div>
            <button
              onClick={() => setShowQR(false)}
              className="w-full py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
