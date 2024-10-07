<template>
    <div class="login">
      <AppLogin msg="A-Z HOUSEHOLD SERVICES"/>
    </div>
  </template>
  
  <script>
  // @ is an alias to /src
  import AppLogin from '@/components/AppLogin.vue'
  
  export default {
    name: 'LoginView',
    components: {
      AppLogin
    }
  }
  </script>
  