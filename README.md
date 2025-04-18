A Python-based GUI tool for visualizing and analyzing set-associative CPU cache behavior.
📌 Features

✔ Interactive cache simulation with configurable:

    Cache size (1KB–16KB)

    Associativity (1–8 ways)

    Replacement policies (LRU, FIFO, Random)
    ✔ Real-time visualization of cache segments (sets)
    ✔ Memory access patterns: Sequential, Random, Stride, Looping
    ✔ Trace file support for real-world workload analysis
    ✔ Miss classification: Cold, Conflict, Capacity misses

🚀 Quick Start

    Install Python 3.8+

    Run the simulator:
    bash

    python cache_simulator.py

🖥️ GUI Overview
1. Control Panel

    Start/Stop/Step: Control simulation flow

    Sliders: Adjust cache size and associativity

    Dropdowns: Select replacement policy and access pattern

    Load Trace: Import memory addresses from a .txt file

2. Cache Segment Display

    Shows first 8 cache sets

    Color-coded blocks:

        🟢 Green: Most Recently Used (MRU) block

        🔴 Red: Other blocks in the set

3. Statistics Panel
Metric	Description
Hits	Successful cache accesses
Misses	Failed cache accesses
Cold Misses	First access to a memory block
Conflict Misses	Block evicted despite set not being full
Capacity Misses	Block evicted because set was full
Hit Ratio	Percentage of accesses that were hits
📂 Trace File Format

Provide a .txt file with one hexadecimal address per line:
plaintext

0x1000  
0x1004  
0x2008  
...  

📊 Example Workflow

    Set cache to 4KB, 4-way LRU

    Select "Sequential" access pattern

    Click Start

    Observe:

        Segment occupancy in real-time

        Miss types and hit ratio

🛠️ Dependencies

    Python 3.8+

    tkinter (included in Python standard library)
