#!/bin/bash
echo "=== PharmaKG Frontend Setup Verification ==="
echo ""

echo "1. Checking Node.js version..."
node --version
echo ""

echo "2. Checking npm version..."
npm --version
echo ""

echo "3. Checking if node_modules exists..."
if [ -d "node_modules" ]; then
    echo "✓ node_modules directory exists"
    echo "  Installed packages: $(ls node_modules | wc -l)"
else
    echo "✗ node_modules not found. Run: npm install"
fi
echo ""

echo "4. Checking configuration files..."
for file in package.json vite.config.ts tsconfig.json tailwind.config.js .eslintrc.json .prettierrc; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done
echo ""

echo "5. Checking source directory structure..."
for dir in src/domains src/layouts src/pages src/shared; do
    if [ -d "$dir" ]; then
        echo "✓ $dir exists"
    else
        echo "✗ $dir missing"
    fi
done
echo ""

echo "6. Counting TypeScript files..."
ts_files=$(find src -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l)
echo "✓ Found $ts_files TypeScript files"
echo ""

echo "7. Checking domain directories..."
for domain in research clinical supply regulatory; do
    if [ -d "src/domains/$domain" ]; then
        files=$(ls src/domains/$domain/*.{ts,tsx} 2>/dev/null | wc -l)
        echo "✓ $domain domain: $files files"
    else
        echo "✗ $domain domain missing"
    fi
done
echo ""

echo "8. Testing TypeScript compilation..."
echo "Running: npx tsc --noEmit"
npx tsc --noEmit 2>&1 | head -20
echo ""

echo "=== Verification Complete ==="
