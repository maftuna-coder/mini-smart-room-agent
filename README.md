# Mini Smart-Room Agent

A Python-based intelligent smart-room agent that demonstrates sensor processing, rule-based decision-making, and adaptation to changing conditions.

## Project Overview

This project simulates an intelligent agent that monitors room temperature and CO₂ levels and makes decisions to improve indoor comfort and air quality.

## Features

- **Sensor simulation** — Processes room temperature and CO₂ readings.
- **Rule-based decisions** — Selects actions such as heating, cooling, and ventilation.
- **Comfort monitoring** — Compares room temperature with a target comfort range.
- **Data drift detection** — Demonstrates how an agent's behavior can become less effective when a timetable or environment changes.
- **Visual analysis** — Includes baseline and drift experiment graphs.

## Technologies Used

- Python
- Data visualization
- Rule-based intelligent systems
- Sensor simulation

## Project Files

- `lab1_Sharabbayeva.py` — Python implementation.
- `lab1_output_baseline.png` — Baseline experiment results.
- `lab1_output_drift.png` — Results after a timetable change.
- `lab1_report_Maftuna_Sharabbayeva.pdf` — Project report.

## Results

The baseline experiment demonstrates the agent's behavior under its original schedule. The drift experiment illustrates how a change in the room's schedule can cause the agent to act at an inappropriate time.

## How to Run

1. Install Python 3.
2. Download or clone this repository.
3. Run the Python file:

```bash
python lab1_Sharabbayeva.py
```

## Author

Maftuna Sharabbaeva

## Disclaimer

This project is an educational simulation of an intelligent agent and is not a production-ready smart-home control system.

## Visual Results

### Baseline Day

This graph shows the smart-room agent's baseline behavior, including room temperature, outdoor temperature, CO₂ levels, and heating, cooling, and ventilation actions.

![Smart-room agent baseline results](https://github.com/maftuna-coder/mini-smart-room-agent/blob/main/lab1_output_baseline.png)

### Schedule Drift

This graph demonstrates how changing the class schedule to 18:00 affects the agent when it continues following its original timetable.

![Smart-room agent schedule drift results](https://github.com/maftuna-coder/mini-smart-room-agent/blob/main/lab1_output_drift.png)

### Analysis

The baseline and drift experiments illustrate why intelligent agents need to detect environmental or schedule changes and adapt their decisions accordingly.
