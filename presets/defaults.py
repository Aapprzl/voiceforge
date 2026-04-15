"""Built-in preset definitions for VoiceForge"""

PRESETS = {
    "streaming": {
        "name": "Streaming",
        "description": "Optimized for gaming streams - aggressive noise reduction with presence boost",
        "NoiseGate": {
            "enabled": True,
            "threshold_db": -35.0,
            "attack_ms": 5.0,
            "release_ms": 50.0
        },
        "NoiseRemoval": {
            "enabled": True,
            "strength": 0.8
        },
        "Compressor": {
            "enabled": True,
            "threshold_db": -18.0,
            "ratio": 4.0,
            "attack_ms": 5.0,
            "release_ms": 80.0
        },
        "Equalizer10Band": {
            "enabled": True,
            "bands": {
                "31Hz": 0,
                "63Hz": 0,
                "125Hz": 0,
                "250Hz": -2,
                "500Hz": 0,
                "1000Hz": 2,
                "2000Hz": 4,
                "4000Hz": 4,
                "8000Hz": 2,
                "16000Hz": 0
            }
        },
        "VoiceEnhancer": {
            "enabled": True,
            "warmth_enabled": True,
            "warmth_intensity": 0.3,
            "presence_enabled": True,
            "presence_intensity": 0.7,
            "deesser_enabled": False,
            "deesser_intensity": 0.5,
            "harmonic_enabled": False,
            "harmonic_intensity": 0.3
        },
        "AutoLeveler": {
            "enabled": True,
            "target_db": -18.0
        },
        "Limiter": {
            "enabled": True
        }
    },
    
    "podcast": {
        "name": "Podcast",
        "description": "Warm and clear - perfect for long-form spoken content",
        "NoiseGate": {
            "enabled": True,
            "threshold_db": -45.0,
            "attack_ms": 15.0,
            "release_ms": 150.0
        },
        "NoiseRemoval": {
            "enabled": True,
            "strength": 0.6
        },
        "Compressor": {
            "enabled": True,
            "threshold_db": -22.0,
            "ratio": 3.0,
            "attack_ms": 15.0,
            "release_ms": 120.0
        },
        "Equalizer10Band": {
            "enabled": True,
            "bands": {
                "31Hz": 0,
                "63Hz": 2,
                "125Hz": 3,
                "250Hz": 4,
                "500Hz": 2,
                "1000Hz": 0,
                "2000Hz": 2,
                "4000Hz": 3,
                "8000Hz": 1,
                "16000Hz": 0
            }
        },
        "VoiceEnhancer": {
            "enabled": True,
            "warmth_enabled": True,
            "warmth_intensity": 0.6,
            "presence_enabled": True,
            "presence_intensity": 0.5,
            "deesser_enabled": True,
            "deesser_intensity": 0.5,
            "harmonic_enabled": True,
            "harmonic_intensity": 0.3
        },
        "AutoLeveler": {
            "enabled": True,
            "target_db": -18.0
        },
        "Limiter": {
            "enabled": True
        }
    },
    
    "gaming": {
        "name": "Gaming",
        "description": "Low latency mode - minimal processing for competitive gaming",
        "NoiseGate": {
            "enabled": True,
            "threshold_db": -30.0,
            "attack_ms": 3.0,
            "release_ms": 30.0
        },
        "NoiseRemoval": {
            "enabled": True,
            "strength": 0.4
        },
        "Compressor": {
            "enabled": True,
            "threshold_db": -15.0,
            "ratio": 2.5,
            "attack_ms": 3.0,
            "release_ms": 50.0
        },
        "Equalizer10Band": {
            "enabled": True,
            "bands": {
                "31Hz": 0,
                "63Hz": 0,
                "125Hz": 0,
                "250Hz": 0,
                "500Hz": 0,
                "1000Hz": 2,
                "2000Hz": 1,
                "4000Hz": 1,
                "8000Hz": 0,
                "16000Hz": 0
            }
        },
        "VoiceEnhancer": {
            "enabled": True,
            "warmth_enabled": False,
            "warmth_intensity": 0.5,
            "presence_enabled": True,
            "presence_intensity": 0.4,
            "deesser_enabled": False,
            "deesser_intensity": 0.5,
            "harmonic_enabled": False,
            "harmonic_intensity": 0.3
        },
        "AutoLeveler": {
            "enabled": False,
            "target_db": -18.0
        },
        "Limiter": {
            "enabled": True
        }
    }
}
