import Navbar from "./components/Navbar.js"
import router from "./utils/router.js"

const app = new Vue({
    el : '#app',
    template : `
        <div> 
            <Navbar v-if="isAuthenticated" :userRole="userRole"></Navbar>
            <router-view></router-view>
        </div>
    `,
    components : {
        Navbar,
    },
    router,
    data() {
        return {
            isAuthenticated: false,
            userRole: null,
        };
    },
    methods: {
        login(role,token) {
            this.isAuthenticated = true;
            this.userRole = role;
            localStorage.setItem('isAuthenticated', true);
            localStorage.setItem('userRole', role);
            localStorage.setItem('token', token);
        },
        logout() {
            this.isAuthenticated = false;
            this.userRole = null;
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('userRole');
            localStorage.removeItem('token');
            this.$router.push('/');
        },
        checkAuthentication() {
            this.isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            this.userRole = localStorage.getItem('userRole');
        },
        handleWindowClose() {
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('userRole');
            localStorage.removeItem('token');
        }
    },
    mounted() {
        this.checkAuthentication();
        if (!this.isAuthenticated && this.$route.path !== '/') {
            this.$router.replace('/');
        }
        window.addEventListener("beforeunload", this.handleWindowClose);
    },
    beforeDestroy() {
        window.removeEventListener("beforeunload", this.handleWindowClose);
    }
})