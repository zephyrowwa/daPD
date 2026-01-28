# analysis/osi_grading.py
"""
Onychomycosis Severity Index (OSI) Scoring and Grading Module.
Analyzes nail segmentation masks and calculates severity score.
"""

import cv2
import numpy as np
from typing import Dict, Tuple, List


class OSIGridAnalyzer:
    """Analyzes nail affected areas using a 4x5 grid overlay."""
    
    def __init__(self, grid_cols=4, grid_rows=5):
        """
        Initialize OSI Grid Analyzer.
        
        Args:
            grid_cols (int): Number of columns in grid (horizontal nail sections)
            grid_rows (int): Number of rows in grid (vertical nail sections)
        """
        self.grid_cols = grid_cols
        self.grid_rows = grid_rows
    
    def detect_nail_contour(self, segmentation_mask: np.ndarray) -> Tuple[np.ndarray, Tuple]:
        """
        Detect the nail contour from segmentation mask.
        
        Args:
            segmentation_mask (np.ndarray): Binary mask of nail
            
        Returns:
            Tuple: (contour, bounding_box)
        """
        # Ensure mask is uint8
        mask_uint8 = (segmentation_mask * 255).astype(np.uint8) if segmentation_mask.max() <= 1 else segmentation_mask.astype(np.uint8)
        
        # Find contours
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, None
        
        # Get largest contour (the nail)
        nail_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(nail_contour)
        
        return nail_contour, (x, y, w, h)
    
    def create_grid_overlay(self, img_height: int, img_width: int, 
                           nail_bbox: Tuple) -> List[List[Tuple]]:
        """
        Create a 4x5 grid overlay on the nail area.
        
        Args:
            img_height (int): Image height
            img_width (int): Image width
            nail_bbox (Tuple): (x, y, width, height) of nail
            
        Returns:
            List[List[Tuple]]: Grid cells as list of rectangles
        """
        x, y, w, h = nail_bbox
        
        # Calculate cell dimensions
        cell_width = w / self.grid_cols
        cell_height = h / self.grid_rows
        
        grid = []
        for row in range(self.grid_rows):
            row_cells = []
            for col in range(self.grid_cols):
                # Calculate cell coordinates
                x1 = int(x + col * cell_width)
                y1 = int(y + row * cell_height)
                x2 = int(x + (col + 1) * cell_width)
                y2 = int(y + (row + 1) * cell_height)
                
                row_cells.append(((x1, y1), (x2, y2)))
            grid.append(row_cells)
        
        return grid
    
    def analyze_grid_cells(self, segmentation_mask: np.ndarray, 
                          affected_mask: np.ndarray, grid: List[List[Tuple]]) -> Dict:
        """
        Analyze each grid cell for infection percentage.
        
        Args:
            segmentation_mask (np.ndarray): Binary mask of nail
            affected_mask (np.ndarray): Binary mask of affected areas
            grid (List[List[Tuple]]): Grid cell coordinates
            
        Returns:
            Dict: Analysis results with area percentage and proximity info
        """
        total_nail_area = np.sum(segmentation_mask > 0)
        total_affected_area = np.sum(affected_mask > 0)
        
        # Calculate area percentage - handle zero nail area gracefully
        if total_nail_area > 0:
            area_percent = (total_affected_area / total_nail_area * 100)
            # Clamp to 0-100 range just in case of floating point errors
            area_percent = max(0, min(100, area_percent))
        else:
            # No nail detected - treat as healthy
            area_percent = 0

        # Determine proximity level (1=distal/tip, 5=proximal/base)
        # Find the topmost affected pixel (closest to base for typical nail orientation)
        affected_rows = np.where(np.any(affected_mask > 0, axis=1))[0]
        
        if len(affected_rows) == 0:
            # No affected area - distal only
            proximity_level = 1
        else:
            # Normalize affected rows to grid rows
            affected_top = affected_rows[0]  # Topmost affected pixel
            max_row = affected_mask.shape[0]
            
            # Handle edge case of very small image
            if max_row <= 0:
                proximity_level = 1
            else:
                # Map to proximity level (1-5)
                # Assuming nail grows from proximal (top) to distal (bottom)
                proximity_ratio = affected_top / max_row
                
                if proximity_ratio > 0.8:
                    proximity_level = 1  # Distal quarter
                elif proximity_ratio > 0.6:
                    proximity_level = 2  # Second quarter
                elif proximity_ratio > 0.4:
                    proximity_level = 3  # Third quarter
                elif proximity_ratio > 0.2:
                    proximity_level = 4  # Proximal quarter
                else:
                    proximity_level = 5  # Matrix involvement
        
        # Final safety check - ensure proximity_level is always 1-5
        proximity_level = max(1, min(5, proximity_level))
        
        return {
            "area_percent": area_percent,
            "proximity_level": proximity_level,
            "total_nail_area_px": int(total_nail_area),
            "affected_area_px": int(total_affected_area)
        }


