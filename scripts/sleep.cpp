#include <iostream>
#include <unistd.h>

using namespace std;

int main()
{
    float millis;
    cin >> millis;
    usleep(millis*1000);
    return 0;
}
