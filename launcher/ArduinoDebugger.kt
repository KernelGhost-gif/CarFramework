import java.io.File

fun main() {
    val root = File(System.getProperty("user.dir"))
    val helper = File(root, "launcher/arduino_ble_debugger.py")
    val python = File(root, ".venv/bin/python")
    if (!helper.isFile || !python.canExecute()) {
        System.err.println("Run from the repository root after running ./setup.sh.")
        return
    }
    val process = try {
        ProcessBuilder(python.path, "-u", helper.path)
            .directory(root).redirectOutput(ProcessBuilder.Redirect.INHERIT)
            .redirectError(ProcessBuilder.Redirect.INHERIT).start()
    } catch (e: Exception) {
        System.err.println("Could not start BLE helper: ${e.message}")
        return
    }
    Runtime.getRuntime().addShutdownHook(Thread { process.destroy() })
    println("Commands: 0-180, left (0), center (90), right (180), help, quit")
    println("Commands entered while connecting will be sent once the board is ready.")
    val output = process.outputStream.bufferedWriter()
    try {
        while (process.isAlive) {
            print("> ")
            System.out.flush()
            val input = readLine()?.trim()?.lowercase() ?: break
            if (input == "quit" || input == "exit") break
            if (input == "help") {
                println("Enter an angle from 0 to 180, left, center, right, or quit.")
                continue
            }
            val angle = when (input) {
                "left" -> 0
                "center" -> 90
                "right" -> 180
                else -> input.toIntOrNull()
            }
            if (angle == null || angle !in 0..180) {
                println("Invalid command. Enter an angle from 0 to 180 or type help.")
                continue
            }
            output.write("$angle\n")
            output.flush()
        }
    } catch (e: java.io.IOException) {
        System.err.println("BLE helper stopped: ${e.message}")
    } finally {
        output.close()
        process.waitFor()
    }
}
