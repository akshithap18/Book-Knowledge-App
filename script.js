const recordButton = document.getElementById('record');
const stopButton = document.getElementById('stop');
const submitButton = document.getElementById('submitButton');
const audioElement = document.getElementById('audio');
const audioDataInput = document.getElementById('audioData');
const pdfInput = document.getElementById('pdfInput');
const timerDisplay = document.getElementById('timer');
const spinner = document.getElementById('spinner');

let mediaRecorder;
let audioChunks = [];
let recordedAudioBlob = null;
let startTime;
let timerInterval;

function formatTime(time) {
  const minutes = Math.floor(time / 60);
  const seconds = Math.floor(time % 60);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

recordButton.addEventListener('click', () => {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.start();

      audioChunks = [];
      startTime = Date.now();
      timerInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
        timerDisplay.textContent = formatTime(elapsedTime);
      }, 1000);

      mediaRecorder.ondataavailable = e => {
        audioChunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        recordedAudioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        // Preview the audio
        const audioURL = URL.createObjectURL(recordedAudioBlob);
        audioElement.src = audioURL;
        audioElement.controls = true;
      };
    })
    .catch(error => {
      console.error('Error accessing microphone:', error);
    });

  recordButton.disabled = true;
  stopButton.disabled = false;
});

stopButton.addEventListener('click', () => {
  if (mediaRecorder) {
    mediaRecorder.stop();
  }

  clearInterval(timerInterval);
  recordButton.disabled = false;
  stopButton.disabled = true;
});

submitButton.addEventListener('click', () => {
  if (!recordedAudioBlob) {
    alert('Please record audio before submitting.');
    return;
  }

  const pdfFile = pdfInput.files[0];
  if (!pdfFile) {
    alert('Please upload a PDF file.');
    return;
  }

  const formData = new FormData();
  formData.append('audio_data', recordedAudioBlob, 'recorded_audio.wav');
  formData.append('pdf_data', pdfFile);

  spinner.style.display = 'block';

  fetch('/upload_audio', {
    method: 'POST',
    body: formData
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      location.reload();
      return response.text();
    })
    .then(data => {
      console.log('Upload successful:', data);
    })
    .catch(error => {
      console.error('Upload error:', error);
      alert('Failed to upload. Please try again.');
    })
    .finally(() => {
      spinner.style.display = 'none';
    });
});
