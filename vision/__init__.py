"""Occupancy detection module: simulated feeds and optional YOLO detection."""

from .occupancy_detector import SimulatedOccupancyDetector, YOLOPersonCounter

__all__ = ["SimulatedOccupancyDetector", "YOLOPersonCounter"]
