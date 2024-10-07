<template>
    <h3>{{ msg }}</h3>
    <div class="login-container">
      <h2>Register</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="username">Username (e-mail):</label>
          <input
            type="text"
            id="username"
            v-model="username"
            required
            class="form-control"
          />
        </div>
        <div class="form-group">
          <label for="password">Password:</label>
          <input
            type="password"
            id="password"
            v-model="password"
            required
            class="form-control"
          />
        </div>
        <button type="submit" class="btn btn-primary">Login</button>
      </form>
      <p>
        <router-link to="/login">Customer/Professional Login</router-link>
      </p>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  
  export default {
    name: 'AppRegister',
    props: {
      msg: String
    },
    setup() {
      const username = ref('');
      const password = ref('');
      const router = useRouter();
  
      const handleRegister = async () => {
        try {
          const response = await axios.post('http://127.0.0.1:5000/register', {
            username: username.value,
            password: password.value,
          });
          localStorage.setItem('access_token', response.data.access_token);
          router.push('/protected'); // Redirect to a protected route
        } catch (error) {
          alert('Login failed. Please check your username and password.');
        }
      };
  
      return {
        username,
        password,
        handleRegister,
      };
    },
  };
  </script>
  
  <style scoped>
  .login-container {
    max-width: 400px;
    margin: 100px auto;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  
  .form-group {
    margin-bottom: 15px;
  }
  </style>
  