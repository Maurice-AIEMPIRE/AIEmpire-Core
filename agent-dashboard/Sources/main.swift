import Cocoa
import Foundation

final class CPUSampler {
    private var previousTicks: [UInt32]?

    func sampleUsage() -> Double? {
        var cpuCount: natural_t = 0
        var infoCount: mach_msg_type_number_t = 0
        var cpuInfo: processor_info_array_t?

        let result = host_processor_info(
            mach_host_self(),
            PROCESSOR_CPU_LOAD_INFO,
            &cpuCount,
            &cpuInfo,
            &infoCount
        )

        guard result == KERN_SUCCESS, let cpuInfo = cpuInfo else {
            return nil
        }

        defer {
            let size = vm_size_t(infoCount) * vm_size_t(MemoryLayout<integer_t>.size)
            vm_deallocate(mach_task_self_, vm_address_t(bitPattern: cpuInfo), size)
        }

        let cpuInfoPtr = UnsafeMutablePointer<integer_t>(cpuInfo)
        let cpuStateMax = Int(CPU_STATE_MAX)
        let cpuInfoSize = Int(cpuCount) * cpuStateMax
        var ticks = [UInt32]()
        ticks.reserveCapacity(cpuInfoSize)
        for index in 0..<cpuInfoSize {
            ticks.append(UInt32(cpuInfoPtr[index]))
        }

        guard let previous = previousTicks else {
            previousTicks = ticks
            return nil
        }

        var totalUsage = 0.0
        var samples = 0
        let stateUser = Int(CPU_STATE_USER)
        let stateSystem = Int(CPU_STATE_SYSTEM)
        let stateIdle = Int(CPU_STATE_IDLE)
        let stateNice = Int(CPU_STATE_NICE)

        for cpu in 0..<Int(cpuCount) {
            let base = cpu * cpuStateMax
            let user = Double(ticks[base + stateUser] - previous[base + stateUser])
            let system = Double(ticks[base + stateSystem] - previous[base + stateSystem])
            let idle = Double(ticks[base + stateIdle] - previous[base + stateIdle])
            let nice = Double(ticks[base + stateNice] - previous[base + stateNice])
            let total = user + system + idle + nice
            if total > 0 {
                totalUsage += (total - idle) / total
                samples += 1
            }
        }

        previousTicks = ticks
        if samples == 0 { return nil }
        return totalUsage / Double(samples)
    }
}

struct MemoryStats {
    let totalBytes: UInt64
    let availableBytes: UInt64
    let usedBytes: UInt64
    let activeBytes: UInt64
    let inactiveBytes: UInt64
    let wiredBytes: UInt64
    let compressedBytes: UInt64
    let purgeableBytes: UInt64

    static func read() -> MemoryStats? {
        var stats = vm_statistics64()
        var count = mach_msg_type_number_t(MemoryLayout<vm_statistics64_data_t>.size / MemoryLayout<integer_t>.size)
        let result = withUnsafeMutablePointer(to: &stats) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                host_statistics64(mach_host_self(), HOST_VM_INFO64, $0, &count)
            }
        }

        guard result == KERN_SUCCESS else { return nil }

        let pageSize = UInt64(vm_kernel_page_size)
        let free = UInt64(stats.free_count)
        let inactive = UInt64(stats.inactive_count)
        let speculative = UInt64(stats.speculative_count)
        let purgeable = UInt64(stats.purgeable_count)
        let active = UInt64(stats.active_count)
        let wired = UInt64(stats.wire_count)
        let compressed = UInt64(stats.compressor_page_count)

        let available = (free + inactive + speculative + purgeable) * pageSize
        let total = ProcessInfo.processInfo.physicalMemory
        let used = total > available ? total - available : 0

        return MemoryStats(
            totalBytes: total,
            availableBytes: available,
            usedBytes: used,
            activeBytes: active * pageSize,
            inactiveBytes: inactive * pageSize,
            wiredBytes: wired * pageSize,
            compressedBytes: compressed * pageSize,
            purgeableBytes: purgeable * pageSize
        )
    }
}

struct SwapUsage {
    var total: UInt64 = 0
    var avail: UInt64 = 0
    var used: UInt64 = 0
    var pageSize: UInt32 = 0
    var encrypted: UInt32 = 0

    static func read() -> SwapUsage? {
        var usage = SwapUsage()
        var size = MemoryLayout<SwapUsage>.size
        let result = sysctlbyname("vm.swapusage", &usage, &size, nil, 0)
        return result == 0 ? usage : nil
    }
}

