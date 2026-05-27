"use strict";

document.addEventListener("DOMContentLoaded", () => {
    // --- State Management ---
    const state = {
        isDockerRunning: false,
        streamController: null,
        appStatus: "Unknown",
    };

    // --- UI Element Cache ---
    const ui = {
        nav: {
            launcher: document.getElementById("nav-launcher"),
            config: document.getElementById("nav-config"),
            logs: document.getElementById("logsTab"),
            documentation: document.getElementById("documentationButton"),
        },
        sections: {
            launcher: document.getElementById("launcher-section"),
            config: document.getElementById("config-section"),
            appLogs: document.getElementById("appLogs-section"),
            footerLogs: document.getElementById("footerLogs"),
        },
        buttons: {
            start: document.getElementById("start-btn"),
            stop: document.getElementById("stop-btn"),
            build: document.getElementById("build-btn"),
            refresh: document.getElementById("refresh-btn"),
            clearLogs: document.getElementById("clear-logs-btn"),
            clearAppLogs: document.getElementById("clear-app-logs-btn"),
            dismiss: document.getElementById("dismiss-btn"),
            startAppLogStream: document.getElementById("startAppLogStreamBtn"),
            stopAppLogStream: document.getElementById("stopAppLogStreamBtn"),
        },
        containers: {
            systemInfo: document.getElementById("system-info"),
            appStatus: document.getElementById("app-status-text"),
            logs: document.getElementById("logs"),
            appLogs: document.getElementById("dockerAppLogContainer"),
            openApp: document.getElementById("open-app-container"),
        },
        links: {
            openLocal: document.getElementById("open-local-btn"),
            openLan: document.getElementById("open-lan-btn"),
        },
        inputs: {
            localBuild: document.getElementById("local-build-checkbox"),
            cleanStop: document.getElementById("clean-stop-checkbox"),
            repository: document.getElementById("repository-select"),
            openaiKey: document.getElementById("openai-key"),
            modalId: document.getElementById("modal-id"),
            modalSecret: document.getElementById("modal-secret"),
            gpu: document.getElementById("gpu-checkbox"),
            gpuOption: document.getElementById("gpu-option"),
            modalForceBuild: document.getElementById(
                "modal-force-build-checkbox"
            ),
            modalGpu: document.getElementById("modal-gpu-select"),
            loggingLevel: document.getElementById("logging-level-select"),
        },
    };

    // --- Log Manager ---
    const createLogManager = (container) => {
        let cursor = null;

        const createCursor = () => {
            const span = document.createElement("span");
            span.className = "cursor";
            return span;
        };

        const init = () => {
            container.innerHTML = "";
            const initialMsg = document.createElement("span");
            initialMsg.className = "text-gray-400";
            initialMsg.textContent = "Awaiting output...";
            cursor = createCursor();
            container.append(initialMsg, cursor);
        };

        const clear = () => {
            init();
            const logEntry = document.createElement("p");
            logEntry.className = "text-gray-400";
            logEntry.innerHTML = "&gt; Logs cleared.";
            append(logEntry, false);
        };

        const append = (element, scroll = true) => {
            if (cursor) {
                cursor.insertAdjacentElement("beforebegin", element);
                if (scroll) {
                    container.scrollTop = container.scrollHeight;
                }
            } else {
                container.appendChild(element);
            }
        };

        const showError = (message) => {
            container.innerHTML = "";
            const errorP = document.createElement("p");
            errorP.className = "text-red-500 font-bold";
            errorP.textContent = `Error: ${message}`;
            cursor = createCursor();
            container.append(errorP, cursor);
        };

        init();
        return { init, clear, append, showError };
    };

    const mainLogManager = createLogManager(ui.containers.logs);
    const appLogManager = createLogManager(ui.containers.appLogs);

    // --- API Service ---
    const api = {
        async fetch(url, options = {}) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(
                        `API error! status: ${response.status}; message: ${
                            errorData.message
                        }; url: ${errorData.url}; body: ${JSON.stringify(
                            errorData.body
                        )}`
                    );
                }
                return response.json();
            } catch (error) {
                console.error("Fetch error:", error);
                mainLogManager.showError(error.message);
                throw error;
            }
        },
        async stream(url, options, logManager, manageAllButtons = true) {
            state.streamController = new AbortController();
            options.signal = state.streamController.signal;

            if (manageAllButtons) {
                setButtonsDisabled(true);
            }
            logManager.init();
            const connectingMsg = document.createElement("p");
            connectingMsg.className = "text-gray-400";
            connectingMsg.textContent = "> Connecting to stream...";
            logManager.append(connectingMsg);

            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`API error: ${errorData.message}`);
                }

                logManager.init(); // Clear on successful connection

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                const processText = async ({ done, value }) => {
                    if (done) {
                        const doneMsg = document.createElement("p");
                        doneMsg.className = "text-green-400 font-bold";
                        doneMsg.textContent = "> Stream finished.";
                        logManager.append(doneMsg);
                        return;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    const events = chunk
                        .split("\\n\\n")
                        .filter((e) => e.trim());

                    for (const eventStr of events) {
                        if (eventStr.includes("event: done")) {
                            return;
                        }
                        if (eventStr.startsWith("data:")) {
                            const data = eventStr.substring(5).trim();
                            if (data.startsWith("LAN Access URL:")) {
                                ui.links.openLan.href = data
                                    .substring(16)
                                    .trim();
                            } else if (data.startsWith("Local Access URL:")) {
                                ui.links.openLocal.href = data
                                    .substring(18)
                                    .trim();
                            } else {
                                const logEntry = document.createElement("p");
                                logEntry.innerHTML = `&gt; ${data}`;
                                logManager.append(logEntry);
                            }
                        }
                    }
                    return reader.read().then(processText);
                };
                await reader.read().then(processText);
            } catch (error) {
                if (error.name !== "AbortError") {
                    logManager.showError(error.message);
                    throw error;
                } else {
                    const abortMsg = document.createElement("p");
                    abortMsg.className = "text-yellow-400 font-bold";
                    abortMsg.textContent = "> Stream stopped by user.";
                    logManager.append(abortMsg);
                }
            } finally {
                if (manageAllButtons) {
                    setButtonsDisabled(false);
                }
                state.streamController = null;
            }
        },
    };

    // --- UI Functions ---
    const setButtonsDisabled = (disabled) => {
        Object.values(ui.buttons).forEach((button) => {
            if (button) button.disabled = disabled;
        });
    };

    const setAppStatus = (
        status,
        color = "text-gray-700 dark:text-gray-300"
    ) => {
        state.appStatus = status;
        ui.containers.appStatus.textContent = status;
        ui.containers.appStatus.className = `text-lg font-semibold ${color}`;
    };

    const setActiveTab = (activeTabId) => {
        Object.values(ui.nav).forEach((tab) => {
            const isActive = tab.id === activeTabId;
            tab.classList.toggle("border-b-2", isActive);
            tab.classList.toggle("border-indigo-500", isActive);
            tab.classList.toggle("text-indigo-500", isActive);
            tab.classList.toggle("text-gray-500", !isActive);
        });

        Object.values(ui.sections).forEach((section) => {
            section.classList.add("hidden");
        });

        if (activeTabId === "nav-launcher") {
            ui.sections.launcher.classList.remove("hidden");
            ui.sections.footerLogs.classList.remove("hidden");
        } else if (activeTabId === "nav-config") {
            ui.sections.config.classList.remove("hidden");
            ui.sections.footerLogs.classList.remove("hidden");
        } else if (activeTabId === "logsTab") {
            ui.sections.appLogs.classList.remove("hidden");
        }
    };

    // --- Core Logic ---
    async function checkAppStatus() {
        try {
            const response = await fetch("https://localhost/api/health/status");
            if (response.ok) {
                const data = await response.json();
                if (data.status === "ok") {
                    setAppStatus("Running", "text-green-400");
                } else {
                    setAppStatus("Unhealthy", "text-yellow-400");
                }
            } else {
                setAppStatus("Not Ready", "text-yellow-400");
            }
        } catch {
            setAppStatus("Not Ready", "text-yellow-400");
        }
    }

    async function loadSystemInfo() {
        ui.containers.systemInfo.innerHTML = "<p>Checking...</p>";
        setButtonsDisabled(true);
        try {
            const [dockerData, gpuData] = await Promise.all([
                api.fetch("/api/dockerRunning"),
                api.fetch("/api/hasGPU"),
            ]);

            state.isDockerRunning = dockerData.status;

            const dockerStatus = dockerData.status
                ? '<span class="text-green-400">Ready</span>'
                : '<span class="text-red-400">Not Running</span>';
            const gpuStatus = gpuData.status
                ? '<span class="text-green-400">Available</span>'
                : '<span class="text-red-400">Not Detected</span>';

            ui.containers.systemInfo.innerHTML = `
                <div><p class="font-bold">Docker</p><p>${dockerStatus}</p></div>
                <div><p class="font-bold">NVIDIA GPU</p><p>${gpuStatus}</p></div>
            `;

            ui.inputs.gpuOption.classList.toggle("hidden", !gpuData.status);
            if (!gpuData.status) {
                ui.inputs.gpu.checked = false;
            }
            await checkAppStatus();
        } catch (error) {
            ui.containers.systemInfo.innerHTML =
                '<p class="text-red-500">Error Fetching System Info</p>';
        } finally {
            setButtonsDisabled(false);
        }
    }

    // --- Event Handlers ---
    function setupEventListeners() {
        ui.nav.launcher.addEventListener("click", () =>
            setActiveTab("nav-launcher")
        );
        ui.nav.config.addEventListener("click", () =>
            setActiveTab("nav-config")
        );
        ui.nav.logs.addEventListener("click", () => setActiveTab("logsTab"));
        ui.nav.documentation.addEventListener("click", () =>
            window.open("https://svdc1.github.io/mirumoji/docs", "_blank")
        );

        ui.buttons.clearLogs.addEventListener("click", () =>
            mainLogManager.clear()
        );
        ui.buttons.clearAppLogs.addEventListener("click", () =>
            appLogManager.clear()
        );
        ui.buttons.dismiss.addEventListener("click", () =>
            ui.containers.openApp.classList.add("hidden")
        );
        ui.buttons.refresh.addEventListener("click", loadSystemInfo);

        ui.buttons.start.addEventListener("click", () => {
            if (!state.isDockerRunning) {
                mainLogManager.showError(
                    "Docker is not running. Please start Docker and refresh."
                );
                return;
            }

            const openAIKey = ui.inputs.openaiKey.value;
            if (!openAIKey) {
                mainLogManager.showError(
                    "Please enter your OpenAI API Key in the Configuration tab."
                );
                setActiveTab("nav-config");
                return;
            }
            if (
                !ui.inputs.gpu.checked &&
                (!ui.inputs.modalId.value || !ui.inputs.modalSecret.value)
            ) {
                mainLogManager.showError(
                    "For CPU mode, both Modal Token ID and Secret are required."
                );
                setActiveTab("nav-config");
                return;
            }

            const body = {
                gpu: ui.inputs.gpu.checked,
                local: ui.inputs.localBuild.checked,
                repository: ui.inputs.repository.value,
                MIRUMOJI_LOGGING_LEVEL: ui.inputs.loggingLevel.value,
                MODAL_FORCE_BUILD: ui.inputs.modalForceBuild.checked,
                MIRUMOJI_MODAL_GPU: ui.inputs.modalGpu.value,
                OPENAI_API_KEY: openAIKey,
                MODAL_TOKEN_ID: ui.inputs.modalId.value,
                MODAL_TOKEN_SECRET: ui.inputs.modalSecret.value,
            };

            api.stream(
                "/api/start",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body),
                },
                mainLogManager
            ).then(() => {
                ui.containers.openApp.classList.remove("hidden");
                checkAppStatus();
            });
        });

        ui.buttons.stop.addEventListener("click", () => {
            if (!state.isDockerRunning) {
                mainLogManager.showError(
                    "Docker is not running. Please start Docker and refresh."
                );
                return;
            }
            api.stream(
                "/api/stop",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        clean: ui.inputs.cleanStop.checked,
                    }),
                },
                mainLogManager
            ).then(checkAppStatus);
        });

        ui.buttons.build.addEventListener("click", () => {
            if (!state.isDockerRunning) {
                mainLogManager.showError(
                    "Docker is not running. Please start Docker and refresh."
                );
                return;
            }
            api.stream(
                "/api/build",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ gpu: ui.inputs.gpu.checked }),
                },
                mainLogManager
            );
        });

        ui.buttons.startAppLogStream.addEventListener("click", () => {
            if (!state.isDockerRunning) {
                appLogManager.showError(
                    "Docker is not running. Please start Docker and refresh."
                );
                return;
            }
            if (state.appStatus !== "Running") {
                appLogManager.showError("Application is not running.");
                return;
            }
            ui.buttons.startAppLogStream.disabled = true;
            ui.buttons.stopAppLogStream.disabled = false;
            api.stream(
                "/api/logs",
                { method: "GET" },
                appLogManager,
                false
            ).finally(() => {
                ui.buttons.startAppLogStream.disabled = false;
                ui.buttons.stopAppLogStream.disabled = true;
            });
        });

        ui.buttons.stopAppLogStream.addEventListener("click", () => {
            if (state.streamController) {
                state.streamController.abort();
            }
        });
    }

    // --- Initialization ---
    function init() {
        setActiveTab("nav-launcher");
        setupEventListeners();
        loadSystemInfo();
        ui.buttons.stopAppLogStream.disabled = true;
    }

    init();
});
