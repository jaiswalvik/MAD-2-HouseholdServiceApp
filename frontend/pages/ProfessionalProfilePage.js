export default {
    template: `
      <div class="row">
        <div class="col-md-4 offset-md-4">
          <h3>Professional Profile</h3>
          
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
          
          <!-- Form -->
          <form @submit.prevent="submitForm" enctype="multipart/form-data">
            <div class="form-group">
              <label for="user_name">User Name</label>
              <input
                id="user_name"
                v-model="form.user_name"
                class="form-control"
                type="text"
                readonly
              />
            </div>  
            <div class="form-group">
              <label for="full_name">Full Name</label>
              <input
                id="full_name"
                v-model="form.full_name"
                class="form-control"
                type="text"
              />
            </div>
  
            <div class="form-group">
              <label for="service_type">Service Type</label>
              <select
                id="service_type"
                v-model="form.service_type"
                class="form-control"
              >
                <option disabled value="">Select a service type</option>
                <option v-for="service in serviceOptions" :key="service.id" :value="service.name">
                  {{ service.name }}
                </option>
              </select>
            </div>
  
            <div class="form-group">
              <label for="experience">Experience</label>
              <input
                id="experience"
                v-model="form.experience"
                class="form-control"
                type="text"
              />
            </div>
  
            <div class="form-group">
              <label for="file">File</label>
              <input
                id="file"
                type="file"
                class="form-control"
                @change="handleFileUpload"
              />
            </div>
  
            <div class="form-group">
              <label for="address">Address</label>
              <textarea
                id="address"
                v-model="form.address"
                class="form-control"
              ></textarea>
            </div>
  
            <div class="form-group">
              <label for="pin_code">Pin Code</label>
              <input
                id="pin_code"
                v-model="form.pin_code"
                class="form-control"
                type="text"
              />
            </div>
  
            <div class="form-group">
              <button type="submit" class="btn btn-primary btn-sm btn-spacing">
                Submit
              </button>
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
          service_type: '',
          experience: '',
          address: '',
          pin_code: '',
          file: null, // File for upload
        },
        serviceOptions: [], 
        messages: [], // Flash messages
        errors: {}, // Validation errors
      };
    },
    mounted() {
      this.fetchProfileData(); // Fetch data when the component mounts
    },
    methods: {
      // Fetch the professional profile data from the server
      async fetchProfileData() {
        try {
          const response = await fetch('/professional/profile', {
            method: 'GET',
            headers: {
              Authorization: 'Bearer ' + localStorage.getItem('token'),
            },
          });
  
          const result = await response.json();
  
          if (response.ok) {
            this.serviceOptions = result.services;
            // Populate the form with the fetched data
            this.form.user_name = result.profile.username;
            this.form.full_name = result.profile.full_name;
            this.form.service_type = result.profile.service_type;
            this.form.experience = result.profile.experience;
            this.form.address = result.profile.address;
            this.form.pin_code = result.profile.pin_code;
          } else {
            this.messages.push({
              category: result.category || 'danger',
              text: result.message || 'An error occurred while fetching profile data.',
            });
          }
        } catch (error) {
          this.messages.push({
            category: 'danger',
            text: 'An unexpected error occurred. Please try again later.',
          });
        }
      },
      handleFileUpload(event) {
        this.form.file = event.target.files[0]; // Store the uploaded file
      },
      async submitForm() {
        this.messages = [];
        this.errors = {};
  
        // Prepare form data for submission
        const formData = new FormData();
        for (const key in this.form) {
          formData.append(key, this.form[key]);
        }
  
        try {
          const response = await fetch('/professional/profile', {
            method: 'POST',
            headers: {
              Authorization: 'Bearer ' + localStorage.getItem('token'),
            },
            body: formData,
          });
  
          const result = await response.json();
  
          if (response.ok) {
            this.messages.push({ category: 'success', text: result.message });
          } else {
            this.errors = result.errors || {};
            this.messages.push({
              category: result.category || 'danger',
              text: result.message || 'An error occurred.',
            });
          }
        } catch (error) {
          this.messages.push({
            category: 'danger',
            text: 'An unexpected error occurred. Please try again later.',
          });
        }
      },
    },
  };
  