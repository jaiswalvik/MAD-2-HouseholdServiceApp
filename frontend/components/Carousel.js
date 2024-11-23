export default {
  props: {
    slides: {
      type: Array,
      required: true,
    },
    carouselId: {
      type: String,
      required: true,
    },
  },
  template: `
    <div :id="carouselId" class="carousel slide" data-bs-ride="carousel" data-bs-interval="3000">
      <!-- Indicators -->
      <div class="carousel-indicators">
        <button
          v-for="(slide, index) in slides"
          :key="index"
          type="button"
          :data-bs-target="'#' + carouselId"
          :data-bs-slide-to="index"
          :class="{ active: index === 0 }"
          :aria-current="index === 0 ? 'true' : undefined"
        ></button>
      </div>
  
      <!-- Carousel Items -->
      <div class="carousel-inner">
        <div
          class="carousel-item"
          :class="{ active: index === 0 }"
          v-for="(slide, index) in slides"
          :key="index"
        >
          <img :src="slide.image" class="d-block w-100" :alt="slide.alt" />
          <div class="carousel-caption d-none d-md-block">
            <button @click="navigateTo(slide.link)" class="btn">
              <h5>{{ slide.title }}</h5>
              <p>{{ slide.description }}</p>
            </button>
          </div>
        </div>
      </div>
  
      <!-- Controls -->
      <button
        class="carousel-control-prev"
        type="button"
        :data-bs-target="'#' + carouselId"
        data-bs-slide="prev"
      >
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
      </button>
      <button
        class="carousel-control-next"
        type="button"
        :data-bs-target="'#' + carouselId"
        data-bs-slide="next"
      >
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
      </button>
    </div>
  `,
  mounted() {
    // Manually initialize the carousel on page load
    const carouselElement = document.getElementById(this.carouselId);
    if (carouselElement) {
      new bootstrap.Carousel(carouselElement);
    }
  },
  methods: {
    navigateTo(url) {
      this.$router.push(url).catch((error) => {
        console.error("Navigation error:", error);
      });
    },
  }
};
