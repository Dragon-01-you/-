// 简化版前端逻辑，确保没有process引用

// 基本的聊天系统功能
class ChatSystem {
    constructor() {
        // 简单的DOM引用
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        
        // 静态API URL，直接设置
        this.apiUrl = 'http://localhost:8000/api/ask';
        
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
        
        // 简单添加消息到界面
        this.addMessage('user', message);
        this.messageInput.value = '';
        
        // 模拟机器人回复
        setTimeout(() => {
            this.addMessage('bot', '这是一条模拟回复。网站图标已添加，您可以在浏览器标签页查看。');
        }, 500);
    }
    
    addMessage(type, content) {
        if (!this.chatMessages) return;
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}-message`;
        msgDiv.textContent = content;
        
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
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
        chatSystem.addMessage('bot', '欢迎使用江西工业智能问答系统！网站图标已成功添加。');
    }
});