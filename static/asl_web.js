// Tab Switching Logic
const tabs = document.querySelectorAll('.tab_btn');
const all_content = document.querySelectorAll('.content');
const line = document.querySelector('.line');

let fetchTextInterval = null; // Store the interval ID

tabs.forEach((tab, index) => {
  tab.addEventListener('click', (e) => {
    tabs.forEach(tab => { tab.classList.remove('active'); });
    tab.classList.add('active');

    line.style.width = e.target.offsetWidth + "px";
    line.style.left = e.target.offsetLeft + "px";

    all_content.forEach(content => { content.classList.remove('active'); });
    all_content[index].classList.add('active');

    // Check if ASL tab is clicked (assuming it's the second button, index = 1)
    if (index === 2) {
      startFetchingRecognizedText();
    } else {
      stopFetchingRecognizedText();
    }
  });
});

// Camera and Prediction Logic
const video = document.getElementById('webcam');
const cameraSection = document.getElementById('camera-section');
let stream = null;

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    cameraSection.style.display = 'flex';
    fetchPrediction();
  } catch (err) {
    console.error('Camera error:', err);
    alert('Could not access webcam.');
  }
}

function stopCamera() {
  if (stream) {
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
    video.srcObject = null;
    cameraSection.style.display = 'none';
  }
}

// Fetch predictions from the backend
async function fetchPrediction() {
  try {
    const response = await fetch('http://127.0.0.1:5000/status');
    const data = await response.json();

    if (data.letter !== undefined) {
      document.getElementById('prediction-text').textContent = `Letter: ${data.letter}`;
    }
  } catch (error) {
    console.error('Error fetching prediction:', error);
  }

  setTimeout(fetchPrediction, 500);
}

function updateRecognizedText(text) {
  const textDisplay = document.getElementById('prediction-text');
  textDisplay.textContent = text;
}

// Handle key presses
document.addEventListener('keydown', function (event) {
  let key = null;

  if (event.key === 'c') {
    key = 'c';
  } else if (event.key === 's') {
    key = 's';
  } else if (event.key === 'b') {
    key = 'b';
  }

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
        console.log('Updated text:', data.recognized_text);
        updateRecognizedText(data.recognized_text);
      })
      .catch((error) => console.error('Error:', error));
  }
});

// Fetch recognized text
function fetchRecognizedText() {
  const textElement = document.getElementById('recognized-text');
  if (!textElement) return; // Safely return if element not found

  fetch('/recognized_text')
    .then(response => response.json())
    .then(data => {
      textElement.innerText =  data.text;
    })
    .catch(error => console.error('Error fetching recognized text:', error));
}

// Start fetching text every 500ms
function startFetchingRecognizedText() {
  if (!fetchTextInterval) {
    fetchTextInterval = setInterval(fetchRecognizedText, 300);
  }
}

// Stop fetching text
function stopFetchingRecognizedText() {
  if (fetchTextInterval) {
    clearInterval(fetchTextInterval);
    fetchTextInterval = null;
  }
}
