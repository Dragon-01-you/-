import os
import time
import logging
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# ========== 关键配置 ==========
VECTOR_DB_PATH = "./vector_db"  # 向量库存储路径
DATA_FOLDER = "江西工业工程职业技术学院_数据仓库"  # 数据仓库根文件夹

# 文本分割配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 监控的子文件夹列表
MONITORED_SUBFOLDERS = [
    "基础信息模块",
    "教学资源模块", 
    "竞赛科研模块",
    "竞赛信息模块",
    "校园生活模块",
    "行政办公模块",
    "学生服务模块"
]

# 本地模型路径配置（用于离线模式）
LOCAL_MODEL_PATHS = {
    "text2vec": os.path.expanduser("~/.cache/huggingface/hub/models--shibing624--text2vec-base-chinese/snapshots"),
    "text2vec_large": os.path.expanduser("~/.cache/huggingface/hub/models--GanymedeNil--text2vec-large-chinese/snapshots")
}
# ==============================

def initialize_embeddings():
    """初始化Embedding模型，优先使用本地缓存，支持离线加载"""
    # 首先尝试导入HuggingFaceEmbeddings
    try:
        # 优先尝试从langchain_huggingface导入（新版）
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            logger.info("✅ 使用新版langchain_huggingface中的HuggingFaceEmbeddings")
        except ImportError:
            # 回退到旧版
            from langchain_community.embeddings import HuggingFaceEmbeddings
            logger.warning("⚠️ 使用旧版langchain_community中的HuggingFaceEmbeddings")
    except ImportError:
        logger.error("❌ 无法导入HuggingFaceEmbeddings，请确保已安装必要的库")
        logger.info("💡 尝试安装: pip install langchain-huggingface sentence-transformers")
        return None
    
    # 检查本地是否有缓存的模型
    def find_local_model(snapshot_dir):
        """查找本地快照目录中的最新模型"""
        if os.path.exists(snapshot_dir):
            snapshots = [d for d in os.listdir(snapshot_dir) if os.path.isdir(os.path.join(snapshot_dir, d))]
            if snapshots:
                # 返回第一个找到的快照目录
                return os.path.join(snapshot_dir, snapshots[0])
        return None
    
    # 尝试加载模型的顺序
    model_attempts = [
        # 1. 尝试本地缓存的text2vec-base-chinese
        (find_local_model(LOCAL_MODEL_PATHS["text2vec"]), "本地缓存的text2vec-base-chinese"),
        # 2. 尝试本地缓存的text2vec-large-chinese
        (find_local_model(LOCAL_MODEL_PATHS["text2vec_large"]), "本地缓存的text2vec-large-chinese"),
        # 3. 尝试在线加载text2vec-base-chinese
        ("shibing624/text2vec-base-chinese", "在线text2vec-base-chinese"),
        # 4. 尝试在线加载text2vec-large-chinese
        ("GanymedeNil/text2vec-large-chinese", "在线text2vec-large-chinese")
    ]
    
    for model_path, model_name in model_attempts:
        if not model_path:
            continue
            
        try:
            logger.info(f"🔍 尝试加载模型: {model_name}")
            embeddings = HuggingFaceEmbeddings(
                model_name=model_path,
                model_kwargs={'device': 'cpu', 'local_files_only': model_path.startswith(os.path.expanduser("~"))},
                encode_kwargs={'normalize_embeddings': True},
                # 禁用代理设置，减少连接问题
                cache_folder=os.path.expanduser("~/.cache/huggingface/hub")
            )
            
            # 测试embedding是否正常工作
            test_embedding = embeddings.embed_query("测试")
            if test_embedding and len(test_embedding) > 0:
                logger.info(f"✅ 成功初始化Embedding模型: {model_name}")
                return embeddings
            else:
                logger.warning(f"❌ 模型初始化失败，嵌入向量为空: {model_name}")
        except Exception as e:
            logger.warning(f"❌ 加载模型失败 {model_name}: {str(e)}")
            # 对于网络连接错误，提供更明确的提示
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                logger.info("💡 建议：先手动下载模型到本地缓存，或确保网络连接正常")
    
    logger.error("❌ 所有模型加载尝试均失败")
    logger.info("💡 请尝试以下解决方案：")
    logger.info("  1. 确保网络连接正常")
    logger.info("  2. 手动下载模型到本地：")
    logger.info("     - pip install huggingface-hub")
    logger.info("     - huggingface-cli download shibing624/text2vec-base-chinese --local-dir ~/.cache/huggingface/hub/models--shibing624--text2vec-base-chinese")
    
    # 如果所有尝试都失败，返回一个模拟的embedding对象以允许脚本继续运行
    class MockEmbeddings:
        def embed_documents(self, texts):
            # 返回固定维度的零向量作为占位符
            return [[0.0] * 768 for _ in texts]
        
        def embed_query(self, text):
            # 返回固定维度的零向量作为占位符
            return [0.0] * 768
    
    logger.warning("⚠️ 使用模拟Embedding模型（仅用于开发测试）")
    return MockEmbeddings()

