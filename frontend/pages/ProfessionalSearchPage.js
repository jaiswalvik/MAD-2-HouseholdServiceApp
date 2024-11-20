export default {
    template: `
      <div>
        <div class="row">
          <div class="col-md-4 offset-md-4">
            <h3>Professional Search</h3>
  
            <!-- Validation Errors -->
            <ul v-if="errors.search_text">
              <li v-for="(error, index) in errors.search_text" :key="index" style="color: red;">
                {{ error }}
              </li>
            </ul>
  
            <!-- Flash Messages -->
            <div v-if="messages.length" class="flash-messages">
              <div
                v-for="(message, index) in messages"
                :key="index"
                :class="'alert alert-' + message.category"
              >
                {{ message.text }}
              </div>
            </div>
  
            <!-- Search Form -->
            <form @submit.prevent="submitSearch">
              <div class="form-group">
                <label for="search_type">Search Type</label>
                <select v-model="form.search_type" id="search_type" class="form-control" required>
                  <option value="service">Service</option>
                  <option value="customer_name">Customer Name</option>
                </select>
              </div>
              <div class="form-group">
                <label for="search_text">Search Text</label>
                <input
                  v-model="form.search_text"
                  id="search_text"
                  type="text"
                  class="form-control"
                  required
                />
              </div>
              <div class="form-group text-center">
                <button type="submit" class="btn btn-primary btn-sm">Submit</button>
              </div>
            </form>
          </div>
        </div>
  
        <br /><br />
  
        <!-- Search Results -->
        <div class="container mt-4">
          <div class="col-md-12">
            <h3 v-if="searchResults.length">Search Results</h3>
            <table v-if="searchResults.length" class="table table-striped">
              <thead>
                <tr>
                  <th>Customer Name</th>
                  <th>Service</th>
                  <th>Status</th>
                  <th>Start Date</th>
                  <th>Remarks</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(result, index) in searchResults" :key="index">
                  <td>{{ result.customer_name }}</td>
                  <td>{{ result.service_name }}</td>
                  <td>{{ result.status }}</td>
                  <td>{{ result.start_date }}</td>
                  <td>{{ result.remarks }}</td>
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
          search_type: "",
          search_text: "",
        },
        errors: {
          search_text: [],
        },
        messages: [],
        searchResults: [],
      };
    },
    methods: {
      async submitSearch() {
        this.messages = [];
        this.errors = { search_text: [] };
  
        try {
          const res = await fetch(`${location.origin}/professional/search`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
            body: JSON.stringify(this.form),
          });
  
          if (res.ok) {
            const data = await res.json();
            this.searchResults = data.results || [];
            this.messages.push({ category: "success", text: data.message });
          } else {
            const errorData = await res.json();
            this.messages.push({
              category: "danger",
              text: errorData.message || "An error occurred during the search.",
            });
          }
        } catch (error) {
          console.error("Unexpected error:", error);
          this.messages.push({
            category: "danger",
            text: "An unexpected error occurred. Please try again later.",
          });
        }
      },
    },
  };
  