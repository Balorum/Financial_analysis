// Define the data object that will be used to plot the chart
const data = {
        labels: dates, // X-axis labels, representing dates for the stock prices
        datasets: [{
            label: 'Price', // Name of the dataset shown in the chart legend
        backgroundColor: 'rgba(255, 99, 132, 0.2)', // Background color for the data points (semi-transparent red)
        borderColor: 'rgb(255, 99, 132)', // Color of the line representing the data (solid red)
        data: closes, // Y-axis data points representing stock closing prices
        fill: true // Fill the area under the line (true for filled, false for no fill)
        }]
    };

    // Define the configuration for the chart
    const config = {
    type: 'line', // Type of chart (line chart in this case)
    data: data, // The data to be plotted
    options: {
        maintainAspectRatio: false, // Disable maintaining the aspect ratio, allowing it to adjust to container size
        plugins: {
            title: {
                display: true, // Display the title on the chart
                text: 'Stock History', // The text to display as the title of the chart
                font: {
                    size: 24 // Font size of the chart title
                }
            }
        },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)' // Color of the vertical grid lines on the X-axis
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)' // Color of the horizontal grid lines on the Y-axis
                    }
                }
            }
        }
    };

    // Get the canvas context where the chart will be drawn
    const ctx = document.getElementById('myChart').getContext('2d');

    // Create a new Chart instance, passing in the context and the configuration
    const myChart = new Chart(ctx, config);


