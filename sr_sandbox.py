import cv2
import numpy as np
from matplotlib import pyplot as plt

def adjust_image_contrast(image, alpha=1.5, beta=0.0):
    """
    Convert image to float and modify contrast

    Args:
    image (numpy.ndarray): Input image
    alpha (float): Contrast control (1.0-3.0 typically)
                   1.0 = original image
                   >1.0 increases contrast
                   <1.0 decreases contrast
    beta (float): Brightness control
                  Added to each pixel value after contrast adjustment

    Returns:
    numpy.ndarray: Contrast-adjusted float image
    """
    # Ensure input is numpy array
    if not isinstance(image, np.ndarray):
        image = np.array(image)

    # Convert to float
    image_float = image.astype(np.float32) / 255.0

    # Apply contrast and brightness
    adjusted = image_float * alpha + beta

    # Clip values to valid range
    adjusted = np.clip(adjusted, 0.0, 1.0)

    return adjusted


def apply_sr_rgb(image, noise_level=0.1):
    """
    Apply stochastic resonance to floating-point image data

    Args:
    image (numpy.ndarray): Input floating-point image (0.0-1.0 range)
    noise_level (float): Standard deviation of noise to add

    Returns:
    numpy.ndarray: Noise-added image with preserved float range
    """
    # Ensure input is float
    if image.dtype != np.float32 and image.dtype != np.float64:
        image = image.astype(np.float32)

    # Split into channels
    channels = cv2.split(image)

    # Apply SR to each channel
    sr_channels = []
    for channel in channels:
        # Generate noise with same data type as input
        noise = np.random.normal(0, noise_level, channel.shape).astype(channel.dtype)

        # Add noise and clip to valid range
        channel_sr = np.clip(channel + noise, 0.0, 1.0)

        sr_channels.append(channel_sr)

    # Merge channels
    return cv2.merge(sr_channels)

def adaptive_sr(image, base_noise=0.1):
    # Calculate local contrast
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    local_std = cv2.boxFilter(np.float32(gray), -1, (21,21))
    
    # Adjust noise level based on local contrast
    noise_map = base_noise * (1.0 - local_std/255.0)
    
    # Apply varying noise levels
    result = np.zeros_like(image)
    for i in range(3):
        channel = image[:,:,i]
        noise = np.random.normal(0, 1, channel.shape) * noise_map
        result[:,:,i] = np.clip(channel + noise, 0, 255).astype(np.uint8)
    
    return result

def main():
    # Read an image
    img = cv2.imread('eyesight_chart.jpg')

    # Adjust contrast
    low_contrast = adjust_image_contrast(img, alpha=0.02, beta=0.18)  # Decrease contrast

    sr_image = apply_sr_rgb(low_contrast, noise_level=0.01)

    # # Visualize
    # plt.figure()
    # plt.imshow(low_contrast)
    # plt.title('Modified contrast')
    # plt.axis('off')
    #
    # plt.figure()
    # plt.imshow(sr_image)
    # plt.title('Modified contrast plus noise')
    # plt.axis('off')
    # plt.show()

    # write to file
    filename = 'results/low_contrast.png'
    cv2.imwrite(filename, low_contrast)

    filename = 'results/low_contrast_sr.png'
    cv2.imwrite(filename,sr_image)


if __name__ == "__main__":
    main()