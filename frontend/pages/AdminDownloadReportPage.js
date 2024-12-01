export default {
    template: `
        <div>
            <div class="row">
                <div class="col-md-12">  
                    <h3>Export Service Requests</h3>
                    <!-- Input for professional ID -->
                    <label for="professionalId">Enter Professional ID:</label>
                    <input type="number" id="professionalId" v-model="professionalId" placeholder="Enter Professional ID" required :disabled="isProcessing" />                   
                    <!-- Export Button -->
                    <button @click="triggerExport" :disabled="isProcessing || !professionalId">
                        {{ isProcessing ? 'Processing...' : 'Export Service Requests' }}
                    </button> 
                    <!-- List of available downloads -->
                    <h3>Available Downloads</h3>
                    <ul>
                    <li v-for="(file, index) in downloads" :key="index">
                        <a :href="file" @click.prevent="downloadFile(file)"">{{ file }}</a>
                    </li>
                    </ul>
                <div>
            </div>
        </div>
    `,
    data() {
      return {
        isProcessing: false,     // Track if the process is ongoing
        downloads: [],           // List of available downloads
        professionalId: '',      // Professional ID input by the user
        timer: null,
      };
    },
    methods: {
      // Method to trigger the export task
      async triggerExport() {
        if (!this.professionalId) {
          alert('Please enter a valid professional ID!');
          return;
        }
  
        this.isProcessing = true; // Disable button to prevent multiple clicks
  
        try {
          // Make an API call to start the Celery task
          const response = await fetch('/admin/export/'+ this.professionalId, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + localStorage.getItem('token'),
            },
          });
          if(response.ok){
            alert('Export triggered successfully!');      
          }
        } catch (error) {
          console.error('Error triggering export:', error);
          alert('Failed to trigger the export. Please try again.');
        } finally {
          this.isProcessing = false; // Enable the button again
        }
      },
      // Method to fetch the list of available downloads
      async fetchDownloads() {
        try {
          const response = await fetch('/admin/reports/list',{
            method: 'GET',
            headers: {
                Authorization: 'Bearer ' + localStorage.getItem('token')
            }
          })
          if(response.ok){
            const data = await response.json();
            this.downloads = data.downloads;
          }else{

          }
        } catch (error) {
          console.error('Error fetching downloads:', error);
        }
      },
      async downloadFile(filename) {
        try {
            const response = await fetch(`/admin/reports/download/${filename}`,
                {
                    method: 'GET',
                    headers: {'Authorization': 'Bearer ' + localStorage.getItem('token')},
                }
            );
            if (!response.ok) {
                alert("Error downloading file.");
                return;
            }
            const blob = await response.blob();
            const link = document.createElement("a");
            link.href = window.URL.createObjectURL(blob);
            link.download = filename;
            link.click();    
            // Clean up the object URL to free memory
            window.URL.revokeObjectURL(link.href);
        }catch (error) {
            console.error("Error downloading file:", error);
            alert("An error occurred while downloading the file.");
        }
      },
    },
    mounted() {
        this.fetchDownloads();
        this.timer = setInterval(() => {
            this.fetchDownloads();
        }, 5000);
    },
    beforeDestroy() {
        clearInterval(this.timer)
    }
};