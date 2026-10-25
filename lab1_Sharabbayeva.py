"""
Practical 1 - Mini smart-room agent  (STUDENT Maftuna Sharabbayeva)
Software Design in Intelligent Systems (ITD2104) - Lecture 1

Your job: complete the five layers marked TODO.
  acquire -> process -> rules -> decide -> act
Everything else (room physics, the day loop, plotting) is already written.
The file runs as it is, but the agent does nothing yet ("idle" all day).

Run:  python lab1_Sharabbayeva.py        (needs matplotlib:  pip install matplotlib)
"""
import math
import random

import matplotlib
matplotlib.use("Agg")                      # save plots without opening a window
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- settings
STEPS_PER_HOUR = 4                         # one step = 15 minutes
STEPS = 24 * STEPS_PER_HOUR                # one day. There are 4 steps per hour. 24 hours × 4 = 96 steps
TIMETABLE = [(9.0, 10.5), (11.0, 12.5), (14.0, 15.5)]   # class times (hours) 09:00–10:30; 11:00–12:30; 14:00–15:30
COMFORT = (20.0, 24.0)                     # comfortable range while occupied, degrees C. means the comfortable temperature is: 20°C to 24°C.
CO2_LIMIT = 1000                           # ppm means CO₂ above 1000 ppm is considered bad air.
PREHEAT_HOURS = 1.0                        # start heating 1 hour before a class
FAULT_RATE = 0.05                          # 5% faulty sensor readings


# ---------------------------------------------------------------- environment (given to students)
def outdoor_temp(hour):
    """Cool autumn day: about 2 degrees C at night, 14 degrees C in the afternoon."""
    return 8 + 6 * math.sin((hour - 9) / 24 * 2 * math.pi)


def is_occupied(hour, timetable):
    return any(start <= hour < end for start, end in timetable)


def environment_step(room, action, hour, occupied):
    """Physics of the room for 15 minutes. Returns energy used in kWh."""
    out = outdoor_temp(hour)
    room["temp"] += 0.07 * (out - room["temp"])          # heat loss to outside
    room["co2"] += 0.05 * (420 - room["co2"])            # slow natural air exchange
    if occupied:                                          # people add heat and CO2
        room["temp"] += 0.2
        room["co2"] += 110
    energy = 0.0
    if action == "heat":
        room["temp"] += 1.9
        energy = 1.5
    elif action == "cool":
        room["temp"] -= 1.0
        energy = 1.2
    elif action == "ventilate":
        room["co2"] -= 300
        room["temp"] += 0.04 * (out - room["temp"])
        energy = 0.2
    room["co2"] = max(room["co2"], 400)
    return energy


# ---------------------------------------------------------------- layer 1: data acquisition
def acquire(step, room, timetable, sensor_offset=0.0):              
    """Read the sensors for this 15-minute step.
    Return a dict: step, hour, temp, co2, occupied.
    step → current 15-minute step; room → actual room state; timetable → class schedule; sensor_offset → possible sensor drift
    """
    hour = step / STEPS_PER_HOUR                                        #hour = step / STEPS_PER_HOUR
    """
    For example:
       step 0  → 0:00
       step 4  → 1:00
       step 36 → 9:00
       step 56 → 14:00 """

    temp = room["temp"] + random.gauss(0, 0.3) + sensor_offset          
    """temp = true room temperature + random noise (random.gauss(0, 0.3)) + sensor_offset
    true temperature + random noise + possible sensor error"""

    co2 = room["co2"] + random.gauss(0, 30)                             #co2  = true CO2 + random noise (random.gauss(0, 30))

    if random.random() < FAULT_RATE:                                    #with probability FAULT_RATE replace temp by a faulty value (-99.0 or 150.0)
        temp = random.choice([-99.0, 150.0])

    occupied = is_occupied(hour, timetable)                             #occupied = is_occupied(hour, timetable)
    return {"step": step, "hour": hour, "temp": temp, "co2": co2,
            "occupied": occupied}



