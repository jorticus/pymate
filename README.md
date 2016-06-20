# pyMATE

For Python 2.x

pyMATE is a python library that can be used to emulate an [Outback MATE unit][mate-product], and talk to any supported
[Outback Power Inc.][outback] device such as an [MX charge controller][mx-product], an [FX inverter][fx-product], a [FlexNET DC monitor][flexnet-product], or a [hub][hub-product] with
multiple devices attached to it.

[outback]:          http://www.outbackpower.com/outback-products/inverters-chargers
[mate-product]:     http://www.outbackpower.com/outback-products/communications/item/mate?category_id=440
[mx-product]:       http://www.outbackpower.com/outback-products/charge-controllers/item/flexmax-6080?category_id=438
[fx-product]:       http://www.outbackpower.com/outback-products/inverters-chargers/category/fxr-grid-hybrid-series
[flexnet-product]:  http://www.outbackpower.com/outback-products/communications/item/flexnet-dc?category_id=440
[hub-product]:      http://www.outbackpower.com/outback-products/communications/item/hub?category_id=440

You will need a simple adapter circuit and a TTL serial port.

For more details, see [jared.geek.nz/pymate](http://jared.geek.nz/pymate)

## Usage

The library makes it very easy to communicate with your Outback product (eg. the MX Charge Controller).
First you need to initialize the device:

    from matenet import MateMX

    # Chose the correct one for your platform:
    mate = MateMX('/dev/ttyUSB0')  # LINUX
    mate = MateMX('COM2')          # WINDOWS

Then check to see if the device is connected and responding
(This will throw a RuntimeError if it cannot communicate)

    mate.scan(port=0)  # 0: No hub, 1-9: hub port

Getting the current device revision:

    print "Revision:", mate.revision   # Prints 'Revision: 000.000.000'

Getting the current MX status

    status = mate.get_status()
    print status

Accessing specific status values

    print "PV Voltage:", status.pv_voltage
    print "Battery Voltage:", status.bat_voltage

Viewing log history

    logpage = mate.get_logpage(-1)  # Get yesterday's log
    print logpage

## Example Server

For convenience, a simple server is included that captures data periodically
and uploads it to a remote server via a REST API.
The remote server then stores the received data into a database of your choice.

See srv1/ for the collector and srv2/ for the REST API.

