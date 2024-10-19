import Navbar from "./components/Navbar.js"
import router from "./utils/router.js"

const app = new Vue({
    el : '#app',
    template : `
        <div> 
            <Navbar v-if="isAuthenticated"> </Navbar>
            <router-view> </router-view>
        </div>
    `,
    components : {
        Navbar,
    },
    router,
    data() {
        return {
            isAuthenticated: false, 
        };
    },
    methods: {
        login() {
            this.isAuthenticated = true;
        },
        logout() {
            this.isAuthenticated = false;
            localStorage.removeItem('token');
            this.$router.push('/');
        }
    }
})