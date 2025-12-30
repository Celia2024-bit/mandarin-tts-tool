/**
 * 工具函数：状态管理、DOM操作、通用工具
 */
const utils = {
    // 全局状态（单例）
    state: {
        isProcessing: false,
        isBatchProcessing: false,
        selectedVoice: "Mandarin Female (Xiaoyi)",
        speedPercent: 0,
        repeatCount: 1,
        loopInterval: 500,
        currentMode: "single",
        selectedSingleText: "",
        selectedSingleIdx: -1,
        selectedSingleAudio: "",
        fullAudioPath: "",
        sentences: [],
        audioCache: new Map(),
        isPlaying: false,
        isLooping: false,
        loopTimer: null,
        repeatCounter: 0
    },

    // DOM元素缓存
    elements: {},

    // 初始化DOM元素缓存
    initElements() {
        this.elements = {
            voiceSelect: document.getElementById('voice-select'),
            speedPercent: document.getElementById('speed-percent'),
            speedValue: document.getElementById('speed-value'),
            playBtn: document.getElementById('play-btn'),
            pauseBtn: document.getElementById('pause-btn'),
            stopBtn: document.getElementById('stop-btn'),
            singleMode: document.getElementById('single-mode'),
            fullMode: document.getElementById('full-mode'),
            repeatMinus: document.getElementById('repeat-minus'),
            repeatPlus: document.getElementById('repeat-plus'),
            repeatCount: document.getElementById('repeat-count'),
            loopBtn: document.getElementById('loop-btn'),
            loopInterval: document.getElementById('loop-interval'),
            statusDisplay: document.getElementById('status-display'),
            inputText: document.getElementById('input-text'),
            processBtn: document.getElementById('process-btn'),
            clearBtn: document.getElementById('clear-btn'),
            sentenceList: document.getElementById('sentence-list'),
            batchGenerateBtn: document.getElementById('batch-generate-btn'),
            ocrImage: document.getElementById('ocr-image'),
            ocrPreview: document.getElementById('ocr-preview'),
            previewImage: document.getElementById('preview-image'),
            ocrProcessBtn: document.getElementById('ocr-process-btn'),
            audioPlayer: document.getElementById('audio-player'),
            audioSource: document.getElementById('audio-source')
        };
    },

    // 更新状态显示
    updateStatus(message, type = "success") {
        const statusEl = this.elements.statusDisplay;
        statusEl.textContent = `Status: ${message}`;
        
        // 移除所有状态类
        statusEl.classList.remove(
            'status-display--success',
            'status-display--error',
            'status-display--warning',
            'status-display--processing'
        );
        
        // 添加当前状态类
        switch(type) {
            case "error":
                statusEl.classList.add('status-display--error');
                break;
            case "warning":
                statusEl.classList.add('status-display--warning');
                break;
            case "processing":
                statusEl.classList.add('status-display--processing');
                break;
            default:
                statusEl.classList.add('status-display--success');
        }
    },

    // 更新按钮状态
    updateButtonStates() {
        const { state, elements } = this;
        
        elements.playBtn.disabled = state.isProcessing || state.isBatchProcessing || (state.isPlaying && !state.isLooping);
        elements.pauseBtn.disabled = !state.isPlaying;
        elements.stopBtn.disabled = !state.isPlaying && !state.isLooping;
        elements.processBtn.disabled = state.isProcessing || state.isBatchProcessing;
        elements.batchGenerateBtn.disabled = state.isProcessing || state.isBatchProcessing || state.sentences.length === 0;
        elements.ocrProcessBtn.disabled = state.isProcessing || state.isBatchProcessing;
    },

    // 设置播放模式
    setMode(mode) {
        const { state, elements } = this;
        state.currentMode = mode;
        
        if (mode === 'single') {
            elements.singleMode.classList.add('btn--mode-active');
            elements.fullMode.classList.remove('btn--mode-active');
        } else {
            elements.fullMode.classList.add('btn--mode-active');
            elements.singleMode.classList.remove('btn--mode-active');
        }
        
        this.updateStatus(`Ready | Mode: ${mode.charAt(0).toUpperCase() + mode.slice(1)}`);
    },

    // 渲染句子列表
    renderSentenceList(sentences) {
        const { sentenceList } = this.elements;
        sentenceList.innerHTML = '';
        
        if (sentences.length === 0) {
            sentenceList.innerHTML = `
                <div class="sentence-list__empty">
                    没有检测到可分割的句子
                </div>
            `;
            return;
        }

        sentences.forEach((sentence, index) => {
            const sentenceItem = document.createElement('div');
            sentenceItem.className = 'sentence-item';
            sentenceItem.innerHTML = `
                <div class="sentence-item__content">
                    <span class="sentence-item__index">${index + 1}</span>
                    <p class="sentence-item__text">${sentence}</p>
                </div>
            `;
            
            // 点击句子播放（绑定到window，避免闭包问题）
            sentenceItem.addEventListener('click', () => {
                window.app.generateSingleSentence(sentence, index);
            });
            
            sentenceList.appendChild(sentenceItem);
        });
    },

    // 清空句子列表
    clearSentenceList() {
        const { sentenceList } = this.elements;
        sentenceList.innerHTML = `
            <div class="sentence-list__empty">
                点击"Process Text"生成句子列表
            </div>
        `;
    },

    // 清除循环计时器
    clearLoopTimer() {
        if (this.state.loopTimer) {
            clearTimeout(this.state.loopTimer);
            this.state.loopTimer = null;
        }
    },

    // 处理图片预览
    handleImagePreview(file) {
        const { ocrPreview, previewImage } = this.elements;
        const reader = new FileReader();
        
        reader.onload = (event) => {
            previewImage.src = event.target.result;
            ocrPreview.classList.remove('hidden');
        };
        
        reader.readAsDataURL(file);
    }
};