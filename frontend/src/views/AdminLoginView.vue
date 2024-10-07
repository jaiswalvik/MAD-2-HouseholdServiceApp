<template>
    <div class="login">
      <AppAdminLogin msg="A-Z HOUSEHOLD SERVICES"/>
    </div>
  </template>
  
  <script>
  // @ is an alias to /src
  import AppAdminLogin from '@/components/AppAdminLogin.vue'
  
  export default {
    name: 'AdminLoginView',
    components: {
      AppAdminLogin
    }
  }
  </script>
  