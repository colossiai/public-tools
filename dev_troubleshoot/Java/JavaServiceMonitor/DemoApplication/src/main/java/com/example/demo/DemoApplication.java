package com.example.demo;

import io.micrometer.core.annotation.Timed;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}

@RestController
class DemoController {
    private final AtomicBoolean cpuLoadRunning = new AtomicBoolean(false);
    private final AtomicInteger activeThreads = new AtomicInteger(0);
    private Thread cpuLoadThread;
    
    @Timed(value = "hello.requests", description = "Time spent serving hello")
    @GetMapping("/hello")
    public String hello() {
        return "Hello, world!";
    }


    @Timed(value = "cpuload.start.requests", description = "Requests to start CPU load")
    @GetMapping("/cpu-load/start")
    public String startCpuLoad() {
        if (cpuLoadRunning.compareAndSet(false, true)) {
            int threadCount = Math.min(5, Runtime.getRuntime().availableProcessors());

            activeThreads.set(threadCount);
            
            cpuLoadThread = new Thread(() -> {
                Thread[] workers = new Thread[threadCount];
                
                // Start worker threads
                for (int i = 0; i < threadCount; i++) {
                    workers[i] = new Thread(() -> {
                        while (cpuLoadRunning.get()) {
                            performCalculations();
                        }
                        activeThreads.decrementAndGet();
                    });
                    workers[i].setDaemon(true);
                    workers[i].setName("cpu-load-worker-" + i);
                    workers[i].start();
                }
                
                // Monitor and wait for completion
                while (activeThreads.get() > 0) {
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            });
            
            cpuLoadThread.setDaemon(true);
            cpuLoadThread.setName("cpu-load-monitor");
            cpuLoadThread.start();
            
            return String.format("CPU load started with %d threads. Process should show high CPU usage.", threadCount);
        }
        return "CPU load is already running!";
    }

    @Timed(value = "cpuload.stop.requests", description = "Requests to stop CPU load")
    @GetMapping("/cpu-load/stop")
    public String stopCpuLoad() {
        if (cpuLoadRunning.compareAndSet(true, false)) {
            return "CPU load stopped. It may take a moment for threads to complete.";
        }
        return "CPU load is not running.";
    }

    @Timed(value = "cpuload.status.requests", description = "Requests for CPU load status")
    @GetMapping("/cpu-load/status")
    public String getCpuLoadStatus() {
        return String.format("CPU load running: %s, Active worker threads: %d", 
                           cpuLoadRunning.get(), activeThreads.get());
    }

    private void performCalculations() {
        // CPU-intensive calculations
        double result = 0;
        for (int i = 1; i < 100000; i++) {
            result += Math.sqrt(i) * Math.log(i);
            result = Math.sin(result) * Math.cos(result);
        }
    }

}
