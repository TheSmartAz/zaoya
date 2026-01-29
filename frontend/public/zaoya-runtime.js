/**
 * Zaoya Runtime - Safe JavaScript helpers for generated pages
 *
 * This runtime supports two modes:
 * 1. Preview mode (iframe) - communicates via postMessage
 * 2. Published mode (standalone) - makes API calls directly
 */
(function() {
  'use strict'

  // Detect if running in published mode (has meta tags)
  const publicIdMeta = document.querySelector('meta[name="zaoya-public-id"]');
  const apiBaseMeta = document.querySelector('meta[name="zaoya-api-base"]');
  const isPublished = !!publicIdMeta;
  const publicId = isPublished ? (publicIdMeta?.content || '') : '';
  const apiBase = isPublished ? (apiBaseMeta?.content || '') : '';

  // Toast notification system
  function showToast(message, type = 'info') {
    if (!isPublished) {
      // Send to parent in preview mode
      window.parent.postMessage({
        type: 'ZAOYA_TOAST',
        message: message,
        toastType: type
      }, '*');
      return;
    }

    // Create toast element for published pages
    const existing = document.querySelector('.zaoya-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'zaoya-toast';
    toast.textContent = message;

    Object.assign(toast.style, {
      position: 'fixed',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      padding: '12px 24px',
      borderRadius: '8px',
      backgroundColor: type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#1f2937',
      color: 'white',
      fontSize: '14px',
      fontWeight: '500',
      zIndex: '9999',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      opacity: '0',
      transition: 'opacity 0.3s ease'
    });

    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
    });

    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  // Send message to parent (preview mode only)
  function postMessage(type, data) {
    if (!isPublished) {
      window.parent.postMessage({ type, ...data }, '*');
    }
  }

  /**
   * Submit form data to Zaoya backend
   * Works in both preview and published modes
   */
  async function submitForm(formElement, options = {}) {
    if (!formElement || formElement.tagName !== 'FORM') {
      console.error('Zaoya: Invalid form element');
      return { success: false, error: 'Invalid form element' };
    }

    const formData = new FormData(formElement);
    const data = Object.fromEntries(formData.entries());
    const formId = formElement.dataset.zaoyaForm || formElement.dataset.formId || 'default';

    if (!isPublished) {
      // Preview mode: send to parent
      postMessage('ZAOYA_FORM_SUBMIT', { formId, data, options });
      return { success: true, mode: 'preview' };
    }

    // Published mode: submit to API
    try {
      const response = await fetch(`${apiBase}/api/submissions/${publicId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          form_id: formId,
          data: data
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Submission failed');
      }

      const result = await response.json();

      // Track successful submission
      track('form_submit', { form_id: formId });

      return { success: true, mode: 'published', ...result };
    } catch (error) {
      console.error('Zaoya: Form submission failed', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Track analytics event
   */
  async function track(eventType, data = {}) {
    if (!isPublished) {
      // Preview mode: send to parent
      postMessage('ZAOYA_TRACK', { event: eventType, data });
      return;
    }

    // Published mode: send to API (fire and forget)
    if (navigator.sendBeacon) {
      const blob = new Blob(
        [JSON.stringify({ type: eventType, data })],
        { type: 'application/json' }
      );
      navigator.sendBeacon(`${apiBase}/api/track/${publicId}`, blob);
    } else {
      // Fallback to fetch with keepalive
      fetch(`${apiBase}/api/track/${publicId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: eventType, data }),
        keepalive: true
      }).catch(() => {
        // Silently fail - tracking shouldn't break the page
      });
    }
  }

  /**
   * Navigate to a path (preview mode only)
   */
  function navigate(path) {
    if (!isPublished) {
      postMessage('ZAOYA_NAVIGATE', { path });
    }
  }

  // Public API
  window.Zaoya = {
    submitForm,
    track,
    toast: showToast,
    navigate,

    // Expose helper for form auto-attachment
    _version: '1.0.0',
    _isPublished: isPublished,
    _publicId: publicId
  };

  /**
   * Auto-attach to forms with data-zaoya-form attribute
   */
  function initForms() {
    const forms = document.querySelectorAll('form[data-zaoya-form]');

    forms.forEach(form => {
      // Skip if already initialized
      if (form.hasAttribute('data-zaoya-initialized')) return;

      form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        const originalText = submitBtn?.textContent || submitBtn?.value || '';
        const originalDisabled = submitBtn?.disabled;

        // Show loading state
        if (submitBtn) {
          submitBtn.disabled = true;
          if (submitBtn.tagName === 'BUTTON') {
            submitBtn.textContent = form.dataset.submittingText || 'Submitting...';
          } else {
            submitBtn.value = form.dataset.submittingText || 'Submitting...';
          }
        }

        const result = await Zaoya.submitForm(form);

        // Reset button state
        if (submitBtn) {
          submitBtn.disabled = originalDisabled;
          if (submitBtn.tagName === 'BUTTON') {
            submitBtn.textContent = originalText;
          } else {
            submitBtn.value = originalText;
          }
        }

        if (result.success) {
          // Show success message
          const successMsg = form.dataset.successMessage || 'Thanks for your submission!';
          showToast(successMsg, 'success');

          // Handle redirect if specified
          const redirectUrl = form.dataset.redirectUrl;
          if (redirectUrl && isPublished) {
            setTimeout(() => {
              window.location.href = redirectUrl;
            }, 500);
          } else {
            form.reset();
          }
        } else {
          showToast(result.error || 'Something went wrong. Please try again.', 'error');
        }
      });

      form.setAttribute('data-zaoya-initialized', 'true');
    });
  }

  /**
   * Initialize tracking for page views and CTA clicks
   */
  function initTracking() {
    if (!isPublished) return;

    // Track initial page view
    track('page_view', {
      referrer: document.referrer || '',
      screen: `${window.screen.width}x${window.screen.height}`,
    });

    // Track clicks on elements with data-track attribute
    document.addEventListener('click', function(e) {
      const tracked = e.target.closest('[data-track]');
      if (tracked) {
        const eventName = tracked.getAttribute('data-track');
        track('cta_click', {
          element: eventName,
          tag: tracked.tagName.toLowerCase(),
          text: tracked.textContent?.trim().slice(0, 50) || ''
        });
      }
    }, true);

    // Track all button/link clicks as CTAs (if not explicitly tracked)
    document.addEventListener('click', function(e) {
      const element = e.target.closest('button, a[href]');
      if (element && !element.hasAttribute('data-track')) {
        const label =
          element.getAttribute('aria-label') ||
          element.textContent?.trim().slice(0, 50) ||
          element.getAttribute('href')?.slice(0, 50) ||
          'unknown';
        track('cta_click', {
          element: 'auto',
          tag: element.tagName.toLowerCase(),
          text: label
        });
      }
    }, true);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initForms();
      initTracking();
    });
  } else {
    // DOM already ready
    initForms();
    initTracking();
  }

  // Notify parent that runtime is ready (preview mode)
  if (!isPublished) {
    window.parent.postMessage({ type: 'ZAOYA_READY' }, '*');
  }
})();
