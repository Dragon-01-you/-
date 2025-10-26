import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
# 关键修正：1.0.0版本Document在langchain_core.documents下
from langchain_core.documents import Document

def load_documents_with_source(data_path):
    """加载文档并保存来源（文件名）"""
    documents = []
    txt_files = []
    
    # 遍历所有txt文件
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                txt_files.append(file_path)
    
    print(f"找到 {len(txt_files)} 个文本文件")
    
    for file_path in txt_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取文件名作为来源（如“奖学金.txt”）
            source = os.path.basename(file_path)
            
            # 创建Document对象，强制保存来源信息
            doc = Document(
                page_content=content,
                metadata={"source": source}
            )
            documents.append(doc)
            print(f"   ✅ 加载成功：{source}")
        
        except Exception as e:
            print(f"   ❌ 加载失败 {os.path.basename(file_path)}: {str(e)}")
    
    return documents

def main():
    print("🎯 重新构建带来源信息的向量数据库（适配langchain_core==1.0.0）")
    
    # 1. 配置路径
    data_path = "江西工业工程职业技术学院_数据仓库"
    db_path = "./vector_db"  # 覆盖旧向量库
    
    # 2. 强制删除旧向量库（彻底清理）
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        print("✅ 已删除旧向量数据库")
    
    # 3. 初始化文本分割器和嵌入模型
    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separator="\n"
    )
    embeddings = HuggingFaceEmbeddings(
        model_name="GanymedeNil/text2vec-large-chinese"
    )
    print("✅ 文本工具和嵌入模型初始化完成")
    
    # 4. 加载文档（带文件名来源）
    print("\n📄 加载文档...")
    documents = load_documents_with_source(data_path)
    if len(documents) == 0:
        print("❌ 未加载到任何文档")
        return
    
    # 5. 分割文本（每个块都保留来源）
    print("\n✂️  分割文本...")
    all_chunks = []
    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        for chunk in chunks:
            chunk_doc = Document(
                page_content=chunk,
                metadata={"source": doc.metadata["source"]}  # 分割后不丢失来源
            )
            all_chunks.append(chunk_doc)
    print(f"✅ 文本分割完成，共 {len(all_chunks)} 个块")
    
    # 6. 构建新向量库
    print("\n🛠️  构建向量数据库...")
    vector_db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=db_path
    )
    print("✅ 新向量数据库构建完成！")
    print(f"📁 数据库位置：{db_path}")

if __name__ == "__main__":
    main()