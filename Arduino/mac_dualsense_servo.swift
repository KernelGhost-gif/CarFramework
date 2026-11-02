import CoreBluetooth
import Foundation
import GameController

private enum ServoBLE {
    static let deviceName = "UNO-R4-Servo"
    static let service = CBUUID(string: "19B10000-E8F2-537E-4F6C-D104768A1214")
    static let angle = CBUUID(string: "19B10001-E8F2-537E-4F6C-D104768A1214")
}

final class ServoBridge: NSObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    private var central: CBCentralManager!
    private var peripheral: CBPeripheral?
    private var angleCharacteristic: CBCharacteristic?
    private var controller: GCController?
    private var pollTimer: Timer?
    private var lastAngle: Int?
    private var controllerObserver: NSObjectProtocol?
    private var disconnectObserver: NSObjectProtocol?

    override init() {
        super.init()
        central = CBCentralManager(delegate: self, queue: .main)
        controllerObserver = NotificationCenter.default.addObserver(
            forName: .GCControllerDidConnect, object: nil, queue: .main
        ) { [weak self] _ in
            self?.selectController()
        }
        disconnectObserver = NotificationCenter.default.addObserver(
            forName: .GCControllerDidDisconnect, object: nil, queue: .main
        ) { [weak self] notification in
            guard let self,
                  let disconnected = notification.object as? GCController,
                  disconnected === self.controller else { return }
            self.stopReadingController()
            print("DualSense disconnected; waiting for a controller")
        }

        selectController()
        GCController.startWirelessControllerDiscovery(completionHandler: nil)
    }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        switch central.state {
        case .poweredOn:
            print("Bluetooth ready; looking for \(ServoBLE.deviceName)...")
            scanForBoard()
        case .poweredOff:
            print("Bluetooth is off. Turn it on in System Settings → Bluetooth.")
        case .unauthorized:
            print("Bluetooth access is not authorized for this app.")
        case .unsupported:
            print("This Mac does not report BLE support to CoreBluetooth.")
        default:
            break
        }
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        let advertisedName = advertisementData[CBAdvertisementDataLocalNameKey] as? String
        guard peripheral.name == ServoBLE.deviceName || advertisedName == ServoBLE.deviceName else {
            return
        }

        central.stopScan()
        self.peripheral = peripheral
        peripheral.delegate = self
        print("Found \(ServoBLE.deviceName); connecting...")
        central.connect(peripheral)
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        print("Connected to \(ServoBLE.deviceName); discovering servo control...")
        peripheral.discoverServices([ServoBLE.service])
    }

    func centralManager(
        _ central: CBCentralManager,
        didDisconnectPeripheral peripheral: CBPeripheral,
        error: Error?
    ) {
        angleCharacteristic = nil
        self.peripheral = nil
        print("UNO disconnected; scanning again")
        scanForBoard()
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        if let error {
            print("BLE service discovery failed: \(error.localizedDescription)")
            return
        }
        guard let service = peripheral.services?.first(where: { $0.uuid == ServoBLE.service }) else {
            print("UNO servo service was not found")
            return
        }
        peripheral.discoverCharacteristics([ServoBLE.angle], for: service)
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverCharacteristicsFor service: CBService,
        error: Error?
    ) {
        if let error {
            print("BLE characteristic discovery failed: \(error.localizedDescription)")
            return
        }
        guard let characteristic = service.characteristics?.first(where: { $0.uuid == ServoBLE.angle }) else {
            print("UNO servo angle characteristic was not found")
            return
        }
        angleCharacteristic = characteristic
        print("Servo link ready. Move the DualSense left stick horizontally; press Ctrl+C to stop.")
        send(angle: 90)
    }

    private func scanForBoard() {
        guard central.state == .poweredOn, peripheral == nil else { return }
        central.scanForPeripherals(withServices: [ServoBLE.service])
    }

    private func selectController() {
        guard controller == nil,
              let found = GCController.controllers().first(where: { $0.extendedGamepad != nil }) else {
            return
        }
        controller = found
        let label = found.vendorName ?? "Game Controller"
        print("Using \(label); left stick horizontal controls the servo")
        pollTimer?.invalidate()
        pollTimer = Timer.scheduledTimer(withTimeInterval: 0.04, repeats: true) { [weak self] _ in
            self?.readController()
        }
    }

    private func stopReadingController() {
        pollTimer?.invalidate()
        pollTimer = nil
        controller = nil
        lastAngle = nil
    }

    private func readController() {
        guard let gamepad = controller?.extendedGamepad else { return }
        var x = max(-1.0, min(1.0, Double(gamepad.leftThumbstick.xAxis.value)))
        if abs(x) < 0.08 { x = 0 }
        let angle = Int(((x + 1.0) * 90.0).rounded())
        if let lastAngle, abs(angle - lastAngle) < 2 { return }
        send(angle: angle)
    }

    private func send(angle: Int) {
        guard let peripheral, let characteristic = angleCharacteristic else { return }
        let boundedAngle = min(180, max(0, angle))
        guard let data = String(boundedAngle).data(using: .ascii) else { return }
        peripheral.writeValue(data, for: characteristic, type: .withResponse)
        lastAngle = boundedAngle
        print("\rServo: \(boundedAngle)°   ", terminator: "")
        fflush(stdout)
    }
}

let bridge = ServoBridge()
withExtendedLifetime(bridge) {
    RunLoop.main.run()
}
