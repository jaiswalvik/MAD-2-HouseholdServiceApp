import Carousel from "../components/Carousel.js";

export default {
  components: {
    Carousel,
  },
  data() {
    return {
      services: [],
      serviceType: null,
      carouselSlides: [
        {
          image: "/static/static/images/cleaning.jpg",
          alt: "Cleaning Services",
          link: "/customer/dashboard?service_type=cleaning",
          title: "Cleaning Services",
          description: "Keep your home or office spotless with our professional cleaning services.",
        },
        {
          image: "/static/static/images/plumber.jpg",
          alt: "Plumbing Services",
          link: "/customer/dashboard?service_type=plumbing",
          title: "Plumbing Services",
          description: "Fix leaks and plumbing issues with our experienced plumbers.",
        },
        {
          image: "/static/static/images/electrical.jpg",
          alt: "Electrical Services",
          link: "/customer/dashboard?service_type=electrical",
          title: "Electrical Services",
          description: "Get reliable electrical services for your home or office needs.",
        },
        {
          image: "/static/static/images/painting.jpg",
          alt: "Painting Services",
          link: "/customer/dashboard?service_type=painting",
          title: "Painting Services",
          description: "Beautify your space with our expert painting services.",
        },
        {
          image: "/static/static/images/haircut.jpg",
          alt: "Haircut at Home Services",
          link: "/customer/dashboard?service_type=haircut",
          title: "Haircut at Home",
          description: "Get a professional haircut at the comfort of your home.",
        },
      ],
      serviceRequests: [],
      serviceDict: {},
      profDict: {},
    };
  },
  mounted() {
    const queryParams = this.$route.query;
    if (queryParams.service_type) {
      this.serviceType = queryParams.service_type;
    }
    this.fetchServices();
    this.fetchServiceHistory();
  },
  watch: {
    // Watch for changes in the query parameters (in case the user navigates to the same page with different query)
    "$route.query.service_type": function(newServiceType) {
      this.serviceType = newServiceType;
      this.fetchServices();
    }
  },
  methods: {
    async fetchServices() {
      try {
        const apiUrl = this.serviceType
          ? `/customer/dashboard?service_type=${this.serviceType}`
          : "/customer/dashboard";
        const response = await fetch(apiUrl,{
            method : 'GET',
            headers: {
                Authorization: "Bearer " + localStorage.getItem("token")
            }
        });
        const data = await response.json();
        this.services = data.services || [];
        this.serviceRequests = data.service_requests || [];
        this.serviceDict = data.service_dict || {};
        this.profDict = data.prof_dict || {};
      } catch (error) {
        console.error("Error fetching services:", error);
      }
    },
  },     
  template: `
    <div class="container">
      <div class="row">
        <div class="col-md-4 offset-md-4">        
          <h3>Customer Dashboard</h3>
        </div>
      </div>
  
      <!-- Carousel Section -->
      <Carousel :slides="carouselSlides" carousel-id="serviceCarousel" />
  
      <!-- Services Table -->
      <table class="table table-striped mt-4">
        <thead>
          <tr>
            <th>Service Name</th>
            <th>Description</th>
            <th>Price</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="service in services" :key="service.id">
            <td>{{ service.name }}</td>
            <td>{{ service.description }}</td>
            <td>{{ service.price }}</td>
            <td>
              <a :href="'/customer/create_service_request/' + service.id" class="btn btn-primary">
                Request
              </a>
            </td>
          </tr>
        </tbody>
      </table>
      <h3>Service History</h3>
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Service Name</th>
            <th>Professional</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="serviceRequest in serviceRequests" :key="serviceRequest.id">
            <td>{{ serviceDict[serviceRequest.service_id]?.name }}</td>
            <td>{{ profDict[serviceRequest.professional_id]?.full_name }}</td>
            <td>{{ serviceRequest.service_status }}</td>
            <td>
              <a v-if="serviceRequest.service_status !== 'completed'" :href="'/customer/close_service_request/' + serviceRequest.id" class="btn btn-success">
                Close
              </a>
              <span v-else>Closed</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
};
