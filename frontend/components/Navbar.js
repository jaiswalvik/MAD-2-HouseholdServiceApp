export default {
    template : `    
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <router-link to="/" class="navbar-brand" >A-Z Household Services</router-link>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <router-link to="/admin/dashboard" class="nav-link">Home</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/admin/profile" class="nav-link">Profile</router-link>
                    </li>
                    <li class="nav-item"></li>
                        <router-link to="/admin/search" class="nav-link">Search</router-link>
                    </li>
                    <li class="nav-item"></li>
                        <router-link to="/admin/summary" class="nav-link">Summary</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/logout" class="nav-link">Logout</router-link>
                    </li>
                </ul>
            </div>
        </nav>
    `
}