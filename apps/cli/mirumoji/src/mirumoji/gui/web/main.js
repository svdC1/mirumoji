
document.addEventListener('DOMContentLoaded', () => {
    // --- State ---
    let isDockerRunning = false;
    let appStatusInterval = null;

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
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    const dismissBtn = document.getElementById('dismiss-btn');
    const appStatusText = document.getElementById('app-status-text');
    const logs = document.getElementById('logs');
    const systemInfo = document.getElementById('system-info');
    const gpuOption = document.getElementById('gpu-option');
    const openAppContainer = document.getElementById('open-app-container');
    const openLocalBtn = document.getElementById('open-local-btn');
    const openLanBtn = document.getElementById('open-lan-btn');

    // Config form elements
    const localBuildCheckbox = document.getElementById('local-build-checkbox');
    const cleanStopCheckbox = document.getElementById('clean-stop-checkbox');
    const repositorySelect = document.getElementById('repository-select');
    const openaiKeyInput = document.getElementById('openai-key');
    const modalIdInput = document.getElementById('modal-id');
    const modalSecretInput = document.getElementById('modal-secret');
    const gpuCheckbox = document.getElementById('gpu-checkbox');

    const allButtons = [startBtn, stopBtn, buildBtn, refreshBtn, clearLogsBtn];

    // --- Core Functions ---
    const setButtonsDisabled = (disabled) => {
        allButtons.forEach(button => button.disabled = disabled);
    };

    const showError = (message) => {
        logs.innerHTML = `<p class="text-red-500 font-bold">Error: ${message}</p>`;
    };
    
    const setAppStatus = (status, color = 'text-gray-700 dark:text-gray-300') => {
        appStatusText.textContent = status;
        appStatusText.className = `text-lg font-semibold ${color}`;
    };

    const stopAppStatusCheck = () => {
        if (appStatusInterval) {
            clearInterval(appStatusInterval);
            appStatusInterval = null;
        }
    };

    const checkAppStatus = async () => {
        try {
            // Use a specific port for the health check
            const healthCheckUrl = 'https://localhost/api/health/status';

            const response = await fetch(healthCheckUrl, { method: 'GET', signal: AbortSignal.timeout(4000) });

            if (response.ok) {
                const data = await response.json();
                if (data.status === 'ok') {
                    setAppStatus('Running', 'text-green-400');
                } else {
                    setAppStatus('Unhealthy', 'text-yellow-400');
                }
            } else {
                 setAppStatus('Not Ready', 'text-yellow-400');
            }
        } catch (error) {
            setAppStatus('Not Ready', 'text-yellow-400');
            // If the app is consistently not ready, we can assume it's stopped.
            // This also handles cases where the fetch fails due to network errors.
        }
    };

    const startAppStatusCheck = () => {
        stopAppStatusCheck(); // Clear any existing interval
        checkAppStatus(); // Check immediately
        appStatusInterval = setInterval(checkAppStatus, 5000); // Then check every 5 seconds
    };
    
    /**
     * Fetches data from the API.
     * @param {string} url - The URL to fetch.
     * @param {object} options - The options for the fetch request.
     * @param {boolean} stream - Whether to stream the response.
     * @returns {Promise<any>} - The JSON response or a promise that resolves when streaming is complete.
     */
    async function fetchData(url, options, stream = false) {
        setButtonsDisabled(true);
        openAppContainer.classList.add('hidden');
        if (url.endsWith('/stop')) {
            stopAppStatusCheck();
            setAppStatus('Stopped', 'text-red-400');
        } else {
            setAppStatus('Working...');
        }
        
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
                        logs.innerHTML += '<p class="text-green-400 font-bold">> Stream finished.</p>';
                        logs.scrollTop = logs.scrollHeight;
                        setButtonsDisabled(false);
                        return;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    const events = chunk.split('\\n\\n').filter(e => e.trim());

                    for (const eventStr of events) {
                        if (eventStr.includes('event: done')) {
                            setButtonsDisabled(false);
                            if (url.endsWith('/start')) {
                                openAppContainer.classList.remove('hidden');
                                startAppStatusCheck();
                            }
                            return; // Stop processing
                        }
                        if (eventStr.startsWith('data:')) {
                            const data = eventStr.substring(5).trim();
                            // Check for special URL data
                            if(data.startsWith('LAN Access URL:')){
                                openLanBtn.href = data.substring(16).trim();
                            } else if(data.startsWith('Local Access URL:')){
                                openLocalBtn.href = data.substring(18).trim();
                            } else {
                                const logEntry = document.createElement('p');
                                logEntry.innerHTML = `&gt; ${data}`;
                                logs.appendChild(logEntry);
                            }
                        }
                    }
                    logs.scrollTop = logs.scrollHeight;
                    return reader.read().then(processText);
                };
                return reader.read().then(processText);
            }
            
            setButtonsDisabled(false);
            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            showError(error.message);
            setButtonsDisabled(false);
             setAppStatus('Error', 'text-red-500');
        }
    }


    // --- Initial Data Loading ---
    async function loadSystemInfo() {
        systemInfo.innerHTML = '<p>Checking...</p>';
        setButtonsDisabled(true);
        isDockerRunning = false;
        try {
            // This is a non-stream call, so we don't need the full fetchData logic
            const response = await fetch('/api/dockerRunning');
            const dockerData = await response.json();
            isDockerRunning = dockerData.status;

            const gpuResponse = await fetch('/api/hasGPU');
            const gpuData = await gpuResponse.json();

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
                gpuCheckbox.checked = false;
            }

        } catch (error) {
            systemInfo.innerHTML = '<p class="text-red-500">Could not load system info.</p>';
        } finally {
            setButtonsDisabled(false);
        }
    }

    // --- Event Listeners ---
    clearLogsBtn.addEventListener('click', () => {
        logs.innerHTML = '<span class="text-gray-400">Logs cleared.</span><span class="cursor"></span>';
    });
    
    dismissBtn.addEventListener('click', () => {
        openAppContainer.classList.add('hidden');
    });

    startBtn.addEventListener('click', () => {
        if (!isDockerRunning) {
            showError("Docker is not running. Please start Docker Desktop and refresh.");
            return;
        }

        const useGpu = gpuCheckbox.checked;
        const modalId = modalIdInput.value;
        const modalSecret = modalSecretInput.value;
        const openAIKey = openaiKeyInput.value;

        if (!openAIKey) {
            alert('Please enter your OpenAI API Key in the Configuration section.');
            setActiveTab(navConfig);
            configSection.classList.remove('hidden');
            launcherSection.classList.add('hidden');
            openaiKeyInput.focus();
            return;
        }

        if (!useGpu && (!modalId || !modalSecret)) {
            alert('For CPU mode, both Modal Token ID and Modal Token Secret are required.');
            setActiveTab(navConfig);
            configSection.classList.remove('hidden');
            launcherSection.classList.add('hidden');
            modalIdInput.focus();
            return;
        }

        const requestBody = {
            "gpu": useGpu,
            "local": localBuildCheckbox.checked,
            "repository": repositorySelect.value,
            "OPENAI_API_KEY": openAIKey,
            "MODAL_TOKEN_ID": modalId,
            "MODAL_TOKEN_SECRET": modalSecret
        };

        fetchData('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        }, true);
    });

    stopBtn.addEventListener('click', () => {
        if (!isDockerRunning) {
            showError("Docker is not running. Please start Docker Desktop and refresh.");
            return;
        }
        stopAppStatusCheck();
        fetchData('/api/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ "clean": cleanStopCheckbox.checked })
        }, true);
    });

    buildBtn.addEventListener('click', () => {
        if (!isDockerRunning) {
            showError("Docker is not running. Please start Docker Desktop and refresh.");
            return;
        }
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
    // Start checking app status on load, in case the app is already running
    startAppStatusCheck();
});
