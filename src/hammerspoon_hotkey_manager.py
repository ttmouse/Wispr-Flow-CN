import os
import json
import time
import subprocess
import threading
from typing import Dict, Any, Optional

# 尝试不同的导入方式以适应不同的运行环境
try:
    # 最后尝试直接导入（当在同一目录时）
    from hotkey_manager_base import HotkeyManagerBase
except ImportError:
    try:
        # 然后尝试从src包导入
        from src.hotkey_manager_base import HotkeyManagerBase
    except ImportError:
        # 首先尝试相对导入（当作为模块导入时）
        from .hotkey_manager_base import HotkeyManagerBase

class HammerspoonHotkeyManager(HotkeyManagerBase):
    """基于Hammerspoon的热键管理器"""
    
    def __init__(self, settings_manager=None):
        super().__init__(settings_manager)
        self.communication_file = '/tmp/asr_hotkey_communication.json'
        self.status_file = '/tmp/asr_hotkey_status.json'
        self.lua_script_path = None
        self.monitoring_thread = None
        self.should_stop_monitoring = False
        self.error_count = 0
        self.last_error = ''
        self.last_status_check = 0
        
        # 获取当前热键设置
        if self.settings_manager:
            self.hotkey_type = self.settings_manager.get_hotkey()
        
        self._create_lua_script()
    
    def _create_lua_script(self) -> None:
        """创建Hammerspoon Lua脚本"""
        script_dir = os.path.join(os.path.dirname(__file__), 'hammerspoon_scripts')
        os.makedirs(script_dir, exist_ok=True)
        
        self.lua_script_path = os.path.join(script_dir, 'hotkey_listener.lua')
        
        lua_script = f'''
-- ASR热键监听脚本
local communication_file = "{self.communication_file}"
local status_file = "{self.status_file}"
local hotkey_type = "{self.hotkey_type}"
local hotkey_obj = nil
local is_recording = false
local start_time = 0

-- 写入状态文件
local function write_status(active, error_msg)
    local status = {{
        active = active,
        scheme = "hammerspoon",
        hotkey_type = hotkey_type,
        error_count = 0,
        last_error = error_msg or "",
        timestamp = os.time(),
        is_recording = is_recording
    }}
    
    local file = io.open(status_file, "w")
    if file then
        file:write(hs.json.encode(status))
        file:close()
    end
end

-- 写入通信文件
local function write_communication(action, timestamp)
    local data = {{
        action = action,
        timestamp = timestamp or os.time(),
        hotkey_type = hotkey_type
    }}
    
    local file = io.open(communication_file, "w")
    if file then
        file:write(hs.json.encode(data))
        file:close()
    end
end

-- 热键按下回调
local function on_hotkey_press()
    if not is_recording then
        is_recording = true
        start_time = os.time()
        write_communication("press", start_time)
        write_status(true)
        print("[ASR] 热键按下，开始录音")
    end
end

-- 热键释放回调
local function on_hotkey_release()
    if is_recording then
        is_recording = false
        local end_time = os.time()
        write_communication("release", end_time)
        write_status(true)
        print("[ASR] 热键释放，停止录音")
    end
end

-- 获取修饰键映射
local function get_modifier_key(key_type)
    if key_type == "fn" then
        return "fn"
    elseif key_type == "ctrl" then
        return "ctrl"
    elseif key_type == "alt" then
        return "alt"
    elseif key_type == "cmd" then
        return "cmd"
    else
        return "fn"  -- 默认使用fn键
    end
end

-- 启动热键监听
local function start_hotkey_listening()
    if hotkey_obj then
        hotkey_obj:delete()
    end
    
    local modifier = get_modifier_key(hotkey_type)
    
    -- 对于fn键，使用特殊处理
    if modifier == "fn" then
        -- Hammerspoon对fn键的支持有限，使用事件监听
        hotkey_obj = hs.eventtap.new({{hs.eventtap.event.types.flagsChanged}}, function(event)
            local flags = event:getFlags()
            if flags.fn and not is_recording then
                on_hotkey_press()
            elseif not flags.fn and is_recording then
                on_hotkey_release()
            end
        end)
        hotkey_obj:start()
    else
        -- 对于其他修饰键，使用标准热键绑定
        hotkey_obj = hs.hotkey.bind({{modifier}}, "", on_hotkey_press, on_hotkey_release)
    end
    
    write_status(true)
    print("[ASR] Hammerspoon热键监听已启动，热键类型: " .. hotkey_type)
end

-- 停止热键监听
local function stop_hotkey_listening()
    if hotkey_obj then
        hotkey_obj:delete()
        hotkey_obj = nil
    end
    is_recording = false
    write_status(false)
    print("[ASR] Hammerspoon热键监听已停止")
end

-- 更新热键类型
local function update_hotkey_type(new_type)
    hotkey_type = new_type
    stop_hotkey_listening()
    start_hotkey_listening()
end

-- 监听配置文件变化
local config_watcher = hs.pathwatcher.new("/tmp/asr_hotkey_config.json", function(files)
    for _, file in pairs(files) do
        if file:match("asr_hotkey_config.json$") then
            local config_file = io.open("/tmp/asr_hotkey_config.json", "r")
            if config_file then
                local content = config_file:read("*all")
                config_file:close()
                
                local success, config = pcall(hs.json.decode, content)
                if success and config then
                    if config.action == "update_hotkey" and config.hotkey_type then
                        update_hotkey_type(config.hotkey_type)
                    elseif config.action == "stop" then
                        stop_hotkey_listening()
                    elseif config.action == "start" then
                        start_hotkey_listening()
                    end
                end
            end
        end
    end
end)

-- 启动配置监听
config_watcher:start()

-- 初始启动
start_hotkey_listening()

-- 定期更新状态
local status_timer = hs.timer.doEvery(5, function()
    write_status(hotkey_obj ~= nil)
end)

print("[ASR] Hammerspoon热键脚本已加载")
'''
        
        try:
            with open(self.lua_script_path, 'w', encoding='utf-8') as f:
                f.write(lua_script)
            self.logger.info(f"Lua脚本已创建: {self.lua_script_path}")
        except Exception as e:
            self.logger.error(f"创建Lua脚本失败: {e}")
            self.last_error = f"创建Lua脚本失败: {e}"
    
    def _check_hammerspoon_available(self) -> bool:
        """检查Hammerspoon是否可用"""
        try:
            # 检查hs命令是否存在
            result = subprocess.run(['which', 'hs'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                self.logger.warning("Hammerspoon命令行工具(hs)未找到")
                return False
            
            # 检查Hammerspoon是否正在运行
            try:
                test_result = subprocess.run(['hs', '-c', 'print("test")'], 
                                           capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    self.logger.info("Hammerspoon可用且正在运行")
                    return True
                else:
                    self.logger.warning("Hammerspoon未运行或无法执行命令")
                    return False
            except subprocess.TimeoutExpired:
                self.logger.warning("Hammerspoon命令执行超时")
                return False
                
        except Exception as e:
            self.logger.error(f"检查Hammerspoon可用性失败: {e}")
            return False
    
    def start_listening(self) -> bool:
        """启动热键监听"""
        try:
            if not self._check_hammerspoon_available():
                self.last_error = "Hammerspoon未安装或不可用"
                self.logger.error(self.last_error)
                return False
            
            # 加载Lua脚本到Hammerspoon
            cmd = ['hs', '-c', f'dofile("{self.lua_script_path}")']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.last_error = f"加载Lua脚本失败: {result.stderr}"
                self.logger.error(self.last_error)
                return False
            
            # 启动监控线程
            self.should_stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self._monitor_communication, daemon=True)
            self.monitoring_thread.start()
            
            self.is_active = True
            self.logger.info("Hammerspoon热键监听已启动")
            return True
            
        except Exception as e:
            self.last_error = f"启动热键监听失败: {e}"
            self.logger.error(self.last_error)
            self.error_count += 1
            return False
    
    def stop_listening(self) -> None:
        """停止热键监听"""
        try:
            # 发送停止命令
            self._send_config_command({'action': 'stop'})
            
            # 停止监控线程
            self.should_stop_monitoring = True
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2)
            
            self.is_active = False
            self.logger.info("Hammerspoon热键监听已停止")
            
        except Exception as e:
            self.logger.error(f"停止热键监听失败: {e}")
    
    def cleanup(self) -> None:
        """清理资源"""
        self.stop_listening()
        
        # 清理临时文件
        for file_path in [self.communication_file, self.status_file, '/tmp/asr_hotkey_config.json']:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.error(f"清理文件失败 {file_path}: {e}")
    
    def _check_hammerspoon_process(self) -> bool:
        """检查Hammerspoon进程是否正在运行"""
        try:
            # 使用pgrep检查Hammerspoon进程
            result = subprocess.run(['pgrep', '-f', 'Hammerspoon'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"检查Hammerspoon进程失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取热键管理器状态"""
        try:
            # 首先检查Hammerspoon进程是否运行
            hammerspoon_running = self._check_hammerspoon_process()
            
            if not hammerspoon_running:
                return {
                    'active': False,
                    'scheme': 'hammerspoon',
                    'hotkey_type': self.hotkey_type,
                    'error_count': self.error_count,
                    'last_error': 'Hammerspoon进程未运行',
                    'is_recording': False,
                    'hammerspoon_running': False
                }
            
            # 读取状态文件
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    
                # 检查状态是否过期（超过30秒认为过期）
                current_time = time.time()
                if current_time - status_data.get('timestamp', 0) > 30:
                    status_data['active'] = False
                    status_data['last_error'] = '状态过期'
                
                # 添加进程运行状态
                status_data['hammerspoon_running'] = True
                return status_data
            else:
                return {
                    'active': False,
                    'scheme': 'hammerspoon',
                    'hotkey_type': self.hotkey_type,
                    'error_count': self.error_count,
                    'last_error': '状态文件不存在',
                    'is_recording': False,
                    'hammerspoon_running': True
                }
                
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            return {
                'active': False,
                'scheme': 'hammerspoon',
                'hotkey_type': self.hotkey_type,
                'error_count': self.error_count + 1,
                'last_error': f'获取状态失败: {e}',
                'is_recording': False,
                'hammerspoon_running': False
            }
    
    def update_hotkey(self, hotkey_type: str) -> bool:
        """更新热键类型"""
        try:
            self.hotkey_type = hotkey_type
            
            # 发送更新命令
            config = {
                'action': 'update_hotkey',
                'hotkey_type': hotkey_type
            }
            
            return self._send_config_command(config)
            
        except Exception as e:
            self.logger.error(f"更新热键类型失败: {e}")
            self.last_error = f"更新热键类型失败: {e}"
            return False
    
    def update_delay_settings(self) -> None:
        """更新延迟设置（Hammerspoon方案暂不支持）"""
        pass
    
    def reset_state(self) -> None:
        """重置状态"""
        self.error_count = 0
        self.last_error = ''
    
    def force_reset(self) -> None:
        """强制重置"""
        self.stop_listening()
        self.reset_state()
        self.start_listening()
    
    def _send_config_command(self, config: Dict[str, Any]) -> bool:
        """发送配置命令到Hammerspoon"""
        try:
            config_file = '/tmp/asr_hotkey_config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f)
            return True
        except Exception as e:
            self.logger.error(f"发送配置命令失败: {e}")
            return False
    
    def _monitor_communication(self) -> None:
        """监控通信文件，处理热键事件"""
        last_timestamp = 0
        
        while not self.should_stop_monitoring:
            try:
                if os.path.exists(self.communication_file):
                    with open(self.communication_file, 'r') as f:
                        data = json.load(f)
                    
                    timestamp = data.get('timestamp', 0)
                    if timestamp > last_timestamp:
                        last_timestamp = timestamp
                        action = data.get('action')
                        
                        if action == 'press' and self.press_callback:
                            self.press_callback()
                        elif action == 'release' and self.release_callback:
                            self.release_callback()
                
                time.sleep(0.1)  # 100ms检查间隔
                
            except Exception as e:
                self.logger.error(f"监控通信文件失败: {e}")
                time.sleep(1)  # 出错时等待更长时间

# 为了向后兼容，保留原名称
HotkeyManager = HammerspoonHotkeyManager