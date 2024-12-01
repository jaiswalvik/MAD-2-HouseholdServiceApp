export default {
    template: `
        <div class="row">
            <div class="col-md-4 offset-md-4">        
                <h3>Service - Remarks</h3>
                
                <!-- Flash Messages -->
                <div v-if="flashMessages.length" class="flash-messages">
                    <div 
                        v-for="(message, index) in flashMessages" 
                        :key="index" 
                        class="alert" 
                        :class="'alert-' + message.category">
                        {{ message.text }}
                    </div>
                </div>

                <!-- Service Remarks Form -->
                <form @submit.prevent="submitForm">
                    <div class="form-group">
                        <label for="requestId">Request ID</label>
                        <input 
                            type="text" 
                            id="requestId" 
                            v-model="formData.request_id" 
                            class="form-control" 
                            readonly>
                    </div>
                    <div class="form-group">
                        <label for="serviceName">Service Name</label>
                        <input 
                            type="text" 
                            id="serviceName" 
                            v-model="formData.service_name" 
                            class="form-control" 
                            readonly>
                    </div>
                    <div class="form-group">
                        <label for="fullName">Full Name</label>
                        <input 
                            type="text" 
                            id="fullName" 
                            v-model="formData.full_name" 
                            class="form-control" 
                            readonly>
                    </div>
                    <div class="form-group">
                        <label for="serviceDescription">Service Description</label>
                        <input 
                            type="text" 
                            id="serviceDescription" 
                            v-model="formData.service_description" 
                            class="form-control" 
                            readonly>
                    </div>
                    <div class="form-group">
                        <label for="remarks">Remarks</label>
                        <textarea 
                            id="remarks" 
                            v-model="formData.remarks" 
                            class="form-control">
                        </textarea>
                    </div>
                    <div class="form-group">
                        <label for="rating">Rating</label>
                        <input 
                            type="number" 
                            id="rating" 
                            v-model="formData.rating" 
                            class="form-control">
                    </div>
                    <div class="form-group text-center">
                        <button type="submit" class="btn btn-primary btn-sm btn-spacing">Submit</button>
                        <button @click="cancel" type="button" class="btn btn-secondary btn-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    `,
    props: {
        id: {
            type: [String, Number],
            default: null
        }
    },
    created() {
        if (this.id) {
            this.fetchServiceRequest();
        }else{
            alert('No service request provided');
            this.$router.push('/customer/dashboard');
        }
    },
    data() {
        return {
            flashMessages: [], // Array to hold flash messages
            formData: {
                request_id: '', 
                service_name: '',
                full_name: '',
                service_description: '',
                remarks: '',
                rating: 0,
            },
        };
    },
    methods: {
        async submitForm() {
            try {
                const response = await fetch(`/customer/close_service_request/${this.formData.request_id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type' : 'application/json',
                        'Authorization' : `Bearer ${localStorage.getItem('token')}`,
                    },
                    body: JSON.stringify(this.formData),
                });
                if (response.ok) {
                    const data = await response.json();
                    console.log("data:"+data);
                    this.flashMessages = [{ text:data.message, category: data.category }];
                    this.$router.push('/customer/dashboard');
                } else {
                    const errorData = await response.json();
                    this.flashMessages = [{ text: errorData.message, category: data.category }];
                }
            } catch (error) {
                this.flashMessages = [{ text: 'An error occurred. Please try again later.', category: 'danger' }];
                console.log(error);
            }
        },
        cancel() {
            this.$router.push('/customer/dashboard'); // Navigate to the dashboard
        },
        async fetchServiceRequest() {
            try {
                const response = await fetch(`customer/close_service_request/${this.id}`, {
                    method : 'GET',
                    headers: {  'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.formData = data;
                } else {
                    this.flashMessages = [{ text: 'Failed to load service request data', category: 'danger' }];
                }
            } catch (error) {
                this.flashMessages = [{ text: 'An error occurred. Please try again later.', category: 'danger' }];
                console.error(error);
            }
        }    
    },
};
