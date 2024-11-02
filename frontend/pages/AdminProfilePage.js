export default {
    template: `
    <div class="row">
        <div class="col-md-4 offset-md-4">        
            <h3>Admin Profile</h3>
            <div v-if="message" :class="'alert alert-' + category" role="alert">
                    {{ message }}
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            message: '',
            category: '',
        };
    },
    created() {
        this.fetchProfileData();
    },
    methods: {
        async fetchProfileData() {
            try {
                const response = await fetch('/admin/profile', {
                    method: 'POST',
                    headers: {  'Authorization': 'Bearer ' + localStorage.getItem('token') }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.message = data.message;
                    this.category = data.category;
                } else {
                    this.message = 'Failed to load profile data';
                    this.category = 'danger';
                }
            } catch (error) {             
                this.message = 'An error occurred while fetching the profile data';
                this.category = 'danger';
            }
        }
    },
}