# ---------------------------------------------------------------- layer 2: processing & features; "Can I trust the sensor data?"
def process(raw, history):
    """Clean the raw reading and build features.
    Return a dict: hour, temp, co2, occupied, trend, faulty.
    """
    faulty = raw["temp"] < -30.0 or raw["temp"] > 60.0                  #faulty = temperature outside the realistic range -30..60 degrees C
    """
    If temperature is:
        -99°C → faulty
        150°C → faulty
    But:
        21°C → good
        35°C → good
    """

    if faulty:                                              #if faulty, use the last good temperature from history (or 20.0 at the start)
        temp = 20.0
        for previous in reversed(history):                  #It finds the last good temperature. That's called using historical information to clean the data
            if not previous["faulty"]:
                temp = previous["temp"]
                break
    else:
        temp = raw["temp"]

    previous_temp = history[-1]["temp"] if history else temp                   
    trend = temp - previous_temp                                        #trend = current temperature minus previous temperature
    """This tells us whether temperature is increasing or decreasing.
    For example:
        Previous = 19°C
        Current  = 21°C
         trend = 21 - 19 = +2°C
    So the room is getting warmer.
    The practical calls this layer data cleaning and feature building.
    """

    return {"hour": raw["hour"], "temp": temp, "co2": raw["co2"],
            "occupied": raw["occupied"], "trend": trend, "faulty": faulty}



# ---------------------------------------------------------------- layer 3: knowledge (rules) "What situation are we in?"
def rules(f, timetable, occupancy_model=None):
    """Apply comfort rules. Return a dict of True/False flags:
    expected_use, too_cold, too_hot, bad_air, frost.
    """
    hour = f["hour"]                                                

    if occupancy_model is not None:
        step = int(round(hour * STEPS_PER_HOUR))                      #expected_use: room is occupied now OR a class starts within PREHEAT_HOURS
        step = max(0, min(STEPS - 1, step))                           #too_cold / too_hot: expected_use and temperature near the edge of COMFORT (20-24)
        current_expected = occupancy_model[step] > 0.5                #bad_air: room occupied and CO2 > CO2_LIMIT
        future_expected = any(                                        #frost: room not expected to be used and temperature < 14 (protect the building)
            occupancy_model[s] > 0.5                                  #BONUS: if occupancy_model is given, use the learned probabilities instead of the timetable
            for s in range(
                step + 1,
                min(STEPS, step + int(PREHEAT_HOURS * STEPS_PER_HOUR) + 1)
            )
        )
        expected_use = current_expected or future_expected             
    else:                                                               
        expected_use = f["occupied"] or any(
            hour <= start <= hour + PREHEAT_HOURS
            for start, _ in timetable
        )

    low, high = COMFORT

    # A 1 °C safety buffer compensates for noisy sensor readings and helps
    # keep the true room temperature inside the required comfort band.
    too_cold = expected_use and f["temp"] < low + 1.0               #Comfort starts at: 20°C. So the agent starts heating when: temperature < 21°C
    too_hot = expected_use and f["temp"] > high - 1.0               # Comfort ends at: 24°C. So cooling starts when: temperature > 23°C
    bad_air = f["occupied"] and f["co2"] > CO2_LIMIT                #If: people are inside AND CO₂ > 1000 ppm then: bad_air = True
    frost = (not expected_use) and f["temp"] < 14.0                 
    #If nobody is expected to use the room and temperature falls below 14°C, the system protects the building by heating.
                                                                    

    return {"expected_use": expected_use, "too_cold": too_cold, "too_hot": too_hot,
            "bad_air": bad_air, "frost": frost}



# ---------------------------------------------------------------- layer 4: decision
def decide(f, r):
    """Choose ONE action: "heat", "cool", "ventilate" or "idle".
    """
    # Fresh air has priority, but only when ventilation should not make
    # the room too cold.
    if r["bad_air"] and f["temp"] >= COMFORT[0]:      #If the air is bad and the room isn't too cold: VENTILATE
        return "ventilate"
    if r["frost"] or r["too_cold"]:                   #If the room needs protection or is too cold: HEAT
        return "heat"
    if r["too_hot"]:                                  #If too hot: COOL
        return "cool"
    return "idle"



# ---------------------------------------------------------------- layer 5: actuation + feedback
def act(room, action, hour, occupied, log_row):
    """Send the action to the room (environment_step) and record feedback.
    Already done for you: energy, true temperature/CO2 and comfort violation.
    """
    energy = environment_step(room, action, hour, occupied)
    low, high = COMFORT
    """
    In simple words: "Were people inside while the actual temperature was outside 20–24°C?"
    If yes: comfort violation = True
    """
    violation = occupied and not (low <= room["temp"] <= high)   # judged on the TRUE temperature
    log_row.update({"action": action, "energy": energy, "true_temp": room["temp"],
                    "true_co2": room["co2"], "violation": violation})    
    return energy


