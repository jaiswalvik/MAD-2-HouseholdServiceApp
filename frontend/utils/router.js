import Home from "../pages/HomePage.js";
import LoginPage from "../pages/LoginPage.js";
import RegisterPage from "../pages/RegisterPage.js";
import AdminLoginPage from "../pages/AdminLoginPage.js";
import AdminDashboardPage from "../pages/AdminDashboardPage.js";
import AdminProfilePage from "../pages/AdminProfilePage.js";
import AdminSearchPage from "../pages/AdminSearchPage.js";
import AdminSummaryPage from "../pages/AdminSummaryPage.js";
import CustomerDashboardPage from "../pages/CustomerDashboardPage.js";
import ProfessionalDashboardPage from "../pages/ProfessionalDashboardPage.js";
import AdminCreateServicesPage from "../pages/AdminCreateServicesPage.js";
import AdminUpdateServicesPage from "../pages/AdminUpdateServicesPage.js";
import AdminDeleteServicesPage from "../pages/AdminDeleteServicesPage.js";

const routes = [
    {path : '/', component : Home},
    {path : '/login', component : LoginPage},
    {path : '/register', component : RegisterPage},
    {path : '/admin/login', component : AdminLoginPage},
    {path : '/admin/dashboard', component: AdminDashboardPage },
    {path : '/admin/profile', component: AdminProfilePage },
    {path : '/admin/search', component: AdminSearchPage },
    {path : '/admin/summary', component: AdminSummaryPage }, 
    {path : '/customer/dashboard', component: CustomerDashboardPage },
    {path : '/professional/dashboard', component: ProfessionalDashboardPage },
    {path : '/admin/services/create_services', component : AdminCreateServicesPage},
    {path : '/admin/services/update_service/:id',component: AdminUpdateServicesPage,props: true},
    {path : '/admin/services/delete_service/:id',component: AdminDeleteServicesPage,props: true}, 
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