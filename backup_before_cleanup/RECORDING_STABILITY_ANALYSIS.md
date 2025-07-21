# 录音功能不稳定问题分析与解决方案

## 问题现象
- 热键状态显示正常（绿色）
- 热键响应正常，能触发录音
- 但录音结果不稳定：有时能检测到声音，有时显示"未检测到声音"
- 从日志可以看出录音功能本身是工作的

## 根本原因分析

### 1. 音频检测阈值问题
**当前设置**：
- 默认音量阈值：`0.003`
- 最少有效帧数：`3帧`（约0.2秒）
- 最大静音帧数：`40帧`（约1.5秒）

**问题**：
- 阈值可能过高，导致正常说话声音被判定为静音
- 环境噪音、麦克风灵敏度、说话距离都会影响检测
- 不同用户的说话音量差异很大

### 2. 音频设备状态不稳定
**可能原因**：
- macOS 系统音频设备状态变化
- 其他应用占用音频设备
- 系统音频服务重启
- 蓝牙耳机连接状态变化

### 3. 录音时机问题
**观察到的模式**：
- 用户按下热键后立即开始说话
- 但音频检测需要一定时间来"预热"
- 如果说话太快，可能错过有效音频

## 详细技术分析

### 音频检测逻辑
```python
# 当前检测逻辑（audio_capture.py）
def _is_valid_audio(self, data):
    audio_data = np.frombuffer(data, dtype=np.float32)
    volume = np.sqrt(np.mean(np.square(audio_data)))  # RMS值
    is_valid = volume > self.volume_threshold  # 0.003
    
    if is_valid:
        self.silence_frame_count = 0
        self.valid_frame_count += 1
    else:
        self.silence_frame_count += 1
    
    return is_valid
```

**问题点**：
1. **固定阈值**：不适应不同环境和用户
2. **无自适应**：不能根据环境噪音调整
3. **无预热期**：录音开始时可能错过前几帧

### 录音停止条件
```python
# 停止录音的条件
if self.valid_frame_count < self.min_valid_frames:  # 少于3帧有效音频
    return np.array([], dtype=np.float32)  # 返回空数组
```

**问题**：如果用户说话时间很短（如"是"、"好"），可能被判定为无效

## 解决方案

### 方案1：动态阈值调整（推荐）

#### 实现自适应音量检测
```python
class AdaptiveAudioCapture:
    def __init__(self):
        self.base_threshold = 0.001  # 降低基础阈值
        self.noise_level = 0.0       # 环境噪音水平
        self.adaptive_threshold = self.base_threshold
        self.calibration_frames = 10  # 校准帧数
        self.noise_samples = []
    
    def calibrate_noise_level(self):
        """校准环境噪音水平"""
        if len(self.noise_samples) >= self.calibration_frames:
            self.noise_level = np.mean(self.noise_samples)
            self.adaptive_threshold = max(
                self.base_threshold,
                self.noise_level * 2.5  # 噪音水平的2.5倍作为阈值
            )
            self.noise_samples = []
    
    def _is_valid_audio(self, data):
        audio_data = np.frombuffer(data, dtype=np.float32)
        volume = np.sqrt(np.mean(np.square(audio_data)))
        
        # 收集噪音样本（录音开始前）
        if len(self.noise_samples) < self.calibration_frames:
            self.noise_samples.append(volume)
            return False  # 校准期间不算有效音频
        
        # 使用自适应阈值
        is_valid = volume > self.adaptive_threshold
        return is_valid
```

#### 优化参数设置
```python
# 更宽松的检测参数
self.min_valid_frames = 2      # 降低到2帧（约0.13秒）
self.max_silence_frames = 60   # 增加到2秒
self.volume_threshold = 0.001  # 降低基础阈值
```

### 方案2：预录音缓冲（推荐）

