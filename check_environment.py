import os
import sys

def check_environment():
    print("=" * 60)
    print("江西工业工程职业技术学院 AI助手 - 环境检查")
    print("=" * 60)
    
    # 检查Python版本
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查必要库
    libraries = [
        "chromadb", "langchain", "sentence_transformers", 
        "torch", "langchain_community"
    ]
    
    print("\n📦 检查必要库...")
    missing_libs = []
    for lib in libraries:
        try:
            if lib == "sentence_transformers":
                import sentence_transformers
            else:
                __import__(lib.replace("-", "_"))
            print(f"   ✅ {lib}")
        except ImportError:
            print(f"   ❌ {lib} - 未安装")
            missing_libs.append(lib)
    
    # 检查数据文件夹
    print("\n📁 检查数据文件夹...")
    data_path = "江西工业工程职业技术学院_数据仓库"
    if os.path.exists(data_path):
        # 统计文件数量
        count = 0
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith(".txt"):
                    count += 1
        print(f"   ✅ 找到数据文件夹，包含 {count} 个文本文件")
        
        # 显示一些文件示例
        txt_files = []
        for root, dirs, files in os.walk(data_path):
            for file in files[:3]:  # 只显示前3个
                if file.endswith(".txt"):
                    txt_files.append(file)
        if txt_files:
            print(f"   示例文件: {', '.join(txt_files)}")
    else:
        print(f"   ❌ 数据文件夹不存在: {data_path}")
        missing_libs.append("数据文件夹")
    
    # 总结
    print("\n" + "=" * 60)
    if not missing_libs:
        print("🎉 所有检查通过！环境准备就绪！")
        print("下一步：构建向量数据库")
        print('请回复 "环境检查完成" 继续下一步')
    else:
        print("❌ 以下项目需要修复：")
        for item in missing_libs:
            print(f"   - {item}")
        print("\n请先安装缺失的库，然后重新运行此检查")
    
    print("=" * 60)

if __name__ == "__main__":
    check_environment()