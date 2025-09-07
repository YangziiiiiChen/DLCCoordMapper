import cv2
import numpy as np
import pandas as pd
import os
import pickle
from tkinter import messagebox
from dialogs import CoordinateInputDialog, BodyPartSelectionDialog
from typing import Optional, Tuple

class InteractiveCalibrationTool:
    def __init__(self):
        self.video_path = None
        self.csv_path = None
        self.cap = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.dlc_data = None
        self.selected_bodypart = None
        self.bodyparts = []
        self.calibration_points = []
        self.window_name = "DeepLabCut Calibration Tool - Space: Pause, C: Add calibration point"
        self.current_frame_img = None
        self.root = None
        self.inputting_coordinates = False

    def load_csv(self, csv_path: str) -> bool:
        """Load DeepLabCut CSV file"""
        try:
            self.csv_path = csv_path
            self.dlc_data = pd.read_csv(csv_path, header=[0, 1, 2])
            self.bodyparts = list(self.dlc_data.columns.get_level_values(1).unique())
            self.bodyparts = [bp for bp in self.bodyparts if bp and bp != 'coords']
            
            print("CSV file loaded successfully:")
            print(f"  Path: {csv_path}")
            print(f"  Number of rows: {len(self.dlc_data)}")
            print(f"  Body parts: {self.bodyparts}")
            return True
        except Exception as e:
            print(f"Failed to load CSV file: {e}")
            return False
    
    def select_bodypart(self, root) -> bool:
        """Select the body part to calibrate"""
        if not self.bodyparts:
            messagebox.showerror("Error", "No body part data found in CSV file", parent=root)
            return False
        
        dialog = BodyPartSelectionDialog(root, self.bodyparts)
        root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.selected_bodypart = dialog.result
            print(f"Selected body part: {self.selected_bodypart}")
            return True
        else:
            print("No body part selected")
            return False
    
    def get_dlc_coordinate(self, frame_num: int) -> Optional[Tuple[float, float, float]]:
        """Get DeepLabCut coordinates for a specific frame"""
        if self.dlc_data is None or self.selected_bodypart is None:
            return None
        if frame_num >= len(self.dlc_data):
            return None
        try:
            scorer = self.dlc_data.columns.get_level_values(0)[0]
            x = self.dlc_data.loc[frame_num, (scorer, self.selected_bodypart, 'x')]
            y = self.dlc_data.loc[frame_num, (scorer, self.selected_bodypart, 'y')]
            try:
                likelihood = self.dlc_data.loc[frame_num, (scorer, self.selected_bodypart, 'likelihood')]
                return (float(x), float(y), float(likelihood))
            except:
                return (float(x), float(y), 1.0)
        except Exception as e:
            print(f"Failed to get coordinates for frame {frame_num}: {e}")
            return None
    
    def load_video(self, video_path: str) -> bool:
        """Load video file"""
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"Cannot open video file: {video_path}")
            return False
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        print("Video loaded successfully:")
        print(f"  Total frames: {self.total_frames}")
        print(f"  FPS: {self.fps:.2f}")
        return True
    
    def add_calibration_point(self):
        """Add the current frame as a calibration point"""
        if self.inputting_coordinates:
            return
        self.inputting_coordinates = True
        dlc_coord = self.get_dlc_coordinate(self.current_frame)
        if dlc_coord is None:
            messagebox.showerror("Error", f"Cannot get DeepLabCut coordinates for frame {self.current_frame}", parent=self.root)
            self.inputting_coordinates = False
            return
        if len(dlc_coord) > 2 and dlc_coord[2] < 0.5:
            if not messagebox.askyesno("Low confidence warning", 
                f"Frame {self.current_frame} has low confidence ({dlc_coord[2]:.3f}). Use anyway?", 
                parent=self.root):
                self.inputting_coordinates = False
                return
        dialog = CoordinateInputDialog(self.root, self.current_frame, dlc_coord)
        self.root.wait_window(dialog.dialog)
        if dialog.result is not None:
            world_coord = dialog.result
            pixel_coord = (dlc_coord[0], dlc_coord[1])
            self.calibration_points.append((world_coord, pixel_coord, self.current_frame))
            print(f"Added calibration point {len(self.calibration_points)}: "
                  f"Frame {self.current_frame}, World ({world_coord[0]:.1f}, {world_coord[1]:.1f}) -> "
                  f"Pixel ({pixel_coord[0]:.1f}, {pixel_coord[1]:.1f})")
        else:
            print("Cancelled adding calibration point")
        self.inputting_coordinates = False
    
    def draw_calibration_info(self, frame):
        """Draw calibration info on the frame"""
        display_frame = frame.copy()
        current_dlc_coord = self.get_dlc_coordinate(self.current_frame)
        if current_dlc_coord:
            x, y = int(current_dlc_coord[0]), int(current_dlc_coord[1])
            cv2.circle(display_frame, (x, y), 8, (255, 255, 0), 2)
            cv2.circle(display_frame, (x, y), 3, (255, 255, 0), -1)
            coord_text = f"{self.selected_bodypart}: ({x}, {y})"
            if len(current_dlc_coord) > 2:
                coord_text += f" conf:{current_dlc_coord[2]:.3f}"
            cv2.putText(display_frame, coord_text, (x+15, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        for i, (world_coord, pixel_coord, frame_num) in enumerate(self.calibration_points):
            x, y = int(pixel_coord[0]), int(pixel_coord[1])
            if frame_num == self.current_frame:
                color = (0, 255, 0)
                cv2.circle(display_frame, (x, y), 10, color, 3)
            else:
                color = (0, 0, 255)
                cv2.circle(display_frame, (x, y), 6, color, 2)
            cv2.circle(display_frame, (x, y), 2, color, -1)
            label = f"P{i+1}({world_coord[0]:.1f},{world_coord[1]:.1f})"
            cv2.putText(display_frame, label, (x+12, y-8), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        if self.inputting_coordinates:
            info_text = "Please input world coordinates in popup..."
            color = (0, 255, 255)
        else:
            info_text = f"Current body part: {self.selected_bodypart} ({len(self.calibration_points)} points added)"
            color = (0, 255, 0) if len(self.calibration_points) >= 4 else (0, 165, 255)
        cv2.putText(display_frame, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        frame_info = f"Frame: {self.current_frame}/{self.total_frames}"
        cv2.putText(display_frame, frame_info, (10, display_frame.shape[0] - 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        controls_info = "Space: Play/Pause | C: Add point | A/D: Step | R: Remove last | ESC: Exit"
        cv2.putText(display_frame, controls_info, (10, display_frame.shape[0] - 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        status_info = f"Calibration points: {len(self.calibration_points)}"
        if len(self.calibration_points) >= 4:
            status_info += " (ready to compute matrix)"
            status_color = (0, 255, 0)
        else:
            status_info += " (need at least 4)"
            status_color = (0, 165, 255)
        cv2.putText(display_frame, status_info, (10, display_frame.shape[0] - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        coordinate_info = "World coordinate range: (0,0) to (75,75)"
        cv2.putText(display_frame, coordinate_info, (10, display_frame.shape[0] - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        csv_info = f"CSV: {os.path.basename(self.csv_path) if self.csv_path else 'None'}"
        cv2.putText(display_frame, csv_info, (10, display_frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        return display_frame
    
    def get_current_frame(self):
        """Get current frame"""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        if ret:
            self.current_frame_img = frame
            return frame
        return None
    
    def run_calibration(self, root):
        """Run interactive calibration"""
        if not self.cap or not self.cap.isOpened():
            print("Please load a video file first")
            return False
        if self.dlc_data is None or self.selected_bodypart is None:
            print("Please load CSV file and select a body part first")
            return False
        self.root = root
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        print(f"\nCalibration started - Body part: {self.selected_bodypart}")
        print("Controls:")
        print("  - Space: Play/Pause video")
        print("  - A/D: Step backward/forward")
        print("  - C: Add current frame as calibration point (using DLC coords)")
        print("  - R: Remove last calibration point")
        print("  - ESC: Exit calibration")
        print("  - World coordinate range: (0,0) to (75,75)")
        print("  - Recommended: choose 4-15 evenly distributed points\n")
        playing = True
        while True:
            if playing and not self.inputting_coordinates:
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame = 0
                    continue
                self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.current_frame_img = frame
            else:
                frame = self.get_current_frame()
                if frame is None:
                    break
            display_frame = self.draw_calibration_info(frame)
            cv2.imshow(self.window_name, display_frame)
            wait_time = 30 if (playing and not self.inputting_coordinates) else 1
            key = cv2.waitKey(wait_time) & 0xFF
            if key == 27:
                if not self.inputting_coordinates:
                    break
            elif key == ord(' '):
                if not self.inputting_coordinates:
                    playing = not playing
                    print("Video playing" if playing else "Video paused")
            elif key in [ord('c'), ord('C')]:
                if not playing:
                    self.add_calibration_point()
                else:
                    print("Pause the video before adding calibration point")
            elif key in [ord('d'), ord('D')]:
                if not playing and not self.inputting_coordinates and self.current_frame < self.total_frames - 1:
                    self.current_frame += 1
            elif key in [ord('a'), ord('A')]:
                if not playing and not self.inputting_coordinates and self.current_frame > 0:
                    self.current_frame -= 1
            elif key in [ord('r'), ord('R')]:
                if not self.inputting_coordinates and len(self.calibration_points) > 0:
                    removed_point = self.calibration_points.pop()
                    print(f"Removed calibration point: Frame {removed_point[2]}, "
                          f"World ({removed_point[0][0]:.1f}, {removed_point[0][1]:.1f})")
        cv2.destroyAllWindows()
        print(f"\nCalibration finished! Total {len(self.calibration_points)} points:")
        for i, (world_coord, pixel_coord, frame_num) in enumerate(self.calibration_points):
            print(f"  P{i+1}: Frame {frame_num}, World ({world_coord[0]:.1f}, {world_coord[1]:.1f}) -> "
                  f"Pixel ({pixel_coord[0]:.1f}, {pixel_coord[1]:.1f})")
        return len(self.calibration_points) >= 4
    
    def calculate_homography(self) -> Optional[np.ndarray]:
        """Compute homography matrix from calibration points"""
        if len(self.calibration_points) < 4:
            print("Not enough calibration points to compute homography")
            return None
        pixel_points = [point[1] for point in self.calibration_points]
        world_points = [point[0] for point in self.calibration_points]
        pixel_array = np.array(pixel_points, dtype=np.float32)
        world_array = np.array(world_points, dtype=np.float32)
        H, _ = cv2.findHomography(pixel_array, world_array, cv2.RANSAC)
        print("\nCalibration accuracy check:")
        print("ID | Frame | World coords      | Pixel coords      | Converted        | Error")
        print("-" * 75)
        errors = []
        for i, (world_coord, pixel_coord, frame_num) in enumerate(self.calibration_points):
            pixel_array = np.array([[pixel_coord[0], pixel_coord[1]]], dtype=np.float32).reshape(-1, 1, 2)
            converted = cv2.perspectiveTransform(pixel_array, H)
            converted_coord = (converted[0][0][0], converted[0][0][1])
            error = np.sqrt((converted_coord[0] - world_coord[0])**2 + 
                            (converted_coord[1] - world_coord[1])**2)
            errors.append(error)
            print(f"{i+1:2d} | {frame_num:4d} | ({world_coord[0]:6.1f}, {world_coord[1]:6.1f}) | "
                  f"({pixel_coord[0]:6.1f}, {pixel_coord[1]:6.1f}) | "
                  f"({converted_coord[0]:6.1f}, {converted_coord[1]:6.1f}) | {error:5.2f}")
        avg_error = np.mean(errors)
        max_error = np.max(errors)
        print("-" * 75)
        print(f"Average error: {avg_error:.2f}")
        print(f"Max error: {max_error:.2f}")
        if avg_error > 2.0:
            print("Warning: Average error is high, check calibration point accuracy")
        elif avg_error < 0.5:
            print("Excellent calibration accuracy!")
        else:
            print("Good calibration accuracy")
        return H
    
    def save_calibration_data(self, filename: str, homography_matrix: np.ndarray):
        """Save calibration data"""
        data = {
            'video_path': self.video_path,
            'csv_path': self.csv_path,
            'selected_bodypart': self.selected_bodypart,
            'fps': self.fps,
            'calibration_points': self.calibration_points,
            'homography_matrix': homography_matrix.tolist() if homography_matrix is not None else None
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f"Calibration data saved to: {filename}")
