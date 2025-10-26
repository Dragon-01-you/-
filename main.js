// 聊天系统主类
class ChatSystem {
    constructor() {
        // DOM元素引用
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.errorModal = document.getElementById('errorModal');
        this.errorMessage = document.getElementById('errorMessage');
        this.closeErrorButton = document.getElementById('closeErrorButton');
        
        // API配置 - 支持环境变量和动态配置
        this.apiUrl = this.getApiUrl();
        
        // 状态管理
        this.isLoading = false;
        this.chatHistory = [];
        
        // 初始化事件监听器
        this.initEventListeners();
    }
    
    getApiUrl() {
        // 优先使用环境变量（Vercel部署时可以设置）
        if (process && process.env && process.env.API_URL) {
            return process.env.API_URL;
        }
        
        // 检测是否在开发环境
        const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        
        // 根据环境返回不同的API地址
        if (isDev) {
            return 'http://localhost:8000/api/ask';
        } else {
            // 生产环境使用相对路径，配合Vercel的代理功能或直接使用绝对路径
            // 注意：部署后需要将这里修改为您实际的后端API地址
            return '/api/ask';
        }
    }
        
    initEventListeners() {
        // 发送按钮点击事件
        this.sendButton.addEventListener('click', () => this.handleSendMessage());
        
        // 输入框键盘事件
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // 输入框输入事件 - 自动调整高度
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
        });
        
        // 关闭错误模态框事件
        this.closeErrorButton.addEventListener('click', () => this.hideErrorModal());
        
        // 点击错误模态框背景关闭
        this.errorModal.addEventListener('click', (e) => {
            if (e.target === this.errorModal) {
                this.hideErrorModal();
            }
        });
    }
    
    handleSendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) {
            return;
        }
        
        // 添加用户消息
        this.addMessage(message, 'user');
        
        // 清空输入框并重置高度
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // 显示加载状态
        this.showLoading();
        
        // 调用API获取回答
        this.fetchAnswer(message);
    }
    
    async fetchAnswer(message) {
        try {
            // 模拟API调用延迟
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 调用真实API
            const response = await this.callApi(message);
            
            // 添加AI回答
            this.addMessage(response, 'ai');
            
            // 更新聊天历史
            this.chatHistory.push({
                role: 'user',
                content: message
            });
            
            this.chatHistory.push({
                role: 'assistant',
                content: response.answer
            });
        } catch (error) {
            this.hideLoading();
            this.showError('网络连接出现问题，请检查后端服务是否运行。');
            console.error('API调用错误:', error);
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.style.opacity = '0';
        
        const time = this.getCurrentTime();
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">
                    ${this.formatMessageContent(content)}
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        
        // 使用Anime.js实现动画
        anime({
            targets: messageDiv,
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 300,
            easing: 'easeOutQuad'
        });
        
        // 滚动到底部
        this.scrollToBottom();
    }
    
    formatMessageContent(content) {
        // 如果是字符串，转换为段落
        if (typeof content === 'string') {
            return content.split('\n').map(p => `<p>${p}</p>`).join('');
        }
        
        // 如果是对象，根据类型格式化
        if (typeof content === 'object') {
            let html = '';
            
            if (content.answer) {
                html += content.answer.split('\n').map(p => `<p>${p}</p>`).join('');
            }
            
            // 如果是实时搜索，添加标识
            if (content.is_real_time) {
                html += '<div class="message-realtime">';
                html += '<p><small>🔄 此回答包含实时搜索信息</small></p>';
                html += '</div>';
            }
            
            if (content.sources && content.sources.length > 0) {
                html += '<div class="message-sources">';
                html += '<p><small><strong>📚 信息来源于：</strong></small></p>';
                html += '<p><small>';
                html += content.sources.map(source => source.title || source).join('、');
                html += '</small></p>';
                html += '</div>';
            }
            
            return html || '<p>暂无相关信息</p>';
        }
        
        return `<p>${content}</p>`;
    }
    
    showLoading() {
        this.isLoading = true;
        this.sendButton.disabled = true;
        this.loadingIndicator.style.display = 'flex';
        
        // 动画显示加载指示器
        anime({
            targets: this.loadingIndicator,
            opacity: [0, 1],
            translateY: [-10, 0],
            duration: 200,
            easing: 'easeOutQuad'
        });
        
        this.scrollToBottom();
    }
    
    hideLoading() {
        this.isLoading = false;
        this.sendButton.disabled = false;
        
        // 动画隐藏加载指示器
        anime({
            targets: this.loadingIndicator,
            opacity: [1, 0],
            translateY: [0, -10],
            duration: 200,
            easing: 'easeInQuad',
            complete: () => {
                this.loadingIndicator.style.display = 'none';
            }
        });
    }
    
    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.errorModal.classList.add('show');
        
        // 动画显示模态框
        anime({
            targets: this.errorModal,
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuad'
        });
    }
    
    hideErrorModal() {
        anime({
            targets: this.errorModal,
            opacity: [1, 0],
            duration: 200,
            easing: 'easeInQuad',
            complete: () => {
                this.errorModal.classList.remove('show');
            }
        });
    }
    
    scrollToBottom() {
        // 延迟滚动以确保DOM已更新
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }
    
    // 调用真实的后端API
    async callApi(message) {
        // 准备请求数据
        const payload = {
            question: message,
            chat_history: this.chatHistory
        };
        
        // 发送请求到后端API
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`API错误: ${response.status}`);
        }
        
        // 解析响应数据
        const data = await response.json();
        
        // 构建返回格式，适配现有UI
        return {
            answer: data.answer || '未获取到回答',
            sources: data.sources ? data.sources.map(src => ({ title: src, url: '#' })) : [],
            is_real_time: data.is_real_time || false
        };
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new ChatSystem();
});

// 防止页面刷新时丢失焦点
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        setTimeout(() => {
            document.getElementById('messageInput')?.focus();
        }, 100);
    }
});