def get_osi_score(area_percent: float, proximity_level: int) -> Dict:
    """
    Calculates the Onychomycosis Severity Index (OSI) score and classification.
    
    Parameters:
    - area_percent (float): The percentage of the nail plate affected (0-100).
    - proximity_level (int): The horizontal quarter of the nail affected (1-5).
        1: Distal quarter
        2: Second quarter
        3: Third quarter
        4: Proximal quarter
        5: Matrix involvement (lunula/proximal fold)
        
    Returns:
    - dict: A dictionary containing the numeric score and severity classification.
    """
    
    # Sanitize inputs - clamp to valid ranges instead of rejecting
    # This ensures ALL nails get scored, preventing "Unable to calculate grading"
    area_percent = max(0, min(100, float(area_percent)))
    proximity_level = max(1, min(5, int(proximity_level)))
    
    # 1. Determine Area Score (A)
    if area_percent == 0:
        area_score = 0
    elif 1 <= area_percent <= 10:
        area_score = 1
    elif 11 <= area_percent <= 25:
        area_score = 2
    elif 26 <= area_percent <= 50:
        area_score = 3
    elif 51 <= area_percent <= 75:
        area_score = 4
    else:  # 76 <= area_percent <= 100
        area_score = 5

    # 2. Proximity Score (P) - already clamped to 1-5
    proximity_score = proximity_level

    # 3. Calculate Final Score
    # Formula: Score = Area Score * Proximity Score
    total_score = area_score * proximity_score

    # 4. Determine Severity Category
    if total_score == 0:
        severity = "Clinically Cured / No involvement"
    elif 1 <= total_score <= 5:
        severity = "Mild"
    elif 6 <= total_score <= 15:
        severity = "Moderate"
    else:  # 16 to 25 (max possible)
        severity = "Severe"

    return {
        "area_score": area_score,
        "proximity_score": proximity_score,
        "total_osi_score": total_score,
        "severity": severity,
        "area_percent": area_percent,
        "proximity_level": proximity_level
    }


def draw_grid_on_image(image: np.ndarray, grid: List[List[Tuple]], 
                      affected_mask: np.ndarray = None,
                      cell_info: Dict = None) -> np.ndarray:
    """
    Draw OSI grid overlay on nail image.
    
    Args:
        image (np.ndarray): Input image (BGR)
        grid (List[List[Tuple]]): Grid cell coordinates
        affected_mask (np.ndarray): Optional mask showing affected areas
        cell_info (Dict): Optional cell-by-cell analysis info
        
    Returns:
        np.ndarray: Image with grid overlay
    """
    output = image.copy()
    
    # Color scheme
    grid_color = (0, 255, 0)  # Green for grid lines
    affected_color = (0, 0, 255)  # Red for affected areas
    grid_thickness = 3  # Thicker grid for visibility
    
    # Draw grid cells with thicker lines
    for row in grid:
        for (x1, y1), (x2, y2) in row:
            # Draw rectangle with thicker border
            cv2.rectangle(output, (x1, y1), (x2, y2), grid_color, grid_thickness)
    
    # Highlight affected areas if mask provided
    if affected_mask is not None:
        affected_mask_uint8 = (affected_mask * 255).astype(np.uint8) if affected_mask.max() <= 1 else affected_mask.astype(np.uint8)
        # Create a semi-transparent red overlay for infected areas
        affected_overlay = np.zeros_like(output, dtype=np.uint8)
        affected_overlay[affected_mask_uint8 > 127] = [0, 0, 255]  # Red in BGR
        # Blend the overlay with the original image
        output = cv2.addWeighted(output, 0.85, affected_overlay, 0.25, 0)
    
    return output


