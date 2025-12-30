/**
 * 应用入口文件
 * 负责初始化、事件绑定、业务逻辑串联
 * 修复：语速默认值同步、Repeat次数限制、Loop无限循环分离
 */
window.app = {
    // 初始化应用
    async init() {
        // 初始化工具函数
        utils.initElements();
        const { state, elements } = utils;

        // 关键修复：强制同步滑块值与JS状态（解决语速默认值不一致）
        elements.speedPercent.value = state.speedPercent;
        elements.speedValue.textContent = `${state.speedPercent}%`;

        // 初始化状态
        utils.updateStatus('Ready');
        utils.updateButtonStates();
        elements.voiceSelect.value = state.selectedVoice;

        // 绑定事件监听
        this.bindEventListeners();
    },

    // 绑定所有事件监听
    bindEventListeners() {
        const { state, elements } = utils;

        // 语速控制
        elements.speedPercent.addEventListener('input', (e) => {
            const value = e.target.value;
            elements.speedValue.textContent = `${value}%`;
            state.speedPercent = parseInt(value);
        });

        // 播放控制
        elements.playBtn.addEventListener('click', () => this.playAudio());
        elements.pauseBtn.addEventListener('click', () => this.pauseAudio());
        elements.stopBtn.addEventListener('click', () => this.stopAudio());

        // 模式选择
        elements.singleMode.addEventListener('click', () => utils.setMode('single'));
        elements.fullMode.addEventListener('click', () => utils.setMode('full'));

        // 重复次数控制
        elements.repeatMinus.addEventListener('click', () => {
            if (state.repeatCount > 1) {
                state.repeatCount--;
                elements.repeatCount.value = state.repeatCount;
            }
        });

        elements.repeatPlus.addEventListener('click', () => {
            if (state.repeatCount < 99) {
                state.repeatCount++;
                elements.repeatCount.value = state.repeatCount;
            }
        });

        elements.repeatCount.addEventListener('change', (e) => {
            const value = parseInt(e.target.value);
            state.repeatCount = Math.max(1, Math.min(99, value));
            elements.repeatCount.value = state.repeatCount;
        });

        // 循环控制
        elements.loopBtn.addEventListener('click', () => this.toggleLoop());

        // 循环间隔
        elements.loopInterval.addEventListener('change', (e) => {
            const value = parseInt(e.target.value);
            state.loopInterval = Math.max(100, Math.min(5000, value));
            elements.loopInterval.value = state.loopInterval;
        });

        // 文本处理
        elements.processBtn.addEventListener('click', () => this.processText());
        elements.clearBtn.addEventListener('click', () => this.clearText());

        // 批量生成
        elements.batchGenerateBtn.addEventListener('click', () => this.batchGenerateAudio());

        // OCR相关
        elements.ocrImage.addEventListener('change', (e) => this.handleImageSelection(e));
        elements.ocrProcessBtn.addEventListener('click', () => this.performOCR());

        // 音频事件
        elements.audioPlayer.addEventListener('ended', () => this.handleAudioEnded());

        // 语音选择
        elements.voiceSelect.addEventListener('change', (e) => {
            state.selectedVoice = e.target.value;
            utils.updateStatus(`Voice changed to: ${state.selectedVoice} (需要重新生成音频)`, 'warning');
        });
    },

    // 处理文本（分句+生成全文音频）
    async processText() {
        const { state, elements } = utils;

        if (state.isProcessing) {
            utils.updateStatus('Processing: Please wait for tasks to finish...', 'processing');
            return;
        }

        const text = elements.inputText.value.trim();
        if (!text) {
            utils.updateStatus('Error: Input text is empty', 'error');
            return;
        }

        state.isProcessing = true;
        utils.updateButtonStates();
        utils.updateStatus('Processing: Splitting text into sentences...', 'processing');

        try {
            // 1. 调用API分句
            const splitResult = await api.splitText(text);
            state.sentences = splitResult.sentences;
            utils.renderSentenceList(splitResult.sentences);
            
            // 2. 生成全文音频
            utils.updateStatus('Processing: Generating full text audio...', 'processing');
            const audioResult = await api.generateFullAudio(text, state.selectedVoice, state.speedPercent);
            
            state.fullAudioPath = audioResult.audioUrl;
            utils.updateStatus(`Ready | Generated ${splitResult.count} sentences and full audio`);
            this.playAudio(true);

        } catch (error) {
            utils.updateStatus(`Error: ${error.message}`, 'error');
        } finally {
            state.isProcessing = false;
            utils.updateButtonStates();
        }
    },

    // 生成单句音频
// 生成单句音频
    async generateSingleSentence(sentence, idx) {
        const { state } = utils;

        if (state.isBatchProcessing || state.isProcessing) {
            utils.updateStatus("Processing: Please wait for tasks to finish...", 'processing');
            return;
        }
        
        if (!sentence) {
            utils.updateStatus("Error: Selected sentence is invalid", 'error');
            return;
        }

        // 关键修复1：点击新句子时，先停止旧音频和计时器
        this.stopAudio(); // 调用已有的stopAudio函数，停止所有播放和计时器

        state.selectedSingleText = sentence;
        state.selectedSingleIdx = idx;
        state.currentMode = 'single';
        utils.setMode('single');
        
        utils.updateStatus(`Processing: Generating audio for sentence ${idx + 1}... (Voice: ${state.selectedVoice})`, 'processing');

        try {
            // 检查缓存
            const cacheKey = `${state.selectedVoice}_${state.speedPercent}_${sentence}`;
            if (state.audioCache.has(cacheKey)) {
                state.selectedSingleAudio = state.audioCache.get(cacheKey);
                utils.updateStatus(`Ready | Play Type: Single Sentence (Cached) (Voice: ${state.selectedVoice})`);
                this.playAudio(true, false); // 这里是首次播放，isRepeat=false
                return;
            }

            // 调用API生成音频
            const audioUrl = await api.generateSingleAudio(sentence, state.selectedVoice, state.speedPercent);
            
            // 缓存音频地址
            state.audioCache.set(cacheKey, audioUrl);
            state.selectedSingleAudio = audioUrl;
            
            utils.updateStatus(`Ready | Play Type: Single Sentence Audio Generated (Voice: ${state.selectedVoice})`);
            this.playAudio(true, false); // 首次播放，isRepeat=false

        } catch (error) {
            utils.updateStatus(`Error: Play Type: Single Sentence ${error.message} (Voice: ${state.selectedVoice})`, 'error');
        } finally {
            utils.updateButtonStates();
        }
    },

    // 批量生成所有句子音频
    async batchGenerateAudio() {
        const { state } = utils;

        if (state.isProcessing || state.isBatchProcessing || state.sentences.length === 0) {
            utils.updateStatus("Error: No sentences to process or already processing", 'error');
            return;
        }

        state.isBatchProcessing = true;
        utils.updateButtonStates();
        utils.updateStatus(`Processing: Pre-generating audio for ${state.sentences.length} sentences...`, 'processing');

        try {
            let successCount = 0;
            const total = state.sentences.length;

            // 并行生成所有句子音频
            const promises = state.sentences.map(async (sentence) => {
                const cacheKey = `${state.selectedVoice}_${state.speedPercent}_${sentence}`;
                if (state.audioCache.has(cacheKey)) {
                    successCount++;
                    return;
                }

                try {
                    const audioUrl = await api.generateSingleAudio(sentence, state.selectedVoice, state.speedPercent);
                    state.audioCache.set(cacheKey, audioUrl);
                    successCount++;
                } catch (error) {
                    console.error(`生成句子音频失败: ${sentence}`, error);
                }
            });

            await Promise.all(promises);
            utils.updateStatus(`Ready | Batch generation completed: ${successCount}/${total} sentences successfully generated`);

        } catch (error) {
            utils.updateStatus(`Error: Batch generation failed - ${error.message}`, 'error');
        } finally {
            state.isBatchProcessing = false;
            utils.updateButtonStates();
        }
    },

    // 播放音频（修复：播放前重置重复计数）
// 播放音频（最终修复版：解决加载冲突+Repeat计数问题）
    playAudio(skipWarning = false, isRepeat = false) {
        const { state, elements } = utils;

        if (!skipWarning && !state.selectedSingleAudio && !state.fullAudioPath) {
            utils.updateStatus("Error: No audio generated yet", 'error');
            return;
        }

        // 只有用户主动点击Play才重置计数器
        if (!isRepeat) {
            state.repeatCounter = 0;
        }

        // 根据当前模式选择音频
        let audioUrl = state.currentMode === 'single' ? state.selectedSingleAudio : state.fullAudioPath;
        
        if (!audioUrl) {
            audioUrl = state.fullAudioPath;
            if (audioUrl) {
                utils.setMode('full');
            } else {
                utils.updateStatus("Error: No audio available", 'error');
                return;
            }
        }

        // 关键修复2：先移除旧的canplay监听，避免重复触发
        elements.audioPlayer.removeEventListener('canplay', this._onAudioCanPlay);
        // 关键修复3：设置音频源后，等待加载完成再播放
        elements.audioSource.src = audioUrl;
        elements.audioPlayer.load();

        // 定义加载完成后的播放函数
        this._onAudioCanPlay = () => {
            elements.audioPlayer.play()
                .then(() => {
                    state.isPlaying = true;
                    utils.updateStatus(`Playing: ${state.currentMode === 'single' ? 'Single Sentence' : 'Full Text'} (Voice: ${state.selectedVoice})`, 'processing');
                    utils.updateButtonStates();
                })
                .catch(error => {
                    // 捕获播放错误，给出明确提示
                    utils.updateStatus(`Error: Failed to play audio - ${error.message}`, 'error');
                });
            // 播放后移除监听，避免重复触发
            elements.audioPlayer.removeEventListener('canplay', this._onAudioCanPlay);
        };

        // 监听音频加载完成事件
        elements.audioPlayer.addEventListener('canplay', this._onAudioCanPlay);
    },

    // 暂停音频
    pauseAudio() {
        const { state, elements } = utils;

        if (state.isPlaying) {
            elements.audioPlayer.pause();
            state.isPlaying = false;
            utils.updateStatus(`Paused: ${state.currentMode === 'single' ? 'Single Sentence' : 'Full Text'}`, 'warning');
            utils.updateButtonStates();
        }
    },

    stopAudio() {
        const { state, elements } = utils;

        // 关键修复4：停止音频前，先移除canplay监听，避免残留触发
        elements.audioPlayer.removeEventListener('canplay', this._onAudioCanPlay);
        // 停止播放并重置进度
        elements.audioPlayer.pause();
        elements.audioPlayer.currentTime = 0;
        state.isPlaying = false;
        
        // 清除所有计时器和状态
        utils.clearLoopTimer();
        state.repeatCounter = 0;
        state.isLooping = false;
        elements.loopBtn.classList.remove('btn--danger');
        elements.loopBtn.classList.add('btn--purple');
        
        utils.updateStatus(`Stopped | Ready (Voice: ${state.selectedVoice})`);
        utils.updateButtonStates();
    },
    // 切换循环模式
    toggleLoop() {
        const { state, elements } = utils;

        state.isLooping = !state.isLooping;
        if (state.isLooping) {
            elements.loopBtn.classList.add('btn--danger');
            elements.loopBtn.classList.remove('btn--purple');
            utils.updateStatus(`Loop enabled | Interval: ${state.loopInterval}ms`, 'warning');
        } else {
            elements.loopBtn.classList.remove('btn--danger');
            elements.loopBtn.classList.add('btn--purple');
            utils.clearLoopTimer();
            state.repeatCounter = 0; // 重置重复计数
            utils.updateStatus(`Loop disabled`);
        }
    },

    // 处理音频播放结束（修复：Repeat和Loop互斥，明确终止条件）
    handleAudioEnded() {
        const { state } = utils;
        state.isPlaying = false;

        // 核心修复：Repeat和Loop二选一生效，互不干扰
        if (state.isLooping) {
            // ① 无限Loop模式：只在Loop开启时生效
            state.loopTimer = setTimeout(() => {
                this.playAudio(true, true);
            }, state.loopInterval);
            utils.updateStatus(`Loop: Playing again in ${state.loopInterval}ms`, 'processing');
        } else {
            // ② 有限Repeat模式：严格按设置次数执行，用完即停
            state.repeatCounter++;
            if (state.repeatCounter < state.repeatCount) {
                setTimeout(() => {
                    this.playAudio(true, true);
                }, state.loopInterval);
                utils.updateStatus(`Repeat: ${state.repeatCounter}/${state.repeatCount} completed`, 'processing');
            } else {
                // 终止条件：重复次数用尽，重置状态并停止
                state.repeatCounter = 0;
                utils.clearLoopTimer();
                utils.updateStatus(`Completed | Ready (Voice: ${state.selectedVoice})`);
            }
        }

        utils.updateButtonStates();
    },

    // 处理图片选择
    handleImageSelection(e) {
        const file = e.target.files[0];
        if (file) {
            utils.handleImagePreview(file);
        }
    },

    // 执行OCR识别
    async performOCR() {
        const { state, elements } = utils;
        const file = elements.ocrImage.files[0];

        if (!file) {
            utils.updateStatus("Error: No image selected", 'error');
            return;
        }

        utils.updateStatus("Processing: Performing OCR on image...", 'processing');
        
        try {
            const ocrText = await api.ocrImage(file);
            elements.inputText.value = ocrText;
            utils.updateStatus(`Success: OCR completed, text imported`);
            
            // 自动分句
          //  setTimeout(() => this.processText(), 500);
        } catch (error) {
            utils.updateStatus(`Error: OCR processing failed - ${error.message}`, 'error');
        }
    },

    // 清空文本
    clearText() {
        const { state, elements } = utils;
        elements.inputText.value = '';
        utils.clearSentenceList();
        state.sentences = [];
        state.fullAudioPath = '';
        utils.updateStatus('Ready | Text cleared');
    }
};

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app.init();
});