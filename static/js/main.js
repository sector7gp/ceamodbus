document.addEventListener('DOMContentLoaded', () => {
    const feedbackSpeed = document.getElementById('feedback-speed');
    const setSpeedDisplay = document.getElementById('set-speed-display');
    const speedFill = document.getElementById('speed-fill');
    const enableToggle = document.getElementById('enable-toggle');
    const speedInput = document.getElementById('speed-input');
    const setSpeedBtn = document.getElementById('set-speed-btn');
    const connectBtn = document.getElementById('connect-btn');
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    const alarmBox = document.getElementById('alarm-box');
    const alarmCode = document.getElementById('alarm-code');

    let pollingInterval;

    async function updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            // Update UI
            feedbackSpeed.innerHTML = `${data.feedback_speed} <span class="unit">RPM</span>`;
            setSpeedDisplay.innerHTML = `${data.set_speed} <span class="unit">RPM</span>`;

            // Progress bar (assuming 6000 max RPM for visual)
            const percent = Math.min((data.feedback_speed / 6000) * 100, 100);
            speedFill.style.width = `${percent}%`;

            enableToggle.checked = data.is_enabled;

            // Connection indicator
            if (data.error) {
                connectionDot.className = 'dot disconnected';
                connectionText.textContent = 'Hardware no detectado';
            } else {
                connectionDot.className = 'dot connected';
                connectionText.textContent = 'Conectado';
            }

            // Alarms
            if (data.alarm_code > 0) {
                alarmBox.classList.remove('hidden');
                alarmCode.textContent = `Alarma: ${data.alarm_code}`;
            } else {
                alarmBox.classList.add('hidden');
            }

        } catch (error) {
            console.error('Error fetching status:', error);
            connectionDot.className = 'dot disconnected';
            connectionText.textContent = 'Error de Servidor';
        }
    }

    async function setSpeed() {
        const rpm = parseInt(speedInput.value);
        if (isNaN(rpm)) return;

        try {
            const response = await fetch('/api/speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rpm })
            });
            if (response.ok) {
                updateStatus();
                speedInput.value = '';
            }
        } catch (error) {
            alert('Error al setear velocidad');
        }
    }

    async function toggleMotor() {
        const enabled = enableToggle.checked;
        try {
            await fetch(`/api/toggle?enabled=${enabled}`, { method: 'POST' });
            updateStatus();
        } catch (error) {
            alert('Error al cambiar estado del motor');
        }
    }

    setSpeedBtn.addEventListener('click', setSpeed);
    enableToggle.addEventListener('change', toggleMotor);
    connectBtn.addEventListener('click', updateStatus);

    // Initial load and start polling
    updateStatus();
    pollingInterval = setInterval(updateStatus, 1000);
});
