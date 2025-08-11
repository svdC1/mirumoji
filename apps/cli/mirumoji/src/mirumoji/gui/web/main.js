
document.addEventListener('DOMContentLoaded', () => {
    // --- Navigation ---
    const navLauncher = document.getElementById('nav-launcher');
    const navConfig = document.getElementById('nav-config');
    const launcherSection = document.getElementById('launcher-section');
    const configSection = document.getElementById('config-section');

    const setActiveTab = (activeTab) => {
        const tabs = [navLauncher, navConfig];
        tabs.forEach(tab => {
            if (tab === activeTab) {
                tab.classList.add('border-b-2', 'border-indigo-500', 'text-indigo-500');
                tab.classList.remove('text-gray-500');
            } else {
                tab.classList.remove('border-b-2', 'border-indigo-500', 'text-indigo-500');
                tab.classList.add('text-gray-500');
            }
        });
    };

    navLauncher.addEventListener('click', () => {
        launcherSection.classList.remove('hidden');
        configSection.classList.add('hidden');
        setActiveTab(navLauncher);
    });

    navConfig.addEventListener('click', () => {
        configSection.classList.remove('hidden');
        launcherSection.classList.add('hidden');
        setActiveTab(navConfig);
    });

    // --- UI Elements ---
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const buildBtn = document.getElementById('build-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const statusText = document.getElementById('status-text');
    const logs = document.getElementById('logs');
    const systemInfo = document.getElementById('system-info');
    const gpuOption = document.getElementById('gpu-option');

    // Config form elements
    const localBuildCheckbox = document.getElementById('local-build-checkbox');
    const cleanStopCheckbox = document.getElementById('clean-stop-checkbox');
    const repositorySelect = document.getElementById('repository-select');
    const openaiKeyInput = document.getElementById('openai-key');
    const modalIdInput = document.getElementById('modal-id');
    const modalSecretInput = document.getElementById('modal-secret');
    const gpuCheckbox = document.getElementById('gpu-checkbox');

    /**
     * Fetches data from the API.
     * @param {string} url - The URL to fetch.
     * @param {object} options - The options for the fetch request.
     * @param {boolean} stream - Whether to stream the response.
     * @returns {Promise<any>} - The JSON response or a promise that resolves when streaming is complete.
     */
    async function fetchData(url, options, stream = false) {
        statusText.textContent = 'Working...';
        if (stream) {
            logs.innerHTML = '<span class="text-gray-400">Connecting to stream...</span><span class="cursor"></span>';
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: `HTTP error! status: ${response.status}` }));
                throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
            }

            if (stream) {
                logs.innerHTML = ''; // Clear logs on successful connection
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                const processText = async ({ done, value }) => {
                    if (done) {
                        statusText.textContent = 'Done';
                        logs.innerHTML += '<p class="text-green-400 font-bold">> Stream finished.</p>';
                        logs.scrollTop = logs.scrollHeight;
                        return;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    const events = chunk.split('\\n\\n').filter(e => e.trim());

                    for (const eventStr of events) {
                        if (eventStr.includes('event: done')) {
                            statusText.textContent = 'Done';
                            logs.innerHTML += '<p class="text-green-400 font-bold">> Stream finished.</p>';
                            return; // Stop processing
                        }
                        if (eventStr.startsWith('data:')) {
                            const data = eventStr.substring(5).trim();
                            const logEntry = document.createElement('p');
                            logEntry.innerHTML = `&gt; ${data}`;
                            logs.appendChild(logEntry);
                        }
                    }
                    logs.scrollTop = logs.scrollHeight;
                    return reader.read().then(processText);
                };
                return reader.read().then(processText);
            }

            statusText.textContent = 'Idle';
            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            statusText.textContent = 'Error';
            const logEntry = document.createElement('p');
            logEntry.className = 'text-red-500 font-bold';
            logEntry.textContent = `Error: ${error.message}`;
            logs.innerHTML = ''; // Clear previous logs
            logs.appendChild(logEntry);
        }
    }


    // --- Initial Data Loading ---
    async function loadSystemInfo() {
        systemInfo.innerHTML = '<p>Checking...</p>';
        try {
            const dockerData = await fetchData('/api/dockerRunning');
            const gpuData = await fetchData('/api/hasGPU');

            let dockerStatus = dockerData.status
                ? '<span class="text-green-400">Ready</span>'
                : '<span class="text-red-400">Not Running</span>';
            let gpuStatus = gpuData.status
                ? '<span class="text-green-400">Available</span>'
                : '<span class="text-red-400">Not Detected</span>';

            systemInfo.innerHTML = `
                <div>
                    <p class="font-bold">Docker</p>
                    <p>${dockerStatus}</p>
                </div>
                <div>
                    <p class="font-bold">NVIDIA GPU</p>
                    <p>${gpuStatus}</p>
                </div>
            `;

            if (gpuData.status) {
                gpuOption.classList.remove('hidden');
            } else {
                gpuOption.classList.add('hidden');
                gpuCheckbox.checked = false; // Ensure it's unchecked if no GPU
            }

        } catch (error) {
            systemInfo.innerHTML = '<p class="text-red-500">Could not load system info.</p>';
        }
    }

    // --- Event Listeners ---
    startBtn.addEventListener('click', () => {
        const openAIKey = openaiKeyInput.value;

        if (!openAIKey) {
            alert('Please enter your OpenAI API Key in the Configuration section.');
            setActiveTab(navConfig);
            configSection.classList.remove('hidden');
            launcherSection.classList.add('hidden');
            openaiKeyInput.focus();
            return;
        }

        const requestBody = {
            "gpu": gpuCheckbox.checked,
            "local": localBuildCheckbox.checked,
            "repository": repositorySelect.value,
            "OPENAI_API_KEY": openAIKey,
            "MODAL_TOKEN_ID": modalIdInput.value,
            "MODAL_TOKEN_SECRET": modalSecretInput.value
        };

        fetchData('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        }, true);
    });

    stopBtn.addEventListener('click', () => {
        fetchData('/api/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ "clean": cleanStopCheckbox.checked })
        }, true);
    });

    buildBtn.addEventListener('click', () => {
        const requestBody = {
            "gpu": gpuCheckbox.checked
        };
        fetchData('/api/build', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        }, true);
    });

    refreshBtn.addEventListener('click', () => {
        loadSystemInfo();
    });

    // --- Initial Setup ---
    setActiveTab(navLauncher);
    loadSystemInfo();
});
