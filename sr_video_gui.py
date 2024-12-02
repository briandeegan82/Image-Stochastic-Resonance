import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageEnhance, ImageTk, ImageFilter
import numpy as np
import time
import random


class PsychophysicsTestApp:
    def __init__(self, master):
        self.master = master
        master.title("Psychophysics Image Test")
        master.geometry("1200x900")

        # Configure grid layout
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

        # Image loading frame
        self.load_frame = tk.Frame(master)
        self.load_frame.grid(row=0, column=0, columnspan=2, pady=10)

        self.load_button = tk.Button(self.load_frame, text="Load Image", command=self.load_image)
        self.load_button.pack()

        # Original image display
        self.original_frame = tk.Frame(master, borderwidth=1, relief=tk.SUNKEN)
        self.original_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.original_frame.grid_rowconfigure(2, weight=1)
        self.original_frame.grid_columnconfigure(0, weight=1)

        self.original_label = tk.Label(self.original_frame, text="Original Image")
        self.original_label.grid(row=0, column=0)

        self.original_image_label = tk.Label(self.original_frame)
        self.original_image_label.grid(row=1, column=0, sticky="nsew")

        # Adjustment sliders for original image
        self.adjustment_frame = tk.Frame(self.original_frame)
        self.adjustment_frame.grid(row=2, column=0, pady=10)

        # Brightness slider
        tk.Label(self.adjustment_frame, text="Brightness").grid(row=0, column=0, padx=5)
        self.brightness_slider = tk.Scale(
            self.adjustment_frame,
            from_=0.0,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_modifications
        )
        self.brightness_slider.set(1.0)
        self.brightness_slider.grid(row=0, column=1, padx=5)

        # Contrast slider
        tk.Label(self.adjustment_frame, text="Contrast").grid(row=1, column=0, padx=5)
        self.contrast_slider = tk.Scale(
            self.adjustment_frame,
            from_=0.0,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_modifications
        )
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, padx=5)

        # Processed image display
        self.processed_frame = tk.Frame(master, borderwidth=1, relief=tk.SUNKEN)
        self.processed_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.processed_frame.grid_rowconfigure(2, weight=1)
        self.processed_frame.grid_columnconfigure(0, weight=1)

        self.processed_label = tk.Label(self.processed_frame, text="Processed Image")
        self.processed_label.grid(row=0, column=0)

        self.processed_image_label = tk.Label(self.processed_frame)
        self.processed_image_label.grid(row=1, column=0, sticky="nsew")

        # Noise slider for processed image
        self.noise_frame = tk.Frame(self.processed_frame)
        self.noise_frame.grid(row=2, column=0, pady=10)

        tk.Label(self.noise_frame, text="Noise").pack(side=tk.LEFT)
        self.noise_slider = tk.Scale(
            self.noise_frame,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_modifications
        )
        self.noise_slider.set(0.0)
        self.noise_slider.pack(side=tk.LEFT)

        # Bind resize event
        master.bind('<Configure>', self.on_resize)

        # Initial state
        self.original_pil_image = None
        self.processed_pil_image = None
        self.last_width = 1200
        self.last_height = 900

        # Noise update variables
        self.noise_update_interval = 66  # ~15 times per second (1000ms / 15)
        self.is_noise_updating = False
        self.noise_seed = None

    def on_resize(self, event):
        """Handle window resize events"""
        # Only resize if the window size has changed significantly
        if (abs(event.width - self.last_width) > 50 or
                abs(event.height - self.last_height) > 50):
            self.last_width = event.width
            self.last_height = event.height

            # Reprocess images if they exist
            if self.original_pil_image is not None:
                self.display_images()

    def load_image(self):
        """Open file dialog to load an image"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            # Load the original image
            self.original_pil_image = Image.open(file_path)

            # Display images
            self.display_images()

    def display_images(self):
        """Display images scaled to current window size"""
        if self.original_pil_image is None:
            return

        # Stop any ongoing noise updates
        self.stop_noise_updates()

        # Calculate display dimensions
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()

        # Divide window width by 2 to accommodate two images
        display_width = (window_width - 40) // 2  # Subtract padding

        # Calculate height maintaining aspect ratio
        original_aspect = self.original_pil_image.width / self.original_pil_image.height
        display_height = int(display_width / original_aspect)

        # Ensure height doesn't exceed window height
        max_height = window_height - 250  # Leave room for buttons and sliders
        if display_height > max_height:
            display_height = max_height
            display_width = int(display_height * original_aspect)

        # Resize and display original image
        original_display = self.original_pil_image.copy()
        original_display = original_display.resize((display_width, display_height), Image.LANCZOS)
        self.original_photo = ImageTk.PhotoImage(original_display)
        self.original_image_label.config(image=self.original_photo)

        # Create a copy for processing
        self.processed_pil_image = self.original_pil_image.copy()

        # Apply current brightness, contrast, and noise settings
        self.target_size = (display_width, display_height)
        self.noise_seed = random.randint(0, 2 ** 32 - 1)  # Use Python's random module

        # Start periodic noise updates
        self.start_noise_updates()

    def apply_image_modifications(self, pil_image, brightness_value, contrast_value, noise_value, target_size,
                                  noise_seed=None):
        """Apply brightness, contrast, and noise modifications to an image"""
        # Apply brightness
        brightness_enhancer = ImageEnhance.Brightness(pil_image)
        brightness_image = brightness_enhancer.enhance(float(brightness_value))

        # Apply contrast
        contrast_enhancer = ImageEnhance.Contrast(brightness_image)
        contrast_image = contrast_enhancer.enhance(float(contrast_value))

        # Convert to numpy array for noise
        noise_image = np.array(contrast_image)

        # Use provided noise seed if available
        if noise_seed is not None:
            np.random.seed(noise_seed)

        # Generate and add noise
        noise = np.random.normal(0, float(noise_value) * 255, noise_image.shape).astype(np.uint8)
        noisy_image = np.clip(noise_image + noise, 0, 255).astype(np.uint8)

        # Convert back to PIL Image
        final_image = Image.fromarray(noisy_image)

        # Resize
        final_image = final_image.resize(target_size, Image.LANCZOS)

        return final_image

    def start_noise_updates(self):
        """Start periodic noise updates"""
        if not self.is_noise_updating:
            self.is_noise_updating = True
            self.update_noise_periodically()

    def stop_noise_updates(self):
        """Stop periodic noise updates"""
        self.is_noise_updating = False

    def update_noise_periodically(self):
        """Update noise image periodically"""
        if not self.is_noise_updating or self.original_pil_image is None:
            return

        # Apply current modifications with new noise seed
        self.noise_seed = random.randint(0, 2 ** 32 - 1)  # Use Python's random module
        processed_display = self.apply_image_modifications(
            self.processed_pil_image,
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            self.noise_slider.get(),
            self.target_size,
            self.noise_seed
        )
        self.processed_photo = ImageTk.PhotoImage(processed_display)
        self.processed_image_label.config(image=self.processed_photo)

        # Schedule next update
        self.master.after(self.noise_update_interval, self.update_noise_periodically)

    def update_modifications(self, value):
        """Update image modifications based on slider values"""
        if self.original_pil_image is not None:
            # Stop current updates
            self.stop_noise_updates()

            # Restart periodic updates
            self.start_noise_updates()


def main():
    root = tk.Tk()
    app = PsychophysicsTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()