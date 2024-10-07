<template>
    <h3>{{ msg }}</h3>
    <div class="login-container">
      <h2>Admin LOGIN</h2>
      <form @submit.prevent="handleLogin">
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
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  
  export default {
    name: 'AppAdminLogin',
    props: {
      msg: String
    },
    setup() {
      const username = ref('');
      const password = ref('');
      const router = useRouter();
  
      const handleLogin = async () => {
        try {
          const response = await axios.post('http://127.0.0.1:5000/admin/login', {
            username: username.value,
            password: password.value,
          });
          console.log(response.data);
          localStorage.setItem('access_token', response.data.access_token);
          router.push('/protected'); // Redirect to a protected route
        }catch (error) {
          if (error.response) {
            alert(`Login failed: ${error.response.data.message || error.response.data.error || 'Unknown error'}`);
          } else {
            alert("An error occurred during the login process.");
          }
        }
      };
  
      return {
        username,
        password,
        handleLogin,
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
  