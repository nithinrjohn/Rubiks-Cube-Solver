/*
  WiFiAccessPoint.ino creates a WiFi access point and provides a web server on it.

  Steps:
  1. Connect to the access point "yourAp"
  2. Point your web browser to http://192.168.4.1/H to turn the LED on or http://192.168.4.1/L to turn it off
     OR
     Run raw TCP "GET /H" and "GET /L" on PuTTY terminal with 192.168.4.1 as IP address and 80 as port

  Created for arduino-esp32 on 04 July, 2018
  by Elochukwu Ifediora (fedy0)
*/

#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiAP.h>

#include <CustomBoardPinDefs.h>
#include <PWMServo.h>

#include <String.h>

using namespace team967;

#include <BluetoothSerial.h>

BluetoothSerial bt;

// Set these to your desired credentials.
const char *ssid = "yourAP";
const char *password = "yourPassword";

WiFiServer server(80);

PWMServo rackServo1(PCB_GPIO_0, 0);
PWMServo rackServo2(PCB_GPIO_1, 1);
PWMServo rackServo3(PCB_GPIO_2, 2);
PWMServo rackServo4(PCB_GPIO_3, 3);

PWMServo servo1(PCB_GPIO_4, 4);
PWMServo servo2(PCB_GPIO_5, 5);
PWMServo servo3(PCB_GPIO_6, 6);
PWMServo servo4(PCB_GPIO_7, 7);

void serialsetup()
{
  Serial.begin(115200);
}

String serialloop()
{
  if(Serial.available() > 0)
  {
    String currentLine = Serial.readStringUntil('\n'); 

    Serial.println("Received: " + currentLine);
    return currentLine;
  }
}

void btsetup()
{
  bt.begin("ESP32BT");
}

void btloop()
{
  if(bt.available())
  {
    String currentLine = bt.readStringUntil('\n'); 

    Serial.println(currentLine);
  }
}

void wifisetup()
{
  Serial.println();
  Serial.println("Configuring access point...");

  // You can remove the password parameter if you want the AP to be open.
  WiFi.softAP(ssid, password);
  IPAddress myIP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(myIP);
  server.begin();

  Serial.println("Server started");
}

void wifiloop()
{
  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    Serial.println("New Client.");           // print a message out the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        Serial.print(c);
        currentLine += c;
        if(c == '\n')
        {
          uint8_t buf[100];
          currentLine.getBytes(buf, currentLine.length());
          client.write(buf, currentLine.length());
          Serial.println(currentLine);
          currentLine = "";
        }
      }
    }
  }  
  // close the connection:
  client.stop();
  Serial.println("Client Disconnected.");
}

void servosetup() {
  rackServo1.begin();
  rackServo2.begin();
  rackServo3.begin();
  rackServo4.begin();

  servo1.begin();
  servo2.begin();
  servo3.begin();
  servo4.begin();
  
  rackServo1.setAngleDegrees(0);
  rackServo2.setAngleDegrees(0);
  rackServo3.setAngleDegrees(0);
  rackServo4.setAngleDegrees(0);

  servo1.setAngleDegrees(0);
  servo2.setAngleDegrees(0);
  servo3.setAngleDegrees(0);
  servo4.setAngleDegrees(0);
}

void up() {
  
}

void down() {
  
}

void right() {
  
}

void left() {
  
}

void front() {
  
}

void back() {
  
}

void upP() {
  
}

void downPrime() {
  
}

void rightPrime() {
  
}

void leftPrime() {
  
}

void frontPrime() {
  
}

void backPrime() {
  
}


void setup() {
  serialsetup();
  servosetup();
}

void loop() {
  String input = serialloop();
  String cmds[30];
  char* txt = (char*)input.c_str();
  char* token = strtok(txt, " ");
   
  while(token != NULL) {
    Serial.println(token);
    
    token = strtok(NULL, " ");
  }
}
