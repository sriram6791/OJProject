echo "Testing C++ Docker execution..."
$testDir = "C:\temp\test_cpp"
if (Test-Path $testDir) { Remove-Item -Recurse -Force $testDir }
New-Item -ItemType Directory -Path $testDir -Force | Out-Null

# Create test.cpp
@'
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
'@ | Out-File -FilePath "$testDir\test.cpp" -Encoding utf8

echo "Created test.cpp"
echo "Running Docker command:"
docker run --rm -v "${testDir}:/code" gcc:latest sh -c "cd /code && g++ test.cpp -o test && chmod +x test && ./test"

echo "Exit code: $LASTEXITCODE"
echo "Cleaning up..."
Remove-Item -Recurse -Force $testDir
echo "Done!"
