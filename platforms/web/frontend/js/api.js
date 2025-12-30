/**
 * 后端API请求封装
 * 所有与后端的交互都集中在这里
 */
const api = {
    // API基础地址
    baseUrl: "http://localhost:5000/api",
    audioBaseUrl: "http://localhost:5000/audio",

    /**
     * 分句接口
     * @param {string} text - 输入文本
     * @returns {Promise<{sentences: string[], count: number}>} 分句结果
     */
    async splitText(text) {
        const response = await fetch(`${this.baseUrl}/split-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || '分句失败');
        }

        return data;
    },

    /**
     * 生成单句音频
     * @param {string} sentence - 句子
     * @param {string} voice - 语音类型
     * @param {number} speed - 语速
     * @returns {Promise<string>} 音频URL
     */
    async generateSingleAudio(sentence, voice, speed) {
        const response = await fetch(`${this.baseUrl}/generate-single-audio`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sentence,
                voice,
                speed
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || '单句音频生成失败');
        }

        return `${this.audioBaseUrl}/${data.filename}`;
    },

    /**
     * 生成全文音频
     * @param {string} text - 全文文本
     * @param {string} voice - 语音类型
     * @param {number} speed - 语速
     * @returns {Promise<{audioUrl: string, sentences: string[]}>} 音频URL和分句结果
     */
    async generateFullAudio(text, voice, speed) {
        const response = await fetch(`${this.baseUrl}/generate-full-audio`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                voice,
                speed
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || '全文音频生成失败');
        }

        return {
            audioUrl: `${this.audioBaseUrl}/${data.filename}`,
            sentences: data.sentences
        };
    },

    /**
     * OCR识别
     * @param {File} imageFile - 图片文件
     * @returns {Promise<string>} 识别后的文本
     */
    async ocrImage(imageFile) {
        const formData = new FormData();
        formData.append('image', imageFile);

        const response = await fetch(`${this.baseUrl}/ocr-image`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'OCR识别失败');
        }

        return data.text;
    }
};