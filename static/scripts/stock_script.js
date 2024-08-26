function updateBackgroundColor(positive, negative) {
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