#### 实现录音预热机制
```python
class BufferedAudioCapture:
    def __init__(self):
        self.pre_buffer = []  # 预录音缓冲区
        self.pre_buffer_size = 5  # 保留最近5帧
        self.recording_started = False
    
    def start_recording(self):
        # 开始录音时，将预缓冲的音频也包含进来
        self.frames.extend(self.pre_buffer)
        self.recording_started = True
    
    def read_audio(self):
        data = self.stream.read(1024, exception_on_overflow=False)
        
        if not self.recording_started:
            # 录音开始前，维护预缓冲区
            self.pre_buffer.append(data)
            if len(self.pre_buffer) > self.pre_buffer_size:
                self.pre_buffer.pop(0)
        else:
            # 正常录音处理
            self.frames.append(data)
```

### 方案3：多级检测策略

#### 实现渐进式音频检测
```python
class MultiLevelDetection:
    def __init__(self):
        self.detection_levels = [
            0.0005,  # 极低阈值
            0.001,   # 低阈值
            0.003,   # 中等阈值
            0.008    # 高阈值
        ]
        self.level_counts = [0, 0, 0, 0]
    
    def _is_valid_audio(self, data):
        audio_data = np.frombuffer(data, dtype=np.float32)
        volume = np.sqrt(np.mean(np.square(audio_data)))
        
        # 统计各级别的检测结果
        for i, threshold in enumerate(self.detection_levels):
            if volume > threshold:
                self.level_counts[i] += 1
        
        # 如果任何级别检测到足够的音频，认为有效
        return any(count >= 2 for count in self.level_counts)
```

### 方案4：用户自定义校准

#### 添加音量校准功能
```python
def calibrate_user_voice(self):
    """用户语音校准"""
    print("请说话3秒进行音量校准...")
    
    calibration_data = []
    start_time = time.time()
    
    while time.time() - start_time < 3:
        data = self.stream.read(1024)
        audio_data = np.frombuffer(data, dtype=np.float32)
        volume = np.sqrt(np.mean(np.square(audio_data)))
        calibration_data.append(volume)
    
    # 计算用户的平均音量和推荐阈值
    avg_volume = np.mean(calibration_data)
    max_volume = np.max(calibration_data)
    
    # 设置阈值为平均音量的30%
    recommended_threshold = avg_volume * 0.3
    self.volume_threshold = max(0.0005, recommended_threshold)
    
    print(f"校准完成，推荐阈值: {self.volume_threshold:.5f}")
```

## 立即可实施的改进

### 1. 调整现有参数
```python
# 在 audio_capture.py 中修改
self.volume_threshold = 0.001      # 降低阈值
self.min_valid_frames = 2          # 降低最少帧数
self.max_silence_frames = 50       # 增加静音容忍度
```

### 2. 添加调试信息
```python
def _is_valid_audio(self, data):
    audio_data = np.frombuffer(data, dtype=np.float32)
    volume = np.sqrt(np.mean(np.square(audio_data)))
    is_valid = volume > self.volume_threshold
    
    # 添加调试输出
    if self.read_count % 10 == 0:  # 每10帧输出一次
        print(f"音量: {volume:.5f}, 阈值: {self.volume_threshold:.5f}, 有效: {is_valid}")
    
    return is_valid
```

### 3. 增加设置选项
在设置界面添加：
- 音量敏感度滑块（调整阈值）
- 录音延迟设置
- 音频校准按钮

## 测试和验证

### 测试场景
1. **安静环境**：正常说话
2. **嘈杂环境**：有背景噪音
3. **低声说话**：测试敏感度
4. **快速指令**：短词汇（"是"、"好"）
5. **不同距离**：远离/靠近麦克风

### 验证指标
- **检测成功率**：>95%
- **误触发率**：<5%
- **响应延迟**：<200ms
- **用户满意度**：主观评价

## 长期优化方向

1. **机器学习优化**：使用用户数据训练个性化检测模型
2. **多麦克风支持**：自动选择最佳音频源
3. **语音活动检测**：使用VAD算法替代简单音量检测
4. **实时反馈**：录音时显示音量指示器

## 实施优先级

**高优先级（立即实施）**：
1. 降低音量阈值到0.001
2. 减少最少有效帧数到2
3. 添加调试输出

**中优先级（1周内）**：
1. 实现自适应阈值
2. 添加用户校准功能
3. 优化设置界面

**低优先级（长期）**：
1. 实现预录音缓冲
2. 多级检测策略
3. 机器学习优化

通过这些改进，可以显著提高录音功能的稳定性和用户体验。