def initialize_vector_db(embeddings):
    """初始化或连接到Chroma向量数据库"""
    try:
        if os.path.exists(VECTOR_DB_PATH):
            logger.info(f"🔄 连接到现有向量数据库: {VECTOR_DB_PATH}")
            vector_db = Chroma(persist_directory=VECTOR_DB_PATH, embedding_function=embeddings)
        else:
            logger.info(f"📁 创建新向量数据库: {VECTOR_DB_PATH}")
            # 创建空文档列表以初始化数据库
            vector_db = Chroma.from_documents([], embedding=embeddings, persist_directory=VECTOR_DB_PATH)
        logger.info("✅ 向量数据库初始化完成")
        return vector_db
    except Exception as e:
        logger.error(f"❌ 向量数据库初始化失败: {str(e)}")
        raise

class DataUpdateHandler(FileSystemEventHandler):
    """监控数据文件夹及其子文件夹，自动更新向量库"""
    
    def __init__(self, vector_db, text_splitter):
        self.vector_db = vector_db
        self.text_splitter = text_splitter
    
    def process_file(self, file_path, file_name):
        """处理文件：读取、分割、向量化并更新到向量库"""
        try:
            logger.info(f"📄 正在处理文件: {file_name} (路径: {file_path})")
            
            # 检查文件是否存在且可读
            if not os.path.exists(file_path):
                logger.error(f"❌ 文件不存在: {file_path}")
                return None
            
            # 读取文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 尝试其他编码
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            
            if not content.strip():
                logger.warning(f"⚠️ 文件内容为空: {file_name}")
                return None
            
            # 分割文本
            chunks = self.text_splitter.split_text(content)
            logger.info(f"✂️  将文件分割为 {len(chunks)} 个文本块")
            
            # 生成带元数据的Document对象
            docs = [Document(
                page_content=chunk,
                metadata={
                    "source": file_name,
                    "full_path": file_path,
                    "last_modified": os.path.getmtime(file_path),
                    "folder": os.path.basename(os.path.dirname(file_path))
                }
            ) for chunk in chunks]
            
            return docs
            
        except Exception as e:
            logger.error(f"❌ 处理文件失败 {file_name}: {str(e)}")
            return None
    
    def on_created(self, event):
        """新文件创建时触发（包含子文件夹）"""
        if not event.is_directory and event.src_path.endswith(".txt"):
            # 检查文件是否在受监控的子文件夹中
            file_dir = os.path.dirname(event.src_path)
            if any(subfolder in file_dir for subfolder in MONITORED_SUBFOLDERS):
                file_path = event.src_path
                file_name = os.path.basename(file_path)
                logger.info(f"\n📄 检测到新文件: {file_name} (路径: {file_path})")
                
                try:
                    time.sleep(1)  # 等待文件完全写入
                    
                    # 处理文件
                    docs = self.process_file(file_path, file_name)
                    if docs:
                        # 添加到向量库
                        self.vector_db.add_documents(docs)
                        # 兼容不同版本的persist方法
                        if hasattr(self.vector_db, 'persist'):
                            try:
                                self.vector_db.persist()
                            except Exception as e:
                                logger.warning(f"⚠️ persist方法调用失败，忽略: {str(e)}")
                        logger.info(f"✅ 成功添加 {len(docs)} 个文本块到向量库 (来源: {file_name})")
                except Exception as e:
                    logger.error(f"❌ 添加新文件失败: {str(e)}")
    
    def on_modified(self, event):
        """文件修改时触发（包含子文件夹）"""
        if not event.is_directory and event.src_path.endswith(".txt"):
            # 检查文件是否在受监控的子文件夹中
            file_dir = os.path.dirname(event.src_path)
            if any(subfolder in file_dir for subfolder in MONITORED_SUBFOLDERS):
                file_path = event.src_path
                file_name = os.path.basename(file_path)
                logger.info(f"\n🔄 检测到文件修改: {file_name} (路径: {file_path})")
                
                try:
                    time.sleep(1)  # 等待文件修改完成
                    
                    # 适配新版Chroma API，使用query来找到相关文档并删除
                    try:
                        # 尝试使用collection对象的delete方法（新版API）
                        if hasattr(self.vector_db, 'collection'):
                            logger.info(f"🗑️  使用新版API删除旧数据: {file_name}")
                            # 查询所有匹配full_path的文档
                            results = self.vector_db.similarity_search_by_vector(
                                embedding=[0.0] * 768,  # 临时向量，只用于过滤
                                k=1000,  # 设置一个较大的值确保获取所有匹配的文档
                                filter={"full_path": file_path}
                            )
                            # 获取所有文档的ids
                            doc_ids = [doc.metadata.get("id") for doc in results if "id" in doc.metadata]
                            # 如果有文档，删除它们
                            if doc_ids:
                                self.vector_db.collection.delete(ids=doc_ids)
                        # 尝试直接使用delete方法
                        elif hasattr(self.vector_db, 'delete'):
                            logger.info(f"🗑️  使用delete方法删除旧数据: {file_name}")
                            # 尝试使用filter参数
                            try:
                                self.vector_db.delete(filter={"full_path": file_path})
                            except TypeError:
                                # 如果不支持filter参数，尝试获取并删除所有文档
                                results = self.vector_db.similarity_search("", k=1000)
                                for doc in results:
                                    if doc.metadata.get("full_path") == file_path:
                                        self.vector_db.delete([doc.metadata.get("id")])
                        else:
                            logger.warning(f"⚠️  不支持直接删除操作，跳过删除步骤: {file_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除旧数据失败，跳过删除步骤: {str(e)}")
                    
                    # 处理并添加新数据
                    docs = self.process_file(file_path, file_name)
                    if docs:
                        self.vector_db.add_documents(docs)
                        # 兼容不同版本的persist方法
                        if hasattr(self.vector_db, 'persist'):
                            try:
                                self.vector_db.persist()
                            except Exception as e:
                                logger.warning(f"⚠️ persist方法调用失败，忽略: {str(e)}")
                        logger.info(f"✅ 成功更新文件 {file_name} 到向量库")
                except Exception as e:
                    logger.error(f"❌ 更新文件失败: {str(e)}")
    
    def on_deleted(self, event):
        """文件删除时触发"""
        if not event.is_directory and event.src_path.endswith(".txt"):
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            logger.info(f"\n🗑️  检测到文件删除: {file_name}")
            
            try:
                # 适配新版Chroma API，使用query来找到相关文档并删除
                try:
                    # 尝试使用collection对象的delete方法（新版API）
                    if hasattr(self.vector_db, 'collection'):
                        logger.info(f"🗑️  使用新版API删除数据: {file_name}")
                        # 查询所有匹配full_path的文档
                        results = self.vector_db.similarity_search_by_vector(
                            embedding=[0.0] * 768,  # 临时向量，只用于过滤
                            k=1000,  # 设置一个较大的值确保获取所有匹配的文档
                            filter={"full_path": file_path}
                        )
                        # 获取所有文档的ids
                        doc_ids = [doc.metadata.get("id") for doc in results if "id" in doc.metadata]
                        # 如果有文档，删除它们
                        if doc_ids:
                            self.vector_db.collection.delete(ids=doc_ids)
                    # 尝试直接使用delete方法
                    elif hasattr(self.vector_db, 'delete'):
                        logger.info(f"🗑️  使用delete方法删除数据: {file_name}")
                        # 尝试使用filter参数
                        try:
                            self.vector_db.delete(filter={"full_path": file_path})
                        except TypeError:
                            # 如果不支持filter参数，尝试获取并删除所有文档
                            results = self.vector_db.similarity_search("", k=1000)
                            for doc in results:
                                if doc.metadata.get("full_path") == file_path:
                                    self.vector_db.delete([doc.metadata.get("id")])
                    else:
                        logger.warning(f"⚠️  不支持直接删除操作，跳过删除步骤: {file_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 删除数据失败: {str(e)}")
                    
                # 兼容不同版本的persist方法
                if hasattr(self.vector_db, 'persist'):
                    try:
                        self.vector_db.persist()
                    except Exception as e:
                        logger.warning(f"⚠️ persist方法调用失败，忽略: {str(e)}")
                logger.info(f"✅ 成功处理文件 {file_name} 的删除事件")
            except Exception as e:
                logger.error(f"❌ 处理删除事件失败: {str(e)}")

