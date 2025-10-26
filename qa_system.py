import os
import requests
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

class JXIEEQASystem:
    def __init__(self):
        print("🎯 初始化江西工业工程职业技术学院问答系统...")
        
        # 加载向量数据库
        self.embeddings = HuggingFaceEmbeddings(
            model_name="GanymedeNil/text2vec-large-chinese"
        )
        self.vector_db = Chroma(
            persist_directory="./vector_db",
            embedding_function=self.embeddings
        )
        
        # 创建检索器（优化：降低相似度阈值，增加关联匹配）
        self.retriever = self.vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 3,  # 增加检索数量，避免漏找
                "score_threshold": 0.3  # 降低阈值，提高关联文档召回率
            }
        )
        
        # Ollama配置
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "deepseek-r1:7b"
        
        # 对话历史：新增“前一轮文档来源”存储，用于追问关联
        self.chat_history = []
        self.last_sources = []  # 保存前一轮检索到的文档来源（如["奖学金.txt"]）
        
        print("✅ 问答系统初始化完成！")
        print(f"🤖 已连接Ollama模型: {self.model_name}")
        print("💡 支持连续追问（如先问'奖学金'，再问'那助学金呢？'）")
        print("💡 输入'退出'结束，输入'清空历史'重置对话记录")
    
    def clear_history(self):
        """清空对话历史和前一轮来源"""
        self.chat_history = []
        self.last_sources = []
        return "✅ 对话历史已清空，可重新开始提问"
    
    def search_documents(self, question):
        """优化检索：追问时优先关联前一轮文档来源"""
        try:
            # 如果有前一轮来源，检索时优先匹配这些来源的文档
            if self.last_sources:
                # 拼接“历史来源+当前问题”作为检索关键词，增强关联
                enhanced_question = f"基于{', '.join(self.last_sources)}文档，回答：{question}"
                docs = self.retriever.invoke(enhanced_question)
                # 若关联检索到结果，直接返回；若无，再用原问题检索
                if docs:
                    return docs
            
            # 无历史来源或关联检索失败，用原问题检索
            return self.retriever.invoke(question)
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []
    
    def format_context(self, docs):
        """格式化上下文，同时更新前一轮文档来源"""
        context = ""
        current_sources = []  # 记录当前轮的文档来源
        for i, doc in enumerate(docs):
            content = doc.page_content
            source = doc.metadata.get('source', '未知来源')
            current_sources.append(source)
            context += f"【资料{i+1} - 来源：{source}】\n{content}\n\n"
        
        # 更新“前一轮来源”，用于下一次追问关联
        self.last_sources = current_sources
        return context
    
    def ask_ollama(self, prompt):
        """调用Ollama API生成回答"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "top_p": 0.8,
                    "num_predict": 1000,
                    "num_ctx": 2048  # 扩大上下文窗口，适配更长的历史关联
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json().get("response", "❌ 模型返回为空")
            else:
                return f"❌ Ollama API调用失败: {response.status_code}\n响应: {response.text}"
                
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接到Ollama服务，请确保Ollama正在运行"
        except Exception as e:
            return f"❌ 调用Ollama模型失败: {str(e)}"
    
    def smart_qa(self, question):
        """智能问答：优化追问关联，优先从历史文档找信息"""
        print(f"\n🔍 正在搜索相关资料...")
        
        try:
            # 处理特殊指令
            if question.strip() == "清空历史":
                return self.clear_history()
            
            # 1. 检索相关文档（已优化：关联前一轮来源）
            docs = self.search_documents(question)
            if not docs:
                return "❌ 没有找到相关学校资料"
            print(f"✅ 找到 {len(docs)} 条相关记录")
            
            # 2. 格式化上下文（更新前一轮来源）
            context = self.format_context(docs)
            all_sources = self.last_sources  # 直接用当前轮的来源
            
            # 3. 拼接对话历史（强调追问需关联前一轮资料）
            history_str = ""
            if self.chat_history:
                recent_history = self.chat_history[-3:]  # 保留最近3轮，避免过载
                for h in recent_history:
                    history_str += f"用户之前问：{h['question']}\n助手之前答：{h['answer']}\n\n"
            
            # 4. 优化提示词：强制模型优先从历史关联的资料中找信息
            prompt = f"""你是江西工业工程职业技术学院的智能助手，必须按以下优先级回答：
