## Java Native Interface (JNI)

Purpose:
JNI is a programming framework that allows Java code running in the Java Virtual Machine (JVM) to call and be called by native applications and libraries written in other languages like C and C++.

## Java Native Access (JNA)

Purpose:
JNA provides Java programs easy access to native shared libraries (DLLs on Windows, shared objects on Unix) without writing anything but Java code.

| Feature     | JNI                                             | JNA                                                |
| ----------- | ----------------------------------------------- | -------------------------------------------------- |
| Ease of Use | Complex                                         | Simple                                             |
| Performance | High                                            | Moderate                                           |
| Native Code | Required                                        | Yes (C/C++) No (Java only)                         |
| Setup       | Involves multiple steps and tools (javah, etc.) | Minimal setup, direct mapping in Java              |
| Use Cases   | Performance-critical applications               | Quick integration, prototyping, less critical apps |
