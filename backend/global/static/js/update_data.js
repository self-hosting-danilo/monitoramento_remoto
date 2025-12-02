
async function updateData() {
    try {
        const response = await fetch(HOSPITAL_DATA_URL);
        const data = await response.json();

        if (data.pressure !== undefined) {
            createOrUpdateGauge('pressure-gauge', data.pressure, 12, 0, '', [
                { min: 0, max: 5, color: '#ff4444' },
                { min: 5, max: 6, color: '#ffaa00' },
                { min: 6, max: 12, color: '#00cc44' }
            ]);
        }
        if (data.purity !== undefined) {
            createOrUpdateGauge('purity-gauge', data.purity, 100, 0, '', [
                { min: 0, max: 86, color: '#ff4444' },
                { min: 86, max: 90, color: '#ffaa00' },
                { min: 90, max: 100, color: '#00cc44' }
            ]);
        }
        if (data.product_pressure !== undefined) {
            createOrUpdateGauge('product-gauge', data.product_pressure, 12, 0, '', [
                { min: 0, max: 5, color: '#ff4444' },
                { min: 5, max: 6, color: '#ffaa00' },
                { min: 6, max: 12, color: '#00cc44' }
            ]);
        }

        if (data.dew_point !== undefined) {
            createOrUpdateGauge('dew-gauge', data.dew_point, 10, -100, '', [
                { min: -100, max: -45, color: '#00cc44' },
                { min: -45, max: -10, color: '#ffaa00' },
                { min: -10, max: 10, color: '#ff4444' }
            ]);
        }

        if (data.vacuo !== undefined) {
            createOrUpdateGauge('vacuo-gauge', Math.abs(data.vacuo), 760, 0, '', [
                { min: 0, max: 300, color: '#ff4444' },
                { min: 300, max: 500, color: '#ffaa00' },
                { min: 500, max: 760, color: '#00cc44' }
            ]);
        }

        if (data.rede !== undefined) {
            createOrUpdateGauge('rede-gauge', data.rede, 12, 0, '', [
                { min: 0, max: 5, color: '#ff4444' },
                { min: 5, max: 6, color: '#ffaa00' },
                { min: 6, max: 12, color: '#00cc44' }
            ]);
        }
        updateStatusText('c1-status', data.C1);
        updateStatusText('c2-status', data.C2);


    } catch (error) {
        
    }
}

function updateStatusText(id, value) {
    const el = document.querySelector(`#${id} .status-text`);
    if (!el) return;

    el.textContent = value;

    // cor automática
    if (value === "Ligado") {
        el.style.color = "#00cc44";
    } else if (value === "Desligado") {
        el.style.color = "#001fccff";
        el.textContent = "Stand-by";
    } else if (value === "Stand-by") {
        el.style.color = "#001fccff";
    }
    else {
        el.style.color = "#666";
    }
}

setInterval(updateData, 5000);

window.addEventListener('load', updateData);