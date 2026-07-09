/**
 * ReceiptUploader Component
 * Handles drag-and-drop, file browse, and camera capture for receipts
 */
class ReceiptUploader {
  constructor(container, onFileSelected, onScanRequested) {
    this.container = container;
    this.onFileSelected = onFileSelected;
    this.onScanRequested = onScanRequested;
    this.currentFile = null;
    this.render();
  }

  render() {
    this.container.innerHTML = `
      <div class="receipt-uploader">
        <div id="receipt-drop-zone" class="border-2 border-dashed border-outline-variant rounded-2xl p-6 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all relative overflow-hidden group">
          <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="relative z-10">
            <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-primary text-3xl">cloud_upload</span>
            </div>
            <p class="text-on-surface font-semibold mb-1">Drag & Drop Receipt</p>
            <p class="text-on-surface-variant text-sm mb-3">or choose an option below</p>
            <div class="flex flex-wrap gap-2 justify-center">
              <button type="button" id="receipt-browse-btn" class="px-4 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm font-medium hover:bg-surface-container-high transition-all flex items-center gap-2">
                <span class="material-symbols-outlined text-base">folder_open</span>
                Browse Files
              </button>
              <button type="button" id="receipt-camera-btn" class="px-4 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm font-medium hover:bg-surface-container-high transition-all flex items-center gap-2">
                <span class="material-symbols-outlined text-base">photo_camera</span>
                Take Photo
              </button>
            </div>
            <p class="text-xs text-on-surface-variant mt-3">Supports JPG, PNG, WebP, PDF (max 5MB)</p>
          </div>
          <input type="file" id="receipt-file-input" class="hidden" accept="image/jpeg,image/png,image/webp,application/pdf" />
        </div>
        <div id="receipt-preview-container" class="hidden mt-4">
          <div class="relative rounded-xl overflow-hidden border border-outline-variant bg-surface-container">
            <img id="receipt-preview-img" class="w-full max-h-64 object-contain" alt="Receipt preview" />
            <div class="absolute top-2 right-2 flex gap-2">
              <button type="button" id="receipt-scan-btn" class="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-bold flex items-center gap-1 hover:brightness-110 transition-all shadow-lg">
                <span class="material-symbols-outlined text-sm">document_scanner</span>
                Scan with AI
              </button>
              <button type="button" id="receipt-remove-btn" class="px-3 py-1.5 bg-error text-white rounded-lg text-xs font-bold flex items-center gap-1 hover:brightness-110 transition-all shadow-lg">
                <span class="material-symbols-outlined text-sm">delete</span>
              </button>
            </div>
          </div>
          <div id="receipt-file-info" class="mt-2 text-xs text-on-surface-variant"></div>
        </div>
        <div id="camera-modal" class="hidden fixed inset-0 z-[150] bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div class="bg-surface rounded-2xl p-6 max-w-2xl w-full shadow-2xl">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">photo_camera</span>
                Capture Receipt
              </h3>
              <button type="button" id="camera-close-btn" class="p-2 hover:bg-surface-container-high rounded-lg transition-colors">
                <span class="material-symbols-outlined text-on-surface-variant">close</span>
              </button>
            </div>
            <div class="relative rounded-xl overflow-hidden bg-black aspect-video mb-4">
              <video id="camera-video" class="w-full h-full object-cover" autoplay playsinline></video>
              <canvas id="camera-canvas" class="hidden"></canvas>
            </div>
            <div class="flex gap-3 justify-center">
              <button type="button" id="camera-capture-btn" class="px-6 py-3 bg-primary text-white rounded-xl font-bold flex items-center gap-2 hover:brightness-110 transition-all shadow-lg shadow-primary/30">
                <span class="material-symbols-outlined">photo_camera</span>
                Capture
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    this._setupEventListeners();
  }

  _setupEventListeners() {
    const dropZone = this.container.querySelector('#receipt-drop-zone');
    const fileInput = this.container.querySelector('#receipt-file-input');
    const browseBtn = this.container.querySelector('#receipt-browse-btn');
    const cameraBtn = this.container.querySelector('#receipt-camera-btn');
    const removeBtn = this.container.querySelector('#receipt-remove-btn');
    const scanBtn = this.container.querySelector('#receipt-scan-btn');
    const cameraModal = this.container.querySelector('#camera-modal');
    const cameraClose = this.container.querySelector('#camera-close-btn');
    const cameraCapture = this.container.querySelector('#camera-capture-btn');
    const video = this.container.querySelector('#camera-video');
    const canvas = this.container.querySelector('#camera-canvas');

    // Browse files
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    dropZone.addEventListener('click', (e) => {
      if (e.target === dropZone || e.target.closest('.relative.z-10')) {
        fileInput.click();
      }
    });

    // File selected
    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        this._handleFile(e.target.files[0]);
      }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('border-primary', 'bg-primary/10');
    });

    dropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-primary', 'bg-primary/10');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-primary', 'bg-primary/10');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        this._handleFile(e.dataTransfer.files[0]);
      }
    });

    // Remove receipt
    removeBtn.addEventListener('click', () => this._clearFile());

    // Scan receipt
    scanBtn.addEventListener('click', () => {
      if (this.currentFile && this.onScanRequested) {
        this.onScanRequested(this.currentFile);
      }
    });

    // Camera
    cameraBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this._openCamera(video);
    });

    cameraClose.addEventListener('click', () => this._closeCamera(video));

    cameraCapture.addEventListener('click', () => {
      this._capturePhoto(video, canvas);
    });
  }

  _handleFile(file) {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Unsupported file type. Please use JPG, PNG, WebP, or PDF.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 5MB.');
      return;
    }

    this.currentFile = file;

    const previewContainer = this.container.querySelector('#receipt-preview-container');
    const previewImg = this.container.querySelector('#receipt-preview-img');
    const fileInfo = this.container.querySelector('#receipt-file-info');

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      previewImg.src = url;
      previewImg.classList.remove('hidden');
      previewContainer.classList.remove('hidden');
    } else {
      // PDF - show icon instead
      previewImg.src = '';
      previewImg.alt = 'PDF Receipt';
      previewContainer.classList.remove('hidden');
    }

    fileInfo.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    if (this.onFileSelected) {
      this.onFileSelected(file);
    }
  }

  _clearFile() {
    this.currentFile = null;
    const previewContainer = this.container.querySelector('#receipt-preview-container');
    const fileInput = this.container.querySelector('#receipt-file-input');
    previewContainer.classList.add('hidden');
    fileInput.value = '';
    if (this.onFileSelected) {
      this.onFileSelected(null);
    }
  }

  async _openCamera(video) {
    const modal = this.container.querySelector('#camera-modal');
    modal.classList.remove('hidden');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      video.srcObject = stream;
      this.cameraStream = stream;
    } catch (err) {
      toast.error('Camera not available. Please upload a file instead.');
      modal.classList.add('hidden');
    }
  }

  _closeCamera(video) {
    const modal = this.container.querySelector('#camera-modal');
    modal.classList.add('hidden');
    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach(track => track.stop());
      this.cameraStream = null;
    }
  }

  _capturePhoto(video, canvas) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      const file = new File([blob], `camera_receipt_${Date.now()}.jpg`, { type: 'image/jpeg' });
      this._handleFile(file);
      this._closeCamera(video);
    }, 'image/jpeg', 0.9);
  }

  getFile() {
    return this.currentFile;
  }

  clear() {
    this._clearFile();
  }
}
