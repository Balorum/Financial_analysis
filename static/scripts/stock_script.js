// Function to update the width of the background color strips based on positive and negative values
function updateBackgroundColor(positive, negative) {
    // Select the elements representing the green and red strips
    const greenStrip = document.querySelector('.green-strip');
    const redStrip = document.querySelector('.red-strip');

    // Set the width of the green strip based on the positive value (percentage)
    greenStrip.style.width = `${positive * 100}%`;
    
    // Set the width of the red strip based on the negative value (percentage)
    redStrip.style.width = `${negative * 100}%`;
}

// Wait until the DOM content is fully loaded before executing the initial setup
document.addEventListener("DOMContentLoaded", function() {
    // Fetch initial values for positive and negative from server-side variables
    // const initialValue = {{ value }}; // Example of how server-side templating might inject values
    updateBackgroundColor(pos, neg); // Call the function with initial values to set the strip widths
});
