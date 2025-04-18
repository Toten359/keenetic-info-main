#!/usr/bin/env python3
import subprocess
import re
import argparse
import json

def analyze_camera_stream(camera_url):
    """
    Analyze a camera stream using ffprobe to get fps, bitrate, and resolution.
    
    Args:
        camera_url (str): URL of the camera stream (e.g., rtsp://192.168.1.100:554/stream)
        
    Returns:
        dict: Dictionary containing fps, bitrate, and resolution information
    """
    try:
        # Run ffprobe command to get stream information in JSON format
        cmd = [
            'ffprobe', 
            '-v', 'error',
            '-select_streams', 'v:0',  # Select video stream
            '-show_entries', 'stream=width,height,r_frame_rate,bit_rate',
            '-of', 'json',
            camera_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        # Parse the JSON output
        data = json.loads(result.stdout)
        
        if 'streams' not in data or not data['streams']:
            raise Exception("No video stream found")
        
        stream_info = data['streams'][0]
        
        # Extract resolution
        width = stream_info.get('width')
        height = stream_info.get('height')
        resolution = f"{width}x{height}" if width and height else "Unknown"
        
        # Extract fps (comes as a fraction like "30000/1001")
        fps = "Unknown"
        if 'r_frame_rate' in stream_info:
            fps_fraction = stream_info['r_frame_rate']
            if '/' in fps_fraction:
                num, den = map(int, fps_fraction.split('/'))
                fps = round(num / den, 2)
            else:
                fps = float(fps_fraction)
        
        # Extract bitrate (comes in bits/s)
        bitrate = "Unknown"
        if 'bit_rate' in stream_info:
            bitrate_bps = int(stream_info['bit_rate'])
            bitrate = f"{bitrate_bps / 1000:.2f} kbps"
        
        return {
            "resolution": resolution,
            "fps": fps,
            "bitrate": bitrate
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout while connecting to camera"}
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Analyze web camera stream properties')
    parser.add_argument('url', help='Camera stream URL (e.g., rtsp://192.168.1.100:554/stream)')
    args = parser.parse_args()
    
    print(f"Analyzing camera stream at: {args.url}")
    result = analyze_camera_stream(args.url)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nCamera Stream Properties:")
        print(f"Resolution: {result['resolution']}")
        print(f"FPS: {result['fps']}")
        print(f"Bitrate: {result['bitrate']}")

if __name__ == "__main__":
    main()
