# IMechE Design Challenge 2024

### Downloading firmware
OS: Raspberry Pi OS (Legacy, 32-bit) Lite

* **Step 1:** \
To download this script, it is necessary to have git installed:

```shell
sudo apt-get update && sudo apt-get install git -y
```

* **Step 2:** \
Once git is installed, use the following command to clone the repo into home-directory:

```shell
cd ~ && git clone [https://github.com/dw-0/kiauh.git](https://github.com/shehan-m/IMechE-Design-Challenge-2024/
```

* **Step 2:** \
Now install prerequisites for firmware:

```shell
sudo apt-get install python3-opencv
```
```shell
sudo apt-get install fswebcam
```


### Prerequisites for firmware

OpenCV (`sudo apt-get install python3-opencv`) is need for target detection. fswebcam (`sudo apt-get install fswebcam`) is need if a webcam is used.
