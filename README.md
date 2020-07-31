# QuickfusoR

This project is a prototype UI for infusion pumps that uses QR codes for
programming the pump.

This is intended to minimize the usual sources of human error.

* By eliminating confusing calculations
* By eliminating confusing panel UI 

## Disclaimer

As if it didn't need saying : this is not a certified medical device. Aside from the fact that there's nothing to control an actual infusion pump, the code lacks the kind of rigour I would expect from a real medical device. In particular it suffers from one of the "hilarious" faults discussed in Thimbleby's lecture where you can use the UI buttons to drop the rate of infusion to a negative value. And if you show it your QR business card it will crash.

## Inspiration

This project was inspired by [this lecture](http://www.gresham.ac.uk/lectures-and-events/designing-it-to-make-healthcare-safer) by Prof. Harold Thimbleby which arrived in front of my eyes via one of the various healthcare IT channels I read.

## Hardware

The software as presented uses the following

* A Raspberry Pi 2 Model B
    * Starting with a standard Raspbian image
* The Raspberry Pi Camera Module
    * I went for the model with no IR filter, so that an IR lamp can be used to illuminate the QR code in dim light without disturbing patients
* A [Display-O-Tron HAT](https://shop.pimoroni.com/products/display-o-tron-hat)
    * While you can get a 320x240 TFT touchscreen for a mere £8 more, many medical appliances have displays which are roughly equivalent to the 16x3 character LCD on this device
    * It has 6 useful capacitive touch buttons
    * Programming for a 16x3 text display and 6 buttons is quicker and easier than doing it for a snazzy touchscreen
    * It also has a cool 6-LED bar graph which I thought would make a nice infusion rate throbber! (it does)

## Software

There are two parts to the software :

* An application used to produce QR codes
* The "pump" software on the device

The former was written in C# by my collaborator Kat Hobdell, the latter in Python by myself.

### QR Codes

The QR code data essentially takes the format of a Python configuration file, without the leading section header. This is open to revision, a simple format has been selected to try and keep QR size down and make for easy parsing (with the standard Python config library).

Possibly the fiddliest part was writing the code to recognise QR codes on the Pi. All the available examples spawn UI to the X11 server and use a camera at /dev/video0 ; this project has no "real" screen so no X11, and the Pi camera module doesn't get a device at /dev/video0. I think there is scope for an improvement in the QR recognition as the underlying library supports real-time recognition from streams ; presently it uses a snapshot which means you have to hold the code reasonably still at an appropriate distance from the camera (in good light).

### Pump UI

The pump UI was written as a state machine.

* "Wait" state
    * The pump waits for someone to push the button to start a scan
* "Scan" state
    * The pump tries to find a QR code
    * Once it finds one, it parses the data and sets up the parameters for the next state
* "Verify" state
    * The pump asks the user to verify the patient's name
* "Infusion" state
    * The pump infuses fluid at the prescribed rate
    * Optionally, the up and down buttons can adjust the rate


