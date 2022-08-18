#include <ESP32Servo.h>

Servo servos[4];  // create servo object to control a servo
// 16 servo objects can be created on the ESP32

int servoPins[4] = { 23, 22, 21, 32 };

//gripper consts
int GRIP_MAX = 180;
int GRIP_MIN = 120;

//arms
int RIGHT_ARM = 1;
int LEFT_ARM = 2;

//directions
int RIGHT = 180;
int MID = 90;
int LEFT = 0;

//axes
int Z = 1;
int X = 2;

void setup() {
  Serial.begin(115200);
  
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

  //right arm
  servos[0].write(90);
  servos[1].write(120);

  //left arm
  servos[2].write(90);
  servos[3].write(120);
}

void turn(int arm, int angle, int sec = 1.5) {
  if(arm == RIGHT_ARM)
  {
    servos[0].write(angle);
  }
  else
  {
    servos[2].write(angle);    
  }
  delay(sec*1000);
}

void openGrip(int arm, int sec = 1.5)
{
  if(arm == RIGHT_ARM)
  {
    servos[1].write(180);
  }
  else
  {
    servos[3].write(180);    
  }
  delay(sec*1000);
}

void closeGrip(int arm, int sec = 1.5)
{
  if(arm == RIGHT_ARM)
  {
    servos[1].write(120);
  }
  else
  {
    servos[3].write(120);    
  }
  delay(sec*1000);
}

void rotateCube(int dir, int axis = Z)
{
  //rotates cube on Z axis by default
  if(axis == Z)
  {
    //rotates cube along Z axis
    openGrip(RIGHT_ARM);
    turn(LEFT_ARM, dir);
    closeGrip(RIGHT_ARM);
    openGrip(LEFT_ARM);
    turn(LEFT_ARM, MID);
    closeGrip(LEFT_ARM);    
  }
  else
  {
    //rotates cube along X axis
    openGrip(LEFT_ARM);
    turn(RIGHT_ARM, dir);
    closeGrip(LEFT_ARM);
    openGrip(RIGHT_ARM);
    turn(RIGHT_ARM, MID);
    closeGrip(RIGHT_ARM);
  }
}

void turnCube(int arm, int dir)
{
  turn(arm, dir);
  openGrip(arm);
  turn(arm, MID);
  closeGrip(arm);
}

void up(bool prime = false, bool twice = false) {
  rotateCube(RIGHT);
  rotateCube(RIGHT);
  
  turnCube(RIGHT_ARM, prime ? LEFT : RIGHT);
  if(twice) turnCube(RIGHT_ARM, prime ? LEFT : RIGHT);
  
  rotateCube(LEFT);
  rotateCube(LEFT);
}

void down(bool prime = false, bool twice = false) {
  turnCube(RIGHT_ARM, prime ? LEFT : RIGHT);
  if(twice) turnCube(RIGHT_ARM, prime ? LEFT : RIGHT);
}

void right(bool prime = false, bool twice = false) {
  rotateCube(RIGHT);
  
  turnCube(RIGHT_ARM, prime ? LEFT : RIGHT);
  if(twice) turnCube(RIGHT_ARM, prime ? LEFT : RIGHT);
}

void left(bool prime = false, bool twice = false) {
  rotateCube(LEFT);
  
  turnCube(RIGHT_ARM, prime ? RIGHT : LEFT); 
  if(twice) turnCube(RIGHT_ARM, prime ? RIGHT : LEFT); 
}

void back(bool prime = false, bool twice = false) {
  turnCube(LEFT_ARM, prime ? LEFT : RIGHT);
  if(twice) turnCube(LEFT_ARM, prime ? LEFT : RIGHT);
}

void front(bool prime = false, bool twice = false) {
  rotateCube(RIGHT, X);
  rotateCube(RIGHT, X);

  turnCube(LEFT_ARM, prime ? LEFT : RIGHT);
  if(twice) turnCube(LEFT_ARM, prime ? LEFT : RIGHT);

  rotateCube(LEFT, X);
  rotateCube(LEFT, X);
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

void loop() {
  /*
    String input = serialloop();
    String cmds[30];
    char* txt = (char*)input.c_str();
    char* token = strtok(txt, " ");
     
    while(token != NULL) {
      Serial.println(token);
      
      token = strtok(NULL, " ");
  */
  String input = serialloop();
  Serial.println("loop: " + input);
  
  if(input == "u")
  {
    up();
  }
  else if(input == "d")
  {
    down();
  }
  else if(input == "r")
  {
    right();
  }
  else if(input == "l")
  {
    left();
  }
  else if(input == "b")
  {
    back();
  }
  else if(input == "f")
  {
    front();
  }
  
  if(input == "u\'")
  {
    up(true);
  }
  else if(input == "d\'")
  {
    down(true);
  }
  else if(input == "r\'")
  {
    right(true);
  }
  else if(input == "l\'")
  {
    left(true);
  }
  else if(input == "b\'")
  {
    back(true);
  }
  else if(input == "f\'")
  {
    front(true);
  }
  
  if(input == "u2")
  {
    up(true, true);
  }
  else if(input == "d2")
  {
    down(true, true);
  }
  else if(input == "r2")
  {
    right(true,true);
  }
  else if(input == "l2")
  {
    left(true, true);
  }
  else if(input == "b2")
  {
    back(true, true);
  }
  else if(input == "f2")
  {
    front(true, true);
  }

}
