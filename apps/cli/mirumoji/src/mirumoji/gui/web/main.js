document.addEventListener("DOMContentLoaded", () => {
    // --- State ---
    let isDockerRunning = false;

    // --- Navigation ---
    const navLauncher = document.getElementById("nav-launcher");
    const navConfig = document.getElementById("nav-config");
    const launcherSection = document.getElementById("launcher-section");
    const configSection = document.getElementById("config-section");
    const logsSection = document.getElementById("appLogs-section");
    const navLogs = document.getElementById("logsTab");
    const navDocumentation = document.getElementById("documentationButton");
    const footerLogs = document.getElementById("footerLogs");

    const setActiveTab = (activeTab) => {
        const tabs = [navLauncher, navConfig, navLogs];
        tabs.forEach((tab) => {
            if (tab === activeTab) {
                tab.classList.add(
                    "border-b-2",
                    "border-indigo-500",
                    "text-indigo-500"
                );
                tab.classList.remove("text-gray-500");
            } else {
                tab.classList.remove(
                    "border-b-2",
                    "border-indigo-500",
                    "text-indigo-500"
                );
                tab.classList.add("text-gray-500");
            }
        });
    };

    navLauncher.addEventListener("click", () => {
        launcherSection.classList.remove("hidden");
        footerLogs.classList.remove("hidden");
        configSection.classList.add("hidden");
        logsSection.classList.add("hidden");
        setActiveTab(navLauncher);
    });

    navDocumentation.addEventListener("click", () => {
        window.open("https://svdc1.github.io/mirumoji/docs", "_blank").focus();
    });

    navLogs.addEventListener("click", () => {
        logsSection.classList.remove("hidden");
        footerLogs.classList.add("hidden");
        configSection.classList.add("hidden");
        launcherSection.classList.add("hidden");
        setActiveTab(navLogs);
    });
    navConfig.addEventListener("click", () => {
        configSection.classList.remove("hidden");
        footerLogs.classList.remove("hidden");
        launcherSection.classList.add("hidden");
        logsSection.classList.add("hidden");
        setActiveTab(navConfig);
    });

    // --- UI Elements ---
    const startBtn = document.getElementById("start-btn");
    const stopBtn = document.getElementById("stop-btn");
    const startAppLogStreamBtn = document.getElementById(
        "startAppLogStreamBtn"
    );
    const stopAppLogStreamBtn = document.getElementById("stopAppLogStreamBtn");
    const appLogContainer = document.getElementById("dockerAppLogContainer");
    const buildBtn = document.getElementById("build-btn");
    const refreshBtn = document.getElementById("refresh-btn");
    const clearLogsBtn = document.getElementById("clear-logs-btn");
    const dismissBtn = document.getElementById("dismiss-btn");
    const appStatusText = document.getElementById("app-status-text");
    const logs = document.getElementById("logs");
    const systemInfo = document.getElementById("system-info");
    const gpuOption = document.getElementById("gpu-option");
    const openAppContainer = document.getElementById("open-app-container");
    const openLocalBtn = document.getElementById("open-local-btn");
    const openLanBtn = document.getElementById("open-lan-btn");

    // Config form elements
    const localBuildCheckbox = document.getElementById("local-build-checkbox");
    const cleanStopCheckbox = document.getElementById("clean-stop-checkbox");
    const repositorySelect = document.getElementById("repository-select");
    const openaiKeyInput = document.getElementById("openai-key");
    const modalIdInput = document.getElementById("modal-id");
    const modalSecretInput = document.getElementById("modal-secret");
    const gpuCheckbox = document.getElementById("gpu-checkbox");

    // Fetch Abort Controller
    let abortController = new AbortController();

    const allButtons = [startBtn, stopBtn, buildBtn, refreshBtn, clearLogsBtn];

    // --- Core Functions ---
    const setButtonsDisabled = (disabled) => {
        allButtons.forEach((button) => (button.disabled = disabled));
    };

    const showError = (message, showContainer = logs) => {
        showContainer.innerHTML = `<p class="text-red-500 font-bold">Error: ${message}</p>`;
    };

    const setAppStatus = (
        status,
        color = "text-gray-700 dark:text-gray-300"
    ) => {
        appStatusText.textContent = status;
        appStatusText.className = `text-lg font-semibold ${color}`;
    };

    const checkAppStatus = async () => {
        try {
            // Hit main application API's health status endpoint
            const healthCheckUrl = "https://localhost/api/health/status";

            const response = await fetch(healthCheckUrl, {
                method: "GET",
            });

            if (response.ok) {
                const data = await response.json();
                if (data.status === "ok") {
                    setAppStatus("Running", "text-green-400");
                    return "Running";
                } else {
                    setAppStatus("Unhealthy", "text-yellow-400");
                    return "Unhealthy";
                }
            } else {
                setAppStatus("Not Ready", "text-yellow-400");
                return "Not Ready";
            }
        } catch (error) {
            setAppStatus("Not Ready", "text-yellow-400");
            // Handle cases where the fetch fails due to network errors.
        }
    };

    /**
     * Fetches data from the API.
     * @param {string} url - The URL to fetch.
     * @param {object} options - The options for the fetch request.
     * @param {boolean} stream - Whether to stream the response.
     * @param {HTMLElement} streamContainer - Container to include stream logs
     * @param {boolean} disableButtons - Whether to disable buttons while fetch is running
     * @returns {Promise<any>} - The JSON response or a promise that resolves when streaming is complete.
     */
    async function fetchData(
        url,
        options,
        stream = false,
        streamContainer = logs,
        disableButtons = true
    ) {
        // Disable all buttons and hide open app container if visible
        if (disableButtons) {
            setButtonsDisabled(true);
        }
        openAppContainer.classList.add("hidden");

        // If stream display connecting message
        if (stream) {
            streamContainer.innerHTML =
                '<span class="text-gray-400">Connecting to stream...</span><span class="cursor"></span>';
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    `API error! status: ${response.status}; message: ${errorData.message}; url: ${errorData.url}; body: ${errorData.body}`
                );
            }

            if (stream) {
                streamContainer.innerHTML = ""; // Clear logs on successful connection
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                const processText = async ({ done, value }) => {
                    if (done) {
                        streamContainer.innerHTML +=
                            '<p class="text-green-400 font-bold">> Stream finished.</p>';
                        streamContainer.scrollTop = logs.scrollHeight;
                        if (disableButtons) {
                            setButtonsDisabled(false);
                        }
                        return;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    const events = chunk
                        .split("\\n\\n")
                        .filter((e) => e.trim());

                    for (const eventStr of events) {
                        if (eventStr.includes("event: done")) {
                            if (disableButtons) {
                                setButtonsDisabled(false);
                            }
                            return; // Stop processing
                        }
                        if (eventStr.startsWith("data:")) {
                            const data = eventStr.substring(5).trim();
                            // Check for special URL data
                            if (data.startsWith("LAN Access URL:")) {
                                openLanBtn.href = data.substring(16).trim();
                            } else if (data.startsWith("Local Access URL:")) {
                                openLocalBtn.href = data.substring(18).trim();
                            } else {
                                const logEntry = document.createElement("p");
                                logEntry.innerHTML = `&gt; ${data}`;
                                streamContainer.appendChild(logEntry);
                            }
                        }
                    }
                    streamContainer.scrollTop = streamContainer.scrollHeight;
                    return reader.read().then(processText);
                };
                return reader.read().then(processText);
            }
            return await response.json();
        } catch (error) {
            if (error.name === "AbortError") {
                console.log("Fetch Aborted", error.message);
            } else {
                console.error("Fetch error:", error);
                showError(error.message);
                throw error;
            }
        } finally {
            if (disableButtons) {
                setButtonsDisabled(false);
            }
        }
    }

    // --- Initial Data Loading ---
    async function loadSystemInfo() {
        systemInfo.innerHTML = "<p>Checking...</p>";
        setButtonsDisabled(true);
        isDockerRunning = false;
        try {
            const dockerData = await fetchData(
                "/api/dockerRunning",
                { method: "GET" },
                false
            );
            isDockerRunning = dockerData.status;

            const gpuData = await fetchData(
                "/api/hasGPU",
                { method: "GET" },
                false
            );

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
                gpuOption.classList.remove("hidden");
            } else {
                gpuOption.classList.add("hidden");
                gpuCheckbox.checked = false;
            }
            await checkAppStatus();
        } catch (error) {
            systemInfo.innerHTML =
                '<p class="text-red-500">Error Fetching System Info</p>';
        } finally {
            setButtonsDisabled(false);
        }
    }

    // --- Event Listeners ---
    clearLogsBtn.addEventListener("click", () => {
        logs.innerHTML =
            '<span class="text-gray-400"> > Logs cleared.</span><span class="cursor"></span>';
    });

    dismissBtn.addEventListener("click", () => {
        openAppContainer.classList.add("hidden");
    });

    startBtn.addEventListener("click", () => {
        if (!isDockerRunning) {
            showError(
                "Docker is not running. Please start Docker Desktop and refresh."
            );
            return;
        }

        const useGpu = gpuCheckbox.checked;
        const modalId = modalIdInput.value;
        const modalSecret = modalSecretInput.value;
        const openAIKey = openaiKeyInput.value;

        if (!openAIKey) {
            showError(
                "Please enter your OpenAI API Key in the Configuration section."
            );
            setActiveTab(navConfig);
            configSection.classList.remove("hidden");
            logsSection.classList.add("hidden");
            launcherSection.classList.add("hidden");
            logs.focus();
            return;
        }

        if (!useGpu && (!modalId || !modalSecret)) {
            showError(
                "For CPU mode, both Modal Token ID and Modal Token Secret are required."
            );
            setActiveTab(navConfig);
            configSection.classList.remove("hidden");
            logsSection.classList.add("hidden");
            launcherSection.classList.add("hidden");
            logs.focus();
            return;
        }

        const requestBody = {
            gpu: useGpu,
            local: localBuildCheckbox.checked,
            repository: repositorySelect.value,
            OPENAI_API_KEY: openAIKey,
            MODAL_TOKEN_ID: modalId,
            MODAL_TOKEN_SECRET: modalSecret,
        };

        fetchData(
            "/api/start",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            },
            true
        );
    });

    stopBtn.addEventListener("click", () => {
        if (!isDockerRunning) {
            showError(
                "Docker is not running. Please start Docker Desktop and refresh."
            );
            return;
        }
        fetchData(
            "/api/stop",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ clean: cleanStopCheckbox.checked }),
            },
            true
        );
    });

    buildBtn.addEventListener("click", () => {
        if (!isDockerRunning) {
            showError(
                "Docker is not running. Please start Docker Desktop and refresh."
            );
            return;
        }
        const requestBody = {
            gpu: gpuCheckbox.checked,
        };
        fetchData(
            "/api/build",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            },
            true
        );
    });

    refreshBtn.addEventListener("click", () => {
        loadSystemInfo();
    });

    startAppLogStreamBtn.addEventListener("click", () => {
        if (!isDockerRunning) {
            showError(
                "Docker is not running. Please start Docker Desktop and refresh.",
                appLogContainer
            );
            return;
        }
        checkAppStatus().then((value) => {
            if (value && value !== "Running") {
                showError("App is not Running", appLogContainer);
                return;
            }
        });
        abortController = new AbortController();

        fetchData(
            "/api/logs",
            { method: "GET", signal: abortController.signal },
            true,
            appLogContainer,
            false
        );
    });

    stopAppLogStreamBtn.addEventListener("click", () => {
        if (!isDockerRunning) {
            showError(
                "Docker is not running. Please start Docker Desktop and refresh.",
                appLogContainer
            );
            return;
        }
        abortController.abort("Stopped by User");
        appLogContainer.innerHTML =
            '<p class="text-green-400 font-bold">> Stream finished.</p>';
    });

    // --- Initial Setup ---
    setActiveTab(navLauncher);
    loadSystemInfo();
});
