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
    const poleInput = document.getElementById('pole-input');
    const setPoleBtn = document.getElementById('set-pole-btn');
    const maxSpeedInput = document.getElementById('max-speed-input');
    const setMaxSpeedBtn = document.getElementById('set-max-speed-btn');

    // Sequencer Elements
    const seqSpeedA = document.getElementById('seq-speed-a');
    const seqSpeedB = document.getElementById('seq-speed-b');
    const seqInterval = document.getElementById('seq-interval');
    const seqToggleBtn = document.getElementById('seq-toggle-btn');
    const seqActiveBadge = document.getElementById('seq-active-badge');

    // System Elements
    const rs485Toggle = document.getElementById('rs485-toggle');
    const returnToggle = document.getElementById('return-toggle');
    const saveBtn = document.getElementById('save-btn');
    const restoreBtn = document.getElementById('restore-btn');
    const connectBtn = document.getElementById('connect-btn');
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    const alarmBox = document.getElementById('alarm-box');
    const alarmCode = document.getElementById('alarm-code');
    const resetAlarmBtn = document.getElementById('reset-alarm-btn');

    let isUpdating = false;
    let initialSyncDone = false;

    async function updateStatus() {
        if (isUpdating) return;
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            // Populate inputs on first load
            if (!initialSyncDone) {
                seqSpeedA.value = data.sequencer.speed_a;
                seqSpeedB.value = data.sequencer.speed_b;
                seqInterval.value = data.sequencer.interval;
                initialSyncDone = true;
            }

            // Update Primary Stats
            feedbackSpeed.innerHTML = `${data.feedback_speed} <span class="unit">RPM</span>`;
            setSpeedDisplay.innerHTML = `${data.set_speed} <span class="unit">RPM</span>`;

            // Progress bar
            const max = data.max_analogue_speed || 3000;
            const percent = Math.min((data.feedback_speed / max) * 100, 100);
            speedFill.style.width = `${percent}%`;

            // Config Stats
            polePairsDisplay.textContent = data.pole_pairs;
            maxAnalogueDisplay.textContent = `${data.max_analogue_speed} RPM`;
            accTimeDisplay.textContent = data.acc_time;
            rs485StatusDisplay.textContent = data.rs485_status;
            driverVersionDisplay.textContent = data.version;

            // Update Sequencer UI
            if (data.sequencer.active) {
                seqToggleBtn.textContent = 'Detener Secuencia';
                seqToggleBtn.className = 'btn-danger w-full';
                seqActiveBadge.classList.remove('hidden');
                seqActiveBadge.textContent = `Apuntando a ${data.sequencer.current_target}`;
            } else {
                seqToggleBtn.textContent = 'Iniciar Secuencia';
                seqToggleBtn.className = 'btn-primary w-full';
                seqActiveBadge.classList.add('hidden');
            }

            // Logic States (Update only if user isn't interacting)
            if (!document.activeElement || (document.activeElement.type !== 'checkbox' && document.activeElement.type !== 'radio')) {
                enableToggle.checked = data.is_enabled;
                brakeToggle.checked = data.is_braked;
                if (data.is_forward) dirFwd.checked = true;
                else dirRev.checked = true;

                // System states
                rs485Toggle.checked = data.rs485_status === 1;
            }

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
            const headers = { 'Content-Type': 'application/json' };
            const response = await fetch(url, {
                method: 'POST',
                headers: body ? headers : {},
                body: body !== null ? JSON.stringify(body) : null
            });
            const resData = await response.json();

            if (resData.status === 'error') {
                alert(`Error en Hardware: ${resData.message}`);
            }

            await updateStatus();
        } catch (error) {
            console.error(`Error in ${url}:`, error);
        } finally {
            isUpdating = false;
        }
    }

    async function toggleSequencer() {
        const isActive = seqToggleBtn.textContent.includes('Detener');
        if (isActive) {
            await postAction('/api/sequencer/stop');
        } else {
            const body = {
                speed_a: parseInt(seqSpeedA.value),
                speed_b: parseInt(seqSpeedB.value),
                interval: parseFloat(seqInterval.value)
            };
            await postAction('/api/sequencer/start', body);
        }
    }

    setSpeedBtn.addEventListener('click', () => {
        postAction('/api/speed', { rpm: parseInt(speedInput.value) });
        speedInput.value = '';
    });

    seqToggleBtn.addEventListener('click', toggleSequencer);

    setAccBtn.addEventListener('click', () => {
        postAction('/api/acc_time', { seconds: parseInt(accInput.value) });
        accInput.value = '';
    });

    setPoleBtn.addEventListener('click', () => {
        postAction(`/api/pole_pairs?count=${parseInt(poleInput.value)}`);
        poleInput.value = '';
    });

    setMaxSpeedBtn.addEventListener('click', () => {
        postAction(`/api/max_speed?rpm=${parseInt(maxSpeedInput.value)}`);
        maxSpeedInput.value = '';
    });

    enableToggle.addEventListener('change', () => {
        postAction(`/api/toggle?enabled=${enableToggle.checked}`);
    });

    brakeToggle.addEventListener('change', () => {
        postAction(`/api/brake?braked=${brakeToggle.checked}`);
    });

    [dirFwd, dirRev].forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.checked) postAction(`/api/direction?forward=${dirFwd.checked}`);
        });
    });

    rs485Toggle.addEventListener('change', () => {
        postAction(`/api/rs485_control?enabled=${rs485Toggle.checked}`);
    });

    returnToggle.addEventListener('change', () => {
        postAction(`/api/return_data?enabled=${returnToggle.checked}`);
    });

    saveBtn.addEventListener('click', () => postAction('/api/save'));
    restoreBtn.addEventListener('click', () => {
        if (confirm('¿Seguro quieres restaurar los ajustes de fábrica?')) postAction('/api/restore');
    });

    resetAlarmBtn.addEventListener('click', () => postAction('/api/reset_alarm'));
    connectBtn.addEventListener('click', updateStatus);

    // Initial load and start polling
    updateStatus();
    setInterval(updateStatus, 500); // 2Hz for more real-time feeling
});
