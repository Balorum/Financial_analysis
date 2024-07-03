async function fetchData() {
    try {
        const response = await fetch('/data');
        const data = await response.json();
        console.log(data); // Log the data to check if it's fetched correctly
        const dataContainer = document.getElementById('data-container');
        dataContainer.innerHTML = '';
        data.forEach(item => {
            const div = document.createElement('div');
            div.textContent = item.value;
            dataContainer.appendChild(div);
        });
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

setInterval(fetchData, 5000); // Fetch data every 5 seconds
window.onload = fetchData; // Fetch data on page load