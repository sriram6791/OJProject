#!/bin/bash
echo "Testing C++ Docker execution..."

mkdir -p /tmp/test_cpp
cd /tmp/test_cpp

cat > test.cpp << 'EOF'
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
EOF

echo "Created test.cpp"
echo "Running Docker command:"
docker run --rm -v /tmp/test_cpp:/code gcc:latest sh -c "cd /code && g++ test.cpp -o test && chmod +x test && ./test"

echo "Exit code: $?"
echo "Cleaning up..."
rm -rf /tmp/test_cpp
echo "Done!"
