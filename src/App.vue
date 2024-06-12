<template>
  <div id="app">
    <h1>AI Shopping List</h1>
    <button @click="startRecording" :disabled="isRecording">Start Recording</button>
    <button @click="stopRecording" :disabled="!isRecording">Stop Recording</button>
    <button @click="uploadFile" :disabled="!audioBlob">Generate Text</button>
    <button @click="fetchShoppingList">Show Shopping List</button>
    <div v-if="response">
      <h2></h2>
      <p>{{ response.text }}</p>
      <h2>Shopping Items List</h2>
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>Quantity</th>
            <th>Unit</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in response.items" :key="item.item">
            <td>{{ item.item }}</td>
            <td>{{ item.quantity }}</td>
            <td>{{ item.unit }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <br><br><br> <br><br><br> <br><br><br> <br><br><br> <br><br><br>
    <h4>Project by Chinmoy Talukdar</h4>

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
    async fetchShoppingList() {
  try {
    const res = await axios.get('http://127.0.0.1:5000/shopping-list');
    this.response = {
      //text: 'Shopping List Fetched from Database',
      items: res.data.shopping_list,
    };
  } catch (error) {
    console.error('Error fetching shopping list:', error);
    alert('Failed to fetch shopping list.');
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
table {
  width: 50%;
  margin: 20px auto;
  border-collapse: collapse;
}
th, td {
  padding: 10px;
  border: 1px solid #ddd;
}
th {
  background-color: #f2f2f2;
}
</style>
