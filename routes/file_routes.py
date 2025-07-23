from flask import Blueprint, request, jsonify, send_file
import os
import shutil
from utils.file_utils import get_file_list, delete_file, delete_folder_contents, create_zip_archive, format_file_size
from config import OUTPUT_FOLDER, UPLOAD_FOLDER

file_bp = Blueprint('files', __name__)

@file_bp.route('/list/<file_type>')
def list_files(file_type):
    try:
        if file_type not in ['images', 'videos', 'uploads']:
            return jsonify({"error": "Invalid file type"}), 400
        
        if file_type == 'uploads':
            # Handle uploads directory differently
            sessions = []
            if os.path.exists(UPLOAD_FOLDER):
                for session_id in os.listdir(UPLOAD_FOLDER):
                    session_path = os.path.join(UPLOAD_FOLDER, session_id)
                    if os.path.isdir(session_path):
                        files = get_file_list(session_path)
                        total_size = sum(f['size'] for f in files)
                        sessions.append({
                            'session_id': session_id,
                            'files': files,
                            'file_count': len(files),
                            'total_size': total_size,
                            'total_size_formatted': format_file_size(total_size)
                        })
        else:
            # Handle output files (images/videos)
            folder_path = os.path.join(OUTPUT_FOLDER, file_type)
            sessions = []
            if os.path.exists(folder_path):
                for session_id in os.listdir(folder_path):
                    session_path = os.path.join(folder_path, session_id)
                    if os.path.isdir(session_path):
                        files = get_file_list(session_path)
                        total_size = sum(f['size'] for f in files)
                        sessions.append({
                            'session_id': session_id,
                            'files': files,
                            'file_count': len(files),
                            'total_size': total_size,
                            'total_size_formatted': format_file_size(total_size)
                        })
        
        return jsonify({
            "success": True,
            "file_type": file_type,
            "sessions": sessions
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@file_bp.route('/delete', methods=['POST'])
def delete_files():
    try:
        data = request.get_json()
        file_type = data.get('file_type')
        session_id = data.get('session_id')
        filename = data.get('filename')  # Optional, if not provided, delete entire session
        
        if file_type not in ['images', 'videos', 'uploads']:
            return jsonify({"error": "Invalid file type"}), 400
        
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        # Determine the correct path based on file type
        if file_type == 'uploads':
            session_path = os.path.join(UPLOAD_FOLDER, session_id)
        else:
            session_path = os.path.join(OUTPUT_FOLDER, file_type, session_id)
        
        if filename:
            # Delete specific file
            file_path = os.path.join(session_path, filename)
            if delete_file(file_path):
                return jsonify({"success": True, "message": "File deleted successfully"})
            else:
                return jsonify({"error": "Failed to delete file"}), 500
        else:
            # Delete entire session folder
            if os.path.exists(session_path):
                shutil.rmtree(session_path)  # Remove entire directory tree
                return jsonify({"success": True, "message": "Session deleted successfully"})
            else:
                return jsonify({"error": "Session not found"}), 404
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@file_bp.route('/delete-all/<file_type>', methods=['POST'])
def delete_all_files(file_type):
    """Delete all files of a specific type"""
    try:
        if file_type not in ['images', 'videos', 'uploads']:
            return jsonify({"error": "Invalid file type"}), 400
        
        # Determine the correct path based on file type
        if file_type == 'uploads':
            target_path = UPLOAD_FOLDER
        else:
            target_path = os.path.join(OUTPUT_FOLDER, file_type)
        
        if not os.path.exists(target_path):
            return jsonify({"success": True, "message": f"No {file_type} directory found"})
        
        # Count files before deletion for reporting
        total_deleted = 0
        for session_id in os.listdir(target_path):
            session_path = os.path.join(target_path, session_id)
            if os.path.isdir(session_path):
                files = get_file_list(session_path)
                total_deleted += len(files)
                shutil.rmtree(session_path)
        
        return jsonify({
            "success": True, 
            "message": f"All {file_type} deleted successfully",
            "files_deleted": total_deleted
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@file_bp.route('/cleanup-all', methods=['POST'])
def cleanup_all():
    """Delete all files from uploads, images, and videos"""
    try:
        total_deleted = 0
        results = {}
        
        # Clean uploads
        if os.path.exists(UPLOAD_FOLDER):
            upload_count = 0
            for session_id in os.listdir(UPLOAD_FOLDER):
                session_path = os.path.join(UPLOAD_FOLDER, session_id)
                if os.path.isdir(session_path):
                    files = get_file_list(session_path)
                    upload_count += len(files)
                    shutil.rmtree(session_path)
            results['uploads'] = upload_count
            total_deleted += upload_count
        
        # Clean images
        images_path = os.path.join(OUTPUT_FOLDER, 'images')
        if os.path.exists(images_path):
            images_count = 0
            for session_id in os.listdir(images_path):
                session_path = os.path.join(images_path, session_id)
                if os.path.isdir(session_path):
                    files = get_file_list(session_path)
                    images_count += len(files)
                    shutil.rmtree(session_path)
            results['images'] = images_count
            total_deleted += images_count
        
        # Clean videos
        videos_path = os.path.join(OUTPUT_FOLDER, 'videos')
        if os.path.exists(videos_path):
            videos_count = 0
            for session_id in os.listdir(videos_path):
                session_path = os.path.join(videos_path, session_id)
                if os.path.isdir(session_path):
                    files = get_file_list(session_path)
                    videos_count += len(files)
                    shutil.rmtree(session_path)
            results['videos'] = videos_count
            total_deleted += videos_count
        
        # Clean audio (from TTS)
        audio_path = os.path.join(OUTPUT_FOLDER, 'audio')
        if os.path.exists(audio_path):
            audio_count = 0
            for session_id in os.listdir(audio_path):
                session_path = os.path.join(audio_path, session_id)
                if os.path.isdir(session_path):
                    files = get_file_list(session_path)
                    audio_count += len(files)
                    shutil.rmtree(session_path)
            results['audio'] = audio_count
            total_deleted += audio_count
        
        # Clean temp directory
        temp_path = 'temp'
        if os.path.exists(temp_path):
            temp_count = 0
            for item in os.listdir(temp_path):
                item_path = os.path.join(temp_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    temp_count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    temp_count += 1
            results['temp'] = temp_count
            total_deleted += temp_count
        
        return jsonify({
            "success": True,
            "message": f"Complete cleanup completed! {total_deleted} items deleted",
            "details": results,
            "total_deleted": total_deleted
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@file_bp.route('/download-zip/<file_type>/<session_id>')
def download_zip(file_type, session_id):
    try:
        if file_type not in ['images', 'videos', 'uploads']:
            return jsonify({"error": "Invalid file type"}), 400
        
        # Determine the correct path based on file type
        if file_type == 'uploads':
            session_path = os.path.join(UPLOAD_FOLDER, session_id)
        else:
            session_path = os.path.join(OUTPUT_FOLDER, file_type, session_id)
        
        if not os.path.exists(session_path):
            return jsonify({"error": "Session not found"}), 404
        
        zip_name = f"{file_type}_{session_id}.zip"
        zip_path = create_zip_archive(session_path, zip_name)
        
        if zip_path and os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, download_name=zip_name)
        else:
            return jsonify({"error": "Failed to create zip file"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@file_bp.route('/download-file/<file_type>/<session_id>/<filename>')
def download_file(file_type, session_id, filename):
    try:
        if file_type not in ['images', 'videos', 'uploads']:
            return jsonify({"error": "Invalid file type"}), 400
        
        # Determine the correct path based on file type
        if file_type == 'uploads':
            file_path = os.path.join(UPLOAD_FOLDER, session_id, filename)
        else:
            file_path = os.path.join(OUTPUT_FOLDER, file_type, session_id, filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({"error": "File not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@file_bp.route('/storage-info')
def get_storage_info():
    """Get storage information for all file types"""
    try:
        storage_info = {}
        
        # Calculate uploads storage
        uploads_size = 0
        uploads_count = 0
        if os.path.exists(UPLOAD_FOLDER):
            for session_id in os.listdir(UPLOAD_FOLDER):
                session_path = os.path.join(UPLOAD_FOLDER, session_id)
                if os.path.isdir(session_path):
                    files = get_file_list(session_path)
                    uploads_count += len(files)
                    uploads_size += sum(f['size'] for f in files)
        
        storage_info['uploads'] = {
            'count': uploads_count,
            'size': uploads_size,
            'size_formatted': format_file_size(uploads_size)
        }
        
        # Calculate output files storage
        for file_type in ['images', 'videos', 'audio']:
            type_size = 0
            type_count = 0
            type_path = os.path.join(OUTPUT_FOLDER, file_type)
            
            if os.path.exists(type_path):
                for session_id in os.listdir(type_path):
                    session_path = os.path.join(type_path, session_id)
                    if os.path.isdir(session_path):
                        files = get_file_list(session_path)
                        type_count += len(files)
                        type_size += sum(f['size'] for f in files)
            
            storage_info[file_type] = {
                'count': type_count,
                'size': type_size,
                'size_formatted': format_file_size(type_size)
            }
        
        # Calculate temp storage
        temp_size = 0
        temp_count = 0
        temp_path = 'temp'
        if os.path.exists(temp_path):
            for item in os.listdir(temp_path):
                item_path = os.path.join(temp_path, item)
                if os.path.isfile(item_path):
                    temp_count += 1
                    temp_size += os.path.getsize(item_path)
        
        storage_info['temp'] = {
            'count': temp_count,
            'size': temp_size,
            'size_formatted': format_file_size(temp_size)
        }
        
        # Calculate total
        total_size = sum(info['size'] for info in storage_info.values())
        total_count = sum(info['count'] for info in storage_info.values())
        
        storage_info['total'] = {
            'count': total_count,
            'size': total_size,
            'size_formatted': format_file_size(total_size)
        }
        
        return jsonify({
            "success": True,
            "storage_info": storage_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500