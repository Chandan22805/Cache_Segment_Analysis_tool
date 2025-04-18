import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import OrderedDict, deque
import random

class SetAssociativeCache:
    def __init__(self, cache_size_kb=1, block_size=64, associativity=4, policy="LRU"):
        self.block_size = block_size
        self.associativity = associativity
        self.cache_size_bytes = cache_size_kb * 1024
        self.num_sets = max(1, self.cache_size_bytes // (block_size * associativity))
        self.policy = policy
        
        if policy == "LRU":
            self.cache = [OrderedDict() for _ in range(self.num_sets)]
        elif policy == "FIFO":
            self.cache = [deque(maxlen=associativity) for _ in range(self.num_sets)]
        else:  # Random
            self.cache = [[] for _ in range(self.num_sets)]
            
        self.stats = {
            "hits": 0,
            "misses": 0,
            "cold": 0,
            "conflict": 0,
            "capacity": 0,
            "accesses": 0
        }

    def access(self, address):
        block_num = address // self.block_size
        set_num = block_num % self.num_sets
        self.stats["accesses"] += 1
        
        if self._check_hit(set_num, block_num):
            self.stats["hits"] += 1
            return "hit"
        
        self._handle_miss(set_num, block_num)
        return "miss"

    def _check_hit(self, set_num, block_num):
        if self.policy == "LRU":
            if block_num in self.cache[set_num]:
                self.cache[set_num].move_to_end(block_num)
                return True
        else:
            if block_num in self.cache[set_num]:
                return True
        return False

    def _handle_miss(self, set_num, block_num):
        self._classify_miss(set_num)
        
        if self._is_set_full(set_num):
            self._evict_block(set_num)
            
        if self.policy == "LRU":
            self.cache[set_num][block_num] = True
        elif self.policy == "FIFO":
            self.cache[set_num].append(block_num)
        else:  # Random
            self.cache[set_num].append(block_num)
            
        self.stats["misses"] += 1

    def _is_set_full(self, set_num):
        return len(self.cache[set_num]) >= self.associativity

    def _evict_block(self, set_num):
        if self.policy == "LRU":
            self.cache[set_num].popitem(last=False)
        elif self.policy == "FIFO":
            self.cache[set_num].popleft()
        else:  # Random
            self.cache[set_num].pop(random.randint(0, len(self.cache[set_num])-1))

    def _classify_miss(self, set_num):
        if all(len(s) == 0 for s in self.cache):
            self.stats["cold"] += 1
        elif len(self.cache[set_num]) >= self.associativity:
            self.stats["capacity"] += 1
        else:
            self.stats["conflict"] += 1

    def get_hit_rate(self):
        if self.stats["accesses"] == 0:
            return 0
        return (self.stats["hits"] / self.stats["accesses"]) * 100

class CacheAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Cache Simulator")
        self.root.geometry("1200x700")
        
        # Initialize all variables first
        self.size_slider = None
        self.assoc_slider = None
        self.policy_var = tk.StringVar(value="LRU")
        self.pattern_var = tk.StringVar(value="Random")
        self.stats_labels = {}
        self.set_frames = []
        
        self.cache = SetAssociativeCache()
        self.addresses = []
        self.current_access = 0
        self.running = False
        self.access_patterns = ["Random", "Sequential", "Stride-2", "Stride-4", "Looping"]
        
        self.setup_ui()

    def setup_ui(self):
        self.setup_controls()
        self.setup_cache_display()
        self.setup_stats()

    def setup_controls(self):
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Control buttons
        ttk.Button(control_frame, text="Start", command=self.start).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Step", command=self.step).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        
        # Cache configuration
        ttk.Label(control_frame, text="Cache (KB):").pack(side=tk.LEFT, padx=5)
        self.size_slider = ttk.Scale(control_frame, from_=1, to=16)
        self.size_slider.set(1)
        self.size_slider.pack(side=tk.LEFT)
        
        ttk.Label(control_frame, text="Ways:").pack(side=tk.LEFT, padx=5)
        self.assoc_slider = ttk.Scale(control_frame, from_=1, to=8)
        self.assoc_slider.set(4)
        self.assoc_slider.pack(side=tk.LEFT)
        
        # Policy selection
        ttk.Label(control_frame, text="Policy:").pack(side=tk.LEFT, padx=5)
        policy_menu = ttk.Combobox(control_frame, textvariable=self.policy_var,
                                 values=["LRU", "FIFO", "Random"], state="readonly")
        policy_menu.pack(side=tk.LEFT, padx=5)
        
        # Pattern selection
        ttk.Label(control_frame, text="Pattern:").pack(side=tk.LEFT, padx=5)
        pattern_menu = ttk.Combobox(control_frame, textvariable=self.pattern_var,
                                  values=self.access_patterns, state="readonly")
        pattern_menu.pack(side=tk.LEFT, padx=5)
        
        # Trace file button
        ttk.Button(control_frame, text="Load Trace", command=self.load_trace).pack(side=tk.LEFT, padx=10)
        
        # Configure commands AFTER widgets exist
        self.size_slider.config(command=self.update_cache_config)
        self.assoc_slider.config(command=self.update_cache_config)

    def setup_cache_display(self):
        self.cache_frame = ttk.LabelFrame(self.root, text="Cache Sets (First 8)", padding="10")
        self.cache_frame.pack(fill=tk.BOTH, expand=True)
        
        self.set_frames = []
        for i in range(min(8, self.cache.num_sets)):
            frame = ttk.Frame(self.cache_frame)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            ttk.Label(frame, text=f"Set {i}", font=('Helvetica', 10, 'bold')).pack()
            self.set_frames.append(frame)
            self.update_set_display(i)

    def setup_stats(self):
        self.stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding="10")
        self.stats_frame.pack(fill=tk.X)
        
        stats_grid = ttk.Frame(self.stats_frame)
        stats_grid.pack(fill=tk.X)
        
        self.stats_labels = {
            "hits": ttk.Label(stats_grid, text="Hits: 0"),
            "misses": ttk.Label(stats_grid, text="Misses: 0"),
            "cold": ttk.Label(stats_grid, text="Cold Misses: 0"),
            "conflict": ttk.Label(stats_grid, text="Conflict Misses: 0"),
            "capacity": ttk.Label(stats_grid, text="Capacity Misses: 0"),
            "hit_ratio": ttk.Label(stats_grid, text="Hit Ratio: 0.0%"),
            "accesses": ttk.Label(stats_grid, text="Total Accesses: 0")
        }
        
        for i, (_, label) in enumerate(self.stats_labels.items()):
            label.grid(row=0, column=i, padx=5, pady=5)

    def update_cache_config(self, *args):
        try:
            cache_size = int(self.size_slider.get())
            associativity = int(self.assoc_slider.get())
            policy = self.policy_var.get()
            self.cache = SetAssociativeCache(
                cache_size_kb=cache_size,
                associativity=associativity,
                policy=policy
            )
            self.setup_cache_display()
            self.update_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Configuration error: {str(e)}")

    def update_set_display(self, set_num):
        for widget in self.set_frames[set_num].winfo_children()[1:]:
            widget.destroy()
        
        if self.cache.policy == "LRU":
            blocks = list(self.cache.cache[set_num].keys())
        else:
            blocks = list(self.cache.cache[set_num])
            
        for i, block in enumerate(blocks[:4]):
            block_str = f"0x{block * self.cache.block_size:04X}"
            bg_color = "#d4edda" if i == len(blocks)-1 else "#f8d7da"
            
            label = tk.Label(
                self.set_frames[set_num],
                text=block_str,
                relief=tk.RIDGE,
                width=10,
                bg=bg_color
            )
            label.pack()
            
        if len(blocks) > 4:
            ttk.Label(self.set_frames[set_num], text="...").pack()

    def update_stats(self):
        total = self.cache.stats["accesses"]
        hit_rate = self.cache.get_hit_rate()
        
        self.stats_labels["hits"].config(text=f"Hits: {self.cache.stats['hits']}")
        self.stats_labels["misses"].config(text=f"Misses: {self.cache.stats['misses']}")
        self.stats_labels["cold"].config(text=f"Cold: {self.cache.stats['cold']}")
        self.stats_labels["conflict"].config(text=f"Conflict: {self.cache.stats['conflict']}")
        self.stats_labels["capacity"].config(text=f"Capacity: {self.cache.stats['capacity']}")
        self.stats_labels["hit_ratio"].config(text=f"Hit Ratio: {hit_rate:.1f}%")
        self.stats_labels["accesses"].config(text=f"Total Accesses: {total}")

    def generate_addresses(self, count=1000):
        pattern = self.pattern_var.get()
        if pattern == "Random":
            self.addresses = [random.randint(0, 0xFFFF) for _ in range(count)]
        elif pattern == "Sequential":
            self.addresses = [i * 4 for i in range(count)]
        elif pattern == "Stride-2":
            self.addresses = [i * 8 for i in range(count)]
        elif pattern == "Stride-4":
            self.addresses = [i * 16 for i in range(count)]
        elif pattern == "Looping":
            base = [i * 4 for i in range(16)]
            self.addresses = [base[i % 16] for i in range(count)]

    def load_trace(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filepath:
            try:
                with open(filepath) as f:
                    self.addresses = [int(line.strip(), 16) for line in f if line.strip()]
                messagebox.showinfo("Success", f"Loaded {len(self.addresses)} addresses")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load trace: {str(e)}")

    def step(self):
        if not self.addresses:
            self.generate_addresses()
            
        if self.current_access >= len(self.addresses):
            messagebox.showinfo("Complete", "Reached end of address sequence")
            self.current_access = 0
            
        address = self.addresses[self.current_access]
        result = self.cache.access(address)
        
        set_num = (address // self.cache.block_size) % self.cache.num_sets
        if set_num < len(self.set_frames):
            self.update_set_display(set_num)
        
        self.update_stats()
        self.current_access += 1

    def start(self):
        if not self.running:
            self.running = True
            self.run()

    def stop(self):
        self.running = False

    def run(self):
        if self.running:
            self.step()
            self.root.after(100, self.run)

    def reset(self):
        self.stop()
        self.cache = SetAssociativeCache(
            cache_size_kb=int(self.size_slider.get()),
            associativity=int(self.assoc_slider.get()),
            policy=self.policy_var.get()
        )
        self.current_access = 0
        self.setup_cache_display()
        self.update_stats()

if __name__ == "__main__":
    root = tk.Tk()
    app = CacheAnalyzerGUI(root)
    root.mainloop()