/**
 * @file scan.cpp
 * @author Ryan Walker
 * @date 26 Nov 2019
 * @brief Code for scan and waveform class.
 *
 * Scan is the main class for the SEM, while waveform is the
 * class for each waveform. 
 */

#include "scan.h"
#include "SPI.h"
#include "ADC.h"

extern scan* pscan;        // Pointer to the scan object
#define SS 9               // Slave select pin

/* Timer ISR, this is tiggeer at a set frequency to update the DACs*/
void tim_isr(void){
  digitalWrite(2, !digitalRead(2)); 
  pscan->update(); 
}

/* This is a free running timer that triggers the ADC */
void pdb_isr(void) {
  PDB0_SC &=~PDB_SC_PDBIF; // clear interrupt
}

/* This functions reads from the ADC and then writes to the UART*/
void adc0_isr(void) {
  pscan->adc_cb();
}

spi_tx(uint8_t* data, int len)
{
  digitalWrite(SS, false);
  while(len--)
    SPI.transfer(*data++); 
  digitalWrite(SS, true);
}

void scan::adc_cb(void){
  sample = adc.adc0->readSingle(); 
  
  if((sysState == Calibrating) && (sample > sampleMax)){
    sampleMax = sample;
    FastBeamAxis->updateMaxPos(); 
    SlowBeamAxis->updateMaxPos(); 
  }

  Serial2.write(sample);
}

scan::scan(scan** scanp, int interval)
:interval(interval),    sysState(Quiet), 
 sf(20e3),                sample(0), 
 sampleMax(0),          calFin(false),
 spiClockSpeed(7e6)
{
	*scanp = this;
  float dt = float(interval) / 1e6;

  pinMode(SS, OUTPUT);                                            // sets the digital pin 13 as output
  SPI.begin();                                                    //SS(9), MOSI(11), MISO(12), SCK(13)
  SPI.beginTransaction(SPISettings(spiClockSpeed, MSBFIRST, SPI_MODE0)); 

  FastScanAxis = new waveform(60 ,   dt, DACC, NULL);
  SlowScanAxis = new waveform(1  ,   dt, DACD, FastScanAxis);
  FastBeamAxis = new waveform(60 ,   dt, DACA, NULL);
  SlowBeamAxis = new waveform(1  ,   dt, DACB, FastBeamAxis);
   
  /* ADC Config Below */
  pinMode(A8, INPUT);
  adc.setResolution(8);
  adc.setAveraging(1, ADC_0);                                     // set number of averages
  adc.setConversionSpeed(ADC_CONVERSION_SPEED::MED_SPEED, ADC_0); // LOW_SPEED adds +16 ADCK
  adc.setSamplingSpeed(ADC_SAMPLING_SPEED::HIGH_SPEED);

  adc.adc0->stopPDB();
  
  pinMode(2, OUTPUT);    // sets the digital pin 13 as output
  digitalWrite(SS, true);
}

scan::setFreq(String data)
{
  char* tk = strtok(data.c_str(), ",");
  float f[5] = {0};
  
  int i(0);
  while(tk != NULL){
    f[i] = atof(tk);
    i++;
    tk = strtok(NULL, ",");
  }
  
  FastScanAxis->updateFreq(f[0]);
  SlowScanAxis->updateFreq(f[1]);
  FastBeamAxis->updateFreq(f[2]);
  SlowBeamAxis->updateFreq(f[3]);
  sf = f[4];
  Serial.println("set fre");
  Serial.println(sf);
}

void scan::run(void)
{
  sysState = Scanning; 
  
  /* Zero out all the waveforms.*/	
  FastScanAxis->start();
  SlowScanAxis->start();
  
  DACTimer.begin(tim_isr, interval);  // Start the DAC timer
  
  // Start the ADC
  adc.adc0->startSingleRead(A8); 
  adc.enableInterrupts(ADC_0);
  adc.adc0->startPDB(sf);
}

void scan::cal(void)
{
  sysState = Calibrating;
  sampleMax = 0;
  
  FastBeamAxis->start();
  SlowBeamAxis->start();
  
  DACTimer.begin(tim_isr, interval);  // Start the DAC timer
  
  // Start the ADC
  adc.adc0->startSingleRead(A8); 
  adc.enableInterrupts(ADC_0);
  adc.adc0->startPDB(sf);
  
}

void scan::stop(void)
{
  DACTimer.end();              // Stop the DAC output 
  adc.adc0->stopPDB();
  
  FastScanAxis->null();
  SlowScanAxis->null();
  
  if(sysState == Calibrating){
    calFin = true;
    // Move the Beams into position
    FastBeamAxis->pos = FastBeamAxis->maxPos;
    SlowBeamAxis->pos = SlowBeamAxis->maxPos;
    FastBeamAxis->write();
    SlowBeamAxis->write();
  }
  
  sysState = Quiet; 
}

void scan::update(void)
{
  if(sysState == Scanning){
    FastScanAxis->update();
    SlowScanAxis->update();
    if(SlowScanAxis->_fin())  stop();
  }

  if(sysState == Calibrating){
    FastBeamAxis->update();
    SlowBeamAxis->update();
    if(SlowBeamAxis->_fin()) stop(); 
  }
}

void scan::calMsg(void)
{
  char buf[128];

  sprintf(buf, 
          "Calibration Finished xpos: %fV, ypos: %fV, Sample Max: %fV", 
          FastBeamAxis->maxPos*3.3, 
          SlowBeamAxis->maxPos*3.3, 
          (float(sampleMax)/256)*3.3);
  
  Serial.println(buf);

  calFin = false;
}

waveform::waveform(float freq, float dt, uint8_t dacNum, waveform* slave)
: dt(dt), fin(false), dacn(dacNum), rawDac(0), pos(0), maxPos(0), slave(slave), syncT(0)
{
  updateFreq(freq); 
	spiData = new uint8_t[3]();
  spiData[0] = dacNum | WU_DACn;
  null();  // Null out the axis.
}

void waveform::write(void)
{
  rawDac = 0xffff * pos; 
  spiData[2] = rawDac & 0xFF;         // Upper nibble 
  spiData[1] = rawDac >> 8;           // Lower nibble
  spi_tx(spiData, 3); 
}

void waveform::null(void)
{
  pos = 0;
  write();
}

void waveform::start(void)
{ 
  fin = false;
  t   = 0;
  
  /* If we are the master */
  if( slave ){
    syncT = 0;
  }
}

float waveform::update(void)
{
  tick();

  if( t >= T )
    fin = true;
  else if( dacn == DACC){
    if( t < halfT )
      pos = t * slope;
    else
      pos = -1 + (t * slope);

  }
  else{
    if( t < halfT )
      pos = t * slope;
    else
      pos = 2 - (t * slope);
  }
  if( slave ){                    // If we have a slave waveform (are the master)
    if( t >= syncT){              // And out time is greater than it's period
      slave->start();             // Restart the slave to zero
      slave->fin = false;         // Slave is not finished anymore 
      syncT = (slave->T + syncT); // Update the sync timer. 
    } 
  }

  write();    // Write to SPI bus.
  return(pos);
}
