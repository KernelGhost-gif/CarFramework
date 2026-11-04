# Client launcher

On macOS, from the repository root, run:

```sh
java launcher/ClientLauncher.java
```

This requires Java 11 or newer, Bun, Rust/Cargo, the Swift compiler and macOS developer tools. Run `./setup.sh` first (or `bun install` in `Reciever` if Bun was unavailable during setup), and generate and exchange the keys as described in the root README. Pair the DualSense and prepare the UNO as described in the [controller guide](../controller/README.md).

The launcher starts CarView via `bun run start`, which builds the Rust receiver and opens its Electron interface, then starts the Swift bridge. Startup happens concurrently; the bridge does not wait for the UI build to finish. Allow Bluetooth access if prompted. Open CarView's Connection tab and click **Start receiver** yourself. Output from both processes appears in the terminal. Press Ctrl+C to stop both; if either process exits, the launcher stops the other. The servo holds its last position when the bridge stops.

## Arduino command debugger

To control the UNO directly over BLE without a controller, install the Kotlin
command-line compiler (`kotlinc`) and Java, run `./setup.sh`, then run:

```sh
./launcher/run_arduino_debugger.sh
```

No Gradle project is needed. The Kotlin interface uses the existing Python
virtual environment and its `bleak` package for BLE transport. Power the UNO
with the servo sketch uploaded and grant Bluetooth access if prompted. Stop the
Swift or Python controller bridge first so it does not compete for the board.
Type an angle from `0` to `180`, or `left`, `center`, `right`, `help`, or
`quit`. A command is confirmed after the BLE write succeeds. The servo holds
its last position on exit; use a mechanically safe angle for your linkage.
