#include <iostream>
//#include <sstream>
#include <boost/format.hpp>
#include <cstring>
#include <string>
#include <unistd.h>


#define SUID_DEBUG 1


using std::string;


//string getCommandLine(const string& executableName, uid_t userID, int paramCount, char** params)
//{
//    std::ostringstream result;
//    result << executableName << " " << userID;
//    for (int i = 0; i < paramCount; ++i)
//        result << " " << params[i];
//    return result.str();
//}

char* strToCString(const char* source)
{
    auto dest = new char[std::strlen(source) + 1];
    std::strcpy(dest, source);
    return dest;
}

char* strToCString(const string& source)
{
    return strToCString(source.c_str());
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

int main(int argc, char* argv[])
{
    #ifdef SUID_DEBUG
    std::cout << boost::format("Executor:\nUID = %1%, EUID = %2%\n\n") % getuid() % geteuid();
    #endif

//    string cmdLine = getCommandLine(executableFilename, getuid(), argc - 1, argv + 1);
//    std::cout << cmdLine << "\n";

    auto arguments = new char*[argc + 2];

    arguments[0] = strToCString(executableFilename);
    auto user = std::to_string(getuid());
    arguments[1] = strToCString(user);

    for (int i = 1; i <= argc - 1; ++i)
        arguments[i + 1] = strToCString(argv[i]);
    arguments[argc + 1] = nullptr;

    execv(executableFilename.c_str(), arguments);

    for (int i = 0; i <= argc; ++i)
        delete[] arguments[i];
    delete[] arguments;

    std::cout << "FINISHED\n";

    return 0;
}
