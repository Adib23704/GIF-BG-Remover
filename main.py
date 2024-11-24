from PIL import Image, ImageSequence
from rembg import remove, new_session
import os
from pathlib import Path
import logging
from typing import Union, Optional
import contextlib

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def process_gif(
    input_gif_path: Union[str, Path],
    output_folder: Union[str, Path],
    *,
    keep_temp_files: bool = False,
    model_name: Optional[str] = None
) -> Path:
    """
    Process a GIF file by removing the background from each frame.
    
    Args:
        input_gif_path: Path to the input GIF file
        output_folder: Directory where processed frames will be saved
        keep_temp_files: If True, temporary frame files won't be deleted
        model_name: Specific model to use with rembg (e.g., 'u2net')
    
    Returns:
        Path object pointing to the output directory
    
    Raises:
        FileNotFoundError: If input GIF doesn't exist
        ValueError: If input file is not a GIF
        OSError: If there are issues with file operations
    """
    # Convert paths to Path objects for better path handling
    input_path = Path(input_gif_path)
    output_path = Path(output_folder)
    
    # Validate input
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_path.suffix.lower() != '.gif':
        raise ValueError(f"Input file must be a GIF, got: {input_path.suffix}")
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Processing GIF: {input_path}")
    logging.info(f"Output directory: {output_path}")

    # Create rembg session with specified model
    session = new_session(model_name) if model_name else new_session()
    
    try:
        with Image.open(input_path) as gif:
            frame_count = 0
            duration = gif.info.get('duration', 100)  # Default to 100ms if not specified
            
            for frame in ImageSequence.Iterator(gif):
                frame_count += 1
                logging.debug(f"Processing frame {frame_count}")
                
                # Convert frame to RGBA
                frame = frame.convert("RGBA")
                
                # Prepare file paths
                temp_frame_path = output_path / f"frame_{frame_count:03d}.png"
                output_frame_path = output_path / f"frame_{frame_count:03d}_bg_removed.png"
                
                try:
                    # Save temporary frame
                    frame.save(temp_frame_path, "PNG")
                    
                    # Remove background using the session
                    with open(temp_frame_path, "rb") as input_file:
                        output_data = remove(
                            input_file.read(),
                            session=session  # Use the created session
                        )
                    
                    # Save processed frame
                    with open(output_frame_path, "wb") as output_file:
                        output_file.write(output_data)
                    
                finally:
                    # Clean up temporary file unless keep_temp_files is True
                    if not keep_temp_files:
                        with contextlib.suppress(FileNotFoundError):
                            temp_frame_path.unlink()
            
            logging.info(f"Successfully processed {frame_count} frames")
            return output_path
            
    except Exception as e:
        logging.error(f"Error processing GIF: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process GIF and remove backgrounds from frames")
    parser.add_argument("input_gif", help="Path to input GIF file")
    parser.add_argument("output_dir", help="Output directory for processed frames")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary frame files")
    parser.add_argument("--model", help="Specific model to use with rembg")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(logging.DEBUG if args.debug else logging.INFO)
    
    try:
        process_gif(
            args.input_gif,
            args.output_dir,
            keep_temp_files=args.keep_temp,
            model_name=args.model
        )
    except Exception as e:
        logging.error(f"Failed to process GIF: {str(e)}")
        exit(1)