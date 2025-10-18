#ifndef LOGGER_H
#define LOGGER_H
#include <Arduino.h>

// 0=ERROR 1=WARN 2=INFO 3=DEBUG 4=TRACE
#ifndef LOG_LEVEL
#define LOG_LEVEL 4
#endif

inline void logPrint(const char*level,const char*fmt,va_list args){
  char buf[128];
  vsnprintf(buf,sizeof(buf),fmt,args);
  Serial.print(level); Serial.print(buf); Serial.println();
}

inline void logMsg(int lvl,const char*prefix,const char*fmt,...){
  if(LOG_LEVEL<lvl)return;
  va_list args; va_start(args,fmt); logPrint(prefix,fmt,args); va_end(args);
}

#define LOG_ERROR(...) logMsg(0,"[ERROR] ",__VA_ARGS__)
#define LOG_WARN(...)  logMsg(1,"[WARN ] ",__VA_ARGS__)
#define LOG_INFO(...)  logMsg(2,"[INFO ] ",__VA_ARGS__)
#define LOG_DEBUG(...) logMsg(3,"[DEBUG] ",__VA_ARGS__)
#define LOG_TRACE(...) logMsg(4,"[TRACE] ",__VA_ARGS__)
#endif