final class DashboardController {
    private let cpuSampler = CPUSampler()
    private let totalMemory = ProcessInfo.processInfo.physicalMemory
    private let coreCount = max(1, ProcessInfo.processInfo.activeProcessorCount)
    private let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "HH:mm:ss"
        return formatter
    }()
    private let metaDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter
    }()

    private let statusItem: NSStatusItem
    private let panel: NSPanel
    private let textField: NSTextField
    private let statusLabel: NSTextField
    private let balanceSparkline: NSTextField
    private var swarmListStack = NSStackView()
    private var swarmRows: [(NSTextField, NSProgressIndicator, NSTextField)] = []
    private let progressIndicator: NSProgressIndicator
    private let swarmPromptField: NSTextField
    private let swarmCountField: NSTextField
    private let taskIdField: NSTextField
    private let taskProviderField: NSTextField
    private lazy var swarmStartButton: NSButton = {
        let button = NSButton(title: "Swarm Start", target: self, action: #selector(startCustomSwarm))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var swarmQuick50Button: NSButton = {
        let button = NSButton(title: "Swarm 50", target: self, action: #selector(startQuick50))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var swarmQuick200Button: NSButton = {
        let button = NSButton(title: "Swarm 200", target: self, action: #selector(startQuick200))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var openOutputButton: NSButton = {
        let button = NSButton(title: "Open Output", target: self, action: #selector(openOutputFolder))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var refreshButton: NSButton = {
        let button = NSButton(title: "Refresh Now", target: self, action: #selector(refresh))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var pauseResumeButton: NSButton = {
        let button = NSButton(title: "Pause", target: self, action: #selector(togglePause))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var stopAllButton: NSButton = {
        let button = NSButton(title: "Stop All", target: self, action: #selector(stopAllSwarms))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var startTaskButton: NSButton = {
        let button = NSButton(title: "Start Task", target: self, action: #selector(startTask))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var autoMasterButton: NSButton = {
        let button = NSButton(title: "AutoMaster", target: self, action: #selector(runAutoMaster))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var openLatestButton: NSButton = {
        let button = NSButton(title: "Open Latest", target: self, action: #selector(openLatestOutput))
        button.bezelStyle = .rounded
        return button
    }()
    private lazy var openLogsButton: NSButton = {
        let button = NSButton(title: "Open Logs", target: self, action: #selector(openLogsFolder))
        button.bezelStyle = .rounded
        return button
    }()

    private var timer: Timer?
    private let interval: TimeInterval = 5.0
    private let activeWindow: TimeInterval = 10 * 60
    private let balanceRefreshInterval: TimeInterval = 60.0
    private var lastBalanceFetch: Date?
    private var isBalanceFetchInFlight = false
    private var cachedKimiBalance: String = "--"
    private var dotenvCache: [String: String] = [:]
    private var dotenvLastRead: Date?
    private var balanceHistory: [Double] = []
    private let balanceHistoryLimit = 24
    private var swarmProcess: Process?

    init() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "Agent"

        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Dashboard anzeigen/ausblenden", action: #selector(togglePanel), keyEquivalent: "d"))
        menu.addItem(NSMenuItem(title: "Jetzt aktualisieren", action: #selector(refresh), keyEquivalent: "r"))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Beenden", action: #selector(quit), keyEquivalent: "q"))
        statusItem.menu = menu

        let panelSize = NSSize(width: 680, height: 560)
        panel = NSPanel(
            contentRect: NSRect(origin: .zero, size: panelSize),
            styleMask: [.titled, .nonactivatingPanel, .closable],
            backing: .buffered,
            defer: false
        )
        panel.isFloatingPanel = true
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary]
        panel.title = "Agent Monitor"
        panel.backgroundColor = NSColor.windowBackgroundColor.withAlphaComponent(0.96)
        panel.isMovableByWindowBackground = true

        progressIndicator = NSProgressIndicator(frame: NSRect(x: 16, y: panelSize.height - 40, width: panelSize.width - 32, height: 10))
        progressIndicator.isIndeterminate = false
        progressIndicator.minValue = 0
        progressIndicator.maxValue = 1
        progressIndicator.doubleValue = 0
        panel.contentView?.addSubview(progressIndicator)

        statusLabel = NSTextField(labelWithString: "Swarm: --")
        statusLabel.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
        statusLabel.frame = NSRect(x: 16, y: panelSize.height - 60, width: panelSize.width - 32, height: 16)
        panel.contentView?.addSubview(statusLabel)

        balanceSparkline = NSTextField(labelWithString: "Balance trend: --")
        balanceSparkline.font = NSFont.monospacedSystemFont(ofSize: 11, weight: .regular)
        balanceSparkline.frame = NSRect(x: 16, y: panelSize.height - 78, width: panelSize.width - 32, height: 14)
        panel.contentView?.addSubview(balanceSparkline)

        let swarmTitle = NSTextField(labelWithString: "Strategy View — Active Swarms")
        swarmTitle.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
        swarmTitle.frame = NSRect(x: 16, y: panelSize.height - 104, width: panelSize.width - 32, height: 16)
        panel.contentView?.addSubview(swarmTitle)

        swarmListStack = NSStackView()
        swarmListStack.orientation = .vertical
        swarmListStack.spacing = 6
        swarmListStack.alignment = .leading
        swarmListStack.frame = NSRect(x: 16, y: panelSize.height - 182, width: panelSize.width - 32, height: 70)
        panel.contentView?.addSubview(swarmListStack)

        for _ in 0..<6 {
            let row = NSStackView()
            row.orientation = .horizontal
            row.spacing = 8
            row.alignment = .centerY

            let name = NSTextField(labelWithString: "--")
            name.font = NSFont.systemFont(ofSize: 11, weight: .medium)
            name.frame = NSRect(x: 0, y: 0, width: 220, height: 16)

            let bar = NSProgressIndicator()
            bar.minValue = 0
            bar.maxValue = 100
            bar.doubleValue = 0
            bar.isIndeterminate = false
            bar.controlSize = .small
            bar.frame = NSRect(x: 0, y: 0, width: 200, height: 10)

            let eta = NSTextField(labelWithString: "--")
            eta.font = NSFont.systemFont(ofSize: 10, weight: .regular)
            eta.textColor = NSColor.secondaryLabelColor
            eta.frame = NSRect(x: 0, y: 0, width: 80, height: 16)

            row.addArrangedSubview(name)
            row.addArrangedSubview(bar)
            row.addArrangedSubview(eta)
            swarmListStack.addArrangedSubview(row)
            swarmRows.append((name, bar, eta))
        }

        textField = NSTextField(labelWithString: "")
        textField.font = NSFont.monospacedSystemFont(ofSize: 12, weight: .regular)
        textField.lineBreakMode = .byWordWrapping
        textField.maximumNumberOfLines = 0
        textField.frame = NSRect(x: 16, y: 230, width: panelSize.width - 32, height: panelSize.height - 380)
        panel.contentView?.addSubview(textField)

        swarmPromptField = NSTextField(string: "Aufgabe für Swarm (kurz & klar)")
        swarmPromptField.frame = NSRect(x: 16, y: 150, width: panelSize.width - 200, height: 24)
        panel.contentView?.addSubview(swarmPromptField)

        swarmCountField = NSTextField(string: "100")
        swarmCountField.frame = NSRect(x: panelSize.width - 172, y: 150, width: 60, height: 24)
        panel.contentView?.addSubview(swarmCountField)

        taskIdField = NSTextField(string: "Task ID (z.B. 20260205_014344_24112)")
        taskIdField.frame = NSRect(x: 16, y: 86, width: panelSize.width - 320, height: 24)
        panel.contentView?.addSubview(taskIdField)

        taskProviderField = NSTextField(string: "auto")
        taskProviderField.frame = NSRect(x: panelSize.width - 292, y: 86, width: 60, height: 24)
        panel.contentView?.addSubview(taskProviderField)

        swarmStartButton.frame = NSRect(x: panelSize.width - 104, y: 148, width: 88, height: 26)
        panel.contentView?.addSubview(swarmStartButton)

        swarmQuick50Button.frame = NSRect(x: 16, y: 120, width: 88, height: 24)
        panel.contentView?.addSubview(swarmQuick50Button)

        swarmQuick200Button.frame = NSRect(x: 110, y: 120, width: 96, height: 24)
        panel.contentView?.addSubview(swarmQuick200Button)

        openOutputButton.frame = NSRect(x: 212, y: 120, width: 110, height: 24)
        panel.contentView?.addSubview(openOutputButton)

        refreshButton.frame = NSRect(x: panelSize.width - 130, y: 118, width: 110, height: 24)
        panel.contentView?.addSubview(refreshButton)

        startTaskButton.frame = NSRect(x: panelSize.width - 224, y: 84, width: 96, height: 26)
        panel.contentView?.addSubview(startTaskButton)

        openLatestButton.frame = NSRect(x: panelSize.width - 120, y: 84, width: 104, height: 26)
        panel.contentView?.addSubview(openLatestButton)

        pauseResumeButton.frame = NSRect(x: 16, y: 48, width: 90, height: 26)
        panel.contentView?.addSubview(pauseResumeButton)

        stopAllButton.frame = NSRect(x: 110, y: 48, width: 90, height: 26)
        panel.contentView?.addSubview(stopAllButton)

        autoMasterButton.frame = NSRect(x: 206, y: 48, width: 110, height: 26)
        panel.contentView?.addSubview(autoMasterButton)

        openLogsButton.frame = NSRect(x: 322, y: 48, width: 100, height: 26)
        panel.contentView?.addSubview(openLogsButton)

        positionPanel()
        panel.orderFrontRegardless()

        refresh()
        timer = Timer.scheduledTimer(timeInterval: interval, target: self, selector: #selector(refresh), userInfo: nil, repeats: true)
        timer?.tolerance = 0.5
    }

    private func positionPanel() {
        guard let screen = NSScreen.main else { return }
        let frame = screen.visibleFrame
        let margin: CGFloat = 16
        let x = frame.maxX - panel.frame.width - margin
        let y = frame.maxY - panel.frame.height - margin
        panel.setFrameOrigin(NSPoint(x: x, y: y))
    }

    @objc private func togglePanel() {
        if panel.isVisible {
            panel.orderOut(nil)
        } else {
            positionPanel()
            panel.orderFrontRegardless()
        }
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }

    @objc private func refresh() {
        refreshDotEnvIfNeeded()
        let cpuUsage = cpuSampler.sampleUsage()
        let mem = MemoryStats.read()
        let swap = SwapUsage.read()
        let swarm = readSwarmStats()
        let taskStats = readTaskStats()
        let autoPipeline = isAutoPipelineRunning()
        let gatewayStatus = isGatewayRunning() ? "running" : "stopped"
        let openAIStatus = openAIConfigured() ? "configured" : "missing"
        let paused = isPaused()

        var loads = [Double](repeating: 0.0, count: 3)
        getloadavg(&loads, 3)

        let cpuText = cpuUsage.map { String(format: "%.0f%%", $0 * 100.0) } ?? "--"

        let totalGiB = Double(totalMemory) / 1024.0 / 1024.0 / 1024.0
        let usedGiB = mem.map { Double($0.usedBytes) / 1024.0 / 1024.0 / 1024.0 } ?? 0.0
        let availGiB = mem.map { Double($0.availableBytes) / 1024.0 / 1024.0 / 1024.0 } ?? 0.0
        let pressure = mem.map { Double($0.usedBytes) / Double($0.totalBytes) } ?? 0.0

        let swapGiB = swap.map { Double($0.used) / 1024.0 / 1024.0 / 1024.0 } ?? 0.0

        let lightAgents = max(1, min(Int(availGiB / 0.5), coreCount * 2))
        let mediumAgents = max(1, min(Int(availGiB / 1.0), coreCount))
        let heavyAgents = max(1, min(Int(availGiB / 2.0), max(1, coreCount / 2)))

        statusItem.button?.title = String(format: "CPU %@ | RAM %.1f/%.0f | L %.2f", cpuText, usedGiB, totalGiB, loads[0])

        let latestSwarmName = swarm.latestSwarmName ?? "--"
        let latestSwarmCount = swarm.latestSwarmAgentCount
        let latestSwarmTime = swarm.latestSwarmUpdatedAt.map { timeFormatter.string(from: $0) } ?? "--"
        let lastUpdateAge = swarm.latestSwarmUpdatedAt.map { formatAge(max(0, Date().timeIntervalSince($0))) } ?? "--"
        let activeRatio = swarm.latestTargetCount > 0 ? Double(swarm.latestSwarmAgentCount) / Double(swarm.latestTargetCount) : (swarm.totalAgentFiles > 0 ? Double(swarm.activeAgentFiles) / Double(swarm.totalAgentFiles) : 0)

        maybeRefreshKimiBalance()

        progressIndicator.doubleValue = activeRatio
        if paused {
            statusLabel.stringValue = "Swarm: PAUSED"
            pauseResumeButton.title = "Resume"
        } else if (swarm.activeAgentFiles > 0 || swarm.activeSwarmDirs > 0) {
            statusLabel.stringValue = "Swarm: RUNNING"
            pauseResumeButton.title = "Pause"
        } else {
            statusLabel.stringValue = "Swarm: IDLE"
            pauseResumeButton.title = "Pause"
        }
        balanceSparkline.stringValue = "Balance trend: \(sparkline(for: balanceHistory))"

        // Strategy view rows
        let items = swarm.progressItems
        for idx in 0..<swarmRows.count {
            let (nameLabel, bar, etaLabel) = swarmRows[idx]
            if idx < items.count {
                let item = items[idx]
                nameLabel.stringValue = item.name
                bar.doubleValue = Double(item.pct)
                etaLabel.stringValue = "ETA \(item.eta)"
            } else {
                nameLabel.stringValue = "--"
                bar.doubleValue = 0
                etaLabel.stringValue = "--"
            }
        }

        let text = """
CPU:        \(cpuText)        Load: \(String(format: "%.2f", loads[0]))
RAM:        \(String(format: "%.1f", usedGiB))/\(String(format: "%.0f", totalGiB)) GiB   (frei ~\(String(format: "%.1f", availGiB)) GiB)
Pressure:   \(String(format: "%.0f%%", pressure * 100.0))
Swap:       \(String(format: "%.2f", swapGiB)) GiB
Gateway:    \(gatewayStatus)
Kimi:       ¥\(cachedKimiBalance)
OpenAI:     \(openAIStatus)
Swarm:      total \(swarm.totalAgentFiles) Dateien
Active:     \(swarm.activeAgentFiles) Dateien (<10m) | Swarms: \(swarm.activeSwarmDirs)
Latest:     \(latestSwarmName) (\(latestSwarmCount)) @ \(latestSwarmTime) (age \(lastUpdateAge))
Paused:     \(paused ? "yes" : "no") | Auto: \(autoPipeline ? "on" : "off")
Tasks:      queued \(taskStats.queued) | running \(taskStats.running) | done \(taskStats.done)

Agenten-Schätzung (freiem RAM):
Light 0.5G: \(lightAgents)   Medium 1G: \(mediumAgents)   Heavy 2G: \(heavyAgents)

Tasks (latest 10):
\(taskStats.summary.isEmpty ? "• --" : taskStats.summary)

Live Swarms (ETA):
\(swarm.detailedSummary.isEmpty ? "• --" : swarm.detailedSummary)
"""

        textField.stringValue = text
    }

    private func isGatewayRunning() -> Bool {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/pgrep")
        process.arguments = ["-f", "openclaw-gateway"]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = Pipe()
        do {
            try process.run()
            process.waitUntilExit()
            return process.terminationStatus == 0
        } catch {
            return false
        }
    }

    private func openAIConfigured() -> Bool {
        let key = getEnvValue("OPENAI_API_KEY")
        return !key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private func isAutoPipelineRunning() -> Bool {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/launchctl")
        process.arguments = ["list"]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = Pipe()
        do {
            try process.run()
            process.waitUntilExit()
            if process.terminationStatus != 0 { return false }
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let text = String(data: data, encoding: .utf8) ?? ""
            return text.contains("com.ai-empire.autopipeline")
        } catch {
            return false
        }
    }

    private func isPaused() -> Bool {
        let pausePath = "/Users/maurice/.openclaw/workspace/ai-empire/00_SYSTEM/PAUSE"
        return FileManager.default.fileExists(atPath: pausePath)
    }

    private func maybeRefreshKimiBalance() {
        if isBalanceFetchInFlight {
            return
        }
        if let last = lastBalanceFetch, Date().timeIntervalSince(last) < balanceRefreshInterval {
            return
        }

        let apiKey = getEnvValue("MOONSHOT_API_KEY")
        if apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            cachedKimiBalance = "--"
            return
        }

        isBalanceFetchInFlight = true
        lastBalanceFetch = Date()

        guard let url = URL(string: "https://api.moonshot.ai/v1/users/me/balance") else {
            isBalanceFetchInFlight = false
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")

        URLSession.shared.dataTask(with: request) { [weak self] data, _, _ in
            guard let self else { return }
            defer { self.isBalanceFetchInFlight = false }

            guard let data else { return }
            if let json = try? JSONSerialization.jsonObject(with: data, options: []),
               let dict = json as? [String: Any],
               let dataDict = dict["data"] as? [String: Any],
               let balance = dataDict["available_balance"] as? Double {
                self.cachedKimiBalance = String(format: "%.2f", balance)
                self.recordBalance(balance)
                DispatchQueue.main.async {
                    self.refresh()
                }
            }
        }.resume()
    }

    private func recordBalance(_ value: Double) {
        balanceHistory.append(value)
        if balanceHistory.count > balanceHistoryLimit {
            balanceHistory.removeFirst(balanceHistory.count - balanceHistoryLimit)
        }
    }

    private func getEnvValue(_ key: String) -> String {
        if let value = ProcessInfo.processInfo.environment[key], !value.isEmpty {
            return value
        }
        return dotenvCache[key] ?? ""
    }

    private func refreshDotEnvIfNeeded() {
        let now = Date()
        if let last = dotenvLastRead, now.timeIntervalSince(last) < 30 {
            return
        }
        dotenvLastRead = now
        let path = "/Users/maurice/.openclaw/.env"
        guard let content = try? String(contentsOfFile: path, encoding: .utf8) else {
            dotenvCache = [:]
            return
        }
        var dict: [String: String] = [:]
        for line in content.split(separator: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty || trimmed.hasPrefix("#") { continue }
            let parts = trimmed.split(separator: "=", maxSplits: 1).map(String.init)
            if parts.count == 2 {
                dict[parts[0].trimmingCharacters(in: .whitespacesAndNewlines)] = parts[1].trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }
        dotenvCache = dict
    }

    private func sparkline(for values: [Double]) -> String {
        guard let minVal = values.min(), let maxVal = values.max(), !values.isEmpty else {
            return "--"
        }
        let span = max(maxVal - minVal, 0.0001)
        let levels = Array(" .:-=+*#%@")
        return values.map { value in
            let normalized = (value - minVal) / span
            let idx = min(levels.count - 1, max(0, Int(round(normalized * Double(levels.count - 1)))))
            return String(levels[idx])
        }.joined()
    }

    @objc private func startCustomSwarm() {
        let count = Int(swarmCountField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 100
        let prompt = swarmPromptField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        if prompt.isEmpty {
            return
        }
        startSwarm(count: max(1, count), prompt: prompt)
    }

    @objc private func startQuick50() {
        startSwarm(count: 50, prompt: "Kategorisiere und extrahiere Fakten aus Rechtsstreit-Dokumenten.")
    }

    @objc private func startQuick200() {
        startSwarm(count: 200, prompt: "Finde Beweise, Chronologie und Argumente aus Rechtsstreit-Dokumenten.")
    }

    private func startSwarm(count: Int, prompt: String) {
        if swarmProcess?.isRunning == true {
            return
        }
        statusLabel.stringValue = "Swarm: STARTING"

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/Users/maurice/.openclaw/scripts/task-router.sh")
        process.arguments = ["swarm", "auto", String(count), prompt]

        var env = ProcessInfo.processInfo.environment
        let currentPath = env["PATH"] ?? ""
        let homebrewPath = "/opt/homebrew/bin:/opt/homebrew/opt/node@22/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        env["PATH"] = homebrewPath + ":" + currentPath
        process.environment = env

        process.terminationHandler = { [weak self] _ in
            DispatchQueue.main.async {
                self?.statusLabel.stringValue = "Swarm: IDLE"
                self?.swarmProcess = nil
            }
        }

        do {
            try process.run()
            swarmProcess = process
        } catch {
            statusLabel.stringValue = "Swarm: FAILED"
            swarmProcess = nil
        }
    }

    @objc private func startTask() {
        let taskId = taskIdField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        if taskId.isEmpty { return }
        let provider = taskProviderField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/Users/maurice/.openclaw/scripts/task-router.sh")
        var args = ["task", "start", taskId]
        if !provider.isEmpty { args.append(provider) }
        process.arguments = args
        do { try process.run() } catch {}
    }

    @objc private func togglePause() {
        let paused = isPaused()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/Users/maurice/.openclaw/scripts/task-router.sh")
        process.arguments = [paused ? "resume" : "pause"]
        do { try process.run() } catch {}
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { self.refresh() }
    }

    @objc private func stopAllSwarms() {
        _ = createPauseFile()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sh")
        process.arguments = ["-lc", "pkill -f 'moonshot.ai/v1/chat/completions' || true; pkill -f 'api.openai.com/v1/chat/completions' || true"]
        do { try process.run() } catch {}
    }

    private func createPauseFile() -> Bool {
        let pausePath = "/Users/maurice/.openclaw/workspace/ai-empire/00_SYSTEM/PAUSE"
        if FileManager.default.fileExists(atPath: pausePath) { return true }
        return FileManager.default.createFile(atPath: pausePath, contents: Data(), attributes: nil)
    }

    @objc private func runAutoMaster() {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = ["/Users/maurice/.openclaw/ai-vault/auto_master.py"]
        do { try process.run() } catch {}
    }

    @objc private func openLatestOutput() {
        if let latest = readLatestOutputDir() {
            NSWorkspace.shared.open(URL(fileURLWithPath: latest))
        } else {
            openOutputFolder()
        }
    }

    @objc private func openLogsFolder() {
        let url = URL(fileURLWithPath: "/Users/maurice/.openclaw/ai-vault")
        NSWorkspace.shared.open(url)
    }

    @objc private func openOutputFolder() {
        let url = URL(fileURLWithPath: "/Users/maurice/.openclaw/workspace/ai-empire/04_OUTPUT")
        NSWorkspace.shared.open(url)
    }

    private func readLatestOutputDir() -> String? {
        let basePath = "/Users/maurice/.openclaw/workspace/ai-empire/04_OUTPUT"
        let fm = FileManager.default
        guard let entries = try? fm.contentsOfDirectory(atPath: basePath) else { return nil }
        var latest: (Date, String)?
        for entry in entries {
            if !(entry.hasPrefix("swarm_") || entry.hasPrefix("mega_swarm_") || entry.hasPrefix("kimi_") || entry.hasPrefix("task_")) {
                continue
            }
            let dirPath = (basePath as NSString).appendingPathComponent(entry)
            if let attrs = try? fm.attributesOfItem(atPath: dirPath),
               let mtime = attrs[.modificationDate] as? Date {
                if latest == nil || mtime > latest!.0 {
                    latest = (mtime, dirPath)
                }
            }
        }
        return latest?.1
    }

    private func readSwarmStats() -> SwarmStats {
        let basePath = "/Users/maurice/.openclaw/workspace/ai-empire/04_OUTPUT"
        let fm = FileManager.default
        guard let entries = try? fm.contentsOfDirectory(atPath: basePath) else {
            return SwarmStats(
                totalAgentFiles: 0,
                latestSwarmName: nil,
                latestSwarmAgentCount: 0,
                latestSwarmUpdatedAt: nil,
                latestTargetCount: 0,
                activeAgentFiles: 0,
                activeSwarmDirs: 0,
                taskSummary: "",
                detailedSummary: "",
                progressItems: []
            )
        }

        let now = Date()
        var total = 0
        var latestName: String?
        var latestCount = 0
        var latestDate: Date?
        var activeFiles = 0
        var activeDirs = 0
        var taskLines: [(Date, String)] = []
        var detailedLines: [(Date, String)] = []
        var progressItems: [(Date, SwarmProgressItem)] = []
        var latestTarget = 0

        for entry in entries {
            if !(entry.hasPrefix("swarm_") || entry.hasPrefix("mega_swarm_") || entry.hasPrefix("kimi_") || entry.hasPrefix("task_")) {
                continue
            }
            let dirPath = (basePath as NSString).appendingPathComponent(entry)
            let files = (try? fm.contentsOfDirectory(atPath: dirPath)) ?? []
            let count = files.filter { $0.hasPrefix("agent_") && $0.hasSuffix(".json") }.count
            total += count

            if let attrs = try? fm.attributesOfItem(atPath: dirPath),
               let mtime = attrs[.modificationDate] as? Date {
                if latestDate == nil || mtime > latestDate! {
                    latestDate = mtime
                    latestName = entry
                    latestCount = count
                }
                if now.timeIntervalSince(mtime) <= activeWindow {
                    activeDirs += 1
                }

                let metaPath = (dirPath as NSString).appendingPathComponent("swarm_meta.json")
                var targetCount = count
                var provider = ""
                var status = ""
                var startedAt: Date?
                if let data = try? Data(contentsOf: URL(fileURLWithPath: metaPath)),
                   let json = try? JSONSerialization.jsonObject(with: data, options: []),
                   let dict = json as? [String: Any] {
                    if let t = dict["target_count"] as? Int { targetCount = t }
                    provider = dict["provider"] as? String ?? ""
                    status = dict["status"] as? String ?? ""
                    if let s = dict["started_at"] as? String {
                        startedAt = metaDateFormatter.date(from: s)
                    }
                }
                if entry == latestName { latestTarget = targetCount }
                let pct = targetCount > 0 ? Int((Double(count) / Double(targetCount)) * 100.0) : 0
                var line = "\(entry): \(count)/\(targetCount) (\(pct)%)"
                if !provider.isEmpty { line += " \(provider)" }
                if !status.isEmpty { line += " \(status)" }
                taskLines.append((mtime, line))

                // ETA calculation
                let start = startedAt ?? mtime
                let elapsed = max(1, now.timeIntervalSince(start))
                let rate = Double(count) / elapsed
                let remaining = max(0, targetCount - count)
                let eta = rate > 0 ? Double(remaining) / rate : 0
                let etaText = eta > 0 ? formatAge(eta) : "--"
                var detailed = "\(entry): \(pct)% ETA \(etaText)"
                if !provider.isEmpty { detailed += " \(provider)" }
                if !status.isEmpty { detailed += " \(status)" }
                detailedLines.append((mtime, detailed))
                progressItems.append((mtime, SwarmProgressItem(name: entry, pct: pct, eta: etaText)))
            }

            // Count recently updated agent files
            for file in files where file.hasPrefix("agent_") && file.hasSuffix(".json") {
                let filePath = (dirPath as NSString).appendingPathComponent(file)
                if let fattrs = try? fm.attributesOfItem(atPath: filePath),
                   let fmtime = fattrs[.modificationDate] as? Date {
                    if now.timeIntervalSince(fmtime) <= activeWindow {
                        activeFiles += 1
                    }
                }
            }
        }

        taskLines.sort { $0.0 > $1.0 }
        detailedLines.sort { $0.0 > $1.0 }
        let summary = taskLines.prefix(10).map { "• \($0.1)" }.joined(separator: "\n")
        let detailed = detailedLines.prefix(10).map { "• \($0.1)" }.joined(separator: "\n")
        let progress = progressItems.sorted { $0.0 > $1.0 }.prefix(6).map { $0.1 }

        return SwarmStats(
            totalAgentFiles: total,
            latestSwarmName: latestName,
            latestSwarmAgentCount: latestCount,
            latestSwarmUpdatedAt: latestDate,
            latestTargetCount: latestTarget,
            activeAgentFiles: activeFiles,
            activeSwarmDirs: activeDirs,
            taskSummary: summary,
            detailedSummary: detailed,
            progressItems: progress
        )
    }

    private func readTaskStats() -> TaskStats {
        let base = "/Users/maurice/.openclaw/workspace/ai-empire/00_SYSTEM/tasks"
        let fm = FileManager.default
        guard let entries = try? fm.contentsOfDirectory(atPath: base) else {
            return TaskStats(queued: 0, running: 0, done: 0, summary: "")
        }
        var items: [(Date, String)] = []
        var queued = 0
        var running = 0
        var done = 0
        for entry in entries where entry.hasSuffix(".json") {
            let path = (base as NSString).appendingPathComponent(entry)
            guard let data = try? Data(contentsOf: URL(fileURLWithPath: path)),
                  let json = try? JSONSerialization.jsonObject(with: data),
                  let dict = json as? [String: Any] else { continue }
            let status = (dict["status"] as? String) ?? "queued"
            if status == "queued" { queued += 1 }
            else if status == "running" { running += 1 }
            else { done += 1 }
            let id = entry.replacingOccurrences(of: ".json", with: "")
            let prompt = (dict["prompt"] as? String ?? "--")
            let count = dict["count"] as? Int ?? 0
            let created = (dict["created_at"] as? String) ?? ""
            let line = "\(id) | \(status) | n=\(count) | \(prompt.prefix(60))"
            if let date = parseDate(created) {
                items.append((date, line))
            } else {
                items.append((Date.distantPast, line))
            }
        }
        items.sort { $0.0 > $1.0 }
        let summary = items.prefix(10).map { "• \($0.1)" }.joined(separator: "\n")
        return TaskStats(queued: queued, running: running, done: done, summary: summary)
    }

    private func parseDate(_ value: String) -> Date? {
        let formatter = DateFormatter()
        formatter.locale = Locale.current
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter.date(from: value)
    }

    private func formatAge(_ seconds: TimeInterval) -> String {
        let s = max(0, Int(seconds))
        let m = s / 60
        let h = m / 60
        if h > 0 {
            return String(format: "%dh %02dm", h, m % 60)
        }
        if m > 0 {
            return String(format: "%dm %02ds", m, s % 60)
        }
        return "\(s)s"
    }
}

private struct SwarmStats {
    let totalAgentFiles: Int
    let latestSwarmName: String?
    let latestSwarmAgentCount: Int
    let latestSwarmUpdatedAt: Date?
    let latestTargetCount: Int
    let activeAgentFiles: Int
    let activeSwarmDirs: Int
    let taskSummary: String
    let detailedSummary: String
    let progressItems: [SwarmProgressItem]
}

private struct SwarmProgressItem {
    let name: String
    let pct: Int
    let eta: String
}

private struct TaskStats {
    let queued: Int
    let running: Int
    let done: Int
    let summary: String
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var controller: DashboardController?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        controller = DashboardController()
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