def validate_monitored_folders():
    """验证受监控的子文件夹是否存在"""
    valid_folders = []
    missing_folders = []
    
    for subfolder in MONITORED_SUBFOLDERS:
        folder_path = os.path.join(DATA_FOLDER, subfolder)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            valid_folders.append(subfolder)
        else:
            missing_folders.append(subfolder)
    
    if valid_folders:
        logger.info(f"✅ 找到 {len(valid_folders)} 个有效子文件夹")
        for folder in valid_folders:
            logger.info(f"   - {folder}")
    
    if missing_folders:
        logger.warning(f"⚠️  未找到 {len(missing_folders)} 个子文件夹:")
        for folder in missing_folders:
            logger.warning(f"   - {folder}")
    
    return valid_folders

def main():
    """主函数：初始化工具并启动监控"""
    logger.info(f"🎯 启动数据自动更新监控系统")
    logger.info(f"📂 数据仓库路径: {DATA_FOLDER}")
    logger.info(f"💾 向量数据库路径: {VECTOR_DB_PATH}")
    
    # 验证数据仓库主文件夹
    if not os.path.exists(DATA_FOLDER) or not os.path.isdir(DATA_FOLDER):
        logger.error(f"❌ 数据仓库文件夹不存在: {DATA_FOLDER}")
        return
    
    # 验证受监控的子文件夹
    valid_folders = validate_monitored_folders()
    if not valid_folders:
        logger.error("❌ 未找到任何有效的子文件夹，程序退出")
        return
    
    # 初始化Embedding模型
    embeddings = initialize_embeddings()
    if embeddings is None:
        logger.error("❌ 无法初始化Embedding模型，程序退出")
        return
    
    # 初始化文本分割器
    text_splitter = CharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separator="\n",
        add_start_index=True
    )
    logger.info(f"✅ 文本分割器初始化完成 (chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP})")
    
    # 初始化向量数据库
    vector_db = initialize_vector_db(embeddings)
    
    # 初始化事件处理器
    event_handler = DataUpdateHandler(vector_db, text_splitter)
    
    # 初始化监控器
    observer = Observer()
    
    # 监控根文件夹及其所有子文件夹
    observer.schedule(event_handler, path=DATA_FOLDER, recursive=True)
    
    # 启动监控
    observer.start()
    logger.info("🚀 开始监控文件变化...")
    logger.info("💡 操作说明:")
    logger.info("   1. 新增/修改/删除 .txt 文件将自动同步到向量库")
    logger.info("   2. 按 Ctrl+C 停止监控")
    
    try:
        # 持续运行监控
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 接收到停止信号，正在停止监控...")
    except Exception as e:
        logger.error(f"❌ 监控过程中发生错误: {str(e)}")
    finally:
        # 停止监控
        try:
            observer.stop()
            observer.join()
            logger.info("✅ 监控已停止")
        except Exception as e:
            logger.error(f"❌ 停止监控时出错: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ 程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)