export default {
    template: `
      <div class="container">
        <div class="row">
          <div class="col-md-12 text-center">        
            <h3 class="mt-5">Admin Summary</h3>
          </div>
        </div>
        <div class="row">
          <div class="col-md-6">
            <h3>Overall Customer Ratings</h3>
            <canvas id="reviewsDoughnutChart" width="400" height="200"></canvas>
          </div>
          <div class="col-md-6">
            <h3>Service Request Summary</h3>
            <canvas id="serviceRequests" width="400" height="400"></canvas>
          </div>
        </div>
      </div>
    `,
    data() {
      return {
        reviewsDoughnutChart: null,
        serviceRequestsChart: null,
      };
    },
    methods: {
      async fetchReviewsData() {
        try {
          const response = await fetch(`${location.origin}/admin/summary/reviews`);
          const data = await response.json();
          const labels = data.map(item => item.full_name);
          const reviews = data.map(item => item.reviews);
          this.updateDoughnutChart(labels, reviews);
        } catch (error) {
          console.error('Error fetching data:', error);
        }
      },
      updateDoughnutChart(labels, data) {
        const ctx = document.getElementById('reviewsDoughnutChart').getContext('2d');
        if (this.reviewsDoughnutChart) this.reviewsDoughnutChart.destroy();
        this.reviewsDoughnutChart = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: labels,
            datasets: [{
              label: 'Reviews of Professionals',
              data: data,
              backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)'
              ],
              borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'top' },
              tooltip: {
                callbacks: {
                  label: tooltipItem => `Reviews: ${tooltipItem.raw}`
                }
              }
            }
          }
        });
      },
      async fetchServiceRequests() {
        try {
          const response = await fetch(`${location.origin}/admin/summary/service_requests`);
          const data = await response.json();
          const labels = data.map(item => item.date);
          const count = data.map(item => item.count);
          this.updateServiceRequestChart(labels, count);
        } catch (error) {
          console.error('Error fetching data:', error);
        }
      },
      updateServiceRequestChart(labels, data) {
        const ctx = document.getElementById('serviceRequests').getContext('2d');
        if (this.serviceRequestsChart) this.serviceRequestsChart.destroy();
        this.serviceRequestsChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Service Request Summary',
              data: data,
              backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)'
              ],
              borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'top' },
              tooltip: {
                callbacks: {
                  label: tooltipItem => `Count: ${tooltipItem.raw}`
                }
              }
            }
          }
        });
      }
    },
    mounted() {
      this.fetchReviewsData();
      this.fetchServiceRequests();
    }
  };
  