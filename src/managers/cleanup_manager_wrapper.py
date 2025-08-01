"""
清理管理器包装器 - 第7步减法重构
将Application类中的清理相关方法迁移到此处
"""
import logging
import time


class CleanupManagerWrapper:
    """清理管理器包装器 - 纯粹的方法迁移，不改变任何逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("清理管理器包装器创建成功")
    
    def is_component_ready(self, app_instance, component_name, check_method=None):
        """统一的组件状态检查方法 - 从Application类移过来"""
        try:
            component = getattr(app_instance, component_name, None)
            if component is None:
                return False
            
            # 如果指定了检查方法，调用该方法
            if check_method and hasattr(component, check_method):
                check_attr = getattr(component, check_method)
                # 如果是方法，调用它；如果是属性，直接返回
                if callable(check_attr):
                    return check_attr()
                else:
                    return bool(check_attr)
            
            # 默认检查：组件存在即认为可用
            return True
            
        except Exception as e:
            logging.error(f"检查组件 {component_name} 状态失败: {e}")
            return False
    
    def is_ready_for_recording(self, app_instance):
        """检查是否准备好录音 - 从Application类移过来"""
        return (app_instance.audio_capture_thread is not None and 
                app_instance.funasr_engine is not None and
                app_instance.hotkey_manager is not None)
    
    def cleanup_component(self, app_instance, component_name, cleanup_method='cleanup', timeout=200):
        """统一的组件清理方法 - 从Application类移过来"""
        try:
            component = getattr(app_instance, component_name, None)
            if component is None:
                return True
            
            # 检查组件是否有指定的清理方法
            if hasattr(component, cleanup_method):
                cleanup_func = getattr(component, cleanup_method)
                
                # 如果是线程组件，使用quit和wait
                if hasattr(component, 'quit') and hasattr(component, 'wait'):
                    component.quit()
                    if not component.wait(timeout):
                        logging.warning(f"组件 {component_name} 清理超时")
                        return False
                else:
                    # 调用清理方法
                    cleanup_func()
                
                logging.debug(f"组件 {component_name} 清理完成")
                return True
            else:
                logging.debug(f"组件 {component_name} 没有 {cleanup_method} 方法，跳过清理")
                return True
                
        except AttributeError as e:
            # 属性不存在的错误，通常是正常的，只记录调试信息
            logging.debug(f"组件 {component_name} 清理时属性不存在: {e}")
            return True
        except Exception as e:
            # 其他真正的错误才记录为错误级别
            logging.error(f"清理组件 {component_name} 失败: {e}")
            return False
    
    def cleanup_resources(self, app_instance):
        """清理资源 - 从Application类移过来"""
        try:
            logging.info("开始清理应用程序资源...")
            
            # 定义需要清理的组件列表（按优先级排序）
            components_to_cleanup = [
                ('transcription_thread', 'terminate'),
                ('audio_capture', 'cleanup'),
                ('funasr_engine', 'cleanup'),
                ('hotkey_manager', 'cleanup'),
                ('state_manager', 'cleanup')
            ]
            
            for component_name, method in components_to_cleanup:
                self.cleanup_component(app_instance, component_name, method)
            
            # 清理其他资源
            if hasattr(app_instance, 'tray_icon') and app_instance.tray_icon:
                app_instance.tray_icon.hide()
            
            if hasattr(app_instance, 'main_window') and app_instance.main_window:
                app_instance.main_window.close()
            
            pass  # 资源清理完成
        except Exception as e:
            logging.error(f"资源清理失败: {e}")
        finally:
            # 确保关键资源被清理
            try:
                if hasattr(app_instance, 'app'):
                    app_instance.app.quit()
            except Exception as e:
                logging.error(f"应用退出失败: {e}")
    
    def quick_cleanup(self, app_instance):
        """快速清理关键资源 - 从Application类移过来"""
        pass  # 开始快速清理资源
        
        try:
            # 1. 停止录音相关操作
            if hasattr(app_instance, 'recording') and app_instance.recording:
                app_instance.recording = False
                
            # 2. 停止热键监听，避免在清理过程中触发新的操作
            if hasattr(app_instance, 'hotkey_manager') and app_instance.hotkey_manager:
                try:
                    app_instance.hotkey_manager.stop_listening()
                except Exception as e:
                    logging.error(f"停止热键监听失败: {e}")
            
            # 3. 快速清理资源，避免长时间等待
            self._quick_cleanup_internal(app_instance)
            
            # 4. 恢复系统音量（如果有保存的话）
            if hasattr(app_instance, 'previous_volume') and app_instance.previous_volume is not None:
                try:
                    app_instance.audio_capture.set_system_volume(app_instance.previous_volume)
                    logging.debug(f"系统音量已恢复到: {app_instance.previous_volume}")
                except Exception as e:
                    logging.error(f"恢复系统音量失败: {e}")
            
            # 5. 清理热键管理器（快速版本）
            if hasattr(app_instance, 'hotkey_manager') and app_instance.hotkey_manager:
                try:
                    # 调用停止监听方法，但不等待清理完成
                    app_instance.hotkey_manager.stop_listening()
                except Exception as e:
                    logging.error(f"快速清理热键管理器失败: {e}")
            
            # 6. 关闭主窗口
            if hasattr(app_instance, 'main_window') and app_instance.main_window:
                try:
                    app_instance.main_window.close()
                except Exception as e:
                    logging.error(f"关闭主窗口失败: {e}")
            
            # 7. 隐藏系统托盘图标
            if hasattr(app_instance, 'tray_icon') and app_instance.tray_icon:
                try:
                    app_instance.tray_icon.hide()
                except Exception as e:
                    logging.error(f"隐藏托盘图标失败: {e}")
            
            logging.debug("快速清理完成")
            
        except Exception as e:
            logging.error(f"快速清理失败: {e}")
    
    def _quick_cleanup_internal(self, app_instance):
        """内部快速清理方法 - 从Application类移过来"""
        # 快速停止音频捕获线程
        if hasattr(app_instance, 'audio_capture_thread') and app_instance.audio_capture_thread:
            try:
                app_instance.audio_capture_thread.stop()
                # 不等待线程完全停止，避免阻塞
            except Exception as e:
                logging.error(f"快速停止音频捕获线程失败: {e}")
        
        # 快速停止转写线程
        if hasattr(app_instance, 'transcription_thread') and app_instance.transcription_thread:
            try:
                app_instance.transcription_thread.quit()
                # 不等待线程完全停止，避免阻塞
            except Exception as e:
                logging.error(f"快速停止转写线程失败: {e}")
    
    def cleanup(self, app_instance):
        """清理资源 - 从Application类移过来"""
        try:
            if hasattr(app_instance, 'audio_capture_thread') and app_instance.audio_capture_thread:
                app_instance.audio_capture_thread.stop()
                app_instance.audio_capture_thread.wait()
                
            if hasattr(app_instance, 'transcription_thread') and app_instance.transcription_thread:
                app_instance.transcription_thread.quit()
                app_instance.transcription_thread.wait()
                
            if hasattr(app_instance, 'hotkey_manager') and app_instance.hotkey_manager:
                app_instance.hotkey_manager.stop_listening()
        except Exception as e:
            logging.error(f"清理资源失败: {e}")
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'CleanupManagerWrapper',
            'description': '清理管理器包装器'
        }
