# MoSculp Demo

[http://mosculp.csail.mit.edu/](http://mosculp.csail.mit.edu/)

This is a desktop demo for the following paper. If you find the code useful, please cite the paper.

**MoSculp: Interactive Visualization of Shape and Time**<br/>
[Xiuming Zhang](http://people.csail.mit.edu/xiuming/), [Tali Dekel](http://people.csail.mit.edu/talidekel/), [Tianfan Xue](https://people.csail.mit.edu/tfxue/), [Andrew Owens](http://andrewowens.com/), [Qiurui He](https://www.linkedin.com/in/qiuruihe), [Jiajun Wu](https://jiajunwu.com/), [Stefanie Mueller](https://hcie.csail.mit.edu/stefanie-mueller.html), [William T. Freeman](https://billf.mit.edu/)<br/>
ACM Symposium on User Interface Software and Technology (**UIST**) 2018

<p align="center">
	<img align="center" src="media/teaser.gif" width="800">
</p>


## Overview

This is the user interface presented in the paper, excluding the first 2D keypoint window. That is, it has two windows, the 3D window and the rendering window, allowing you to interactively explore the estimated 3D models as well as the motion sculpture and to customize their renderings.

### What It Looks Like

To see the interface in action before actually trying it, watch
* 01:01 - 01:15 for the 3D window, and
* 01:31 - 02:22 for the rendering window

of [this YouTube video](https://www.youtube.com/watch?v=LlrzWXzyEvI).

### How It Works

The final compositing runs locally on your computer, but the ingredients for compositing have been pre-computed and stored on our server. If it is the first time that you select a certain rendering configuration, ingredient data will be fetched in the background (a process that may take a few seconds, depending on your internet bandwidth) and cached, in `/tmp/mosculp_gui` (make sure you can write to it!), for instant future viewing.

If your internet connection is fast, this on-demand fetching works fine and amortizes the total downloading time over each click. However, if you have a slow connection, you have the option to pre-download all the ingredient data at the startup, such that there's no downloading wait at each click. See [Running the App](#running-the-app) on how to enable pre-downloading.


## Input Videos

The app is shipped with five clips from the paper: *Ballet-1*, *Ballet-2*, *Olympic*, *Federer*, and *Cartwheel*. For your convenience, each of them is summarized here as a GIF.

|           *Ballet-1*          |           *Ballet-2*          |
|-------------------------------|:-----------------------------:|
| ![](media/input_ballet-1.gif) | ![](media/input_ballet-2.gif) |

|         *Federer*            |            *Cartwheel*         |
|------------------------------|:------------------------------:|
| ![](media/input_federer.gif) | ![](media/input_cartwheel.gif) |

|           *Olympic*          |
|------------------------------|
| ![](media/input_olympic.gif) |


## Dependency Installation

The app was developed and tested on Mac OS, but it should work out of the box on Linux. It requires *internet connection* for the reason discussed above. 

Installing the dependency is a breeze, as the app was built with [Kivy](https://kivy.org/), a popular Python-based library for building user interfaces. We assume Mac OS here.

1. Download and install [Kivy2.app](https://kivy.org/downloads/1.10.1/Kivy-1.10.1_osx10.13.5_builtin_python2_r1.dmg), just like any other `.dmg` app. Make sure to install Kivy 2 (that encapsulates Python 2), instead of Kivy 3 (that encapsulates Python 3).

1. Assuming Kivy has been installed to the default location, i.e., `/Applications/Kivy2.app`, install the following Python packages to the Kivy-bundled Python.
    ```
    source /Applications/Kivy2.app/Contents/Resources/venv/bin/activate
    pip install numpy
    pip install scipy
    pip install Pillow
    deactivate
    ```

1. Symlink `/Applications/Kivy2.app/Contents/Resources/script` to `/usr/local/bin/kivy`
    ```
    sudo ln -s /Applications/Kivy2.app/Contents/Resources/script /usr/local/bin/kivy
    ```
    so that you can invoke the Kivy binary by typing simply `kivy`.


## Running the App

To run the app in its on-demand mode, execute
```
kivy main.py
```
You should see a GUI window popping up, and the terminal window (from which you run the command) printing out what the app is doing at each of your clicks (so that you know what is going on if the GUI gets unresponsive).

In this on-demand mode, each click would require some downloading time plus compositing time. If your internet connectition is not fast enough, try the pre-downloading mode by running, e.g.,
```
kivy main.py Ballet-1
```
which pre-downloads all the ingredient data of *Ballet-1* at the app startup, such that the only wait at each click is for compositing.

While pre-downloading, the GUI will appear all white. Please see the terminal window to check your download speed and progress.

You can also pre-download multiple clips with, e.g.,
```
kivy main.py Ballet-1 Cartwheel
```


## Questions

Please open an issue if you encounter any problem.


## Changelog

* Dec. 25, 2018: Initial Release
