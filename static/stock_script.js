function updateBackgroundColor(value) {
            const maxAbsValue = 7;
            let red, green;

            if (value < 0) {
                // Negative values: from red (full) to white
                red = 255;
                green = 255 + Math.round((255 / maxAbsValue) * value); // value is negative, so this subtracts from 255
            } else {
                // Positive values: from white to green (full)
                green = 255;
                red = 255 - Math.round((255 / maxAbsValue) * value); // value is positive, so this subtracts from 255
            }
            const alpha = 0.3; // Adjust this value as needed (0.5 for 50% transparency)

            document.body.style.backgroundColor = `rgba(${red}, ${green}, 0, ${alpha})`;
        }

        // Set initial background color from server value
        document.addEventListener("DOMContentLoaded", function() {
            // const initialValue = {{ value }};
            updateBackgroundColor(initialValue);
        });