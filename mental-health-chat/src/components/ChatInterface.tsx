'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
}

interface ChatInterfaceProps {
    userName: string;
}

interface SpeechRecognitionEvent extends Event {
    results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResult {
    [index: number]: SpeechRecognitionAlternative;
    length: number;
    item(index: number): SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
}

interface SpeechRecognitionResultList {
    [index: number]: SpeechRecognitionResult;
    length: number;
    item(index: number): SpeechRecognitionResult;
}

interface SpeechRecognitionErrorEvent extends Event {
    error: string;
    message: string;
}

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start(): void;
    stop(): void;
    abort(): void;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
    onend: ((this: SpeechRecognition, ev: Event) => any) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
}

declare global {
    interface Window {
        SpeechRecognition: new () => SpeechRecognition;
        webkitSpeechRecognition: new () => SpeechRecognition;
    }
}

export default function ChatInterface({ userName }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Add welcome message
        setMessages([
            {
                id: 'welcome',
                text: `Hello ${userName}! I'm here to listen and support you. Feel free to share what's on your mind.`,
                isUser: false,
                timestamp: new Date()
            }
        ]);

        if (typeof window !== 'undefined') {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                recognitionRef.current = new SpeechRecognition();
                recognitionRef.current.continuous = true;
                recognitionRef.current.interimResults = true;
                recognitionRef.current.lang = 'en-US';

                recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
                    const transcript = Array.from(event.results)
                        .map(result => result[0].transcript)
                        .join('');
                    setTranscript(transcript);
                };

                recognitionRef.current.onend = () => {
                    if (isListening) {
                        recognitionRef.current?.start();
                    }
                };

                recognitionRef.current.onerror = (event: Event) => {
                    const errorEvent = event as SpeechRecognitionErrorEvent;
                    setError(`Speech recognition error: ${errorEvent.error}`);
                    setIsListening(false);
                };
            } else {
                setError('Speech recognition is not supported in your browser');
            }
        }
    }, [userName]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const simulateBotResponse = async (userMessage: string) => {
        setIsTyping(true);
        // Simulate bot thinking time
        await new Promise(resolve => setTimeout(resolve, 1000));

        // In a real app, this would be replaced with your actual bot response
        const botResponse = "I understand how you're feeling. Would you like to talk more about it?";

        setMessages(prev => [...prev, {
            id: Date.now().toString(),
            text: botResponse,
            isUser: false,
            timestamp: new Date()
        }]);
        setIsTyping(false);
    };

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            if (transcript.trim()) {
                const userMessage = transcript.trim();
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    text: userMessage,
                    isUser: true,
                    timestamp: new Date()
                }]);
                setTranscript('');
                simulateBotResponse(userMessage);
            }
        } else {
            setError(null);
            recognitionRef.current?.start();
        }
        setIsListening(!isListening);
    };

    return (
        <div className="flex flex-col h-screen bg-gradient-to-b from-indigo-50 to-purple-50">
            {/* Chat Header */}
            <div className="bg-white/80 backdrop-blur-sm shadow-sm p-4 border-b border-gray-100">
                <h1 className="text-xl font-medium text-gray-800">Welcome, {userName}</h1>
                <p className="text-sm text-gray-500">I'm here to listen and support you</p>
            </div>

            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <AnimatePresence>
                    {messages.map((message) => (
                        <motion.div
                            key={message.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[70%] rounded-2xl p-4 ${message.isUser
                                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
                                    : 'bg-white/80 backdrop-blur-sm text-gray-800 shadow-sm'
                                    }`}
                            >
                                <p className="text-sm leading-relaxed">{message.text}</p>
                                <span className="text-xs opacity-70 mt-1 block">
                                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Typing Indicator */}
                {isTyping && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start"
                    >
                        <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-4 shadow-sm">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Error Message */}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl"
                    >
                        {error}
                    </motion.div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Voice Input Area */}
            <div className="bg-white/80 backdrop-blur-sm p-4 border-t border-gray-100">
                <div className="flex items-center space-x-4">
                    <div className="flex-1 bg-gray-50 rounded-xl p-4 min-h-[60px] text-gray-500">
                        {transcript || 'Click the microphone to start speaking...'}
                    </div>
                    <motion.button
                        onClick={toggleListening}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className={`p-4 rounded-full shadow-lg ${isListening
                            ? 'bg-red-500 text-white'
                            : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
                            }`}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                            />
                        </svg>
                    </motion.button>
                </div>
            </div>
        </div>
    );
} 