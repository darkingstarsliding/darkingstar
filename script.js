// AI智能体前端交互脚本

class AIChat {
    constructor() {
        this.initElements();
        this.attachEventListeners();
        this.messageHistory = [];
        this.isTyping = false;
    }

    initElements() {
        this.sidebar = document.querySelector('.sidebar');
        this.sidebarToggle = document.querySelector('.sidebar-toggle');
        this.messageInput = document.querySelector('.message-input');
        this.sendBtn = document.querySelector('.send-btn');
        this.chatMessages = document.querySelector('.chat-messages');
        this.newChatBtn = document.querySelector('.btn-new');
        this.charCount = document.querySelector('.char-count');
        this.modelSelect = document.querySelector('.model-select');
        this.historyItems = document.querySelectorAll('.history-item');
    }

    attachEventListeners() {
        // 侧边栏切换
        this.sidebarToggle?.addEventListener('click', () => {
            this.sidebar?.classList.toggle('open');
        });

        // 新建对话
        this.newChatBtn?.addEventListener('click', () => {
            this.createNewChat();
        });

        // 发送消息
        this.sendBtn?.addEventListener('click', () => {
            this.sendMessage();
        });

        // 输入框事件
        this.messageInput?.addEventListener('input', () => {
            this.handleInputChange();
        });

        this.messageInput?.addEventListener('keydown', (e) => {
            this.handleKeyPress(e);
        });

        // 历史记录点击
        this.historyItems.forEach(item => {
            item.addEventListener('click', () => {
                this.selectHistory(item);
            });
        });

        // 模型选择
        this.modelSelect?.addEventListener('change', (e) => {
            this.handleModelChange(e.target.value);
        });

        // 附件按钮
        document.querySelector('.attachment-btn')?.addEventListener('click', () => {
            this.handleAttachment();
        });

        // 语音按钮
        document.querySelector('.voice-btn')?.addEventListener('click', () => {
            this.handleVoiceInput();
        });
    }

    // 处理输入框变化
    handleInputChange() {
        const value = this.messageInput.value.trim();
        const maxLength = 2000;
        
        // 更新字符计数
        this.charCount.textContent = `${this.messageInput.value.length}/${maxLength}`;
        
        // 启用/禁用发送按钮
        if (this.sendBtn) {
            this.sendBtn.disabled = !value || this.isTyping;
        }

        // 自动调整高度
        this.autoResizeTextarea();
    }

