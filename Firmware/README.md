# IMechE Design Challenge 2024

## Installation

OS: Raspberry Pi OS (Legacy, 32-bit) Lite

- **Step 1:** \
  To download code, it is necessary to have git installed:

```shell
sudo apt-get update && sudo apt-get install git -y
```

- **Step 2:** \
  Now install prerequisites for firmware:

```shell
sudo apt-get install python3-opencv && sudo apt-get install fswebcam
```

- **Step 3:** \
  Once these are installed, use the following command to clone the repo into the home directory:

```shell
cd ~ && git clone https://github.com/shehan-m/IMechE-Design-Challenge-2024/
```

## How to run code on startup

- **Step 1:** \
  Open the `rc.local` file using nano editor:

```shell
cd ~ && sudo nano /etc/rc.local
```

- **Step 2:** \
  Make bash script executable:

```shell
sudo chmod +x /IMechE-Design-Challenge-2024/Firmware/startup.sh
```

- **Step 3:** \
  Add the following commands above `exit 0`

```shell
sudo apt-get update && sudo apt-get install git -y
```

## Electronics

### Wiring Diagram
![image](Electronics/schematic%20v02_bb.png)

### Limit switch

switch type: SPDT

#### This switch has three terminals:

- Common (COM): The common terminal
- Normally Open (NO): Connected to COM when the switch is pressed
- Normally Closed (NC): Connected to COM when the switch is not pressed

### Stepper driver current limiting

Vref = Imax * 8 * Rs

where, Imax is the current limit of the stepper motor, Rs is the resistance of the current sensing resistor (R5 on driver board)

In our case, Imax is 350 mA and Rs is 0.1 Ohms. Let's run the stepper motor at 60% of its rating. From this we get Vref:

Vref = (0.350 * 0.6) * 8 * 0.1 = 0.17 V
