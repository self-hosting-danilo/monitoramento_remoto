const gauges = {};


function getColorForValue(value, ranges) {
    for (let range of ranges) {
        if (value >= range.min && value <= range.max) return range.color;
    }
    return '#999';
}  


function createOrUpdateGauge(canvasId, value, maxValue, minValue, unit, colorRanges) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error('Canvas não encontrado:', canvasId);
        return;
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        console.error('Valor inválido para', canvasId, ':', value);
        return;
    }

    const ctx = canvas.getContext('2d');
    const valueRange = maxValue - minValue;
    const currentValue = Math.max(minValue, Math.min(maxValue, numValue));
    const filledValue = currentValue - minValue;
    const emptyValue = maxValue - currentValue;

    if (gauges[canvasId]) {
        const chart = gauges[canvasId];
        chart.data.datasets[0].data = [filledValue, emptyValue];
        chart.data.datasets[0].backgroundColor[0] = getColorForValue(numValue, colorRanges);
        chart.options.plugins.gaugeText.value = numValue.toFixed(1);
        chart.update();
        return;
    }

    gauges[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [filledValue, emptyValue],
                backgroundColor: [
                    getColorForValue(numValue, colorRanges),
                    '#e0e0e0'
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '70%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
                gaugeText: { value: numValue.toFixed(1), unit: unit }
            }
        },
        plugins: [{
            id: 'gaugeText',
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                const {left, right, top, bottom} = chart.chartArea;
                const centerX = left + (right - left) / 2;
                const centerY = top + (bottom - top) / 1.1; 

                const value = chart.options.plugins.gaugeText.value;
                const unit = chart.options.plugins.gaugeText.unit;

                ctx.save();
                ctx.font = 'bold 32px Arial';
                ctx.fillStyle = '#333';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(value, centerX, centerY);

                ctx.font = '14px Arial';
                ctx.fillStyle = '#666';
                ctx.fillText(unit, centerX, centerY + 25);
                ctx.restore();
            }
        }]
    });
}
