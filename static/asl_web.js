// Tab Switching Logic
const tabs = document.querySelectorAll('.tab_btn');
const all_content = document.querySelectorAll('.content');
const line = document.querySelector('.line');

let fetchTextInterval = null;

tabs.forEach((tab, index) => {
  tab.addEventListener('click', (e) => {
    tabs.forEach(tab => tab.classList.remove('active'));
    tab.classList.add('active');

    line.style.width = e.target.offsetWidth + "px";
    line.style.left = e.target.offsetLeft + "px";

    all_content.forEach(content => content.classList.remove('active'));
    all_content[index].classList.add('active');

    // Start or stop webcam based on tab
    if (index === 2) { // Camera tab
      startCamera();
      startFetchingRecognizedText();
    } else {
      stopCamera();
      stopFetchingRecognizedText();
    }
  });
});

// Webcam and Prediction Logic
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let stream = null;

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    requestAnimationFrame(captureAndSendFrame);
  } catch (err) {
    console.error('Camera error:', err);
    alert('Could not access webcam.');
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
}

async function captureAndSendFrame() {
  if (!stream) return;

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const imageData = canvas.toDataURL('image/jpeg');

  try {
    const response = await fetch('/predict_frame', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image: imageData }),
    });

    const data = await response.json();
    if (data.letter) {
      document.getElementById('recognized-text').innerText = data.letter;
    }
  } catch (error) {
    console.error('Prediction error:', error);
  }

  requestAnimationFrame(captureAndSendFrame);
}

// Key Press Handling
document.addEventListener('keydown', function (event) {
  let key = null;

  if (event.key === 'c') key = 'c';
  else if (event.key === 's') key = 's';
  else if (event.key === 'b') key = 'b';

  if (key) {
    fetch('/update_text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ key: key }),
    })
      .then((response) => response.json())
      .then((data) => {
        document.getElementById('recognized-text').innerText = data.recognized_text;
      })
      .catch((error) => console.error('Error updating text:', error));
  }
});

// Recognized Text Fetching (for full text updates)
function fetchRecognizedText() {
  const textElement = document.getElementById('recognized-text');
  if (!textElement) return;

  fetch('/recognized_text')
    .then(response => response.json())
    .then(data => {
      textElement.innerText = data.text;
    })
    .catch(error => console.error('Error fetching recognized text:', error));
}

function startFetchingRecognizedText() {
  if (!fetchTextInterval) {
    fetchTextInterval = setInterval(fetchRecognizedText, 300);
  }
}

function stopFetchingRecognizedText() {
  if (fetchTextInterval) {
    clearInterval(fetchTextInterval);
    fetchTextInterval = null;
  }
}
