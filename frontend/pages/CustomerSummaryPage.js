export default {
    template: `
      <div class="container">
        <div class="row">
          <div class="col-md-12 text-center">        
            <h3>Customer Summary</h3>
          </div>
        </div>
        <div class="row">
          <div class="col-md-12">
            <canvas id="serviceRequests" width="400" height="200"></canvas>
          </div>
        </div>
      </div>
    `,
    data() {
      return {
        serviceRequestsChart: null,
      };
    },
    methods: {
      async fetchServiceRequestsCustomer() {
        try {
          // First fetch user ID via claims
          const claimsResponse = await fetch(`${location.origin}/get-claims`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
  
          if (!claimsResponse.ok) {
            console.error('Error fetching claims:', claimsResponse.statusText);
            return;
          }
  
          const claimData = await claimsResponse.json();
          const userId = claimData.claims.user_id;
  
          // Now fetch service request data for this user
          const serviceResponse = await fetch(`${location.origin}/customer/summary/service_requests/${userId}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
  
          if (!serviceResponse.ok) {
            console.error('Error fetching service request data:', serviceResponse.statusText);
            return;
          }
  
          const serviceData = await serviceResponse.json();
          const labels = serviceData.map(item => item.date);
          const counts = serviceData.map(item => item.count);
          this.updateServiceRequestCustomerChart(labels, counts);
  
        } catch (error) {
          console.error('Error fetching data:', error);
        }
      },
      updateServiceRequestCustomerChart(labels, data) {
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
      this.fetchServiceRequestsCustomer();
    }
  };
  