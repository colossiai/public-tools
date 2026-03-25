init-ts () {
  local name=$1

  if [ -z "$name" ]; then
    echo "Usage: init-ts <project-name>"
    return 1
  fi

  echo "Creating TypeScript project: $name"

  mkdir -p "$name"
  cd "$name" || return

  # initialize package.json
  pnpm init

  # install dev dependencies
  # -D: means --save-dev, these dependencies are only needed for development, not production runtime. (compiler)
  # typescript: TypeScript compiler `tsc`
  # tsx: TypeScript runtime to run .ts files directly compiling. a faster, simpler replacement for ts-node.
  # @types/node: TypeScript needs type definitions of node 
  pnpm add -D typescript tsx @types/node

  # create src folder
  mkdir src

  # sample program
  cat > src/index.ts <<'EOF'
function greet(name: string): string {
  return `Hello ${name}`;
}

console.log(greet("TypeScript"));
EOF

  # create production-grade tsconfig.json
  cat > tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "rootDir": "./src",
    "outDir": "./dist",
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "sourceMap": true,
    "declaration": true,
    "removeComments": false,
    "skipLibCheck": true,
    "types": ["node"],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
EOF

  # update package.json scripts
  node - <<'EOF'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json"));

pkg.scripts = {
  dev: "tsx src/index.ts",
  build: "tsc",
  start: "node dist/index.js"
};

fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2));
EOF

  # create .gitignore
  cat > .gitignore <<'EOF'
# Node modules
node_modules/

# TypeScript build output
dist/

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
pnpm-debug.log*

# OS files
.DS_Store

# Editor directories
.vscode/
.idea/
EOF

  echo ""
  echo "✅ TypeScript project ready with production-grade tsconfig.json"
  echo ""
  echo "Next steps:"
  echo "cd $name"
  echo "pnpm run dev"
}