def process_nail_for_grading(cropped_nail_image: np.ndarray, 
                            segmentation_mask: np.ndarray,
                            affected_mask: np.ndarray,
                            nail_bbox_from_detection: Tuple = None) -> Dict:
    """
    Complete pipeline: analyze nail and return OSI score.
    
    Args:
        cropped_nail_image (np.ndarray): Cropped nail image
        segmentation_mask (np.ndarray): Nail segmentation mask
        affected_mask (np.ndarray): Affected area mask
        nail_bbox_from_detection (Tuple): Optional nail bounding box from detection (x1, y1, x2, y2)
        
    Returns:
        Dict: Contains OSI score, grid visualization, and analysis
    """
    analyzer = OSIGridAnalyzer(grid_cols=4, grid_rows=5)
    
    # Ensure masks are uint8
    if segmentation_mask.dtype != np.uint8:
        seg_mask_uint8 = (segmentation_mask * 255).astype(np.uint8) if segmentation_mask.max() <= 1 else segmentation_mask.astype(np.uint8)
    else:
        seg_mask_uint8 = segmentation_mask
    
    if affected_mask is not None and affected_mask.dtype != np.uint8:
        aff_mask_uint8 = (affected_mask * 255).astype(np.uint8) if affected_mask.max() <= 1 else affected_mask.astype(np.uint8)
    else:
        aff_mask_uint8 = affected_mask
    
    # Use nail_bbox from detection if provided, otherwise detect from contour
    if nail_bbox_from_detection is not None:
        x1, y1, x2, y2 = nail_bbox_from_detection
        nail_bbox = (x1, y1, x2 - x1, y2 - y1)  # Convert to (x, y, w, h) format
        print(f"  [DEBUG] Using nail bbox from detection: {nail_bbox}")
    else:
        # Detect nail contour
        nail_contour, nail_bbox = analyzer.detect_nail_contour(seg_mask_uint8)
        
        # If contour detection fails, use full image as bounding box
        if nail_bbox is None:
            print("  [WARNING] Contour detection failed, using full image bounds")
            h, w = cropped_nail_image.shape[:2]
            nail_bbox = (0, 0, w, h)
    
    # Create grid overlay
    grid = analyzer.create_grid_overlay(
        cropped_nail_image.shape[0],
        cropped_nail_image.shape[1],
        nail_bbox
    )
    
    # Analyze grid cells
    grid_analysis = analyzer.analyze_grid_cells(seg_mask_uint8, aff_mask_uint8, grid)
    
    # Calculate OSI score
    osi_result = get_osi_score(
        grid_analysis["area_percent"],
        grid_analysis["proximity_level"]
    )
    
    # Draw grid on image - use a copy to avoid modifying original
    grid_image = draw_grid_on_image(
        cropped_nail_image.copy(),
        grid,
        aff_mask_uint8
    )
    
    # Create nail class segmentation overlay with 70% transparency (30% opaque)
    nail_segmentation_viz = cropped_nail_image.copy()
    
    # Create white overlay for nail class segmentation
    nail_overlay = np.zeros_like(nail_segmentation_viz, dtype=np.uint8)
    nail_overlay[seg_mask_uint8 > 127] = (255, 255, 255)  # White for nail
    
    # Blend with 30% opacity (70% transparent)
    nail_segmentation_viz = cv2.addWeighted(nail_segmentation_viz, 0.7, nail_overlay, 0.3, 0)
    
    return {
        "osi_score": osi_result,
        "grid_analysis": grid_analysis,
        "grid_visualization": grid_image,
        "nail_segmentation_visualization": nail_segmentation_viz,
        "grid_coordinates": grid,
        "nail_bbox": nail_bbox
    }
