#include <cstdlib>
#include <iostream>
#include <sstream>
#include <unistd.h>

using std::string;


string getCommandLine(const string& executableName, uid_t userID, int paramCount, char** params)
{
    std::ostringstream result;
    result << executableName << " " << userID;
    for (int i = 0; i < paramCount; ++i)
        result << " " << params[i];
    return result.str();
}

constexpr string& EXECUTABLE = "/usr/";

int main(int argc, char** argv)
{
    std::cout << "Real UID = " << getuid() << "\n";
    std::cout << getCommandLine(, getuid(), argc - 1, argv + 1);
    return 0;
}
