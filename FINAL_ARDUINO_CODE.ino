#include <Servo.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define OLED_RESET 4
Adafruit_SSD1306 display(128, 64, &Wire, OLED_RESET);

Servo servo_horizontal;
Servo servo_vertical;
Servo servo_vertical2;

// Initial servo positions
int horizontal_angle = 90;
int vertical_angle = 90;
int vertical_angle2 = 90;

void setup() {
  // Attach servos
  servo_horizontal.attach(11);
  servo_vertical.attach(3);
  servo_vertical2.attach(5);

  
  // Set initial positions
  servo_horizontal.write(horizontal_angle);
  servo_vertical.write(vertical_angle);
  servo_vertical2.write(vertical_angle);

  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize the OLED display
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("System Ready");
  display.display();
  delay(2000); // Display initial message for 2 seconds
}

void loop() {
  // Check for incoming serial data
  if (Serial.available()) {
    String received_data = Serial.readStringUntil('\r');

    // Handle mode change
    if (received_data.startsWith("MODE:")) {
      String mode = received_data.substring(5);
      displayMode(mode);
    } 
    // Handle reset command
    else if (received_data == "RESET") {
      resetMotors();
    } 
    // Handle motor control commands
    else {
      handleMotorControl(received_data);
    }
  }
}

// Function to display mode and angles on the OLED
void displayMode(String mode) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.setTextSize(1);
  display.println("Mode:");
  display.setCursor(0, 10);
  display.println(mode);
  display.setCursor(0, 30);
  display.print("H Angle: ");
  display.println(horizontal_angle);
  display.print("V Angle: ");
  display.println(vertical_angle);
  display.display();
}

// Function to reset servos to initial positions
void resetMotors() {
  horizontal_angle = 90;
  vertical_angle = 90;
  vertical_angle2 = 90;

  servo_horizontal.write(horizontal_angle);
  servo_vertical.write(vertical_angle);
  servo_vertical2.write(vertical_angle);

  Serial.print("INIT:");
  Serial.print(horizontal_angle);
  Serial.print(",");
  Serial.println(vertical_angle);

  displayMode("System Reset");
}

// Function to handle motor control commands
void handleMotorControl(String data) {
  if (data.indexOf(',') == -1) {
    Serial.println("Invalid Data Format");
    return;
  }

  int horizontal_adjust = data.substring(0, data.indexOf(',')).toInt();
  int vertical_adjust = data.substring(data.indexOf(',') + 1).toInt();
  int vertical_adjust2 = vertical_adjust;

  horizontal_angle = constrain(horizontal_angle + horizontal_adjust, 0, 180);
  vertical_angle = constrain(vertical_angle + vertical_adjust, 45, 162);
  vertical_angle2 = vertical_angle;

  servo_horizontal.write(horizontal_angle);
  servo_vertical.write(vertical_angle);
  servo_vertical2.write(vertical_angle);

  Serial.print("Horizontal Angle: ");
  Serial.println(horizontal_angle);
  Serial.print("Vertical Angle: ");
  Serial.println(vertical_angle);

  displayMode("Tracking Active");
}
