import cv2
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional

class WeatherCondition(Enum):
    CLEAR = 1
    RAIN = 2
    FOG = 3
    SNOW = 4

class TimeOfDay(Enum):
    DAY = 1
    DAWN_DUSK = 2
    NIGHT = 3

@dataclass
class DrivingConditions:
    weather: WeatherCondition
    time_of_day: TimeOfDay
    vehicle_speed: float  # km/h
    ambient_light: float  # lux, typical range 0-100000
    
class AdaptiveSR:
    def __init__(self):
        self.base_noise_level = 0.1
        self.max_noise_level = 0.3
        
        # Parameters for different conditions
        self.weather_factors = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 1.2,
            WeatherCondition.FOG: 1.5,
            WeatherCondition.SNOW: 1.3
        }
        
        self.time_factors = {
            TimeOfDay.DAY: 0.8,
            TimeOfDay.DAWN_DUSK: 1.2,
            TimeOfDay.NIGHT: 1.5
        }
        
    def detect_local_conditions(self, frame: np.ndarray) -> Tuple[float, float]:
        """
        Analyze frame to detect local lighting and contrast conditions
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate local statistics
        mean_brightness = np.mean(gray) / 255.0
        local_contrast = np.std(gray) / 255.0
        
        return mean_brightness, local_contrast
    
    def calculate_noise_level(self, 
                            conditions: DrivingConditions,
                            local_brightness: float,
                            local_contrast: float) -> float:
        """
        Calculate adaptive noise level based on all conditions
        """
        # Base adjustment from driving conditions
        weather_factor = self.weather_factors[conditions.weather]
        time_factor = self.time_factors[conditions.time_of_day]
        
        # Speed factor - increase noise reduction at higher speeds
        speed_factor = 1.0 + (conditions.vehicle_speed / 130.0) * 0.2  # normalized to typical highway speed
        
        # Light factor - inverse relationship with ambient light
        light_factor = 1.0 + (1.0 - np.clip(conditions.ambient_light / 50000.0, 0, 1)) * 0.5
        
        # Local image characteristics
        brightness_factor = 1.0 + (1.0 - local_brightness) * 0.3
        contrast_factor = 1.0 + (1.0 - local_contrast) * 0.4
        
        # Combine all factors
        noise_level = self.base_noise_level * (
            weather_factor *
            time_factor *
            speed_factor *
            light_factor *
            brightness_factor *
            contrast_factor
        )
        
        return np.clip(noise_level, self.base_noise_level, self.max_noise_level)
    
    def apply_sr(self, 
                 frame: np.ndarray, 
                 conditions: DrivingConditions,
                 roi: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Apply adaptive SR to frame
        roi: Optional (x, y, width, height) for region of interest
        """
        if roi:
            x, y, w, h = roi
            region = frame[y:y+h, x:x+w]
        else:
            region = frame
            
        # Detect local conditions
        local_brightness, local_contrast = self.detect_local_conditions(region)
        
        # Calculate adaptive noise level
        noise_level = self.calculate_noise_level(
            conditions, local_brightness, local_contrast
        )
        
        # Apply SR with bilateral filtering for edge preservation
        result = frame.copy()
        
        if roi:
            # Process only ROI
            processed = self._apply_sr_to_region(region, noise_level)
            result[y:y+h, x:x+w] = processed
        else:
            # Process entire frame
            result = self._apply_sr_to_region(frame, noise_level)
            
        return result
    
    def _apply_sr_to_region(self, region: np.ndarray, noise_level: float) -> np.ndarray:
        """
        Apply SR to specific region with edge preservation
        """
        # Split into channels
        b, g, r = cv2.split(region)
        
        processed_channels = []
        for channel in [b, g, r]:
            # Generate noise
            noise = np.random.normal(0, noise_level * 255, channel.shape)
            
            # Add noise
            noisy = np.clip(channel + noise, 0, 255).astype(np.uint8)
            
            # Apply bilateral filter to preserve edges
            filtered = cv2.bilateralFilter(noisy, 9, 75, 75)
            
            processed_channels.append(filtered)
        
        return cv2.merge(processed_channels)

# Example usage
def process_video_stream(video_source: int = 0):
    cap = cv2.VideoCapture(video_source)
    sr_processor = AdaptiveSR()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Simulate changing driving conditions
        conditions = DrivingConditions(
            weather=WeatherCondition.CLEAR,
            time_of_day=TimeOfDay.DAY,
            vehicle_speed=60.0,  # km/h
            ambient_light=50000.0  # mid-day
        )
        
        # Process frame with SR
        processed = sr_processor.apply_sr(frame, conditions)
        
        # Optional: Process only road area ROI
        # road_roi = (0, frame.shape[0]//2, frame.shape[1], frame.shape[0]//2)
        # processed = sr_processor.apply_sr(frame, conditions, roi=road_roi)
        
        cv2.imshow('Processed', processed)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    process_video_stream()
