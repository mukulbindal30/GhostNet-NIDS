#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define ledGreen 4
#define ledYellow 5
#define ledRed 6
#define buzzer 3
#define trig 9
#define echo 10

unsigned long lastSensorTime = 0;
unsigned long lastAlertTime = 0;
unsigned long lastSerialTime = 0;
const unsigned long sensorInterval = 100;
int dis = 0;
String zoneState = "SAFE";

void setup() {
  Serial.begin(9600);
  
  pinMode(ledGreen, OUTPUT);
  pinMode(ledYellow, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(buzzer, OUTPUT);
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
  
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.clearDisplay();
  display.display();
}

void loop() {
  unsigned long currentTime = millis();

  if (currentTime - lastSensorTime >= sensorInterval) {
    lastSensorTime = currentTime;
    long totalDistance = 0;
    
    for (int i = 0; i < 5; i++) {
      digitalWrite(trig, LOW);
      delayMicroseconds(2);
      digitalWrite(trig, HIGH);
      delayMicroseconds(10);
      digitalWrite(trig, LOW);
      
      long dur = pulseIn(echo, HIGH, 30000);
      totalDistance += (dur * 0.034 / 2);
      delayMicroseconds(50);
    }
    
    dis = totalDistance / 5;
    
    display.clearDisplay();
    display.setTextSize(3);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 10);
    display.print(dis);
    display.setTextSize(2);
    display.print(" cm");
    
    int graphDis = constrain(dis, 0, 60);
    int barWidth = map(graphDis, 60, 0, 0, 128); 
    
    display.drawRect(0, 45, 128, 15, SSD1306_WHITE);
    display.fillRect(0, 45, barWidth, 15, SSD1306_WHITE);
    
    display.display();
  }
  
  if (currentTime - lastSerialTime >= 500) {
    lastSerialTime = currentTime;
    Serial.print("Distance: ");
    Serial.print(dis);
    Serial.print("cm | Zone: ");
    Serial.println(zoneState);
  }

  if (dis > 60 || dis == 0) {
    zoneState = "SAFE";
    digitalWrite(ledGreen, HIGH);
    digitalWrite(ledYellow, LOW);
    digitalWrite(ledRed, LOW);
    noTone(buzzer);
  }
  else if (dis > 30 && dis <= 60) {
    zoneState = "CAUTION";
    digitalWrite(ledGreen, LOW);
    digitalWrite(ledYellow, HIGH);
    digitalWrite(ledRed, LOW);
    
    if (currentTime - lastAlertTime >= 800) {
      lastAlertTime = currentTime;
      tone(buzzer, 1000, 100);
    }
  }
  else if (dis > 15 && dis <= 30) {
    zoneState = "CLOSE";
    digitalWrite(ledGreen, LOW);
    digitalWrite(ledYellow, HIGH);
    digitalWrite(ledRed, HIGH);
    
    if (currentTime - lastAlertTime >= 300) {
      lastAlertTime = currentTime;
      tone(buzzer, 1000, 100);
    }
  }
  else {
    zoneState = "DANGER";
    digitalWrite(ledGreen, LOW);
    digitalWrite(ledYellow, LOW);
    digitalWrite(ledRed, HIGH);
    tone(buzzer, 1000);
  }
}