// Auto-close alerts after 3 seconds
setTimeout(function() {
    $('.alert').alert('close');
}, 3000);

// Function to safely parse JSON
function safeJSONParse(jsonString) {
    try {
        return jsonString === 'null' ? null : JSON.parse(jsonString);
    } catch (e) {
        console.error('Error parsing JSON:', e);
        return null;
    }
}

// Function to initialize charts
function initializeCharts(chartData) {
    // Initialize bar chart
    if (chartData.bar) {
        Plotly.plot('bar', chartData.bar, {});
    }

    // Initialize stack bar chart
    if (chartData.stack_bar) {
        Plotly.plot('stack', chartData.stack_bar, {});
    }

    // Initialize pie charts
    if (chartData.pie1) {
        Plotly.plot('pie11', chartData.pie1, {});
    }
    if (chartData.pie2) {
        Plotly.plot('pie22', chartData.pie2, {});
    }
    if (chartData.pie3) {
        Plotly.plot('pie33', chartData.pie3, {});
    }
    if (chartData.pie4) {
        Plotly.plot('pie44', chartData.pie4, {});
    }
}

// Function to parse chart data from JSON string
function parseChartData(dataString) {
    try {
        return JSON.parse(dataString);
    } catch (e) {
        console.error('Error parsing chart data:', e);
        return null;
    }
} 