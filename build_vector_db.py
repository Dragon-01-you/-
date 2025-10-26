import os
import sys
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.schema import Document
import shutil

def print_step(step, message):
    """打印步骤信息"""
    print(f"\n{'='*50}")
    print(f"步骤 {step}: {message}")
    print(f"{'='*50}")

def load_documents(data_path):
    """加载所有文本文件"""
    documents = []
    txt_files = []
    
    # 遍历所有文件夹和子文件夹
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith(".txt"):
                txt_files.append(os.path.join(root, file))
    
    print(f"找到 {len(txt_files)} 个文本文件")
    
    for i, file_path in enumerate(txt_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建文档对象
            doc = Document(
                page_content=content,
                metadata={"source": os.path.basename(file_path)}
            )
            documents.append(doc)
            
            print(f"   ✅ 已加载: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"   ❌ 加载失败: {os.path.basename(file_path)} - {str(e)}")
    
    return documents

def main():
    print("🎯 开始构建江西工业工程职业技术学院知识库向量数据库")
    
    # 步骤1：检查数据文件夹
    print_step(1, "检查数据文件夹")
    data_path = "江西工业工程职业技术学院_数据仓库"
    
    if not os.path.exists(data_path):
        print("❌ 数据文件夹不存在")
        return
    
    # 步骤2：初始化文本分割器和嵌入模型
    print_step(2, "初始化文本处理工具")
    
    # 文本分割器
    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separator="\n"
    )
    
    # 嵌入模型
    print("正在加载中文嵌入模型...")
    embeddings = HuggingFaceEmbeddings(
        model_name="GanymedeNil/text2vec-large-chinese"
    )
    print("✅ 嵌入模型加载完成")
    
    # 步骤3：加载文档
    print_step(3, "加载文档")
    documents = load_documents(data_path)
    
    if len(documents) == 0:
        print("❌ 没有加载到任何文档")
        return
    
    # 步骤4：分割文本
    print_step(4, "分割文本")
    print("正在分割文本...")
    
    all_texts = []
    for doc in documents:
        texts = text_splitter.split_text(doc.page_content)
        all_texts.extend(texts)
    
    print(f"✅ 文本分割完成，共生成 {len(all_texts)} 个文本块")
    
    # 步骤5：构建向量数据库
    print_step(5, "构建向量数据库")
    
    # 删除旧的数据库
    if os.path.exists("./vector_db"):
        shutil.rmtree("./vector_db")
    
    print("正在构建向量数据库...")
    
    # 创建向量数据库
    vector_db = Chroma.from_texts(
        texts=all_texts,
        embedding=embeddings,
        persist_directory="./vector_db"
    )
    
    # 保存数据库
    vector_db.persist()
    print("✅ 向量数据库构建完成！")
    
    # 步骤6：测试检索
    print_step(6, "测试检索功能")
    
    test_queries = [
        "图书馆",
        "专业",
        "奖学金"
    ]
    
    for query in test_queries:
        print(f"\n测试查询: '{query}'")
        try:
            results = vector_db.similarity_search(query, k=1)
            if results:
                content = results[0].page_content
                # 显示前100个字符
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"  找到相关结果: {preview}")
            else:
                print("  未找到相关结果")
        except Exception as e:
            print(f"  检索失败: {str(e)}")
    
    print("\n🎉 向量数据库构建成功！")
    print("📁 数据库保存在: ./vector_db/")
    print('请回复 "向量数据库构建完成" 继续下一步')

if __name__ == "__main__":
    main()