    // 自动调整文本框高度
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
    }

    // 处理键盘事件
    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    // 发送消息
    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isTyping) return;

        // 添加用户消息
        this.addUserMessage(message);
        
        // 清空输入框
        this.messageInput.value = '';
        this.handleInputChange();
        
        // 显示AI正在输入
        this.showTypingIndicator();
        
        // 模拟AI响应
        setTimeout(() => {
            this.removeTypingIndicator();
            this.addAIMessage(this.generateAIResponse(message));
        }, 1000 + Math.random() * 1000);
    }

    // 添加用户消息
    addUserMessage(text) {
        const messageDiv = this.createMessageElement(text, 'user');
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        this.messageHistory.push({
            role: 'user',
            content: text,
            timestamp: new Date()
        });
    }

    // 添加AI消息
    addAIMessage(text) {
        const messageDiv = this.createMessageElement(text, 'ai');
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        this.messageHistory.push({
            role: 'ai',
            content: text,
            timestamp: new Date()
        });
    }

    // 创建消息元素
    createMessageElement(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = `message-avatar ${type}-avatar`;
        avatarDiv.textContent = type === 'ai' ? '🤖' : 'U';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const senderDiv = document.createElement('div');
        senderDiv.className = 'message-sender';
        senderDiv.textContent = type === 'ai' ? 'AI智能体' : '你';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = this.formatMessage(text);
        
        contentDiv.appendChild(senderDiv);
        contentDiv.appendChild(textDiv);
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        return messageDiv;
    }

    // 格式化消息
    formatMessage(text) {
        // 简单的markdown格式化
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    // 滚动到底部
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    // 显示输入指示器
    showTypingIndicator() {
        this.isTyping = true;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar ai-avatar">🤖</div>
            <div class="message-content">
                <div class="message-sender">AI智能体</div>
                <div class="message-text">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    // 移除输入指示器
    removeTypingIndicator() {
        const typingIndicator = this.chatMessages.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        this.isTyping = false;
    }

    // 生成AI响应(模拟)
    generateAIResponse(userMessage) {
        const responses = [
            `我理解你的问题。关于"${userMessage}"，我可以提供以下建议...`,
            `很好的问题!让我来帮你分析一下"${userMessage}"相关的信息。`,
            `收到你的消息。关于"${userMessage}"，这里有一些想法...`,
            `关于"${userMessage}"这个问题，我认为...`,
            `这是一个有趣的话题!针对"${userMessage}"，我可以为你提供帮助。`
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }

    // 新建对话
    createNewChat() {
        // 清空聊天记录
        this.chatMessages.innerHTML = '';
        
        // 重新添加欢迎消息
        const welcomeMessage = `
            <p>你好!我是AI智能体助手,很高兴为你服务!</p>
            <p>我可以帮你完成以下任务:</p>
            <ul class="feature-list">
                <li>💬 自然语言对话交流</li>
                <li>📝 文本生成与编辑</li>
                <li>🔍 信息检索与分析</li>
                <li>💻 编程代码协助</li>
                <li>🎨 创意设计与建议</li>
            </ul>
            <p>有什么我可以帮助你的吗?</p>
        `;
        
        this.addAIMessage(welcomeMessage);
        
        // 清空历史记录
        this.messageHistory = [];
        
        // 更新侧边栏
        const todaySection = document.querySelector('.history-section:first-child');
        if (todaySection) {
            const newHistoryItem = document.createElement('div');
            newHistoryItem.className = 'history-item active';
            newHistoryItem.innerHTML = `
                <span class="chat-title">新对话</span>
                <span class="chat-time">刚刚</span>
            `;
            
            // 移除其他活动的类
            todaySection.querySelectorAll('.history-item').forEach(item => {
                item.classList.remove('active');
            });
            
            todaySection.insertBefore(newHistoryItem, todaySection.children[1]);
            
            // 添加点击事件
            newHistoryItem.addEventListener('click', () => {
                this.selectHistory(newHistoryItem);
            });
        }
    }

    // 选择历史记录
    selectHistory(item) {
        // 移除所有活动状态
        document.querySelectorAll('.history-item').forEach(i => {
            i.classList.remove('active');
        });
        
        // 添加活动状态
        item.classList.add('active');
        
        // 在移动端关闭侧边栏
        if (window.innerWidth <= 768) {
            this.sidebar?.classList.remove('open');
        }
    }

    // 处理模型变化
    handleModelChange(model) {
        console.log('模型已切换:', model);
        // 这里可以添加模型切换的逻辑
    }

    // 处理附件
    handleAttachment() {
        // 创建文件输入元素
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '*/*';
        
        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                console.log('选择了文件:', file.name);
                // 这里可以添加文件上传和处理的逻辑
            }
        };
        
        fileInput.click();
    }

    // 处理语音输入
    handleVoiceInput() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.lang = 'zh-CN';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            recognition.onstart = () => {
                console.log('开始语音输入...');
            };
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.messageInput.value = transcript;
                this.handleInputChange();
            };
            
            recognition.onerror = (event) => {
                console.error('语音识别错误:', event.error);
            };
            
            recognition.start();
        } else {
            alert('您的浏览器不支持语音输入功能');
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.aiChat = new AIChat();
    console.log('AI智能体已初始化');
});

// 添加CSS动画样式
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: flex;
        gap: 6px;
        padding: 8px 0;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        background: var(--text-secondary);
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.5;
        }
        30% {
            transform: translateY(-8px);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);