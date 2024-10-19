export default {
    template: `
    <div class="row">
        <div class="col-md-4 offset-md-4">        
            <h3>Admin Login</h3>
            <div v-if="message" :class="'alert alert-' + category" role="alert">
                {{ message }}
            </div>
            <form @submit.prevent="submitLogin"> <!-- Prevent default form submission -->
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" v-model="username" required> <!-- Use v-model to bind input -->
                </div>
                <div class="form-group">    
                    <label for="password">Password:</label>
                    <input type="password" id="password" v-model="password" required> <!-- Use v-model to bind input -->
                </div> 
                <div class="form-group">       
                    <input type="submit" value="Login" class="btn btn-primary btn-sm btn-spacing">
                </div>    
            </form>
        </div>
    </div>
    `,
    data() {
        return {
            username: null,
            password: null,
            message: null,      
            category: null,     
        };
    },
    methods: {
        async submitLogin() {
            try {
                const res = await fetch(location.origin + '/admin/login', 
                    {
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({ 'username': this.username, 'password': this.password })
                    });                
                if (res.ok) {
                    const data = await res.json();
                    // Save the token to localStorage or sessionStorage
                    localStorage.setItem('token', data.access_token); 
                    // call the login function
                    this.$root.login();
                    // Redirect to the admin dashboard
                    this.$router.push('/admin/dashboard');
                } else {
                    const errorData = await res.json();  
                    this.message = errorData.message; 
                    this.category = errorData.category; 
                }                
            } catch (error) {
                this.message = 'An unexpected error occurred.';
                this.category = 'danger';
            }
        }
    }
};