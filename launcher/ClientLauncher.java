import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.CountDownLatch;

/** Starts the CarView desktop app and the native macOS controller bridge. */
public class ClientLauncher {
    private static void stop(Process process) {
        if (process == null || !process.isAlive()) return;
        try {
            process.descendants().forEach(ProcessHandle::destroy);
        } catch (RuntimeException e) {
            System.err.println("Could not enumerate child processes: " + e.getMessage());
        } finally {
            process.destroy();
        }
    }

    public static void main(String[] args) throws Exception {
        if (!System.getProperty("os.name").toLowerCase().contains("mac")) {
            System.err.println("The Swift controller bridge requires macOS.");
            System.exit(1);
        }
        Path root = Paths.get("").toAbsolutePath().normalize();
        Path receiver = root.resolve("Reciever");
        Path bridge = root.resolve("controller/run_swift_bridge.sh");
        if (!Files.isRegularFile(receiver.resolve("package.json")) || !Files.isRegularFile(bridge)) {
            System.err.println("Run the launcher from the CarFramework repository root.");
            System.exit(1);
        }

        Process ui = null;
        Process controller = null;
        try {
            System.out.println("Starting CarView (the Rust receiver is built by Bun)...");
            ui = new ProcessBuilder("bun", "run", "start")
                    .directory(receiver.toFile()).inheritIO().start();
            System.out.println("Starting the Swift controller bridge...");
            controller = new ProcessBuilder("/bin/sh", bridge.toString())
                    .directory(root.toFile()).inheritIO().start();

            Process finalUi = ui;
            Process finalController = controller;
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                stop(finalController);
                stop(finalUi);
            }));
            CountDownLatch exited = new CountDownLatch(1);
            ui.onExit().thenRun(exited::countDown);
            controller.onExit().thenRun(exited::countDown);
            exited.await();
            Process finished = ui.isAlive() ? controller : ui;
            int code = finished.exitValue();
            System.err.println((finished == ui ? "CarView" : "Controller bridge")
                    + " exited with code " + code + "; stopping the other process.");
            stop(controller);
            stop(ui);
            System.exit(code);
        } catch (IOException e) {
            stop(controller);
            stop(ui);
            System.err.println("Could not start client: " + e.getMessage());
            System.exit(1);
        }
    }
}
