<template>
  <div id="app">
    <h1>Voice to Text</h1>
    <button @click="startRecording" :disabled="isRecording">Start Recording</button>
    <button @click="stopRecording" :disabled="!isRecording">Stop Recording</button>
    <button @click="uploadFile" :disabled="!audioBlob">Generate Text</button>
    <div v-if="response">
      <h2>Generated text from the audio</h2>
      <p>{{ response.text }}</p>
      <h2>Shopping Items List</h2>
      <ul>
        <li v-for="item in response.items" :key="item.item">
          {{ item.item }}: {{ item.quantity }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      isRecording: false,
      audioBlob: null,
      response: null,
      mediaRecorder: null,
      chunks: [],
    };
  },
  methods: {
    async startRecording() {
      this.isRecording = true;
      this.chunks = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (event) => {
        this.chunks.push(event.data);
      };
      this.mediaRecorder.start();
    },
    stopRecording() {
      this.isRecording = false;
      this.mediaRecorder.stop();
      this.mediaRecorder.onstop = () => {
        this.audioBlob = new Blob(this.chunks, { type: 'audio/wav' });
      };
    },
    async uploadFile() {
      if (!this.audioBlob) {
        alert('Please record audio first.');
        return;
      }

      let formData = new FormData();
      formData.append('file', this.audioBlob, 'audio.wav');

      try {
        const res = await axios.post('http://127.0.0.1:5000/ab', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        this.response = res.data;
      } catch (error) {
        console.error('Error uploading audio:', error);
        alert('Failed to upload file.');
      }
    },
  },
};
</script>

<style>
#app {
  font-family: Arial;
  text-align: center;
  margin-top: 30px;
}
button {
  padding: 10px 15px;
  margin: 5px;
  background-color: #3079d3;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 20px;
}
button:disabled {
  background-color: #ccc;
}
button:hover:not(:disabled) {
  background-color: #333;
}
</style>
