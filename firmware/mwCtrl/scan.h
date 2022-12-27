/**
 * @file scan.h
 * @author Ryan Walker
 * @date 26 Nov 2019
 * @brief Declaration for scan and waveform class.
 *
 * Scan is the main class for the SEM, while waveform is the
 * class for each waveform. 
 *  
 * Scanning Stage
 *   DACA - FastScanAxis (Fast Axis, 10 - 60hz)
 *   DACB - SlowScanAxis (Slow Axis, 0.02 - 0.1hz)
 *
 * Beam Allignment
 *   DACC - FastBeamAxis (Fast Axis, 5 - 10hz)
 *   DACD - SlowBeamAxis (Slow Axis, 0.05 - 0.1hz)
*/

#include "ADC.h"
#include "IntervalTimer.h"
#include "DMAChannel.h"

#define DACA    0b00000000
#define DACB    0b00000001
#define DACC    0b00000010
#define DACD    0b00000011
#define DAC_ALL 0b00000111

#define WU_DACn 0b00011000  // Write to and update DAC n

/* Class to generate a Triangle Wave */
class waveform
{
  friend class scan;

  float f;         /** Freq (hz) */
  float T;         /** Period (s) */
  float halfT;     /** Half of period */
  float dt;        /** Time between samples */
  float slope;     /** Slope of line */
  float pos;       /** Runs from 0 -> 1, current position of tri */
  float maxPos;    /** Max position (Calibration Only)*/ 
  double t;        /** Systime */ 
  bool fin;        /** Is it finished it's cycle     */
  uint8_t dacn;    /** Dac Number*/
  uint8_t *spiData;/** Pointer to the spi output data buffer*/
  uint16_t rawDac; /** DAC raw value */


	/** @brief ctor for the waveform class. 
  *   @param freq frequency you want the waveform to be (hz). 
  *   @param dt how often does the update function get called (uS). 
  *   @param dacNum Which DAC should this waveform output to. 
  */
	waveform(float freq, float dt, uint8_t dacNum, waveform* slave);
  
  float syncT;         /** Synchronisation timer, this is only used by the master */
  waveform* slave;     /** Pointer to the waveform's slave. NULL is the waveform is a slave*/

  updateFreq(float freq){
    f = freq;
    T = 1/freq; halfT = T / 2; slope = 1 / halfT;
  }
  
	inline void tick(){t+=dt;};             /** Tick the waveform's clock (tick ever time = dt)*/
  void write(void);                       /** Write the waveform to the dacs */ 
  void null(void);                        /** Zero the DACs*/
  void updateMaxPos(void){maxPos = pos;};
  void start(void);
  float update(void);
  
  float _pos(){return pos;};   /** Runs from 0 -> 1, current position of tri */
  bool  _fin(){return fin;};   /** Check to see the current waveform is finished */
};

class scan
{
  friend class waveform;                 
  IntervalTimer  DACTimer;             /** Timer triggered to update the DACs  */
  int interval;                        /** Interval at which the timer is triggered at (uS)*/
  uint32_t sf;                          /** ADC sample freq (hz)*/
  volatile uint8_t sample, sampleMax;  /** Params used to calibration */
  bool calFin;                          
  uint32_t spiClockSpeed;
 
  ADC adc;                   
  
  waveform* FastScanAxis;
  waveform* SlowScanAxis;
  waveform* FastBeamAxis;
  waveform* SlowBeamAxis;

public:
  enum State{
    Scanning,
    Calibrating,
    Quiet
  };
private:
  State sysState;

public:

  /** @brief ctor for the scan class. 
  *   @param scanp Static pointer to the class. 
  *   @param interval Interval (in uS) the DAC's will be updated at. 
  *   @param sf Sample Freq (in hz) the system will sample at.. 
  */ 
	scan(scan** scanp, int interval);
  void update(void);        /** Update function, do NOT call this */
  void run(void);           /** Call to initiate a scan */
  void cal(void);           /** Call to initiate a calibration */
  void calMsg(void);        /** This prints out calibration info */
  void stop(void);          /** Call to stop a current scan */
  void adc_cb(void);        /** Callback function Do NOT call this */
  
	/** @brief Call to set the frequency of the waveforms. 
  *   @param data String with the freq (in hz). 
  *	 				eg: "s <FastScan>, <SlowScan>, <FastBeam>, <SlowBeam>"
  */
	setFreq(String data);           
 
  State _sysState(){return sysState;}; /** Get the current system state*/
  bool _calFin(){return calFin;};      /** Is the calibration finished?*/
};
