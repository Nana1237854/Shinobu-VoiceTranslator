# coding:utf-8
"""测试所有导入是否正常"""

print("测试导入...")

try:
    print("1. 测试 icon 导入...")
    from app.common.icon import Icon, Logo
    print(f"   ✓ Icon.TASK = {Icon.TASK}")
    print(f"   ✓ Icon.CLOUD_DOWNLOAD = {Icon.CLOUD_DOWNLOAD}")
    print(f"   ✓ Icon.SELECT = {Icon.SELECT}")
    print(f"   ✓ Logo.SMILEFACE = {Logo.SMILEFACE}")
    
    print("\n2. 测试 database 导入...")
    from app.common.database import Task, TaskStatus, TaskType
    print(f"   ✓ Task 类已导入")
    print(f"   ✓ TaskStatus 枚举已导入")
    print(f"   ✓ TaskType 枚举已导入")
    
    print("\n3. 测试 database service 导入...")
    from app.common.database import getTaskService, sqlRequest
    print(f"   ✓ getTaskService 函数已导入")
    print(f"   ✓ sqlRequest 函数已导入")
    
    print("\n4. 测试 signal_bus 导入...")
    from app.common.signal_bus import signalBus
    print(f"   ✓ signalBus 已导入")
    
    print("\n5. 测试 utils 导入...")
    from app.common.utils import removeFile, showInFolder, openUrl
    print(f"   ✓ removeFile 函数已导入")
    print(f"   ✓ showInFolder 函数已导入")
    print(f"   ✓ openUrl 函数已导入")
    
    print("\n6. 测试下载服务导入...")
    from app.services.downloadservice.download_service import downloadService
    print(f"   ✓ downloadService 已导入")
    print(f"   ✓ 服务可用性: {downloadService.isAvailable()}")
    
    print("\n✅ 所有导入测试通过！")
    
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

