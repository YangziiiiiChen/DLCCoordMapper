import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import cv2
from calibration_tool import InteractiveCalibrationTool

def main():
    root = tk.Tk()
    root.title("DeepLabCut Video Calibration Tool")
    root.geometry("400x300")

    info_frame = tk.Frame(root)
    info_frame.pack(expand=True, fill='both', padx=20, pady=20)
    tk.Label(info_frame, text="DeepLabCut Video Calibration Tool", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(info_frame, text="Calibrate camera using coordinates output from DeepLabCut", font=("Arial", 10)).pack(pady=5)
    tk.Label(info_frame, text="World coordinate range: (0,0) to (75,75)", font=("Arial", 10)).pack(pady=5)

    calibrator = InteractiveCalibrationTool()

    csv_path = filedialog.askopenfilename(
        title="Select DeepLabCut CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not csv_path or not calibrator.load_csv(csv_path):
        root.destroy()
        return

    if not calibrator.select_bodypart(root):
        root.destroy()
        return

    video_path = filedialog.askopenfilename(
        title="Select corresponding video file",
        filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"), ("All files", "*.*")]
    )
    if not video_path or not calibrator.load_video(video_path):
        root.destroy()
        return

    root.withdraw()
    if calibrator.run_calibration(root):
        H = calibrator.calculate_homography()
        if H is not None:
            root.deiconify()
            save = messagebox.askyesno("Save Calibration", "Do you want to save the calibration data?", parent=root)
            if save:
                save_path = filedialog.asksaveasfilename(
                    title="Save calibration data",
                    defaultextension=".pkl",
                    filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")]
                )
                if save_path:
                    calibrator.save_calibration_data(save_path, H)

    root.destroy()

if __name__ == "__main__":
    main()
