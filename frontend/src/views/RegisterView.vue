<template>
    <div class="register">
      <AppRegister msg="A-Z HOUSEHOLD SERVICES"/>
    </div>
  </template>
  
  <script>
  // @ is an alias to /src
  import AppRegister from '@/components/AppRegister.vue'
  
  export default {
    name: 'RegisterView',
    components: {
      AppRegister
    }
  }
  </script>
  