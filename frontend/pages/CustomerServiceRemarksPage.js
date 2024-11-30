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
    data() {
        return {
            flashMessages: [], // Array to hold flash messages
            formData: {
                request_id: '123', // Example pre-filled data
                service_name: 'Cleaning Service',
                full_name: 'John Doe',
                remarks: '',
                rating: 5,
            },
        };
    },
    methods: {
        async submitForm() {
            try {
                const response = await fetch(`/customer/close_service_request/${this.formData.request_id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.formData),
                });

                if (response.ok) {
                    const data = await response.json();
                    this.flashMessages = [{ text: data.message, category: 'success' }];
                } else {
                    const errorData = await response.json();
                    this.flashMessages = [{ text: errorData.message, category: 'danger' }];
                }
            } catch (error) {
                this.flashMessages = [{ text: 'An error occurred. Please try again later.', category: 'danger' }];
                console.error(error);
            }
        },
        cancel() {
            window.location.href = '/customer_dashboard'; // Navigate to the dashboard
        },
    },
};
