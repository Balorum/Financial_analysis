function updateBackgroundColor(value, max_value) {
            let red, green;

            if (value < 0) {
                red = 255;
                green = 255 + Math.round((255 / max_value) * value);
            } else {
                green = 255;
                red = 255 - Math.round((255 / max_value) * value);
            }
            const alpha = 0.3;

            document.body.style.backgroundColor = `rgba(${red}, ${green}, 0, ${alpha})`;
        }

        // Set initial background color from server value
        document.addEventListener("DOMContentLoaded", function() {
            // const initialValue = {{ value }};
            updateBackgroundColor(initialValue, maxValue);
        });