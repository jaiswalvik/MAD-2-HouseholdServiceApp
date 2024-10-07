<template>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <a class="navbar-brand" href="#">Household Services</a>
      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ml-auto">
          <li class="nav-item">
            <router-link to="/login" class="nav-link">Login</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/register" class="nav-link">Register</router-link>
          </li>
        </ul>
      </div>
    </nav>
  </template>
  
  <script>
  export default {};
  </script>
  
  <style scoped>
  .navbar {
    margin-bottom: 20px;
  }
  </style>
  