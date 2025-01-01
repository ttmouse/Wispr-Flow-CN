from context_manager import Context
import time

def test_context():
    print("开始测试上下文管理器...")
    
    # 创建上下文管理器
    context = Context()
    
    # 测试记录操作
    print("\n1. 测试记录操作:")
    context.record_action("测试操作")
    status = context.get_status()
    print(f"最后操作: {status['last_action']}")
    print(f"操作时间: {status['last_action_time']}")
    
    # 测试错误记录
    print("\n2. 测试错误记录:")
    context.record_error("测试错误信息")
    status = context.get_status()
    print(f"是否有错误: {status['has_error']}")
    print(f"错误信息: {status['error_message']}")
    print(f"重试次数: {status['retry_count']}")
    
    # 测试清除错误
    print("\n3. 测试清除错误:")
    context.clear_error()
    status = context.get_status()
    print(f"清除后是否有错误: {status['has_error']}")
    print(f"清除后重试次数: {status['retry_count']}")
    
    # 测试录音状态
    print("\n4. 测试录音状态:")
    context.set_recording_state("recording", duration=1.5, data_size=24576)
    status = context.get_status()
    print(f"录音状态: {status['recording_state']}")
    print(f"录音时长: {status['recording_duration']}秒")
    print(f"音频数据大小: {status['audio_data_size']}字节")
    
    # 测试转写状态
    print("\n5. 测试转写状态:")
    context.set_transcription_state("completed", result="测试转写结果")
    status = context.get_status()
    print(f"转写状态: {status['transcription_state']}")
    print(f"转写结果: {status['transcription_result']}")
    
    # 测试重置
    print("\n6. 测试重置:")
    context.reset()
    status = context.get_status()
    print(f"重置后录音状态: {status['recording_state']}")
    print(f"重置后转写状态: {status['transcription_state']}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_context() 