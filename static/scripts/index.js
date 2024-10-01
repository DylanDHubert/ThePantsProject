document.addEventListener('DOMContentLoaded', function() {
    // Retrieve plot data and CSRF token from HTML attributes
    var plotDiv = document.getElementById('scatter-plot');
    var plotData = window.plotDataJson;
    var csrfToken = window.csrfToken;

    // Now you can plot the data and handle clicks
    Plotly.newPlot('scatter-plot', plotData.data, plotData.layout);

    plotDiv.on('plotly_click', function(eventData) {
        var x = eventData.points[0].x;
        var y = eventData.points[0].y;

        console.log('Clicked point:', x, y);

        fetch('/click/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ x: x, y: y })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Server response:', data);
            if (data.status === 'success' && data.image_links) {
                var imagesContainer = document.getElementById('images-container');
                imagesContainer.innerHTML = '';
                data.image_links.forEach(link => {
                    if (link) {
                        var img = document.createElement('img');
                        img.src = link;
                        img.alt = 'Dropbox Image';
                        img.className = 'dropbox-image';
                        imagesContainer.appendChild(img);
                    }
                });
            } else {
                console.error('Error fetching images:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
