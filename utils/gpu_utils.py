import subprocess
import platform
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)

class GPUDetector:
    def __init__(self):
        self.intel_gpu = False
        self.amd_gpu = False
        self.nvidia_gpu = False
        self.opencl_support = False
        self.available_encoders = []
        self.available_decoders = []
        self.detect_hardware()
    
    def detect_hardware(self):
        """Detect available GPU hardware and capabilities"""
        self._detect_gpus()
        self._detect_opencl()
        self._detect_ffmpeg_codecs()
        self._log_detection_results()
    
    def _detect_gpus(self):
        """Detect available GPU hardware"""
        try:
            # Check for Intel GPU
            if platform.system() == "Windows":
                # Windows GPU detection
                try:
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                          capture_output=True, text=True, timeout=10)
                    gpu_info = result.stdout.lower()
                    if 'intel' in gpu_info:
                        self.intel_gpu = True
                    if 'amd' in gpu_info or 'radeon' in gpu_info:
                        self.amd_gpu = True
                    if 'nvidia' in gpu_info or 'geforce' in gpu_info:
                        self.nvidia_gpu = True
                except:
                    pass
            else:
                # Linux GPU detection
                try:
                    # Check lspci for GPU info
                    result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
                    gpu_info = result.stdout.lower()
                    if 'intel' in gpu_info and ('vga' in gpu_info or 'display' in gpu_info):
                        self.intel_gpu = True
                    if ('amd' in gpu_info or 'radeon' in gpu_info) and ('vga' in gpu_info or 'display' in gpu_info):
                        self.amd_gpu = True
                    if ('nvidia' in gpu_info or 'geforce' in gpu_info) and ('vga' in gpu_info or 'display' in gpu_info):
                        self.nvidia_gpu = True
                except:
                    pass
                
                # Additional check for Intel GPU via /proc/cpuinfo
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpu_info = f.read().lower()
                        if 'intel' in cpu_info:
                            # Most modern Intel CPUs have integrated graphics
                            self.intel_gpu = True
                except:
                    pass
        except Exception as e:
            logging.warning(f"GPU detection failed: {e}")
    
    def _detect_opencl(self):
        """Detect OpenCL support"""
        try:
            # Try to import OpenCV and check OpenCL support
            import cv2
            if hasattr(cv2, 'ocl') and cv2.ocl.haveOpenCL():
                self.opencl_support = True
                # Enable OpenCL for OpenCV
                cv2.ocl.setUseOpenCL(True)
        except ImportError:
            # OpenCV not available, try alternative detection
            try:
                # Check for OpenCL libraries
                if platform.system() == "Windows":
                    opencl_paths = [
                        "C:\\Windows\\System32\\OpenCL.dll",
                        "C:\\Windows\\SysWOW64\\OpenCL.dll"
                    ]
                else:
                    opencl_paths = [
                        "/usr/lib/x86_64-linux-gnu/libOpenCL.so",
                        "/usr/lib/libOpenCL.so",
                        "/usr/local/lib/libOpenCL.so"
                    ]
                
                for path in opencl_paths:
                    if os.path.exists(path):
                        self.opencl_support = True
                        break
            except:
                pass
    
    def _detect_ffmpeg_codecs(self):
        """Detect available FFmpeg hardware encoders and decoders"""
        try:
            # Check for hardware encoders
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, timeout=10)
            encoder_output = result.stdout.lower()
            
            # Intel Quick Sync Video encoders
            if 'h264_qsv' in encoder_output:
                self.available_encoders.append('h264_qsv')
            if 'hevc_qsv' in encoder_output:
                self.available_encoders.append('hevc_qsv')
            
            # AMD AMF encoders
            if 'h264_amf' in encoder_output:
                self.available_encoders.append('h264_amf')
            if 'hevc_amf' in encoder_output:
                self.available_encoders.append('hevc_amf')
            
            # NVIDIA NVENC encoders
            if 'h264_nvenc' in encoder_output:
                self.available_encoders.append('h264_nvenc')
            if 'hevc_nvenc' in encoder_output:
                self.available_encoders.append('hevc_nvenc')
            
            # Software encoder as fallback
            if 'libx264' in encoder_output:
                self.available_encoders.append('libx264')
            
            # Check for hardware decoders
            result = subprocess.run(['ffmpeg', '-hide_banner', '-decoders'], 
                                  capture_output=True, text=True, timeout=10)
            decoder_output = result.stdout.lower()
            
            # Intel Quick Sync Video decoders
            if 'h264_qsv' in decoder_output:
                self.available_decoders.append('h264_qsv')
            if 'hevc_qsv' in decoder_output:
                self.available_decoders.append('hevc_qsv')
            
            # AMD decoders
            if 'h264_amf' in decoder_output:
                self.available_decoders.append('h264_amf')
            if 'hevc_amf' in decoder_output:
                self.available_decoders.append('hevc_amf')
            
            # NVIDIA decoders
            if 'h264_cuvid' in decoder_output:
                self.available_decoders.append('h264_cuvid')
            if 'hevc_cuvid' in decoder_output:
                self.available_decoders.append('hevc_cuvid')
                
        except subprocess.TimeoutExpired:
            logging.warning("FFmpeg codec detection timed out")
        except FileNotFoundError:
            logging.warning("FFmpeg not found in PATH")
        except Exception as e:
            logging.warning(f"FFmpeg codec detection failed: {e}")
    
    def _log_detection_results(self):
        """Log the detection results with emojis"""
        if self.intel_gpu:
            logging.info("🔷 Intel GPU detected")
        if self.amd_gpu:
            logging.info("🔴 AMD GPU detected")
        if self.nvidia_gpu:
            logging.info("🟢 NVIDIA GPU detected")
        
        if self.intel_gpu or self.amd_gpu or self.nvidia_gpu:
            logging.info("✅ GPU acceleration available")
        else:
            logging.info("⚠️ No GPU acceleration detected, using CPU")
        
        if self.opencl_support:
            logging.info("🔷 OpenCV OpenCL support detected")
            logging.info("✅ OpenCL enabled for OpenCV")
        
        if self.available_encoders:
            logging.info(f"🎬 Supported hardware encoders: {', '.join(self.available_encoders)}")
        
        if self.available_decoders:
            logging.info(f"🎞️ Supported hardware decoders: {', '.join(self.available_decoders)}")
    
    def get_optimal_encoder(self):
        """Get the best available encoder based on detected hardware"""
        # Priority order: Hardware encoders first, then software
        if self.intel_gpu and 'h264_qsv' in self.available_encoders:
            return 'h264_qsv'
        elif self.amd_gpu and 'h264_amf' in self.available_encoders:
            return 'h264_amf'
        elif self.nvidia_gpu and 'h264_nvenc' in self.available_encoders:
            return 'h264_nvenc'
        elif 'libx264' in self.available_encoders:
            return 'libx264'
        else:
            return 'libx264'  # Fallback
    
    def get_optimal_decoder(self):
        """Get the best available decoder based on detected hardware"""
        if self.intel_gpu and 'h264_qsv' in self.available_decoders:
            return 'h264_qsv'
        elif self.amd_gpu and 'h264_amf' in self.available_decoders:
            return 'h264_amf'
        elif self.nvidia_gpu and 'h264_cuvid' in self.available_decoders:
            return 'h264_cuvid'
        else:
            return None  # Use default software decoder
    
    def get_gpu_acceleration_params(self):
        """Get GPU-specific acceleration parameters for video processing"""
        params = {}
        
        if self.intel_gpu and 'h264_qsv' in self.available_encoders:
            params['codec'] = 'h264_qsv'
            params['ffmpeg_params'] = ['-preset', 'medium', '-global_quality', '23']
        elif self.amd_gpu and 'h264_amf' in self.available_encoders:
            params['codec'] = 'h264_amf'
            params['ffmpeg_params'] = ['-quality', 'balanced', '-rc', 'vbr_peak']
        elif self.nvidia_gpu and 'h264_nvenc' in self.available_encoders:
            params['codec'] = 'h264_nvenc'
            params['ffmpeg_params'] = ['-preset', 'medium', '-cq', '23']
        else:
            params['codec'] = 'libx264'
            params['ffmpeg_params'] = ['-preset', 'medium', '-crf', '23']
        
        return params
    
    def has_gpu_acceleration(self):
        """Check if any GPU acceleration is available"""
        return self.intel_gpu or self.amd_gpu or self.nvidia_gpu

# Global GPU detector instance
gpu_detector = GPUDetector()