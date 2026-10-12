"""Display a click-through agent pointer without moving the Windows cursor. MIT."""
import ctypes, json, sys, tkinter as tk

args = json.load(sys.stdin)
x, y = int(args["x"]), int(args["y"])
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg="#010101")
root.wm_attributes("-transparentcolor", "#010101")
root.geometry(f"92x52+{x-18}+{y-18}")
canvas = tk.Canvas(root, width=92, height=52, bg="#010101", highlightthickness=0)
canvas.pack()
canvas.create_oval(5, 5, 31, 31, fill="#31d9ff", outline="white", width=3)
canvas.create_text(49, 18, text="AGENT", fill="#31d9ff", anchor="w", font=("Segoe UI", 9, "bold"))
root.update_idletasks()
hwnd = root.winfo_id()
GWL_EXSTYLE = -20
WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x80000, 0x20, 0x80, 0x08000000
u = ctypes.windll.user32
style = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
u.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
root.after(int(args.get("duration_ms", 900)), root.destroy)
root.mainloop()
print(json.dumps({"agent_pointer_shown": True, "target": [x, y], "system_cursor_moved": False}))
