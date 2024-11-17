export default {
    template: `
    <div class="row">
        <div class="col-md-4 offset-md-4">        
            <h3>Customer Profile</h3>         
            <div v-if="message" :class="'alert alert-' + category" role="alert">
                {{ message }}
            </div>            
            <form @submit.prevent="handleSubmit">
                <div class="form-group">
                    <label for="user_name">User Name</label>
                    <input 
                        type="text" 
                        id="user_name" 
                        v-model="form.user_name" 
                        class="form-control" 
                        readonly 
                    />
                </div>
                
                <div class="form-group">
                    <label for="full_name">Full Name</label>
                    <input 
                        type="text" 
                        id="full_name" 
                        v-model="form.full_name" 
                        class="form-control" 
                    />
                </div>
                
                <div class="form-group">
                    <label for="address">Address</label>
                    <input 
                        type="text" 
                        id="address" 
                        v-model="form.address" 
                        class="form-control" 
                    />
                </div>
                
                <div class="form-group">
                    <label for="pin_code">Pin Code</label>
                    <input 
                        type="text" 
                        id="pin_code" 
                        v-model="form.pin_code" 
                        class="form-control" 
                    />
                </div>                
                <div class="form-group text-center">
                    <button type="submit" class="btn btn-primary btn-sm">Submit</button>
                </div>
            </form>
        </div>
    </div>
    `,    
    data() {
        return {
            form: {
                user_name: '',
                full_name: '',
                address: '',
                pin_code: ''
            },
            user_id : '',
            message: '',
            category: '',            
        };
    },
    mounted() {
        this.fetchCustomerProfile();
    },
    methods: {
        async fetchCustomerProfile() {
            try{
                const response = await fetch('/customer/profile', {
                    method: 'GET',
                    headers: {  'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + localStorage.getItem('token') }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.user_id = data.user_id;
                    this.form.user_name = data.username;
                    this.form.full_name = data.full_name;
                    this.form.address = data.address;
                    this.form.pin_code = data.pin_code;
                } else {
                    this.message = 'Failed to load profile data';
                    this.category = 'danger';
                }
            }catch (error) {
                this.message = 'An error occurred while fetching the profile data';
                this.category = 'danger';
            }
        },
        async handleSubmit() {
            try{
                const response = await fetch('/customer/profile', {
                    method: 'POST',
                    headers: {  'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + localStorage.getItem('token') },
                    body: JSON.stringify({ 'full_name': this.form.full_name,
                                           'address': this.form.address,
                                           'pin_code': this.form.pin_code })
                });
                if (response.ok) {
                    const data = await response.json();
                    this.message = data.message
                    this.category = data.category;
                }else{
                    this.message = 'Failed to update profile data';
                    this.category = 'danger';
                }
            }catch (error) {
                this.message = 'An error occurred while updating the profile data';
                this.category = 'danger';
            }            
        }

    }
};
