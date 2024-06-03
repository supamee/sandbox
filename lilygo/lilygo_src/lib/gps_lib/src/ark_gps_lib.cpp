#include "ark_gps_lib.h"
#include <string.h>
#include <stdio.h>
GPS_Point::GPS_Point() {
    timestamp = 0;  // Initialize timestamp with current time
    lat = 0.0f;
    lon = 0.0f;

}

// Parameterized constructor
GPS_Point::GPS_Point(float v1, float v2, size_t t) {
    timestamp = t;
    lat = v1;
    lon = v2;

}

// Accessor methods
size_t GPS_Point::gettime() const { return timestamp; }
float GPS_Point::getlat() const { return lat; }
float GPS_Point::getlon() const { return lon; }

// Mutator methodszzzzzzzzzzzs
void GPS_Point::settime(size_t v) { timestamp = v; }
void GPS_Point::setlat(float v) { lat = v; }
void GPS_Point::setlon(float v) { lon = v; }



// Default constructor
GPSData::GPSData() : latitude(0.0), longitude(0.0), day(0), month(0), year(0), hour(0), minute(0), second(0), ever_valid(false),valid(false){}

// Parameterized constructor
GPSData::GPSData(double lat, double lon, int d, int m, int y, int h, int min, int sec) 
    : latitude(lat), longitude(lon), day(d), month(m), year(y), hour(h), minute(min), second(sec), ever_valid(false),valid(false) {}

void GPSData::setLatitude(double lat) {
    latitude = lat;
}

void GPSData::setLongitude(double lon) {
    longitude = lon;
}

void GPSData::setDate(int d, int m, int y) {
    day = d; 
    month = m; 
    year = y;
}

void GPSData::setTime(int h, int min, int sec) {
    hour = h; 
    minute = min; 
    second = sec;
}

void GPSData::setFromGPRMC( char* gga) {
    char* token;
    char buffer[100];  // temporary buffer to hold a copy of the gga string
    // strncpy(buffer, gga, sizeof(buffer) - 1);
    // buffer[sizeof(buffer) - 1] = '\0';

// $GPRMC,191053.00,V,,,,,,,140823,,,N*7E
    int temp_hour;
    int temp_min;
    int temp_sec;

    // Tokenize the string using comma as delimiter
    token = strtok(gga, ",");

    token = strtok(NULL, ",");
    sscanf(token, "%02d%02d%02d", &hour, &minute, &second);
    // hour=temp_hour;
    // minute=temp_min;
    // second=temp_sec;

    token = strtok(NULL, ",");
    if (token && *token == 'A') {
        valid=true;
        ever_valid=true;
    } else {
        valid=false;
    }
    if (valid){
        token = strtok(NULL, ",");
        if(token && *token-1 != ',') {
            latitude = atof(token);
            latitude /= 100.0;
            float minutes = (latitude - int(latitude)) * 100.0;
            latitude = int(latitude) + minutes / 60.0;
        }

        token = strtok(NULL, ",");
        if(token && *token == 'S') {
            latitude = -latitude;
        }

        token = strtok(NULL, ",");
        if(token) {
            longitude = atof(token);
            longitude /= 100.0;
            float minutes = (longitude - int(longitude)) * 100.0;
            longitude = int(longitude) + minutes / 60.0;
        }

        token = strtok(NULL, ",");
        if(token && *token == 'W') {
            longitude = -longitude;
        }
        token = strtok(NULL, ",");
        //speed
        token = strtok(NULL, ",");
        // //track true
    }
    token = strtok(NULL, ",");
    //date
    if(token) {
        sscanf(token, "%02d%02d%02d", &day, &month, &year);
        }
    // hour=temp_hour;
    // minute=temp_min;
    // second=temp_sec;
    // ... [continue tokenizing other fields if necessary]
}

double GPSData::getLatitude() const {
    return latitude;
}

double GPSData::getLongitude() const {
    return longitude;
}

void GPSData::getDate(int &d, int &m, int &y) const {
    d = day; 
    m = month; 
    y = year;
}

void GPSData::getTime(int &h, int &min, int &sec) const {
    h = hour; 
    min = minute; 
    sec = second;
}
int GPSData::getDate() const{
    return (day*10000) + (month*100) + (year);
}

int GPSData::getTime() const{
    return (hour*10000) + (minute*100) + (second);
}