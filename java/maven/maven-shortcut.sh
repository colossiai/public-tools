# Create maven project

# mvn archetype:generate -DgroupId=com.cruiser -DartifactId=mvn_cmd_demo -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false

mvn_init() {
    local group_id="$1"
    local artifact_id="$2"

    # Validate input parameters
    if [[ -z "$group_id" || -z "$artifact_id" ]]; then
        echo "Usage: mvn_init <groupId> <artifactId>"
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


mvn_multi_init() {

PROJECT_NAME=${1:-demo-mvn-project}
GROUP_ID=${2:-com.example}
VERSION="1.0-SNAPSHOT"

PACKAGE_PATH=$(echo $GROUP_ID | tr '.' '/')

echo "Creating Maven multi-module project: $PROJECT_NAME"

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME" || return

################################
# .gitignore
################################

cat > .gitignore <<EOF
target/
*.log
.idea/
.vscode/
*.iml
EOF

################################
# Parent pom.xml
################################

cat > pom.xml <<EOF
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

<modelVersion>4.0.0</modelVersion>

<groupId>$GROUP_ID</groupId>
<artifactId>$PROJECT_NAME</artifactId>
<version>$VERSION</version>

<packaging>pom</packaging>

<modules>
    <module>common</module>
    <module>service</module>
</modules>

<properties>
    <maven.compiler.source>21</maven.compiler.source>
    <maven.compiler.target>21</maven.compiler.target>
</properties>

</project>
EOF

################################
# Module creator
################################

create_module() {

MODULE=$1

mkdir -p "$MODULE/src/main/java/$PACKAGE_PATH/$MODULE"
mkdir -p "$MODULE/src/test/java/$PACKAGE_PATH/$MODULE"

cat > "$MODULE/pom.xml" <<EOF
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

<modelVersion>4.0.0</modelVersion>

<parent>
    <groupId>$GROUP_ID</groupId>
    <artifactId>$PROJECT_NAME</artifactId>
    <version>$VERSION</version>
</parent>

<artifactId>$MODULE</artifactId>

</project>
EOF

}

################################
# Create modules
################################

create_module common
create_module service

################################
# service depends on common
################################

sed -i.bak '/<\/project>/d' service/pom.xml

cat >> service/pom.xml <<EOF

<dependencies>
    <dependency>
        <groupId>$GROUP_ID</groupId>
        <artifactId>common</artifactId>
        <version>\${project.version}</version>
    </dependency>
</dependencies>


<build>
    <plugins>
    <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-shade-plugin</artifactId>
        <version>3.5.1</version>

        <executions>
            <execution>
                <phase>package</phase>
                <goals>
                <goal>shade</goal>
                </goals>

                <configuration>

                    <createDependencyReducedPom>false</createDependencyReducedPom>

                    <transformers>
                        <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                        <mainClass>$MAIN_CLASS</mainClass>
                        </transformer>
                    </transformers>

                </configuration>

            </execution>
        </executions>
    </plugin>
    </plugins>
</build>


</project>
EOF

rm service/pom.xml.bak

################################
# Sample Common Class
################################

cat > common/src/main/java/$PACKAGE_PATH/common/StringUtils.java <<EOF
package $GROUP_ID.common;

public class StringUtils {

    public static String upper(String s) {
        return s == null ? null : s.toUpperCase();
    }

}
EOF

################################
# Service with demo main()
################################

cat > service/src/main/java/$PACKAGE_PATH/service/UserService.java <<EOF
package $GROUP_ID.service;

import $GROUP_ID.common.StringUtils;

public class UserService {

    public String normalizeName(String name) {
        return StringUtils.upper(name);
    }

    public static void main(String[] args) {

        UserService service = new UserService();

        String input = "uranus";
        String output = service.normalizeName(input);

        System.out.println("Input : " + input);
        System.out.println("Output: " + output);
    }
}
EOF

################################
# build_install.sh
################################

cat > build_install.sh <<EOF
#!/usr/bin/env bash
set -e

echo "Building & install project: mvn clean install"

mvn clean install

echo "Build finished."
EOF

################################
# run.sh
################################

MAIN_CLASS="$GROUP_ID.service.UserService"

cat > run.sh <<EOF
#!/usr/bin/env bash
set -e

echo "Running $MAIN_CLASS"

# java -cp \
# service/target/service-$VERSION.jar:\
# common/target/common-$VERSION.jar \
# $MAIN_CLASS

java -jar service/target/service-$VERSION.jar
EOF

chmod +x build_install.sh
chmod +x run.sh

################################
# Git init
################################

git init >/dev/null 2>&1 || true

echo ""
echo "Project created successfully."
echo ""
echo "Next steps:"
echo "cd $PROJECT_NAME"
echo "./build_install.sh"
echo "./run.sh"

}


mvn_new_module() {
    # Arguments
    MODULE_NAME=$1
    MAIN_CLASS_NAME=${2:-Main}

    if [ -z "$MODULE_NAME" ]; then
        echo "Usage: mvn_new_module <module-name> [MainClassName]"
        return 1
    fi

    PARENT_POM="pom.xml"
    if [ ! -f "$PARENT_POM" ]; then
        echo "Error: Cannot find parent pom.xml in current directory"
        return 1
    fi

    # Auto-detect groupId from parent pom.xml
    GROUP_ID=$(grep -m1 '<groupId>' "$PARENT_POM" | sed 's/.*<groupId>\(.*\)<\/groupId>.*/\1/')
    if [ -z "$GROUP_ID" ]; then
        echo "Error: Cannot detect groupId from parent pom.xml"
        return 1
    fi

    # Detect artifactId and version
    ARTIFACT_ID=$(grep -m1 '<artifactId>' "$PARENT_POM" | sed 's/.*<artifactId>\(.*\)<\/artifactId>.*/\1/')
    VERSION=$(grep -m1 '<version>' "$PARENT_POM" | sed 's/.*<version>\(.*\)<\/version>.*/\1/')

    echo "Detected groupId: $GROUP_ID"
    echo "Creating new module: $MODULE_NAME with main class $MAIN_CLASS_NAME"

    PACKAGE_PATH=$(echo $GROUP_ID | tr '.' '/')
    FULL_CLASS_NAME="$GROUP_ID.$MODULE_NAME.$MAIN_CLASS_NAME"

    # create folder structure
    mkdir -p "$MODULE_NAME/src/main/java/$PACKAGE_PATH/$MODULE_NAME"
    mkdir -p "$MODULE_NAME/src/test/java/$PACKAGE_PATH/$MODULE_NAME"

    # create pom.xml with shade plugin
    cat > "$MODULE_NAME/pom.xml" <<EOF
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>$GROUP_ID</groupId>
    <artifactId>$ARTIFACT_ID</artifactId>
    <version>$VERSION</version>
  </parent>

  <artifactId>$MODULE_NAME</artifactId>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-shade-plugin</artifactId>
        <version>3.5.1</version>
        <executions>
          <execution>
            <phase>package</phase>
            <goals><goal>shade</goal></goals>
            <configuration>
              <createDependencyReducedPom>false</createDependencyReducedPom>
              <transformers>
                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                  <mainClass>$FULL_CLASS_NAME</mainClass>
                </transformer>
              </transformers>
            </configuration>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>

</project>
EOF

    # create main java class
    cat > "$MODULE_NAME/src/main/java/$PACKAGE_PATH/$MODULE_NAME/$MAIN_CLASS_NAME.java" <<EOF
package $GROUP_ID.$MODULE_NAME;

public class $MAIN_CLASS_NAME {
    public static void main(String[] args) {
        System.out.println("Hello from $FULL_CLASS_NAME!");
    }
}
EOF

    # add module to parent pom if not exists
    if ! grep -q "<module>$MODULE_NAME</module>" "$PARENT_POM"; then
        sed -i.bak "/<\/modules>/i\\
    <module>$MODULE_NAME</module>
" "$PARENT_POM"
        rm "$PARENT_POM.bak"
    fi

    echo "Module $MODULE_NAME created successfully."
    echo "Build: mvn clean package -pl $MODULE_NAME -am"
    echo "Run: java -jar $MODULE_NAME/target/$MODULE_NAME-1.0-SNAPSHOT.jar"
}