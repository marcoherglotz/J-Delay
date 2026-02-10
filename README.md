# J-Delay

**JACK Audio Input Latency Compensator**  
*By Marco Herglotz*

![License](https://img.shields.io/badge/license-GPLv3-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

**J-Delay** is a lightweight, persistent latency compensation tool designed for the **JACK Audio Connection Kit**. It solves synchronization issues in hybrid setups (Software + Hardware) by allowing precise millisecond delay adjustments for input channels.

Specially optimized for **Windows** to prevent "Pipe Busy" errors.

---

## Features

*   🎛 **Precision Delay:** Adjust delay from 0.00 to 1000.00 ms via Slider or Text Input.
*   🔗 **Stereo Linking:** Link faders for odd/even channel pairs.
*   🔄 **Dynamic Channels:** Add/Remove channels on the fly (up to 128+).
*   💾 **Auto-Save & Presets:** Remembers your settings and offers 8 Preset Slots.
*   🛡 **Persistent Connection:** Keeps the JACK client alive in the background to prevent Windows named pipe errors.
*   🚦 **Smart Status:** Visual feedback for connection status (Ready/Running/Error).

## Installation

### Prerequisites
*   **Python 3** (Make sure to check "Add to PATH" during installation).
*   **JACK Audio Connection Kit** (e.g., QJackCtl).

### Quick Start (Windows)
1.  Download the repository.
2.  Double-click `run_j_delay.bat`.
3.  The script will automatically install required dependencies (`JACK-Client`, `numpy`) and launch the GUI.

### Manual Start (Linux/macOS)
```bash
pip install JACK-Client numpy
python J-Delay.py
```

## Usage

1.  Start **JACK** (QJackCtl).
2.  Launch **J-Delay**.
3.  Click **ACTIVATE** to register ports in the graph.
4.  Connect your audio source to `j_delay:in_X` and `j_delay:out_X` to your destination.
5.  Adjust the sliders until your audio is synchronized.

## Configuration

Settings (Channel count, Names, Delays) are automatically saved to `J-Delay.ini`.

**Custom Channel Names:**
Enable the "Edit Names" checkbox in the header, then double-click a channel label to rename it (e.g., "Kick Drum").

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the **GNU General Public License v3.0**.
