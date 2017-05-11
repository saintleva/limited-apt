#include <string>
#include <sstream>


std::string getCommandLine(const std::string& executableName, uid_t userID, int paramCount, char** params)
{
    std::ostringstream result;
    result << executableName << " " << userID;
    for (int i = 0; i < paramCount; ++i)
        result << " " << params[i];
    return result.str();
}