1. 先从「对话历史提到的资料」（如之前的奖学金.txt）中提取当前问题的信息；
2. 再结合「当前检索到的资料」补充；
3. 禁止忽略历史资料，直接说“没找到”。

【对话历史】
{history_str}

【当前检索到的资料（含来源）】
{context}

【当前用户问题】
{question}

回答要求：
1. 若历史资料（如奖学金.txt）中有当前问题的信息，必须优先引用；
2. 分点说明，明确区分“历史资料信息”和“当前新资料信息”（如有）；
3. 资料无相关信息时，才回复“资料中没有找到相关信息”；
4. 最后补充“信息来源于：{', '.join(all_sources)}”。

请开始回答："""
            
            # 5. 生成回答并保存历史
            print("🤖 正在生成智能回答...")
            answer = self.ask_ollama(prompt)
            self.chat_history.append({
                "question": question,
                "answer": answer
            })
            
            return f"💡 智能回答：\n{answer}\n"
            
        except Exception as e:
            return f"❌ 问答过程出错: {str(e)}"
    
    def simple_qa(self, question):
        """简化版问答（只返回检索结果）"""
        print(f"\n🔍 正在搜索相关资料...")
        try:
            docs = self.search_documents(question)
            if not docs:
                return "❌ 没有找到相关学校资料"
            
            print(f"✅ 找到 {len(docs)} 条相关记录：")
            result = "基于学校资料，找到以下相关信息：\n\n"
            for i, doc in enumerate(docs, 1):
                content = doc.page_content
                source = doc.metadata.get('source', '未知来源')
                result += f"【信息{i} - 来源：{source}】\n{content}\n{'='*50}\n\n"
                print(f"   📄 信息{i}: {content[:100]}...")
            return result
        except Exception as e:
            return f"❌ 搜索失败: {str(e)}"

def test_ollama_connection():
    """测试Ollama连接"""
    print("🔧 测试Ollama连接...")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json()
            print("✅ Ollama连接成功！")
            print("📋 可用模型：")
            for model in models.get('models', []):
                print(f"   - {model['name']}")
            return True
        else:
            print("❌ 无法获取模型列表")
            return False
    except Exception as e:
        print(f"❌ Ollama连接测试失败: {e}")
        print("💡 请确保：")
        print("   1. Ollama服务正在运行")
        print("   2. DeepSeek模型已下载（运行: ollama pull deepseek-r1:7b）")
        print("   3. 服务地址是 http://localhost:11434")
        return False

def main():
    ollama_available = test_ollama_connection()
    qa_system = JXIEEQASystem()
    
    print("\n" + "="*60)
    print("🎓 江西工业工程职业技术学院智能问答系统")
    print("="*60)
    if ollama_available:
        print("✅ 智能模式：检索 + AI生成回答（优化追问关联）")
    else:
        print("⚠️  简化模式：只显示检索结果")
    print("支持的问题类型：奖学金、助学金、图书馆、专业设置等")
    print("="*60)
    
    while True:
        try:
            question = input("\n❓ 请输入你的问题（输入'退出'结束）: ").strip()
            if question.lower() in ['退出', 'exit', 'quit']:
                print("👋 感谢使用，再见！")
                break
            if not question:
                continue
            
            answer = qa_system.smart_qa(question) if ollama_available else qa_system.simple_qa(question)
            print(f"\n{answer}")
        except KeyboardInterrupt:
            print("\n👋 感谢使用，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()