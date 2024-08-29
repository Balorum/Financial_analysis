// Asynchronous function to fetch data from the server
async function fetchData() {
    // Send a request to the '/data' endpoint and wait for the response
    const response = await fetch('/data');
    
    // Parse the response data as JSON format
    const data = await response.json();
    
    // Get the first <tbody> element of the table with id 'data-table'
    const tableBody = document.getElementById('data-table').getElementsByTagName('tbody')[0];
    
    // Clear any previous data from the table
    tableBody.innerHTML = '';

    // Loop through each item in the fetched data
    data.forEach(item => {
        // Create a new row for the table
        const row = document.createElement('tr');
        
        // Set the inner HTML of the row, using template literals to populate each cell with item data
        row.innerHTML = `
            <td><a href="/stock/${item.id}" target="_blank">${item.title}</a></td> <!-- Clickable link to the stock page -->
            <td style="text-align: left">${item.last}</td> <!-- Last price of the stock -->
            <td>${item.high}</td> <!-- Highest price of the stock -->
            <td>${item.low}</td> <!-- Lowest price of the stock -->
            <td>${item.volume}</td> <!-- Volume of stocks traded -->
            <td>${item.change}</td> <!-- Absolute change in stock price -->
            <td>${item.change_pct}</td> <!-- Percentage change in stock price -->
            <td class="${item.growth ? 'growth-true' : 'growth-false'}">${item.growth}</td> <!-- Growth indicator, with dynamic class for styling -->
        `;
        
        // Append the created row to the table body
        tableBody.appendChild(row);
    });
}

// Set up an interval to fetch new data every 5000 milliseconds (5 seconds)
setInterval(fetchData, 5000);

// Fetch data once when the window loads
window.onload = fetchData;
