import sys
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_logger():
    """测试日志记录器"""
    try:
        # 测试导入
        from app.utils.logger import default_logger, setup_logger

        print("Logger imported successfully!")

        # 测试默认日志记录器
        default_logger.info("这是默认日志记录器的信息消息")
        default_logger.warning("这是默认日志记录器的警告消息")
        default_logger.error("这是默认日志记录器的错误消息")

        # 测试自定义日志记录器
        custom_logger = setup_logger("DEBUG", "logs/test.log")
        custom_logger.debug("这是自定义日志记录器的调试消息")
        custom_logger.info("这是自定义日志记录器的信息消息")

        print("Logger tests completed successfully!")
        return True

    except Exception as e:
        print(f"Error testing logger: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_logger()
