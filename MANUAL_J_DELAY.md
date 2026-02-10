# J-Delay v1.0 - Manual

**Author:** Marco Herglotz
**License:** GPLv3

## Overview
**J-Delay** is a professional latency compensation tool for the JACK Audio Connection Kit. It allows you to delay specific audio input signals by a precise amount of milliseconds to synchronize hybrid setups (Software + Hardware).

## Key Features
*   **Zero-Latency Pass-Through:** Core processing adds no overhead when delay is 0ms.
*   **Persistent Connection:** Solves Windows "Pipe Busy" errors by keeping the client connection alive in the background.
*   **Dynamic Channel Management:** Add/Remove stereo pairs on the fly (+2/-2 Ch).
*   **Stereo Linking:** Link faders for channel pairs (1&2, 3&4...).
*   **Preset System:** 8 Preset Slots to save and load complete setups (Names + Delays + Channel Count).
*   **Auto-Save:** The application remembers your last state (Channel names, delay values) automatically.
*   **Smart Status:** Visual feedback (Red/Green/Yellow LED) for connection status.

## Quick Start
1.  **Install:** Ensure Python 3 (with "Add to PATH") and JACK (QJackCtl) are installed.
2.  **Launch:** Double-click `run_j_delay.bat`. It auto-installs dependencies on first run.
3.  **Activate:** Click the **ACTIVATE** button to register ports in the JACK Graph.

## Configuration & Usage

### 1. Channel Management
*   **[-2 Ch] / [+2 Ch]:** Buttons in the header add or remove stereo pairs.
*   **Rename:** Enable the **"Edit Names"** checkbox, then click on any channel label to rename it (e.g., "Kick", "Snare").

### 2. Presets (1-8)
The header contains 8 preset buttons.
*   **Left-Click:** Load Preset.
*   **Right-Click:** Save current setup to this slot.

### 3. Setting Delay
*   **Slider:** Drag for coarse adjustment (0 - 1000 ms).
*   **Input Field:** Type exact value (e.g. `12.34`) and press Enter.
*   **Link:** Check the "Link" box to couple odd/even channels.

## Technical Details
*   **Config File:** Settings are stored in `J-Delay.ini`.
*   **Buffers:** Uses efficient circular buffers (Ringbuffer) for glitch-free audio delay.
*   **Command Line Arguments:**
    *   `-c <N>`: Force N channels.
    *   `-d <ms>`: Set initial delay.
    *   `-a`: Autostart activation.

---
*Created by Marco Herglotz for the JACK Audio Community.*
