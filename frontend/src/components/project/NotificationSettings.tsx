import { useState } from 'react';
import { Mail, Check, X, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { Project } from '@/types/project';

interface NotificationSettingsProps {
  project: Project;
  onUpdate?: (updates: Partial<Project>) => void;
}

export function NotificationSettings({ project, onUpdate }: NotificationSettingsProps) {
  const [email, setEmail] = useState(project.notification_email || '');
  const [enabled, setEnabled] = useState(project.notification_enabled || false);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [testStatus, setTestStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');

    const token = useAuthStore.getState().token;
    if (!token) {
      setSaveStatus('error');
      setIsSaving(false);
      return;
    }

    try {
      const response = await fetch(`/api/projects/${project.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          notification_email: enabled ? email : null,
          notification_enabled: enabled && !!email,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      const updated = await response.json();
      setSaveStatus('success');
      onUpdate?.({
        notification_email: updated.notification_email ?? email,
        notification_enabled: updated.notification_enabled ?? enabled,
      });

      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestEmail = async () => {
    setIsTesting(true);
    setTestStatus('idle');

    const token = useAuthStore.getState().token;
    if (!token) {
      setTestStatus('error');
      setIsTesting(false);
      return;
    }

    try {
      const response = await fetch(`/api/projects/${project.id}/test-notification`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to send test email');
      }

      setTestStatus('success');
      setTimeout(() => setTestStatus('idle'), 3000);
    } catch {
      setTestStatus('error');
    } finally {
      setIsTesting(false);
    }
  };

  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-100 rounded-lg">
          <Mail size={20} className="text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Email Notifications</h3>
          <p className="text-sm text-gray-500">
            Get notified when someone submits your form
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Enable Toggle */}
        <label className="flex items-center justify-between cursor-pointer">
          <span className="text-sm font-medium text-gray-700">
            Enable email notifications
          </span>
          <div className="relative">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
          </div>
        </label>

        {/* Email Input */}
        {enabled && (
          <div className="space-y-2">
            <label htmlFor="notification-email" className="block text-sm font-medium text-gray-700">
              Notification email address
            </label>
            <div className="flex gap-2">
              <input
                id="notification-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className={`flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  !isEmailValid && email ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              <button
                onClick={handleTestEmail}
                disabled={!isEmailValid || isTesting}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isTesting ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  'Send Test'
                )}
              </button>
            </div>

            {testStatus === 'success' && (
              <p className="text-sm text-green-600 flex items-center gap-1">
                <Check size={14} /> Test email sent!
              </p>
            )}
            {testStatus === 'error' && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <X size={14} /> Failed to send test email.
              </p>
            )}

            {!isEmailValid && email && (
              <p className="text-sm text-red-600">Please enter a valid email address</p>
            )}
          </div>
        )}

        {/* Save Button */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <span className="text-sm text-gray-500">
            {enabled
              ? 'Emails will be sent to ' + (email || 'the address above')
              : 'Email notifications are disabled'}
          </span>
          <button
            onClick={handleSave}
            disabled={isSaving || (enabled && !isEmailValid)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </button>
        </div>

        {saveStatus === 'success' && (
          <p className="text-sm text-green-600 flex items-center gap-1">
            <Check size={14} /> Settings saved!
          </p>
        )}
        {saveStatus === 'error' && (
          <p className="text-sm text-red-600 flex items-center gap-1">
            <X size={14} /> Failed to save settings.
          </p>
        )}
      </div>
    </div>
  );
}
