# Create maven project

# mvn archetype:generate -DgroupId=com.cruiser -DartifactId=mvn_cmd_demo -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false

create_maven_project() {
    local group_id="$1"
    local artifact_id="$2"

    # Validate input parameters
    if [[ -z "$group_id" || -z "$artifact_id" ]]; then
        echo "Usage: create_maven_project <groupId> <artifactId>"
        return 1
    fi

    # Create the Maven project
    mvn archetype:generate \
        -DgroupId="$group_id" \
        -DartifactId="$artifact_id" \
        -DarchetypeArtifactId=maven-archetype-quickstart \
        -DinteractiveMode=false

    echo "Maven project created with groupId: $group_id and artifactId: $artifact_id"
    echo "Set mainClass in pom.xml: <properties> <exec.mainClass>com.example.App</exec.mainClass> </properties>"
    echo "run mainClass: mvnd compile exec:java"
}


create_jmh_project() {
    local group_id="$1"
    local artifact_id="$2"

    # Validate input parameters
    if [[ -z "$group_id" || -z "$artifact_id" ]]; then
        echo "Usage: create_jmh_project <groupId> <artifactId>"
        return 1
    fi

    # Create the Maven JMH project
    # -DarchetypeVersion=1.37: Latest stable JMH version as of 2025
    mvn archetype:generate \
      -DinteractiveMode=false \
      -DarchetypeGroupId=org.openjdk.jmh \
      -DarchetypeArtifactId=jmh-java-benchmark-archetype \
      -DarchetypeVersion=1.37 \
      -DgroupId="$group_id" \
      -DartifactId="$artifact_id"

    echo "Maven JMH project created with groupId: $group_id and artifactId: $artifact_id"
}

mvn_exec() {
    if [ $# -eq 0 ]; then
        echo "Error: Main class must be provided as an argument" >&2
        echo "Usage: mvn_exec <main-class>" >&2
        return 1
    fi

    local mainClass="$1"
    local mvnCmd=$(command -v mvnd || command -v mvn)

    if [ -z "$mvnCmd" ]; then
        echo "Error: Neither 'mvnd' nor 'mvn' found in PATH" >&2
        return 1
    fi

    "$mvnCmd" exec:java -Dexec.mainClass="$mainClass"
}