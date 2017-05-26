#include <cstdlib>
#include <iostream>
#include <sstream>
#include <unistd.h>
#include <boost/filesystem.hpp>

using std::string;


string getCommandLine(const string& executableName, uid_t userID, int paramCount, char** params)
{
    std::ostringstream result;
    result << executableName << " " << userID;
    for (int i = 0; i < paramCount; ++i)
        result << " " << params[i];
    return result.str();
}

const string executableFilename = "limited-apt_privileged";

string getExecutablePath()
{
    string localPath = string("/usr/local/") + executableFilename;
    if (boost::filesystem::exists(localPath))
        return localPath;
    else
        return string("/usr/") + executableFilename;
}

//constexpr string& EXECUTABLE = "/usr/";

int main(int argc, char** argv)
{
    std::cout << "Real UID = " << getuid() << "\n";
    std::cout << getCommandLine("EXECUTABLE", getuid(), argc - 1, argv + 1) << "\n";

    std::cout << getExecutablePath();

    return 0;
}
