CMake provides **many ways** to locate dependencies (e.g. header files, libraries). Here's a breakdown of the main techniques you can use, categorized by typical use case:

### **🧭 1. Manual Specification**

You tell CMake exactly where to look.

**include_directories() / target_include_directories()** For header files.  
  
include_directories("/path/to/include")

target_include_directories(MyTarget PRIVATE /path/to/include)

- 

**link_directories()** For library search paths (not recommended in modern CMake).  
  
link_directories("/path/to/lib")

- 

**target_link_libraries()** For linking the actual library files.  
  
target_link_libraries(MyTarget PRIVATE mylib)

- 

### **🔍 2. Using find_package()**

CMake uses **Find Modules** or **config packages**.

**Find modules (FindXXX.cmake)**: CMake comes with built-in or custom Find\<Package\>.cmake modules.  
  
find_package(OpenSSL REQUIRED)

target_link_libraries(MyTarget PRIVATE OpenSSL::SSL)

- 

**Package config files (\<Package\>Config.cmake)**: Modern libraries often install these for easy integration.  
  
find_package(fmt CONFIG REQUIRED)

target_link_libraries(MyTarget PRIVATE fmt::fmt)

You can help CMake find them using:  
  
list(APPEND CMAKE_PREFIX_PATH "/path/to/package/install")

- 

### **🔧 3. Using pkg-config**

For Unix-like systems, you can leverage pkg-config.

find_package(PkgConfig REQUIRED)

pkg_check_modules(SDL2 REQUIRED sdl2)

include_directories(\${SDL2_INCLUDE_DIRS})

link_libraries(\${SDL2_LIBRARIES})

### **📦 4. Fetching Dependencies (External Projects)**

Let CMake download/build the dependency for you.

**FetchContent** (CMake ≥ 3.11):  
  
include(FetchContent)

FetchContent_Declare(

json

GIT_REPOSITORY https://github.com/nlohmann/json.git

GIT_TAG v3.11.2

)

FetchContent_MakeAvailable(json)

target_link_libraries(MyTarget PRIVATE nlohmann_json::nlohmann_json)

- 

- **ExternalProject_Add()**: More flexible but lower-level than FetchContent.

### **🧱 5. Using CMake targets from external build systems**

When a library provides a CMake-compatible interface:

add_subdirectory(path/to/library)

target_link_libraries(MyTarget PRIVATE LibraryTargetName)

### **🧠 Summary Table**

| **Method** | **Type** | **Use Case** |
|----|----|----|
| include_directories | Manual | Quick and dirty header paths |
| find_package | Built-in | Common system or user-installed libs |
| FetchContent | Modern CMake | Downloading/building dependencies automatically |
| pkg-config | External tool | Linux-style system integration |
| add_subdirectory | Internal | Library source is inside your project tree |

Let me know if you're using a specific library or working on Windows/macOS/Linux — I can give you a tailored example.
