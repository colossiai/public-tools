/*

java --add-exports java.base/jdk.internal.vm.annotation=ALL-UNNAMED -XX:-RestrictContended FalseSharingBenchmark.java

elapsedUnPadded:3852
elapsedPadded:472

*/

import jdk.internal.vm.annotation.Contended;


public class FalseSharingBenchmark {

    public static class PaddedCounter {
        @Contended
        public volatile long countA = 0;
        
        @Contended
        public volatile long countB = 0;
    }

    public static class Counter {
        // These two volatiles will likely share one 64-byte cache line
        public volatile long countA = 0;
        public volatile long countB = 0;
    }

    public static long runUnpadded() throws InterruptedException {
        Counter counter = new Counter();
        
        // Thread 1 increments countA, Thread 2 increments countB
        // MESI will constantly invalidate the cache line for BOTH threads!
        Thread t1 = new Thread(() -> {
            for (int i = 0; i < 100_000_000; i++) counter.countA++;
        });
        Thread t2 = new Thread(() -> {
            for (int i = 0; i < 100_000_000; i++) counter.countB++;
        });

        long start = System.nanoTime();
        t1.start(); t2.start();
        t1.join(); t2.join();
        return System.nanoTime() - start;
    }

    public static long runPadded() throws InterruptedException {
        PaddedCounter counter = new PaddedCounter();
        
        Thread t1 = new Thread(() -> {
            for (int i = 0; i < 100_000_000; i++) counter.countA++;
        });
        Thread t2 = new Thread(() -> {
            for (int i = 0; i < 100_000_000; i++) counter.countB++;
        });

        long start = System.nanoTime();
        t1.start(); t2.start();
        t1.join(); t2.join();
        return System.nanoTime() - start;
    }

    public static void main(String[] args) throws InterruptedException {
        var elapsedUnPadded = runUnpadded()/1_000_000;
        Thread.sleep(2000);
        var elapsedPadded = runPadded()/1_000_000;
        System.out.printf("elapsedUnPadded:%d\n", elapsedUnPadded);
        System.out.printf("elapsedPadded:%d\n",elapsedPadded);
    }
}
