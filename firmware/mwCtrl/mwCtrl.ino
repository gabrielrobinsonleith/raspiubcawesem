#include "DMAChannel.h"
#include "scan.h"

scan* pscan(NULL);

void setup() {
	delay(1000);		        // Delay to allow for reconnection
  Serial.begin(115200);   // Used for native usb
  Serial2.begin(2000000); // P9 - RX, P10 - TX (UART1)

  // xuS DAC rate, xHz ADC sample rate.
  scan* sc = new scan(&pscan, 100); 
}

void loop() {
	Serial.println("Wide Awake");
  
  while(1){
  uint8_t switchValue(0);
    if(Serial.available()) {
    switchValue = Serial.read();
    switch(switchValue) {
      case 'p':                               // Ping (p)
        Serial.write('A');
        break;
      case 'r':                               // Run Scan (r) 
        pscan->run();	
        break;
      case 'k':                               // Kill Scan (stop) (k) 
        pscan->stop();	
        break;
      case 'c':                               // Run Calibration (c) 
        pscan->cal();	
        break;
      case 's':                               // Set dac frequencies
        pscan->setFreq(Serial.readString());
        break;
      }
    }
    if(pscan->_calFin())
      pscan->calMsg();
  }
}
