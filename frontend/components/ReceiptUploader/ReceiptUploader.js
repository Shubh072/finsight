export function initReceiptUploader(container, { onFile, onScanStart, onScanComplete, onScanError }) {
  const dropzone = container.querySelector('[data-dropzone]');
  const fileInput = container.querySelector('[data-file-input]');
  const preview = container.querySelector('[data-preview]');
  const previewImg = container.querySelector('[data-preview-img]');
  const previewPdf = container.querySelector('[data-preview-pdf]');
  const browseBtn = container.querySelector('[data-browse]');
  const cameraBtn = container.querySelector('[data-camera-trigger]');

  let currentFile = null;

  function showPreview(file) {
    currentFile = file;
    preview?.classList.remove('hidden');
    const url = URL.createObjectURL(file);
    if (file.type.startsWith('image/')) {
      previewImg?.classList.remove('hidden');
      previewPdf?.classList.add('hidden');
      if (previewImg) previewImg.src = url;
    } else {
      previewImg?.classList.add('hidden');
      previewPdf?.classList.remove('hidden');
      if (previewPdf) previewPdf.textContent = file.name;
    }
    onFile?.(file);
  }

  browseBtn?.addEventListener('click', () => fileInput?.click());
  cameraBtn?.addEventListener('click', () => {
    container.dispatchEvent(new CustomEvent('receipt:camera-request'));
  });

  fileInput?.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (file) showPreview(file);
  });

  ['dragenter', 'dragover'].forEach((ev) => {
    dropzone?.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.classList.add('border-primary', 'bg-primary/5');
    });
  });

  ['dragleave', 'drop'].forEach((ev) => {
    dropzone?.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-primary', 'bg-primary/5');
    });
  });

  dropzone?.addEventListener('drop', (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) showPreview(file);
  });

  container.querySelector('[data-scan-btn]')?.addEventListener('click', async () => {
    if (!currentFile) return;
    onScanStart?.();
    try {
      const { scanReceipt } = await import('../../js/api/expenseApi.js');
      const res = await scanReceipt(currentFile);
      onScanComplete?.(res?.data || res);
    } catch (err) {
      onScanError?.(err);
    }
  });

  return {
    getFile: () => currentFile,
    setFile(file) {
      if (file) showPreview(file);
    },
    reset() {
      currentFile = null;
      preview?.classList.add('hidden');
      if (fileInput) fileInput.value = '';
    },
  };
}