# ---------------------------------------------------------------- one simulated day
def run_day(sensor_offset=0.0, real_timetable=TIMETABLE, known_timetable=TIMETABLE,
            occupancy_model=None, seed=1):
    random.seed(seed)
    room = {"temp": 16.0, "co2": 450.0}
    history, log = [], []
    for step in range(STEPS):
        raw = acquire(step, room, real_timetable, sensor_offset)
        f = process(raw, history)
        r = rules(f, known_timetable, occupancy_model)
        action = decide(f, r)
        row = dict(f)
        row["step_i"] = step
        row["frost_mode"] = r["frost"]
        act(room, action, f["hour"], raw["occupied"], row)
        history.append(f)
        log.append(row)
    energy = sum(x["energy"] for x in log)
    violations = sum(x["violation"] for x in log)
    faulty = sum(x["faulty"] for x in log)
    wasted = sum(x["energy"] for x in log if x["action"] in ("heat", "cool") and not x["occupied"] and not x["frost_mode"]
                 and not any(y["occupied"] for y in log[x["step_i"]:x["step_i"] + int(PREHEAT_HOURS * STEPS_PER_HOUR) + 1]))
    return log, energy, violations, faulty, wasted


# ---------------------------------------------------------------- bonus: learn occupancy from past days
def learn_occupancy(past_logs):
    """Return the share of past days in which each 15-minute slot was occupied."""
    if not past_logs:
        return [0.0] * STEPS

    probabilities = []
    for step in range(STEPS):
        occupied_count = sum(1 for log in past_logs if log[step]["occupied"])
        probabilities.append(occupied_count / len(past_logs))
    return probabilities



# ---------------------------------------------------------------- plotting
def plot_day(log, title, path):
    hours = [x["hour"] for x in log]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1.4]})
    for x in log:                                          # shade occupied time
        if x["occupied"]:
            ax1.axvspan(x["hour"], x["hour"] + 0.25, color="#DCE6F2", lw=0)
    ax1.axhspan(*COMFORT, color="#E3F4EB", alpha=0.8, lw=0, label="Comfort 20-24 °C")
    ax1.plot(hours, [x["true_temp"] for x in log], color="#1F3864", lw=2, label="Room temperature (true)")
    ax1.plot(hours, [outdoor_temp(h) for h in hours], color="#8793A8", lw=1.2, ls="--", label="Outdoor")
    colors = {"heat": "#C0392B", "cool": "#1F6FB2", "ventilate": "#2E7D32"}
    for a, c in colors.items():
        pts = [(x["hour"], x["true_temp"]) for x in log if x["action"] == a]
        if pts:
            ax1.scatter(*zip(*pts), s=22, color=c, zorder=3, label=a.capitalize())
    ax1.set_ylabel("°C")
    ax1.set_title(title)
    ax1.legend(loc="upper left", fontsize=8, ncol=3, frameon=False)
    ax2.plot(hours, [x["true_co2"] for x in log], color="#6A3D9A", lw=1.8)
    ax2.axhline(CO2_LIMIT, color="#C55A11", ls=":", lw=1.2)
    ax2.set_ylabel("CO₂ ppm")
    ax2.set_xlabel("Hour of day")
    ax2.set_xticks(range(0, 25, 2))
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------- main
if __name__ == "__main__":   # Part B -> run 1, Part C -> runs 2 and 3, Bonus -> run 4
    def report(name, result):
        _, e, v, bad, w = result
        print(f"{name:<34} energy = {e:5.1f} kWh | wasted = {w:4.1f} kWh | comfort violations = {v:2d} | faulty removed = {bad}")

    base = run_day()
    report("1) Baseline", base)
    plot_day(base[0], "Smart-room agent - baseline day", "lab1_output_baseline.png")

    report("2) Drift: sensor reads +3 °C", run_day(sensor_offset=3.0))

    moved = [(9.0, 10.5), (11.0, 12.5), (18.0, 19.5)]     # afternoon class moved to 18:00
    drift = run_day(real_timetable=moved, known_timetable=TIMETABLE)
    report("3) Drift: class moved to 18:00", drift)
    plot_day(drift[0], "Drift - class moved to 18:00, agent still uses the old timetable", "lab1_output_drift.png")

    past = [run_day(real_timetable=moved, seed=s)[0] for s in range(10, 15)]   # 5 previous days
    model = learn_occupancy(past)
    report("4) Bonus: occupancy learned", run_day(real_timetable=moved, occupancy_model=model))
