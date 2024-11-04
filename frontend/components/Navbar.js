export default {
    props: ['userRole'],
    computed: {
        isAdmin() {
            return this.userRole === 'admin';
        },
        isProfessional() {
            return this.userRole === 'professional';
        },
        isCustomer() {
            return this.userRole === 'customer';
        },
    },
    template: `    
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <router-link to="/logout" class="navbar-brand">A-Z Household Services</router-link>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <!-- Admin Links -->
                    <template v-if="isAdmin">
                        <li class="nav-item">
                            <router-link to="/admin/dashboard" class="nav-link">Home</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/admin/profile" class="nav-link">Profile</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/admin/search" class="nav-link">Search</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/admin/summary" class="nav-link">Summary</router-link>
                        </li>                        
                    </template>
                    <!-- Professional Links -->
                    <template v-if="isProfessional">
                        <li class="nav-item">
                            <router-link to="/professional/dashboard" class="nav-link">Home</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/professional/profile" class="nav-link">Profile</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/professional/search" class="nav-link">Search</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/professional/summary" class="nav-link">Summary</router-link>
                        </li>                        
                    </template>
                    <!-- Customer Links -->
                    <template v-if="isCustomer">
                        <li class="nav-item">
                            <router-link to="/customer/dashboard" class="nav-link">Home</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/customer/profile" class="nav-link">Profile</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/customer/search" class="nav-link">Search</router-link>
                        </li>
                        <li class="nav-item">
                            <router-link to="/customer/summary" class="nav-link">Summary</router-link>
                        </li>
                    </template>
                    <!-- Logout Link (Common to All) -->
                    <li class="nav-item">
                        <router-link to="/logout" class="nav-link">Logout</router-link>
                    </li>
                </ul>
            </div>
        </nav>
    `
};
