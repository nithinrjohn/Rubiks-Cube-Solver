#include <ESP32Servo.h>

Servo servos[4];  // create servo object to control a servo
// 16 servo objects can be created on the ESP32

const int servoPins[4] = { 23, 22, 21, 32 };

//gripper consts
const int GRIP_MAX = 170;
const int GRIP_MIN = 115;

//arms
const int RIGHT_ARM = 0;
const int LEFT_ARM = 1;

//directions
const int RIGHT = 180;
const int MID = 90;
const int LEFT = 0;

//axes
const int Z = 1;
const int X = 2;

//standerd operating speed 0.17 sec/60deg
const int SWEEP_ANGLE = 1; // deg
const int SWEEP_DELAY = 10; // ms

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

void turn(int arm, int angle, int ms = SWEEP_DELAY) {
  int servoID = arm*2; // right 0, left 2
  int pos = servos[servoID].read();
  if(ms==0) 
  {
    servos[servoID].write(angle);
    // delay(1000);
  } 
  else 
  {
    for(; pos >= angle; pos -= SWEEP_ANGLE)
    {
      servos[servoID].write(pos);
      delay(ms);
    }
    for(; pos <= angle; pos += SWEEP_ANGLE)
    {
      servos[servoID].write(pos);
      delay(ms);
    }   
  }
  delay(1000);
}

void openGrip(int arm, int sec = 1.5)
{
  int servoID = arm*2 + 1; // right 1, left 3
  for(int pos = servos[servoID].read(); pos <= GRIP_MAX; pos += SWEEP_ANGLE)
  {
      servos[servoID].write(pos);
      delay(SWEEP_DELAY);
  }
  delay(sec*1000);
}

void closeGrip(int arm, int sec = 1.5)
{
  int servoID = arm*2 + 1; // right 1, left 3
  for(int pos = servos[servoID].read(); pos >= GRIP_MIN; pos -= SWEEP_ANGLE)
  {
    servos[servoID].write(pos);
    delay(SWEEP_DELAY);
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
    turn(LEFT_ARM, dir, 0);
    closeGrip(RIGHT_ARM);
    openGrip(LEFT_ARM);
    turn(LEFT_ARM, MID, 0);
    closeGrip(LEFT_ARM);    
  }
  else
  {
    //rotates cube along X axis
    openGrip(LEFT_ARM);
    turn(RIGHT_ARM, dir, 0);
    closeGrip(LEFT_ARM);
    openGrip(RIGHT_ARM);
    turn(RIGHT_ARM, MID, 0);
    closeGrip(RIGHT_ARM);
  }
}

void turnCube(int arm, int dir)
{
  turn(arm, dir);
  openGrip(arm);
  turn(arm, MID, 0);
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

  rotateCube(LEFT);
}

void left(bool prime = false, bool twice = false) {
  rotateCube(LEFT);
  
  turnCube(RIGHT_ARM, prime ? RIGHT : LEFT); 
  if(twice) turnCube(RIGHT_ARM, prime ? RIGHT : LEFT); 

  rotateCube(RIGHT);
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
  
  String input = serialloop();
  String cmds[30];
  char* txt = (char*)input.c_str();
  char* token = strtok(txt, " ");

  int i = 0;
  while(token != NULL) {
    Serial.println(token);
    cmds[i] = token;
    i++;
    token = strtok(NULL, " ");
  }

  i = 0;
  while(cmds[i] != NULL)
  {
    String cmd = cmds[i];
    bool prime = false;
    bool twice = false;
    if(cmd.length() > 1) {
      if(cmd[1] == '\'')
      {
        prime = true;        
      }
      else
      {
        twice = true;
      }
    }

    switch (cmd[0])
    {
      case 'U':
        up(prime, twice);
        break;
      case 'D':
        down(prime, twice);
        break;
      case 'R':
        right(prime, twice);
        break;
      case 'L':
        left(prime, twice);
        break;
      case 'B':
        back(prime, twice);
        break;
      case 'F':
        front(prime, twice);
        break;
    }
    
    i++;
  }
}
