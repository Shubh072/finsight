export function initRecurringSection(container) {
  const toggle = container?.querySelector('[data-recurring-toggle]');
  const panel = container?.querySelector('[data-recurring-panel]');
  const freqSelect = container?.querySelector('[name="recurring_frequency"]');

  toggle?.addEventListener('change', () => {
    if (toggle.checked) {
      panel?.classList.remove('hidden');
    } else {
      panel?.classList.add('hidden');
      if (freqSelect) freqSelect.value = '';
    }
  });

  return {
    isEnabled: () => toggle?.checked,
    getFrequency: () => freqSelect?.value || '',
  };
}
