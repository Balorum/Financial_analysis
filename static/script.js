async function fetchData() {
    const response = await fetch('/data');
    const data = await response.json();
    const tableBody = document.getElementById('data-table').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = ''; // Clear previous data

    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><a href="/stock/${item.id}" target=”_blank”>${item.title}</a></td>
            <td style="text-align: left">${item.last}</td>
            <td>${item.high}</td>
            <td>${item.low}</td>
            <td>${item.volume}</td>
            <td>${item.change}</td>
            <td>${item.change_pct}</td>
            <td class="${item.growth ? 'growth-true' : 'growth-false'}">${item.growth}</td>
        `;
        tableBody.appendChild(row);
    });
}

setInterval(fetchData, 5000); // Fetch data every 5 seconds
window.onload = fetchData; // Fetch data on page load