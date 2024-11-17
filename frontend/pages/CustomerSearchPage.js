export default {
    template: `
      <div>
        <div class="row">
          <div class="col-md-4 offset-md-4">
            <h3>Customer Search</h3>
            <!-- Flash Messages -->
            <div v-if="messages.length" class="flash-messages">
              <div v-for="(message, index) in messages" :key="index" :class="'alert alert-' + message.category">
                {{ message.text }}
              </div>
            </div>
            <!-- Search Form -->
            <form @submit.prevent="submitSearch">
              <div class="form-group">
                <label for="search_type">Search Type</label>
                <select v-model="form.search_type" id="search_type" class="form-control" required>
                  <option value="service">Service Name</option>
                  <option value="location">Location</option>
                  <option value="pin">PIN</option>
                </select>
              </div>
              <div class="form-group">
                <label for="search_text">Search Text</label>
                <input v-model="form.search_text" id="search_text" type="text" class="form-control" />
              </div>
              <div class="form-group text-center">
                <button type="submit" class="btn btn-primary btn-sm">Submit</button>
                <router-link to="/customer/dashboard" class="btn btn-secondary btn-sm">Cancel</router-link>
              </div>
            </form>
          </div>
        </div>
  
        <br /><br />
  
        <!-- Search Results -->
        <div class="container mt-4">
          <div class="col-md-12">
            <h3 v-if="service_professional.length">Services</h3>
            <table v-if="service_professional.length" class="table table-striped">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Location</th>
                  <th>Pin Code</th>
                  <th>Base Price</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(service, index) in service_professional" :key="index">
                  <td>{{ service.service_name }}</td>
                  <td>{{ service.service_description }}</td>
                  <td>{{ service.address }}</td>
                  <td>{{ service.pin_code }}</td>
                  <td>{{ service.service_price }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `,
    data() {
      return {
        form: {
          search_type: "service", // Default value
          search_text: ""
        },
        service_professional: [],
        messages: []
      };
    },
    methods: {
      async submitSearch() {
        this.messages = [];
        try {
          const res = await fetch(`${location.origin}/customer/search`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({
              search_type: this.form.search_type,
              search_text: this.form.search_text
            })
          });
  
          const data = await res.json();
          if (res.ok) {
            this.service_professional = data.data.service_professional;
            this.messages.push({ category: "success", text: data.message });
          } else {
            this.service_professional = [];
            this.messages.push({
              category: data.category || "danger",
              text: data.message || "An error occurred during the search."
            });
          }
        } catch (error) {
          console.error("Unexpected error:", error);
          this.service_professional = [];
          this.messages.push({
            category: "danger",
            text: "An unexpected error occurred. Please try again later."
          });
        }
      }
    }
  };
  