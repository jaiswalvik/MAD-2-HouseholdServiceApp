<template>
    <h3>{{ msg }}</h3>
    <div class="container">
        <p><router-link to="/admin/login">Admin Login</router-link></p>
        <p><router-link to="/login">Customer/Professional Login</router-link></p>      
    </div>
</template>
  
  <script>  
  export default {
    name: 'AppHome',
    props: {
      msg: String
    }
  }    
  </script>
  
  <style>
  .container {
    margin-top: 20px;
    text-align: center;
  }     
  </style>
  