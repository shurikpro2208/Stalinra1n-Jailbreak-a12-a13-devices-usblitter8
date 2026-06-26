import SwiftUI

@main
struct LoaderApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var showInfo = false
    @State private var installingPM = false
    @State private var pmStatus = ""

    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)

            ScrollView {
                VStack(spacing: 20) {
                    Spacer().frame(height: 20)

                    VStack(spacing: 8) {
                        AsyncImage(url: URL(string: "https://static.macupdate.com/products/46911/m/evasi0n-7-logo.webp")) { phase in
                            switch phase {
                            case .success(let image):
                                image
                                    .resizable()
                                    .scaledToFit()
                                    .frame(height: 80)
                            case .failure:
                                Text("stalinra1n")
                                    .font(.system(size: 34, weight: .bold))
                                    .foregroundColor(Color(red: 0.3, green: 0.6, blue: 1.0))
                            case .empty:
                                ProgressView()
                                    .frame(height: 80)
                            @unknown default:
                                EmptyView()
                            }
                        }

                        Text("stalinra1n")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(.white)

                        Text("A12/A13 BootROM Jailbreak")
                            .font(.system(size: 14))
                            .foregroundColor(.gray)
                    }
                    .padding(.vertical, 10)

                    VStack(spacing: 12) {
                        Text("Package Manager")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(.gray)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 4)

                        HStack(spacing: 12) {
                            PMButton(
                                name: "Sileo",
                                icon: "shippingbox.fill",
                                color: Color(red: 0.2, green: 0.5, blue: 1.0),
                                action: { installPM("Sileo") }
                            )
                            PMButton(
                                name: "Zebra",
                                icon: "pawprint.fill",
                                color: Color(red: 1.0, green: 0.7, blue: 0.2),
                                action: { installPM("Zebra") }
                            )
                            PMButton(
                                name: "Cydia",
                                icon: "square.grid.3x3",
                                color: Color(red: 0.5, green: 0.3, blue: 0.8),
                                action: { installPM("Cydia") }
                            )
                        }
                    }
                    .padding(.horizontal, 20)

                    if !pmStatus.isEmpty {
                        Text(pmStatus)
                            .font(.system(size: 12))
                            .foregroundColor(installingPM ? .orange : .green)
                            .padding(.horizontal, 20)
                    }

                    VStack(spacing: 12) {
                        Text("Tools")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(.gray)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 24)

                        VStack(spacing: 0) {
                            ActionRow(
                                icon: "arrow.triangle.2.circlepath",
                                label: "Reinstall Bootstrap",
                                color: .orange,
                                action: reinstallBootstrap
                            )
                            Divider().background(Color.gray.opacity(0.3))
                            ActionRow(
                                icon: "info.circle.fill",
                                label: "System Info",
                                color: .blue,
                                action: { showInfo = true }
                            )
                        }
                        .background(Color(UIColor(white: 0.12, alpha: 1)))
                        .cornerRadius(10)
                        .padding(.horizontal, 20)
                    }

                    VStack(spacing: 4) {
                        Text("Tethered Jailbreak")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(.red.opacity(0.8))
                        Text("Re-exploit via RP2350 after every reboot")
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                    }
                    .padding(.top, 10)

                    Spacer().frame(height: 30)
                }
            }
        }
        .sheet(isPresented: $showInfo) {
            SystemInfoView()
        }
    }

    func installPM(_ name: String) {
        installingPM = true
        pmStatus = "Installing \(name)..."
        DispatchQueue.global().async {
            let task = Process()
            task.launchPath = "/usr/bin/dpkg"
            task.arguments = ["-i", "/bootstrap/\(name.lowercased()).deb"]
            task.launch()
            task.waitUntilExit()
            DispatchQueue.main.async {
                installingPM = false
                pmStatus = task.terminationStatus == 0
                    ? "\(name) installed successfully"
                    : "\(name) installation failed"
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                    pmStatus = ""
                }
            }
        }
    }

    func reinstallBootstrap() {
        DispatchQueue.global().async {
            let task = Process()
            task.launchPath = "/bin/bash"
            task.arguments = ["/bootstrap/reinstall.sh"]
            task.launch()
            task.waitUntilExit()
        }
    }
}

struct PMButton: View {
    let name: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(.white)
                Text(name)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(color.opacity(0.2))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(color.opacity(0.4), lineWidth: 1)
            )
            .cornerRadius(12)
        }
    }
}

struct ActionRow: View {
    let icon: String
    let label: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.system(size: 16))
                    .frame(width: 24)
                Text(label)
                    .foregroundColor(.white)
                    .font(.system(size: 15))
                Spacer()
                Image(systemName: "chevron.right")
                    .foregroundColor(.gray)
                    .font(.system(size: 12))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
        }
    }
}

struct SystemInfoView: View {
    @State private var info: [(String, String)] = []

    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)

            VStack(spacing: 0) {
                HStack {
                    Text("System Info")
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.white)
                    Spacer()
                    Button("Done") {
                        dismiss()
                    }
                    .foregroundColor(.blue)
                }
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .padding(.bottom, 10)

                Divider().background(Color.gray.opacity(0.3))

                List {
                    ForEach(info.indices, id: \.self) { i in
                        HStack {
                            Text(info[i].0)
                                .foregroundColor(.gray)
                                .font(.system(size: 14))
                            Spacer()
                            Text(info[i].1)
                                .foregroundColor(.white)
                                .font(.system(size: 14, weight: .medium))
                                .multilineTextAlignment(.trailing)
                        }
                        .listRowBackground(Color(UIColor(white: 0.1, alpha: 1)))
                        .listRowSeparator(.hidden)
                    }
                }
                .listStyle(.plain)
                .scrollContentBackground(.hidden)
            }
        }
        .onAppear(perform: collectInfo)
    }

    func dismiss() {
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let root = windowScene.windows.first?.rootViewController {
            root.dismiss(animated: true)
        }
    }

    func collectInfo() {
        info = [
            ("Exploit", "stalinra1n (usbliter8)"),
            ("Type", "Tethered (A12/A13)"),
            ("Kernel", readCmd("/usr/bin/uname -r")),
            ("Model", readCmd("/usr/sbin/sysctl -n hw.model")),
            ("Machine", readCmd("/usr/sbin/sysctl -n hw.machine")),
            ("iOS", readCmd("/usr/bin/sw_vers -productVersion")),
            ("Build", readCmd("/usr/bin/sw_vers -buildVersion")),
            ("ECID", readCmd(
                "/usr/sbin/ioreg -p IODeviceTree -n 0 -r | /usr/bin/grep ECID | /usr/bin/awk '{print $4}'"
            )),
            ("BootROM", "Permanent (unpatchable)"),
            ("SEP", "Not compromised"),
        ]
        if let ver = try? String(contentsOfFile: "/bootstrap/version.txt") {
            info.append(("Bootstrap", ver.trimmingCharacters(in: .newlines)))
        }
    }

    func readCmd(_ cmd: String) -> String {
        let task = Process()
        task.launchPath = "/bin/bash"
        task.arguments = ["-c", cmd]
        let pipe = Pipe()
        task.standardOutput = pipe
        task.launch()
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8)?.trimmingCharacters(in: .newlines) ?? "?"
    }
}
