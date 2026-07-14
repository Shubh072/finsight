export function initCameraCapture(container, { onCapture }) {
  const modal = container.querySelector('[data-camera-modal]');
  const video = container.querySelector('[data-camera-video]');
  const canvas = container.querySelector('[data-camera-canvas]');
  const captureBtn = container.querySelector('[data-capture-btn]');
  const closeBtn = container.querySelector('[data-camera-close]');
  let stream = null;

  async function open() {
    if (!navigator.mediaDevices?.getUserMedia) {
      alert('Camera not supported in this browser.');
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      if (video) {
        video.srcObject = stream;
        await video.play();
      }
      modal?.classList.remove('hidden');
    } catch (err) {
      alert('Could not access camera: ' + err.message);
    }
  }

  function close() {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    modal?.classList.add('hidden');
  }

  captureBtn?.addEventListener('click', () => {
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], `receipt_${Date.now()}.jpg`, { type: 'image/jpeg' });
      onCapture?.(file);
      close();
    }, 'image/jpeg', 0.92);
  });

  closeBtn?.addEventListener('click', close);

  return { open, close };
}
