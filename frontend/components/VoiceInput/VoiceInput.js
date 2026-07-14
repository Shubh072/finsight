export function initVoiceInput(btn, form) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!btn || !SpeechRecognition) {
    if (btn) btn.classList.add('hidden');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-IN';
  recognition.interimResults = false;

  btn.addEventListener('click', () => {
    btn.classList.add('animate-pulse');
    recognition.start();
  });

  recognition.onresult = (event) => {
    btn.classList.remove('animate-pulse');
    const text = event.results[0][0].transcript.toLowerCase();
    parseVoice(text, form);
  };

  recognition.onerror = () => btn.classList.remove('animate-pulse');
  recognition.onend = () => btn.classList.remove('animate-pulse');
}

function parseVoice(text, form) {
  const amountMatch = text.match(/(?:₹|rs\.?\s*|rupees?\s*)(\d+(?:\.\d+)?)/i) || text.match(/(\d+(?:\.\d+)?)\s*(?:₹|rs|rupees?)/i);
  const onMatch = text.match(/(?:on|at|from)\s+([a-z\s]+)/i);

  if (amountMatch && form.elements['amount']) {
    form.elements['amount'].value = amountMatch[1];
  }
  if (onMatch && form.elements['merchant_name']) {
    form.elements['merchant_name'].value = onMatch[1].trim().replace(/\s+/g, ' ');
  }
  if (onMatch && form.elements['title'] && !form.elements['title'].value) {
    form.elements['title'].value = onMatch[1].trim();
  }

  const merchants = { swiggy: 'Food', zomato: 'Food', uber: 'Travel', amazon: 'Shopping', netflix: 'Subscription' };
  for (const [m, cat] of Object.entries(merchants)) {
    if (text.includes(m) && form.elements['category']) {
      form.elements['category'].value = cat;
      if (form.elements['merchant_name'] && !form.elements['merchant_name'].value) {
        form.elements['merchant_name'].value = m.charAt(0).toUpperCase() + m.slice(1);
      }
      break;
    }
  }

  form.dispatchEvent(new Event('input', { bubbles: true }));
}
