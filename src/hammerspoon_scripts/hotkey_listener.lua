
-- ASR热键监听脚本
local communication_file = "/tmp/asr_hotkey_communication.json"
local status_file = "/tmp/asr_hotkey_status.json"
local hotkey_type = "fn"
local hotkey_obj = nil
local is_recording = false
local start_time = 0

-- 写入状态文件
local function write_status(active, error_msg)
    local status = {
        active = active,
        scheme = "hammerspoon",
        hotkey_type = hotkey_type,
        error_count = 0,
        last_error = error_msg or "",
        timestamp = os.time(),
        is_recording = is_recording
    }
    
    local file = io.open(status_file, "w")
    if file then
        file:write(hs.json.encode(status))
        file:close()
    end
end

-- 写入通信文件
local function write_communication(action, timestamp)
    local data = {
        action = action,
        timestamp = timestamp or os.time(),
        hotkey_type = hotkey_type
    }
    
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
        hotkey_obj = hs.eventtap.new({hs.eventtap.event.types.flagsChanged}, function(event)
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
        hotkey_obj = hs.hotkey.bind({modifier}, "", on_hotkey_press, on_hotkey_release)
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
