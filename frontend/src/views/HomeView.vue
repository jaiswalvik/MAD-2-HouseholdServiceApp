<template>
  <div class="home">
    <AppHome msg="A-Z HOUSEHOLD SERVICES"/>
  </div>
</template>

<script>
// @ is an alias to /src
import AppHome from '@/components/AppHome.vue'

export default {
  name: 'HomeView',
  components: {
    AppHome
  }
}
</script>
