export default {
    template : `
    <div class="row">
        <div class="col-md-4 offset-md-4">        
            <h3>Login</h3>
            <div v-if="message" :class="'alert alert-' + category" role="alert">
                {{ message }}
            </div>
            <form @submit.prevent="submitLogin">
                <div class="form-group">
                    <label for="username">Username(e-mail):</label>
                    <input type="text" id="username" v-model="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" v-model="password" required>
                </div>
                <div class="form-group" >
                    <input type="submit" value="Login" class="btn btn-primary btn-sm btn-spacing">
                </div>
                <div class="form-group" >
                    <router-link to="/register">Register Customer/Professional</router-link>    
                </div>    
            </form>
        </div>
    </div>
    `,
    data(){
        return {
            username : null,
            password : null,
            message: null,      
            category: null,
        } 
    },
    methods: {
        async submitLogin() {
            try {
                const res = await fetch(location.origin + '/login', 
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
                    // Redirect to differnt dashboard based on user type
                    try {
                        const res = await fetch(location.origin + '/get-claims', 
                            {
                                method: 'GET', 
                                headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token')}, 
                            });                
                        if (res.ok) {
                            const data =await res.json();
                            console.log('Received data:', data.claims);
                            if (data.role === 'customer' && data.redirect === 'customer_dashboard') {
                                this.$router.push('/customer/dashboard');
                            } else if (data.role === 'professional' && data.redirect === 'professional_dashboard') {
                                this.$router.push('/professional/dashboard');
                            } else if (data.role === 'professional' && data.redirect === 'professional_profile') {
                                this.$router.push('/professional/profile');
                            } else if (data.role === 'customer' && data.redirect === 'customer_profile') {
                                this.$router.push('/customer/profile');
                            }else{
                                this.message = 'An unexpected error occurred.';
                                this.category = 'danger';
                            }
                        }else{
                            this.message = 'An unexpected error occurred.';
                            this.category = 'danger';
                        }
                    } catch (error) {
                        this.message = 'An unexpected error occurred.';
                        this.category = 'danger';
                    }        
                }else {
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
}