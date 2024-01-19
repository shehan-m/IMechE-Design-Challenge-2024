# IMechE Design Challenge 2024

## Electronics

### Limit switch

switch type: SPDT

#### This switch has three terminals:

- Common (COM): The common terminal
- Normally Open (NO): Connected to COM when the switch is pressed
- Normally Closed (NC): Connected to COM when the switch is not pressed

### Downloading firmware

OS: Raspberry Pi OS (Legacy, 32-bit) Lite

- **Step 1:** \
  To download this script, it is necessary to have git installed:

```shell
sudo apt-get update && sudo apt-get install git -y
```

- **Step 2:** \
  Once git is installed, use the following command to clone the repo into home-directory:

```shell
cd ~ && git clone https://github.com/shehan-m/IMechE-Design-Challenge-2024/
```

```shell
cd ~ && git init firmware && cd firmware && git remote add -f origin https://github.com/shehan-m/IMechE-Design-Challenge-2024.git && git config core.sparseCheckout true && echo "Firmware/" >> .git/info/sparse-checkout && git pull origin master
```

- **Step 2:** \
  Now install prerequisites for firmware:

```shell
sudo apt-get install python3-opencv
```

```shell
sudo apt-get install fswebcam
```
