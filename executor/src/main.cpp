#include <cstdlib>
#include <iostream>
#include <sstream>

#include <boost/format.hpp>

#include <unistd.h>
//#include <cstdlib>

using std::string;


string getCommandLine(const string& executableName, uid_t userID, int paramCount, char** params)
{
    std::ostringstream result;
    result << executableName << " " << userID;
    for (int i = 0; i < paramCount; ++i)
        result << " " << params[i];
    return result.str();
}

const string executableFilename = "/usr/local/sbin/limited-apt_privileged";

//string getExecutablePath()
//{
//    string localPath = string("/usr/local/") + executableFilename;
//    if (boost::filesystem::exists(localPath))
//        return localPath;
//    else
//        return string("/usr/") + executableFilename;
//}
//
//constexpr string& EXECUTABLE = "/usr/";

int main(int argc, char** argv)
{
//    std::cout << "Real UID = " << getuid() << "\n";
//    std::cout << getCommandLine(executableFilename, getuid(), argc - 1, argv + 1) << "\n";

    std::cout << boost::format("UID = %1%, EUID = %2%\n") % getuid() % geteuid();

//    std::cout << "SUID == " <<  << "EUID == " << geteuid() << "\n";

    string cmdLine = getCommandLine(executableFilename, getuid(), argc - 1, argv + 1);

    std::cout << cmdLine << "\n";

    system(cmdLine.c_str());

    return 0;
}
