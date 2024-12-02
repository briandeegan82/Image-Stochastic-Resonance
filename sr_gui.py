import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageEnhance, ImageTk, ImageFilter
import numpy as np


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
        self.load_button.pack(side=tk.LEFT, padx=5)

        # Noise type selection
        tk.Label(self.load_frame, text="Noise Type:").pack(side=tk.LEFT, padx=5)
        self.noise_type_var = tk.StringVar(value="Gaussian")
        self.noise_type_dropdown = ttk.Combobox(
            self.load_frame,
            textvariable=self.noise_type_var,
            values=[
                "Gaussian",
                "Salt and Pepper",
                "Speckle",
                "Uniform",
                "Exponential"
            ],
            state="readonly",
            width=15
        )
        self.noise_type_dropdown.pack(side=tk.LEFT, padx=5)
        self.noise_type_dropdown.bind('<<ComboboxSelected>>', self.update_modifications)

        # Adjusted (brightness and contrast) image display
        self.adjusted_frame = tk.Frame(master, borderwidth=1, relief=tk.SUNKEN)
        self.adjusted_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.adjusted_frame.grid_rowconfigure(2, weight=1)
        self.adjusted_frame.grid_columnconfigure(0, weight=1)

        self.adjusted_label = tk.Label(self.adjusted_frame, text="Brightness & Contrast Adjusted Image")
        self.adjusted_label.grid(row=0, column=0)

        self.adjusted_image_label = tk.Label(self.adjusted_frame)
        self.adjusted_image_label.grid(row=1, column=0, sticky="nsew")

        # Adjustment sliders for adjusted image
        self.adjustment_frame = tk.Frame(self.adjusted_frame)
        self.adjustment_frame.grid(row=2, column=0, pady=10)

        # Brightness slider
        tk.Label(self.adjustment_frame, text="Brightness").grid(row=0, column=0, padx=5)
        self.brightness_slider = tk.Scale(
            self.adjustment_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
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
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_modifications
        )
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, padx=5)

        # Processed (noise added) image display
        self.processed_frame = tk.Frame(master, borderwidth=1, relief=tk.SUNKEN)
        self.processed_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.processed_frame.grid_rowconfigure(2, weight=1)
        self.processed_frame.grid_columnconfigure(0, weight=1)

        self.processed_label = tk.Label(self.processed_frame, text="Brightness, Contrast & Noise Adjusted Image")
        self.processed_label.grid(row=0, column=0)

        self.processed_image_label = tk.Label(self.processed_frame)
        self.processed_image_label.grid(row=1, column=0, sticky="nsew")

        # Noise slider for processed image
        self.noise_frame = tk.Frame(self.processed_frame)
        self.noise_frame.grid(row=2, column=0, pady=10)

        tk.Label(self.noise_frame, text="Noise Intensity").pack(side=tk.LEFT)
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
        self.adjusted_pil_image = None
        self.last_width = 1200
        self.last_height = 900

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

        # Resize and display original image first
        display_size = (display_width, display_height)

        # Apply brightness and contrast modifications
        self.adjusted_pil_image = self.apply_bc_modifications(
            self.original_pil_image,
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            display_size
        )
        self.adjusted_photo = ImageTk.PhotoImage(self.adjusted_pil_image)
        self.adjusted_image_label.config(image=self.adjusted_photo)

        # Apply brightness, contrast, and noise modifications
        processed_display = self.apply_image_modifications(
            self.original_pil_image,
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            self.noise_slider.get(),
            display_size,
            self.noise_type_var.get()
        )
        self.processed_photo = ImageTk.PhotoImage(processed_display)
        self.processed_image_label.config(image=self.processed_photo)

    def apply_bc_modifications(self, pil_image, brightness_value, contrast_value, target_size):
        """Apply brightness and contrast modifications to an image"""
        # Apply brightness
        brightness_enhancer = ImageEnhance.Brightness(pil_image)
        brightness_image = brightness_enhancer.enhance(float(brightness_value))

        # Apply contrast
        contrast_enhancer = ImageEnhance.Contrast(brightness_image)
        contrast_image = contrast_enhancer.enhance(float(contrast_value))

        # Resize
        final_image = contrast_image.resize(target_size, Image.LANCZOS)

        return final_image

    def apply_image_modifications(self, pil_image, brightness_value, contrast_value, noise_value, target_size, noise_type):
        """Apply brightness, contrast, and noise modifications to an image"""
        # Apply brightness and contrast
        brightness_enhancer = ImageEnhance.Brightness(pil_image)
        brightness_image = brightness_enhancer.enhance(float(brightness_value))

        contrast_enhancer = ImageEnhance.Contrast(brightness_image)
        contrast_image = contrast_enhancer.enhance(float(contrast_value))

        # Convert to numpy array
        noise_image = np.array(contrast_image)

        # Generate noise based on selected type
        if noise_type == "Gaussian":
            # Standard Gaussian (normal) noise
            noise = np.random.normal(0, float(noise_value) * 255, noise_image.shape).astype(np.uint8)
        elif noise_type == "Salt and Pepper":
            # Salt and pepper noise
            noise_mask = np.random.random(noise_image.shape[:2])  # 2D noise mask
            salt_mask = noise_mask < float(noise_value) / 2
            pepper_mask = noise_mask > 1 - float(noise_value) / 2

            # Initialize salt_pepper_noise to match noise_image
            salt_pepper_noise = np.zeros_like(noise_image)

            # Apply salt and pepper noise masks
            if len(noise_image.shape) == 2:  # Grayscale image
                salt_pepper_noise[salt_mask] = 255
                salt_pepper_noise[pepper_mask] = 0
            elif len(noise_image.shape) == 3:  # RGB image
                # Expand salt_mask and pepper_mask to match RGB channels
                salt_pepper_noise[salt_mask, :] = 255
                salt_pepper_noise[pepper_mask, :] = 0

            print("salt_pepper_noise shape:", salt_pepper_noise.shape)
            print("noise_image shape:", noise_image.shape)

            # Apply salt and pepper noise
            noise_image = np.where(salt_pepper_noise != 0, salt_pepper_noise, noise_image)
            noise = np.zeros_like(noise_image)  # Reset noise (if needed elsewhere)


        elif noise_type == "Speckle":
            # Multiplicative noise
            noise = np.random.normal(0, float(noise_value), noise_image.shape)
            noise_image = (noise_image * (1 + noise)).astype(np.uint8)
            noise = np.zeros_like(noise_image)
        elif noise_type == "Uniform":
            # Uniform noise
            noise = np.random.uniform(-float(noise_value) * 255, float(noise_value) * 255, noise_image.shape).astype(np.uint8)
        elif noise_type == "Exponential":
            # Exponential noise
            noise = np.random.exponential(float(noise_value) * 255, noise_image.shape).astype(np.uint8)
        else:
            # Default to Gaussian if unknown type
            noise = np.random.normal(0, float(noise_value) * 255, noise_image.shape).astype(np.uint8)

        # Apply noise
        if noise_type not in ["Salt and Pepper", "Speckle"]:
            noisy_image = np.clip(noise_image + noise, 0, 255).astype(np.uint8)
        else:
            noisy_image = noise_image

        # Convert back to PIL Image
        final_image = Image.fromarray(noisy_image)

        # Resize
        final_image = final_image.resize(target_size, Image.LANCZOS)

        return final_image

    def update_modifications(self, event=None):
        """Update image modifications based on slider values"""
        if self.original_pil_image is not None:
            self.display_images()


def main():
    root = tk.Tk()
    app = PsychophysicsTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()