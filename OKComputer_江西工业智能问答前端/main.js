// 简化版前端逻辑，确保没有process引用

// 基本的聊天系统功能
class ChatSystem {
    constructor() {
        // 简单的DOM引用
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        
        // 使用相对路径API URL，配合vercel.json的代理配置
        this.apiUrl = '/api/ask';
        
        // 初始化事件监听器
        this.initListeners();
    }
    
    initListeners() {
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }
    
    sendMessage() {
        if (!this.messageInput) return;
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // 添加用户消息到界面
        this.addMessage('user', message);
        this.messageInput.value = '';
        
        // 显示加载状态
        const loadingMessage = this.addMessage('bot', '正在思考...');
        
        // 调用真实API
        fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('API请求失败');
            }
            return response.json();
        })
        .then(data => {
            // 移除加载消息
            if (loadingMessage && loadingMessage.parentNode) {
                loadingMessage.parentNode.removeChild(loadingMessage);
            }
            
            // 显示API返回的回答
            if (data.answer) {
                this.addMessage('bot', data.answer);
            } else {
                this.addMessage('bot', '抱歉，未能获取到回答，请稍后重试。');
            }
        })
        .catch(error => {
            console.error('API调用错误:', error);
            // 移除加载消息
            if (loadingMessage && loadingMessage.parentNode) {
                loadingMessage.parentNode.removeChild(loadingMessage);
            }
            this.addMessage('bot', '服务暂时不可用，请稍后再试。');
        });
    }
    
    addMessage(type, content) {
        if (!this.chatMessages) return;
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}-message`;
        msgDiv.textContent = content;
        
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return msgDiv; // 返回创建的消息元素，便于后续操作
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查DOM元素是否存在
    if (document.getElementById('chatMessages') && 
        document.getElementById('messageInput') && 
        document.getElementById('sendButton')) {
        
        // 初始化聊天系统
        const chatSystem = new ChatSystem();
        
        // 显示欢迎消息
        chatSystem.addMessage('bot', '欢迎使用江西工业智能问答系统！请输入您的问题。');
    }
});