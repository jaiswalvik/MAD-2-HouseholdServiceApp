export default {
    props: {
        editing: {
            type: Boolean,
            default: false
        },
        id: {
            type: [String, Number],
            default: null
        }
    },
    data() {
        return {
            service: {
                id: this.id,
                service_type: '',
                name: '',
                description: '',
                price: ''
            },
            message: null,
            category: null
        };
    },
    created() {
        if (this.editing && this.id) {
            this.fetchServiceData();
        }
    },
    methods: {
        async fetchServiceData() {
            try {
                const response = await fetch(`/admin/services/get/${this.id}`,{headers: {'Authorization': 'Bearer ' + localStorage.getItem('token')}});
                if (response.ok) {
                    const data = await response.json();
                    this.service = data;
                } else {
                    this.message = 'Failed to load service data';
                    this.category = 'danger';
                }
            } catch (error) {
                this.message = 'An error occurred while fetching the service data';
                this.category = 'danger';
            }
        },
        async submitForm() {
            try {
                const url = this.editing
                    ? `/admin/services/update/${this.service.id}`
                    : '/admin/services/create_services';
                
                const response = await fetch(url, {
                    method: this.editing ? 'PUT' : 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    },
                    body: JSON.stringify(this.service)
                });

                if (response.ok) {
                    this.message = this.editing ? 'Service updated successfully!' : 'Service created successfully!';
                    this.category = 'success';
                    this.$router.push('/admin/dashboard');
                } else {
                    const errorData = await response.json();
                    this.message = errorData.message || 'An error occurred.';
                    this.category = 'danger';
                }
            } catch (error) {
                this.message = 'An unexpected error occurred.';
                this.category = 'danger';
            }
        }
    },
    template: `
        <div class="row">
            <div class="col-md-4 offset-md-4">
                <h3>{{ editing ? 'Edit Service' : 'New Service' }}</h3>
                
                <div v-if="message" :class="'alert alert-' + category" role="alert">
                    {{ message }}
                </div>

                <form @submit.prevent="submitForm">
                    <div class="form-group">
                        <label for="service_type">Service Type</label>
                        <select id="service_type" v-model="service.service_type" class="form-control" required>
                            <option value="haircut">Hair Cut</option>
                            <option value="cleaning">Cleaning Services</option>
                            <option value="electrical">Electrical Services</option>
                            <option value="painting">Painting Services</option>
                            <option value="plumbing">Plumbing Services</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="name">Name</label>
                        <input type="text" id="name" v-model="service.name" class="form-control" required>
                    </div>

                    <div class="form-group">
                        <label for="description">Description</label>
                        <textarea id="description" v-model="service.description" class="form-control" required></textarea>
                    </div>

                    <div class="form-group">
                        <label for="price">Price</label>
                        <input type="number" id="price" v-model="service.price" class="form-control" required>
                    </div>

                    <div class="form-group text-center">
                        <button type="submit" class="btn btn-primary btn-sm">Submit</button>
                        <router-link to="/admin/dashboard" class="btn btn-secondary btn-sm">Cancel</router-link>
                    </div>
                </form>
            </div>
        </div>
    `
};
