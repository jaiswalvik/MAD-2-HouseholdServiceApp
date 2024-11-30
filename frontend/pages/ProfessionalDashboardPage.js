export default {
    template: `
    <div>
        <div class="row">
            <div class="col-md-12">        
                <h3>Today's Services</h3>
                <div v-if="message" :class="'alert alert-' + category" role="alert">
                        {{ message }}
                </div>        
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Customer Name</th>
                            <th>Service</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="serviceRequest in serviceRequests" :key="serviceRequest.id">
                            <td>{{ custDict[serviceRequest.customer_id].full_name }}</td>
                            <td>{{ serviceDict[serviceRequest.service_id].name }}</td>
                            <td>{{ serviceRequest.service_status }}</td>
                            <td>
                                <button @click="updateRequestStatus('accept', serviceRequest.id)" class="btn btn-success">Accept</button>
                                <button @click="updateRequestStatus('reject', serviceRequest.id)" class="btn btn-danger">Reject</button>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <h3>Rejected/Accepted/Closed Services</h3>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Customer Name</th>
                            <th>Service</th>
                            <th>Status</th>
                            <th>Completion Date</th>
                            <th>Remarks</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="serviceRequestClosed in serviceRequestsClosed" :key="serviceRequestClosed.id">
                            <td>{{ custDict[serviceRequestClosed.customer_id].full_name }}</td>
                            <td>{{ serviceDict[serviceRequestClosed.service_id].name }}</td>
                            <td>{{ serviceRequestClosed.service_status }}</td>
                            <td>{{ serviceRequestClosed.date_of_completion || '' }}</td>
                            <td>{{ serviceRequestClosed.remarks || '' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            message : null,
            category : null,
            serviceRequests: [], // Load from API or parent component
            serviceRequestsClosed: [], // Load from API or parent component
            custDict: {}, // Load from API or parent component
            serviceDict: {} // Load from API or parent component
        };
    },
    mounted() {
        this.fetchProfessionalDashboard();
    },
    methods: {
        async fetchProfessionalDashboard() {
            try {
                const res = await fetch(location.origin + '/professional/dashboard', 
                    {
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token')}, 
                    });                
                if (res.ok) {
                    const data = await res.json();
                    this.serviceRequests= data.service_requests;
                    this.serviceRequestsClosed= data.service_requests_closed;
                    this.custDict= data.cust_dict;
                    this.serviceDict= data.service_dict;                
                } else {
                    res.json().then(data => {
                        console.log(data);
                    });
                    console.log("Error"); 
                }                
            } catch (error) {
                console.log("Error"+error);
            }
        },
        async updateRequestStatus(status, serviceRequestId) {
            try {
                const res = await fetch(location.origin + '/professional/update_request_status/' + status + '/' + serviceRequestId, 
                    {
                        method: 'PUT', 
                        headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token')}, 
                    });                
                if (res.ok) {
                    const data = await res.json();
                    this.message = data.message;
                    this.category = data.category;
                    this.fetchProfessionalDashboard();
                } else {
                    res.json().then(data => {
                        console.log(data);
                    });
                    console.log("Error"); 
                }                
            } catch (error) {
                console.log("Error"+error);
            }
        }
    }
};
