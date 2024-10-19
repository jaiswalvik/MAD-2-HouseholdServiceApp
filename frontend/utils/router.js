import Home from "../pages/HomePage.js";
import LoginPage from "../pages/LoginPage.js";
import RegisterPage from "../pages/RegisterPage.js";
import AdminLoginPage from "../pages/AdminLoginPage.js";
import AdminDashboardPage from "../pages/AdminDashboardPage.js";
import CustomerDashboardPage from "../pages/CustomerDashboardPage.js";
import ProfessionalDashboardPage from "../pages/ProfessionalDashboardPage.js";


const routes = [
    {path : '/', component : Home},
    {path : '/login', component : LoginPage},
    {path : '/register', component : RegisterPage},
    {path : '/admin/login', component : AdminLoginPage},
    {path : '/admin/dashboard', component: AdminDashboardPage },
    {path : '/customer/dashboard', component: CustomerDashboardPage },
    {path : '/professional/dashboard', component: ProfessionalDashboardPage },  
    {path : '/logout', component : {
        template : `
        <div>
            <h3>Logging out...</h3>
        </div>
        `,
        mounted() {
            this.$root.logout();
        }
    }}
]

const router = new VueRouter({
    routes
})

export default router;