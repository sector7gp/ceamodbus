document.addEventListener('DOMContentLoaded', () => {
    // Stats Elements
    const feedbackSpeed = document.getElementById('feedback-speed');
    const setSpeedDisplay = document.getElementById('set-speed-display');
    const speedFill = document.getElementById('speed-fill');
    const polePairsDisplay = document.getElementById('pole-pairs');
    const maxAnalogueDisplay = document.getElementById('max-analogue');
    const accTimeDisplay = document.getElementById('acc-time-display');
    const rs485StatusDisplay = document.getElementById('rs485-status');
    const driverVersionDisplay = document.getElementById('driver-version');

    // Control Elements
    const enableToggle = document.getElementById('enable-toggle');
    const brakeToggle = document.getElementById('brake-toggle');
    const dirFwd = document.getElementById('dir-fwd');
    const dirRev = document.getElementById('dir-rev');

    // Input Elements
    const speedInput = document.getElementById('speed-input');
    const setSpeedBtn = document.getElementById('set-speed-btn');
    const accInput = document.getElementById('acc-input');
    const setAccBtn = document.getElementById('set-acc-btn');

    // System Elements
    const connectBtn = document.getElementById('connect-btn');
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    const alarmBox = document.getElementById('alarm-box');
    const alarmCode = document.getElementById('alarm-code');
    const resetAlarmBtn = document.getElementById('reset-alarm-btn');

    let isUpdating = false;

    async function updateStatus() {
        if (isUpdating) return;
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            // Update Primary Stats
            feedbackSpeed.innerHTML = `${data.feedback_speed} <span class="unit">RPM</span>`;
            setSpeedDisplay.innerHTML = `${data.set_speed} <span class="unit">RPM</span>`;

            // Progress bar (Max 3000 as typical BLDC range, or use data.max_analogue_speed)
            const max = data.max_analogue_speed || 3000;
            const percent = Math.min((data.feedback_speed / max) * 100, 100);
            speedFill.style.width = `${percent}%`;

            // Config Stats
            polePairsDisplay.textContent = data.pole_pairs;
            maxAnalogueDisplay.textContent = `${data.max_analogue_speed} RPM`;
            accTimeDisplay.textContent = data.acc_time;
            rs485StatusDisplay.textContent = data.rs485_status;
            driverVersionDisplay.textContent = data.version;

            // Logic States (Update only if user isn't interacting)
            if (!document.activeElement || document.activeElement.type !== 'checkbox') {
                enableToggle.checked = data.is_enabled;
                brakeToggle.checked = data.is_braked;
            }

            if (data.is_forward) dirFwd.checked = true;
            else dirRev.checked = true;

            // Connection indicator
            if (!data.connected) {
                connectionDot.className = 'dot disconnected';
                connectionText.textContent = 'Hardware No Detectado';
            } else {
                connectionDot.className = 'dot connected';
                connectionText.textContent = 'Hardware Conectado';
            }

            // Alarms
            if (data.alarm_code > 0) {
                alarmBox.classList.remove('hidden');
                alarmCode.textContent = `Alarma detectada: ${data.alarm_code}`;
            } else {
                alarmBox.classList.add('hidden');
            }

        } catch (error) {
            console.error('Error fetching status:', error);
            connectionDot.className = 'dot disconnected';
            connectionText.textContent = 'Error de Servidor';
        }
    }

    // --- Action Handlers ---

    async function postAction(url, body = null) {
        isUpdating = true;
        try {
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: body ? JSON.stringify(body) : null
            });
            await updateStatus();
        } catch (error) {
            console.error(`Error in ${url}:`, error);
        } finally {
            isUpdating = false;
        }
    }

    setSpeedBtn.addEventListener('click', () => {
        postAction('/api/speed', { rpm: parseInt(speedInput.value) });
        speedInput.value = '';
    });

    setAccBtn.addEventListener('click', () => {
        postAction('/api/acc_time', { seconds: parseInt(accInput.value) });
        accInput.value = '';
    });

    enableToggle.addEventListener('change', () => {
        fetch(`/api/toggle?enabled=${enableToggle.checked}`, { method: 'POST' });
    });

    brakeToggle.addEventListener('change', () => {
        fetch(`/api/brake?braked=${brakeToggle.checked}`, { method: 'POST' });
    });

    [dirFwd, dirRev].forEach(radio => {
        radio.addEventListener('change', () => {
            fetch(`/api/direction?forward=${dirFwd.checked}`, { method: 'POST' });
        });
    });

    resetAlarmBtn.addEventListener('click', () => postAction('/api/reset_alarm'));
    connectBtn.addEventListener('click', updateStatus);

    // Initial load and start polling
    updateStatus();
    setInterval(updateStatus, 1000);
});
