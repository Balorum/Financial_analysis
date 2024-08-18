function updateBackgroundColor(positive, negative) {
            let red, green;

            if (positive < negative) {
                red = 255;
                green = 255 + Math.round((255 / positive) * negative);
            } else {
                green = 255;
                red = 255 - Math.round((255 / positive) * negative);
            }
            const alpha = 0.3;

            document.body.style.backgroundColor = `rgba(${red}, ${green}, 0, ${alpha})`;

            const greenStrip = document.querySelector('.green-strip');
            const redStrip = document.querySelector('.red-strip');

            greenStrip.style.width = `${positive * 100}%`;
            redStrip.style.width = `${negative * 100}%`;
        }

        // Set initial background color from server value
        document.addEventListener("DOMContentLoaded", function() {
            // const initialValue = {{ value }};
            updateBackgroundColor(pos, neg);
        });