/**
 * Web Audio API 商業級動態音效合成器與 2D 空間定位系統 (Commercial Procedural & Spatial Sound Engine)
 * 支援 Master / BGM / SFX 三組獨立聲道控制，並根據攝影機與發聲源世界座標進行 2D 立體聲相位定位 (Stereo Panning)。
 */
export class SoundEngine {
    constructor() {
        this.ctx = null;
        this.isMuted = false;
        this.bgOsc = null;
        this.bgGain = null;
        this.initialized = false;

        // 讀取本地保存的音量設定 (0.0 ~ 1.0)
        this.masterVol = parseFloat(localStorage.getItem('BW_VOL_MASTER') ?? '1.0');
        this.bgmVol = parseFloat(localStorage.getItem('BW_VOL_BGM') ?? '0.7');
        this.sfxVol = parseFloat(localStorage.getItem('BW_VOL_SFX') ?? '0.9');

        this.masterGainNode = null;
        this.bgmGainNode = null;
        this.sfxGainNode = null;

        this.initOnUserAction();
    }

    init() {
        if (!this.initialized) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
                this.initialized = true;

                // 建立三組商用聲道架構 (Master -> Destination, BGM/SFX -> Master)
                this.masterGainNode = this.ctx.createGain();
                this.masterGainNode.gain.value = this.isMuted ? 0 : this.masterVol;
                this.masterGainNode.connect(this.ctx.destination);

                this.bgmGainNode = this.ctx.createGain();
                this.bgmGainNode.gain.value = this.bgmVol;
                this.bgmGainNode.connect(this.masterGainNode);

                this.sfxGainNode = this.ctx.createGain();
                this.sfxGainNode.gain.value = this.sfxVol;
                this.sfxGainNode.connect(this.masterGainNode);

                this.startBackgroundDrone(0);
            }
        } else if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    /**
     * 瀏覽器自動播放限制處理：在玩家第一次互動時啟動 AudioContext
     */
    initOnUserAction() {
        const initAudio = () => {
            this.init();
            window.removeEventListener('click', initAudio);
            window.removeEventListener('keydown', initAudio);
        };

        window.addEventListener('click', initAudio);
        window.addEventListener('keydown', initAudio);
    }

    setMasterVolume(vol) {
        this.masterVol = Math.max(0, Math.min(1, vol));
        localStorage.setItem('BW_VOL_MASTER', this.masterVol);
        if (this.masterGainNode && this.ctx) {
            this.masterGainNode.gain.setTargetAtTime(this.isMuted ? 0 : this.masterVol, this.ctx.currentTime, 0.1);
        }
    }

    setBgmVolume(vol) {
        this.bgmVol = Math.max(0, Math.min(1, vol));
        localStorage.setItem('BW_VOL_BGM', this.bgmVol);
        if (this.bgmGainNode && this.ctx) {
            this.bgmGainNode.gain.setTargetAtTime(this.bgmVol, this.ctx.currentTime, 0.1);
        }
    }

    setSfxVolume(vol) {
        this.sfxVol = Math.max(0, Math.min(1, vol));
        localStorage.setItem('BW_VOL_SFX', this.sfxVol);
        if (this.sfxGainNode && this.ctx) {
            this.sfxGainNode.gain.setTargetAtTime(this.sfxVol, this.ctx.currentTime, 0.1);
        }
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        if (this.masterGainNode && this.ctx) {
            this.masterGainNode.gain.setTargetAtTime(this.isMuted ? 0 : this.masterVol, this.ctx.currentTime, 0.1);
        }
        return this.isMuted;
    }

    /**
     * 取得 2D 空間定位節點 (根據聲音來源與攝影機距離計算左右聲道 Pan)
     */
    getSfxDestination(worldX, cameraX = 1000) {
        if (!this.ctx || !this.sfxGainNode) return this.ctx ? this.ctx.destination : null;
        if (typeof worldX === 'number' && typeof this.ctx.createStereoPanner === 'function') {
            const panner = this.ctx.createStereoPanner();
            // 螢幕寬度約 1200 像素，計算相對中心偏移 [-1, 1]
            const panVal = Math.max(-1, Math.min(1, (worldX - cameraX) / 600));
            panner.pan.setValueAtTime(panVal, this.ctx.currentTime);
            panner.connect(this.sfxGainNode);
            return panner;
        }
        return this.sfxGainNode;
    }

    /**
     * 播放背景神聖/暗黑氛圍和弦 (連接至 BGM 聲道)
     */
    startBackgroundDrone(alignment = 0) {
        if (!this.ctx || this.isMuted || this.bgOsc || !this.bgmGainNode) return;
        try {
            this.bgOsc = this.ctx.createOscillator();
            this.bgGain = this.ctx.createGain();
            
            const freq = alignment >= 0 ? 130.81 : 87.31; // C3 vs F2
            this.bgOsc.type = alignment >= 0 ? 'sine' : 'sawtooth';
            this.bgOsc.frequency.setValueAtTime(freq, this.ctx.currentTime);
            
            const filter = this.ctx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(alignment >= 0 ? 400 : 200, this.ctx.currentTime);

            this.bgGain.gain.setValueAtTime(0.01, this.ctx.currentTime);
            this.bgGain.gain.linearRampToValueAtTime(0.05, this.ctx.currentTime + 3);

            this.bgOsc.connect(filter);
            filter.connect(this.bgGain);
            this.bgGain.connect(this.bgmGainNode);
            this.bgOsc.start();
        } catch (e) {
            console.warn("Background audio start failed:", e);
        }
    }

    updateBackgroundTheme(alignment) {
        if (!this.ctx || !this.bgOsc) return;
        const freq = alignment >= 0 ? 130.81 + (alignment * 0.5) : 87.31 - (Math.abs(alignment) * 0.3);
        this.bgOsc.type = alignment >= 0 ? 'sine' : 'sawtooth';
        this.bgOsc.frequency.setTargetAtTime(Math.max(40, freq), this.ctx.currentTime, 2);
    }

    createNoiseBuffer(duration = 1.0) {
        if (!this.ctx) return null;
        const sampleRate = this.ctx.sampleRate;
        const buffer = this.ctx.createBuffer(1, sampleRate * duration, sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < sampleRate * duration; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        return buffer;
    }

    /**
     * 播放雷電神力特效音 (附帶 2D 空間定位)
     */
    playThunder(worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const noiseBuffer = this.createNoiseBuffer(1.5);
        const noise = this.ctx.createBufferSource();
        noise.buffer = noiseBuffer;

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(800, this.ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(50, this.ctx.currentTime + 1.2);

        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.8, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 1.4);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(dest);

        noise.start();
    }

    /**
     * 播放火球轟炸音效
     */
    playFireball(worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const noiseBuffer = this.createNoiseBuffer(1.0);
        const noise = this.ctx.createBufferSource();
        noise.buffer = noiseBuffer;

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(300, this.ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(1500, this.ctx.currentTime + 0.3);
        filter.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + 0.9);

        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.6, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.9);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(dest);

        noise.start();
    }

    playHeal(worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, index) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime + index * 0.1);
            
            gain.gain.setValueAtTime(0, this.ctx.currentTime + index * 0.1);
            gain.gain.linearRampToValueAtTime(0.2, this.ctx.currentTime + index * 0.1 + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + index * 0.1 + 0.6);

            osc.connect(gain);
            gain.connect(dest);
            osc.start(this.ctx.currentTime + index * 0.1);
            osc.stop(this.ctx.currentTime + index * 0.1 + 0.65);
        });
    }

    playSacrifice(worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(300, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.4);

        gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.45);

        osc.connect(gain);
        gain.connect(dest);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.5);
    }

    playCreatureRoar(pitchMod = 1.0, worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        
        const baseFreq = 120 * pitchMod;
        osc.frequency.setValueAtTime(baseFreq * 1.5, this.ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(baseFreq * 0.8, this.ctx.currentTime + 0.5);
        osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.4, this.ctx.currentTime + 0.8);

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(600, this.ctx.currentTime);

        gain.gain.setValueAtTime(0.4, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.85);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(dest);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.9);
    }

    playPet(worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, this.ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(880, this.ctx.currentTime + 0.25);

        gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.3);

        osc.connect(gain);
        gain.connect(dest);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.35);
    }

    playSlap(worldX, cameraX) {
        if (!this.ctx || this.isMuted) return;
        const dest = this.getSfxDestination(worldX, cameraX);
        const noiseBuffer = this.createNoiseBuffer(0.15);
        const noise = this.ctx.createBufferSource();
        noise.buffer = noiseBuffer;

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'highpass';
        filter.frequency.setValueAtTime(500, this.ctx.currentTime);

        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.7, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.15);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(dest);
        noise.start();
    }

    playMiracleCast() {
        if (!this.ctx || this.isMuted) return;
        const dest = this.sfxGainNode || this.ctx.destination;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1760, this.ctx.currentTime + 0.3);

        gain.gain.setValueAtTime(0.25, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.35);

        osc.connect(gain);
        gain.connect(dest);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.4);
    }
}
