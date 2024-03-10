document.getElementById('findBtn').addEventListener('click', function () {
    document.getElementById('loadingDiv').style.display = 'block';
});


// Function to download table data
document.getElementById('downloadBtn0').addEventListener('click', function () {
    downloadTableData0();
});

function downloadTableData0() {
    let rows = document.querySelectorAll('#resultTable tbody tr');
    let data = 'URL,Response Code,Page Size\n'; // CSV header

    rows.forEach(row => {
        let url = row.cells[0].innerText;
        let responseCode = row.cells[1].innerText;
        let pageSize = row.cells[2].innerText;
        data += `${url},${responseCode},${pageSize}\n`; // CSV row
    });

    // Create a blob object and initiate download
    let blob = new Blob([data], { type: 'text/csv' });
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = 'endpoints_results.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function downloadResults() {
    let rows = document.querySelectorAll('#resultTable tbody tr');
    let data = 'URL,Response Code,IP Address\n'; // CSV header

    rows.forEach(row => {
        let url = row.cells[0].innerText;
        let responseCode = row.cells[1].innerText;
        let ipAddress = row.cells[2].innerText;
        data += `${url},${responseCode},${ipAddress}\n`; // CSV row
    });

    // Create a blob object and initiate download
    let blob = new Blob([data], { type: 'text/csv' });
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = 'subdomains_results.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}