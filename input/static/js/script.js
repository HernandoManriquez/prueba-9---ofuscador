document.getElementById('update-time').addEventListener('click', function() {
    fetch('/get_time')
        .then(response => response.text())
        .then(time => {
            document.getElementById('server-time').textContent = time;
        });
});