"""通用下载工具函数"""
import os
import urllib.request
import zipfile
import tarfile
import platform
import logging
from typing import Optional, Callable, Dict, Any

# 使用标准 logging 模块避免循环导入
logger = logging.getLogger(__name__)


def download_file(url: str, target_path: str) -> bool:
    """
    下载文件到指定路径
    
    Args:
        url: 下载链接
        target_path: 目标文件路径
        
    Returns:
        是否下载成功
    """
    try:
        logger.info(f"Downloading from {url} to {target_path}")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        urllib.request.urlretrieve(url, target_path)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def download_and_extract_zip(url: str, extract_dir: str, 
                            target_filename: Optional[str] = None,
                            filter_func: Optional[Callable[[str], bool]] = None) -> bool:
    """
    下载并解压 ZIP 文件
    
    Args:
        url: 下载链接
        extract_dir: 解压目录
        target_filename: 目标文件名（如果需要重命名）
        filter_func: 过滤函数，用于选择要提取的文件
        
    Returns:
        是否成功
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        zip_path = os.path.join(extract_dir, "download.zip")
        
        logger.info(f"Downloading ZIP from {url}...")
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            if filter_func:
                # 使用过滤函数选择文件
                for member in zf.namelist():
                    if filter_func(member):
                        zf.extract(member, extract_dir)
                        if target_filename:
                            extracted_path = os.path.join(extract_dir, member)
                            target_path = os.path.join(extract_dir, target_filename)
                            os.rename(extracted_path, target_path)
                        break
            else:
                # 提取所有文件
                zf.extractall(extract_dir)
                
        os.remove(zip_path)
        return True
    except Exception as e:
        logger.error(f"Failed to download and extract ZIP {url}: {e}")
        return False


def download_and_extract_tarxz(url: str, extract_dir: str, 
                              target_filename: Optional[str] = None,
                              filter_func: Optional[Callable[[str], bool]] = None) -> bool:
    """
    下载并解压 tar.xz 文件
    
    Args:
        url: 下载链接
        extract_dir: 解压目录
        target_filename: 目标文件名（如果需要重命名）
        filter_func: 过滤函数，用于选择要提取的文件
        
    Returns:
        是否成功
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        tar_path = os.path.join(extract_dir, "download.tar.xz")
        
        logger.info(f"Downloading tar.xz from {url}...")
        urllib.request.urlretrieve(url, tar_path)
        
        with tarfile.open(tar_path, 'r:xz') as tf:
            if filter_func:
                # 使用过滤函数选择文件
                for member in tf.getmembers():
                    if filter_func(member.name):
                        tf.extract(member, extract_dir)
                        if target_filename:
                            extracted_path = os.path.join(extract_dir, member.name)
                            target_path = os.path.join(extract_dir, target_filename)
                            if os.path.exists(extracted_path):
                                os.rename(extracted_path, target_path)
                        break
            else:
                # 提取所有文件
                tf.extractall(extract_dir)
                
        os.remove(tar_path)
        return True
    except Exception as e:
        logger.error(f"Failed to download and extract tar.xz {url}: {e}")
        return False


def make_executable(file_path: str) -> None:
    """使文件可执行（Linux/macOS）"""
    if platform.system() != "Windows":
        os.chmod(file_path, 0o755)


def download_executable(url: str, target_path: str, make_exec: bool = True, 
                       retries: int = 3, min_size: int = 1024) -> Dict[str, Any]:
    """
    下载可执行文件的通用函数，支持重试机制
    
    Args:
        url: 下载链接
        target_path: 目标路径
        make_exec: 是否设置可执行权限
        retries: 最大重试次数
        min_size: 最小文件大小（字节），用于验证下载完整性
        
    Returns:
        结果字典，包含 success、error、path 等字段
    """
    last_error = None
    
    for attempt in range(1, retries + 1):
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            temp_path = target_path + ".tmp"
            
            logger.info(f"Downloading executable from {url} (attempt {attempt}/{retries})...")
            urllib.request.urlretrieve(url, temp_path)
            
            # 验证文件大小
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                if file_size < min_size:
                    logger.warning(f"Downloaded file too small ({file_size} bytes), retrying...")
                    os.remove(temp_path)
                    last_error = f"File too small ({file_size} bytes)"
                    continue
                
                # 下载成功，重命名文件
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(temp_path, target_path)
                
                if make_exec and platform.system() != "Windows":
                    os.chmod(target_path, 0o755)
                
                logger.info(f"Downloaded executable to: {target_path} ({file_size} bytes)")
                return {"success": True, "path": target_path, "size": file_size}
        except Exception as e:
            logger.error(f"Failed to download executable (attempt {attempt}/{retries}): {e}")
            last_error = str(e)
            if os.path.exists(target_path + ".tmp"):
                try:
                    os.remove(target_path + ".tmp")
                except:
                    pass
    
    logger.error(f"Failed to download executable after {retries} attempts: {last_error}")
    return {"success": False, "error": last_error}