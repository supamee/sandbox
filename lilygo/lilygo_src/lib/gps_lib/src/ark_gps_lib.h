#ifndef ARK_GPS_LIB_H
#define ARK_GPS_LIB_H
#include <ctime>

class GPS_Point {
private:
    size_t timestamp;   // Stores a timestamp
    float lat;       // First float value
    float lon;       // Second float value

public:
    // Default constructor
    GPS_Point();

    // Parameterized constructor
    GPS_Point(float v1, float v2, size_t t);

    // Accessor methods
    size_t gettime() const;
    float getlat() const;
    float getlon() const;

    // Mutator methods
    void settime(size_t v);
    void setlat(float v);
    void setlon(float v);

    // Utility to display the contents (for demonstration purposes)
    // This is left empty as there's no implementation provided.
};



class GPSData {
public:
    double latitude;
    double longitude;
    int day;
    int month;
    int year;
    int hour;
    int minute;
    int second;
    bool valid;
    bool ever_valid;


    // Default constructor
    GPSData();

    // Parameterized constructor
    GPSData(double lat, double lon, int d, int m, int y, int h, int min, int sec);

    // Setters
    void setLatitude(double lat);
    void setLongitude(double lon);
    void setDate(int d, int m, int y);
    void setTime(int h, int min, int sec);
    void setFromGPRMC(char* gga);

    // Getters
    double getLatitude() const;
    double getLongitude() const;
    void getDate(int &d, int &m, int &y) const;
    void getTime(int &h, int &min, int &sec) const;
    int getDate()const;
    int getTime()const;
    // Display
};

#endif // GPSDATA_H

