import Home from "../pages/HomePage.js";
import LoginPage from "../pages/LoginPage.js";
import RegisterPage from "../pages/RegisterPage.js";
import AdminLoginPage from "../pages/AdminLoginPage.js";
import AdminDashboardPage from "../pages/AdminDashboardPage.js";
import AdminProfilePage from "../pages/AdminProfilePage.js";
import AdminSearchPage from "../pages/AdminSearchPage.js";
import AdminSummaryPage from "../pages/AdminSummaryPage.js";
import AdminCreateServicesPage from "../pages/AdminCreateServicesPage.js";
import AdminDownloadReportPage from "../pages/AdminDownloadReportPage.js";
import CustomerDashboardPage from "../pages/CustomerDashboardPage.js";
import CustomerServiceRemarksPage from "../pages/CustomerServiceRemarksPage.js";
import CustomerProfilePage from "../pages/CustomerProfilePage.js";
import CustomerSearchPage from "../pages/CustomerSearchPage.js";
import CustomerSummaryPage from "../pages/CustomerSummaryPage.js";
import ProfessionalDashboardPage from "../pages/ProfessionalDashboardPage.js";
import ProfessionalProfilePage from "../pages/ProfessionalProfilePage.js";
import ProfessionalSearchPage from "../pages/ProfessionalSearchPage.js";
import ProfessionalSummaryPage from "../pages/ProfessionalSummaryPage.js";

const routes = [
    {path : '/', component : Home},
    {path : '/login', component : LoginPage},
    {path : '/register', component : RegisterPage},
    {path : '/admin/login', component : AdminLoginPage},
    {path : '/admin/dashboard', component: AdminDashboardPage },
    {path : '/admin/profile', component: AdminProfilePage },
    {path : '/admin/search', component: AdminSearchPage },
    {path : '/admin/summary', component: AdminSummaryPage },
    {path : '/admin/downloadReport', component: AdminDownloadReportPage },
    {path : '/admin/services/create_services', component : AdminCreateServicesPage},
    {path : '/admin/services/update/:id',component: AdminCreateServicesPage,props: route => ({ editing: true, id: route.params.id })}, 
    {path : '/customer/dashboard', component: CustomerDashboardPage },
    {path : '/customer/closeServiceRequest/:id', component: CustomerServiceRemarksPage,props: route => ({ id: route.params.id })},
    {path : '/customer/profile', component: CustomerProfilePage },
    {path : '/customer/search', component: CustomerSearchPage }, 
    {path : '/customer/summary', component: CustomerSummaryPage },
    {path : '/professional/dashboard', component: ProfessionalDashboardPage },
    {path : '/professional/profile', component: ProfessionalProfilePage },
    {path : '/professional/search', component: ProfessionalSearchPage }, 
    {path : '/professional/summary', component: ProfessionalSummaryPage },
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