
#include <ESP32Servo.h>

Servo servos[4];  // create servo object to control a servo
// 16 servo objects can be created on the ESP32


int servoPins[4] = { 23, 22, 21, 32 };

void setup() {
  // Allow allocation of all timers
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  for(int i = 0; i < 4; i++)
  {
    servos[i].setPeriodHertz(50);               // standard 50 hz servo
    servos[i].attach(servoPins[i], 625, 2600); // attaches the servo on pin 18 to the servo object
  }
  // using default min/max of 1000us and 2000us
  // different servos may require different min/max settings
  // for an accurate 0 to 180 sweep

  Serial.begin(9600);
  servos[0].write(90);
  servos[1].write(180);
  servos[2].write(90);
  servos[3].write(180);
}

void armtest() {
    servos[1].write(120); 
    delay(1000); 
    servos[3].write(180); 
    delay(1000);
    servos[3].write(120); 
    delay(1000);  
    servos[1].write(180);
    delay(1000); 
    servos[3].write(120); 
    delay(1000); 
}

void loop() {

    Serial.println("----------");
    
    servos[0].write(0);
    delay(3000);     
    servos[0].write(180);
    delay(3000);     
    servos[0].write(90);
    
    delay(5000);     
  

    servos[2].write(0);
    delay(3000);     
    servos[2].write(180);
    delay(3000);     
    servos[2].write(90);

    delay(5000);     

    servos[1].write(90);
    delay(3000); 
    servos[1].write(180);
    delay(5000); 

    servos[3].write(90);
    delay(3000); 
    servos[3].write(180);
    delay(5000); 
}
