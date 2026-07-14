export function initSplitExpense(container) {
  const toggle = container?.querySelector('[data-split-toggle]');
  const panel = container?.querySelector('[data-split-panel]');
  const modeSelect = container?.querySelector('[data-split-mode]');
  const membersList = container?.querySelector('[data-split-members]');
  const addBtn = container?.querySelector('[data-split-add]');

  let members = [{ name: 'You', amount: 0 }];

  function renderMembers() {
    if (!membersList) return;
    membersList.innerHTML = members.map((m, i) => `
      <div class="flex gap-2 items-center">
        <input type="text" data-split-name="${i}" value="${m.name}" placeholder="Name" class="flex-1 bg-surface border border-outline-variant rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40" />
        <input type="number" data-split-amt="${i}" value="${m.amount || ''}" placeholder="Amt" min="0" step="0.01" class="w-24 bg-surface border border-outline-variant rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40" />
        ${i > 0 ? `<button type="button" data-split-rm="${i}" class="p-1 text-error hover:bg-error/10 rounded"><span class="material-symbols-outlined text-sm">close</span></button>` : ''}
      </div>`).join('');

    membersList.querySelectorAll('[data-split-rm]').forEach((btn) => {
      btn.addEventListener('click', () => {
        members.splice(parseInt(btn.dataset.splitRm), 1);
        renderMembers();
      });
    });
  }

  toggle?.addEventListener('change', () => {
    panel?.classList.toggle('hidden', !toggle.checked);
  });

  addBtn?.addEventListener('click', () => {
    members.push({ name: '', amount: 0 });
    renderMembers();
  });

  renderMembers();

  return {
    isEnabled: () => toggle?.checked,
    getSplitJson(totalAmount) {
      if (!toggle?.checked) return null;
      const mode = modeSelect?.value || 'equal';
      const names = membersList?.querySelectorAll('[data-split-name]') || [];
      const amts = membersList?.querySelectorAll('[data-split-amt]') || [];
      const splits = [];
      names.forEach((el, i) => {
        splits.push({ name: el.value || `Person ${i + 1}`, amount: parseFloat(amts[i]?.value) || 0 });
      });
      if (mode === 'equal' && totalAmount > 0) {
        const each = totalAmount / splits.length;
        splits.forEach((s) => { s.amount = Math.round(each * 100) / 100; });
      }
      return { mode, members: splits };
    },
  };
}
