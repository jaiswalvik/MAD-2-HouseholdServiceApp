
export default {
    data() {
        return {
            services: [], // Fetch from API or store
            professionalProfile: [], // Fetch from API or store
            serviceType: {}, // Fetch from API or store
            userDict: {}, // Fetch from API or store
            users: [], // Fetch from API or store
            serviceRequests: [], // Fetch from API or store
            profDict: {}, // Fetch from API or store
        };
    },
    template: `
    <div> <!-- Root element wrapping all content -->
        <div class="row">
            <div class="col-md-12">
                <h3>Manage Services</h3>
                <div class="d-flex justify-content-end">
                    <router-link to="/admin/services/create_services" class="btn btn-outline-success">Create Service</router-link>
                </div>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Base Price</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="service in services" :key="service.id">
                            <td>{{ service.id }}</td>
                            <td>{{ service.name }}</td>
                            <td>{{ service.price }}</td>
                            <td>
                                <router-link :to="'/admin/services/update/' + service.id" class="btn btn-warning">Edit</router-link>
                                <button @click="deleteService(service.id)" class="btn btn-danger">Delete</button>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <h3>Manage Professionals</h3>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Service</th>
                            <th>Experience</th>
                            <th>Reviews</th>
                            <th>Doc</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="professional in professionalProfile" :key="professional.id">
                            <td>{{ professional.id }}</td>
                            <td>{{ professional.full_name }}</td>
                            <td>{{ serviceType[professional.user_id].name }}</td>
                            <td>{{ professional.experience }}</td>
                            <td>{{ professional.reviews }}</td>
                            <td><a :href="'/download/' + professional.filename">{{ professional.filename }}</a></td>
                            <td>
                                <router-link :to="'/admin/manage_user/' + professional.user_id + '/approve/' + userDict[professional.user_id].approve" 
                                    :class="userDict[professional.user_id].approve ? 'btn btn-secondary' : 'btn btn-success'">
                                    {{ userDict[professional.user_id].approve ? 'Reject' : 'Approve' }}
                                </router-link>
                                <router-link :to="'/admin/manage_user/' + professional.user_id + '/blocked/' + userDict[professional.user_id].blocked" 
                                    :class="userDict[professional.user_id].blocked ? 'btn btn-success' : 'btn btn-danger'">
                                    {{ userDict[professional.user_id].blocked ? 'Unblock' : 'Block' }}
                                </router-link>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <h3>Manage Customers</h3>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>User Name</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in users" :key="user[0]">
                            <td>{{ user.id }}</td>
                            <td>{{ user.username }}</td>
                            <td>
                                <router-link :to="'/admin/manage_user/' + user[0] + '/approve/' + user[2]" 
                                    :class="user[2] ? 'btn btn-secondary' : 'btn btn-success'">
                                    {{ user[2] ? 'Reject' : 'Approve' }}
                                </router-link>
                                <router-link :to="'/admin/manage_user/' + user[0] + '/blocked/' + user[3]" 
                                    :class="user[3] ? 'btn btn-success' : 'btn btn-danger'">
                                    {{ user[3] ? 'Unblock' : 'Block' }}
                                </router-link>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <h3>Service Requests</h3>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Assigned Professional</th>
                            <th>Requested Date</th>
                            <th>Status</th>
                            <th>Customer Remarks</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="serviceRequest in serviceRequests" :key="serviceRequest.id">
                            <td>{{ serviceRequest.id }}</td>
                            <td>{{ profDict[serviceRequest.professional_id].full_name }}</td>
                            <td>{{ serviceRequest.date_of_request }}</td>
                            <td>{{ serviceRequest.service_status }}</td>
                            <td>{{ serviceRequest.remarks || "" }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `,
    mounted() {
        this.fetchAdminDashboard();
    },
    methods: {
        async fetchAdminDashboard() {
            try {
                const res = await fetch(location.origin + '/admin/dashboard', 
                    {
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token')}, 
                    });                
                if (res.ok) {
                    const data = await res.json();
                    this.services = data.services;
                    this.professionalProfile = data.professional_profiles;
                    this.serviceType = data.service_type;
                    this.userDict = data.user_dict;
                    this.users = data.customers;
                    this.serviceRequests = data.service_requests;
                    this.profDict = data.prof_dict;
                } else {
                    res.json().then(data => {
                        console.log(data);
                    });
                    console.log("Error"); 
                }                
            } catch (error) {
                console.log("Error");
            }
        },
        async deleteService(serviceId) {
            const confirmed = confirm("Are you sure you want to delete this service?");
            if (!confirmed) return;
    
            try {
                const response = await fetch(`/admin/services/delete/${serviceId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    }
                });
                if (response.ok) {
                    alert("Service deleted successfully!");
                    this.services = this.services.filter(service => service.id !== serviceId);
                } else {
                    const errorData = await response.json();
                    alert(errorData.message || "Failed to delete service.");
                }
            } catch (error) {
                console.error("An error occurred:", error);
                alert("An error occurred while deleting the service.");
            }
        }
    }
};
